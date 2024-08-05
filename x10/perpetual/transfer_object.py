import math
from datetime import timedelta
from decimal import Decimal
from typing import List

from x10.perpetual.accounts import AccountModel, StarkPerpetualAccount
from x10.perpetual.markets import MarketModel
from x10.perpetual.transfers import PerpetualTransferModel, StarkTransferSettlement
from x10.utils.date import utc_now
from x10.utils.model import SettlementSignatureModel
from x10.utils.starkex import generate_nonce, get_transfer_msg

SECONDS_IN_HOUR = 60 * 60
ASSET_ID_FEE = 0
MAX_AMOUNT_FEE = 0


def find_account_by_id(accounts: List[AccountModel], account_id: int):
    return next((account for account in accounts if account.account_id == account_id), None)


def calc_expiration_timestamp():
    expire_time = utc_now() + timedelta(days=7)
    expire_time_with_buffer = expire_time + timedelta(days=14)
    expire_time_with_buffer_as_hours = math.ceil(expire_time_with_buffer.timestamp() / SECONDS_IN_HOUR)

    return expire_time_with_buffer_as_hours


def create_transfer_object(
    from_account_id: int,
    to_account_id: int,
    amount: Decimal,
    transferred_asset: str,
    stark_account: StarkPerpetualAccount,
    accounts: List[AccountModel],
    market: MarketModel,
):
    from_account = find_account_by_id(accounts, from_account_id)
    to_account = find_account_by_id(accounts, to_account_id)

    expiration_timestamp = calc_expiration_timestamp()
    stark_amount = (amount * market.collateral_asset.settlement_resolution).to_integral_exact()

    nonce = generate_nonce()
    transfer_hash = get_transfer_msg(
        asset_id=int(market.l2_config.collateral_id, base=16),
        asset_id_fee=ASSET_ID_FEE,
        receiver_public_key=int(to_account.l2_key, base=16),
        sender_position_id=int(from_account.l2_vault),
        receiver_position_id=int(to_account.l2_vault),
        src_fee_position_id=int(from_account.l2_vault),
        nonce=nonce,
        amount=int(stark_amount),
        max_amount_fee=MAX_AMOUNT_FEE,
        expiration_timestamp=expiration_timestamp,
    )
    (transfer_signature_r, transfer_signature_s) = stark_account.sign(transfer_hash)

    settlement = StarkTransferSettlement(
        amount=int(stark_amount),
        asset_id=int(market.l2_config.collateral_id, base=16),
        expiration_timestamp=expiration_timestamp,
        nonce=nonce,
        receiver_position_id=int(to_account.l2_vault),
        receiver_public_key=to_account.l2_key,
        sender_position_id=int(from_account.l2_vault),
        sender_public_key=from_account.l2_key,
        signature=SettlementSignatureModel(r=transfer_signature_r, s=transfer_signature_s),
    )

    return PerpetualTransferModel(
        from_account=from_account_id,
        to_account=to_account_id,
        amount=amount,
        transferred_asset=transferred_asset,
        settlement=settlement,
    )
