import math
from datetime import timedelta
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.amounts import HumanReadableAmount
from x10.perpetual.markets import MarketModel
from x10.perpetual.transfers import PerpetualTransferModel, StarkTransferSettlement
from x10.utils.date import utc_now
from x10.utils.starkex import get_transfer_msg

SECONDS_IN_HOUR = 60 * 60

def create_transfer_object(
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        transferred_asset: str,
        stark_account: StarkPerpetualAccount,
        # accounts: AccountInfo[]
        market: MarketModel
):
    from_account = accounts()

    expire_time = utc_now() + timedelta(days=7)
    expire_time_with_buffer = expire_time + timedelta(days=7)
    expire_time_with_buffer_as_hours = math.ceil(expire_time_with_buffer.timestamp() / SECONDS_IN_HOUR)

    stark_amount = HumanReadableAmount(amount, market.collateral_asset)
    transfer_hash = get_transfer_msg(
        market.l2_config.collateral_id, # asset_id
        market.l2_config.collateral_id, # asset_id_fee
        to_account_public_key, # receiver_public_key
        from_account_vault_id, # sender_position_id
        to_account_vault_id, # receiver_position_id
        from_account_vault_id, # src_fee_position_id
        generate_nonce(), # nonce
        stark_amount, # amount
        0, # max_amount_fee
        expire_time_with_buffer_as_hours # expiration_timestamp
    )
    (order_signature_r, order_signature_s) = stark_account.sign(transfer_hash)

    settlement = StarkTransferSettlement(
        amount=stark_amount.to_l1_amount(),
        asset_id=market.l2_config.collateral_id,
        # expiry_epoch_millis=to_epoch_millis(expire_time),
        expiration_timestamp=expire_time_with_buffer_as_hours,
        # signature=SignatureModel(r=order_signature_r, s=order_signature_s),
        # stark_key=public_key,
        # collateral_position=Decimal(collateral_position_id),
    )

    return PerpetualTransferModel(
        from_account=from_account_id,
        to_account_id=to_account_id,
        amount=amount,
        transferred_asset=transferred_asset,
        settlement=settlement
    )
