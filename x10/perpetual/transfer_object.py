import math
from datetime import timedelta
from decimal import Decimal
from typing import List

from fast_stark_crypto import get_transfer_msg_hash

from x10.perpetual.accounts import AccountModel, StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig, StarknetDomain
from x10.perpetual.transfers import (
    OnChainPerpetualTransferModel,
    StarkTransferSettlement,
)
from x10.utils.date import utc_now
from x10.utils.model import SettlementSignatureModel
from x10.utils import generate_nonce

ASSET_ID_FEE = 0


def find_account_by_id(accounts: List[AccountModel], account_id: int):
    return next((account for account in accounts if account.id == account_id), None)


def calc_expiration_timestamp():
    expire_time = utc_now() + timedelta(days=7)
    expire_time_with_buffer = expire_time + timedelta(days=14)
    expire_time_with_buffer_seconds = math.ceil(expire_time_with_buffer.timestamp())
    return expire_time_with_buffer_seconds


def create_transfer_object(
    from_vault: int,
    to_vault: int,
    to_l2_key: int,
    amount: Decimal,
    config: EndpointConfig,
    stark_account: StarkPerpetualAccount,
    starknet_domain: StarknetDomain,
    nonce: int | None = None,
) -> OnChainPerpetualTransferModel:
    expiration_timestamp = calc_expiration_timestamp()
    scaled_amount = amount.scaleb(config.collateral_decimals)
    stark_amount = scaled_amount.to_integral_exact()

    if nonce is None:
        nonce = generate_nonce()

    print(f"Nonce: {hex(nonce)}")

    transfer_hash = get_transfer_msg_hash(
        recipient_position_id=to_vault,
        sender_position_id=from_vault,
        amount=int(stark_amount),
        expiration=expiration_timestamp,
        salt=nonce,
        user_public_key=stark_account.public_key,
        domain_name=starknet_domain.name,
        domain_version=starknet_domain.version,
        domain_chain_id=starknet_domain.chain_id,
        domain_revision=starknet_domain.revision,
        collateral_id=1,
    )

    print(f"Transfer hash: {transfer_hash}")

    (transfer_signature_r, transfer_signature_s) = stark_account.sign(transfer_hash)

    settlement = StarkTransferSettlement(
        amount=int(stark_amount),
        asset_id=int(config.collateral_asset_id, base=16),
        expiration_timestamp=expiration_timestamp,
        nonce=nonce,
        receiver_position_id=to_vault,
        receiver_public_key=to_l2_key,
        sender_position_id=from_vault,
        sender_public_key=stark_account.public_key,
        signature=SettlementSignatureModel(r=transfer_signature_r, s=transfer_signature_s),
    )

    return OnChainPerpetualTransferModel(
        from_vault=from_vault,
        to_vault=to_vault,
        amount=amount,
        settlement=settlement,
        transferred_asset=config.collateral_asset_id,
    )
