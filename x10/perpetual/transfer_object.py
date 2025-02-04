import math
from datetime import timedelta
from decimal import Decimal
from typing import List

from x10.perpetual.accounts import AccountModel, StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.transfers import (
    OnChainPerpetualTransferModel,
    StarkTransferSettlement,
)
from x10.utils.date import utc_now
from x10.utils.model import SettlementSignatureModel
from x10.utils.starkex import generate_nonce, get_transfer_msg

SECONDS_IN_HOUR = 60 * 60
ASSET_ID_FEE = 0
MAX_AMOUNT_FEE = 0


def find_account_by_id(accounts: List[AccountModel], account_id: int):
    return next((account for account in accounts if account.id == account_id), None)


def calc_expiration_timestamp():
    expire_time = utc_now() + timedelta(days=7)
    expire_time_with_buffer = expire_time + timedelta(days=14)
    expire_time_with_buffer_as_hours = math.ceil(expire_time_with_buffer.timestamp() / SECONDS_IN_HOUR)

    return expire_time_with_buffer_as_hours


def create_transfer_object(
    from_vault: int,
    from_l2_key: str,
    to_vault: int,
    to_l2_key: str,
    amount: Decimal,
    config: EndpointConfig,
    stark_account: StarkPerpetualAccount,
) -> OnChainPerpetualTransferModel:
    expiration_timestamp = calc_expiration_timestamp()
    scaled_amount = amount.scaleb(config.collateral_decimals)
    stark_amount = scaled_amount.to_integral_exact()

    nonce = generate_nonce()
    transfer_hash = get_transfer_msg(
        asset_id=int(config.collateral_asset_on_chain_id, base=16),
        asset_id_fee=ASSET_ID_FEE,
        sender_position_id=from_vault,
        receiver_position_id=to_vault,
        receiver_public_key=int(to_l2_key, base=16),
        src_fee_position_id=from_vault,
        nonce=nonce,
        amount=int(stark_amount),
        max_amount_fee=MAX_AMOUNT_FEE,
        expiration_timestamp=expiration_timestamp,
    )
    (transfer_signature_r, transfer_signature_s) = stark_account.sign(transfer_hash)

    settlement = StarkTransferSettlement(
        amount=int(stark_amount),
        asset_id=int(config.collateral_asset_on_chain_id, base=16),
        expiration_timestamp=expiration_timestamp,
        nonce=nonce,
        receiver_position_id=to_vault,
        receiver_public_key=int(to_l2_key, 16),
        sender_position_id=from_vault,
        sender_public_key=from_l2_key if isinstance(from_l2_key, int) else int(from_l2_key, 16),
        signature=SettlementSignatureModel(r=transfer_signature_r, s=transfer_signature_s),
    )

    return OnChainPerpetualTransferModel(
        from_vault=from_vault,
        to_vault=to_vault,
        amount=amount,
        settlement=settlement,
        transferred_asset=config.collateral_asset_on_chain_id,
    )
