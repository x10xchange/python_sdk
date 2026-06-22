import decimal
from datetime import timedelta

from x10.config import StarknetDomain
from x10.core.amount import InternalAmount, StarkAmount
from x10.core.stark_account import StarkPerpetualAccount
from x10.models.asset import AssetModel
from x10.models.base import SettlementSignatureModel
from x10.models.order import LimitOrderSettlementModel
from x10.signing.order_object_settlement import (
    SETTLEMENT_EXPIRATION_BUFFER_DAYS,
    hash_limit_order,
)
from x10.utils.date import calc_settlement_expiration, utc_now
from x10.utils.nonce import generate_nonce


def create_limit_order_settlement_data(
    *,
    quote_amount,
    base_amount,
    position_id,
    quote_asset_model: AssetModel,
    base_asset_model: AssetModel,
    starknet_account: StarkPerpetualAccount,
    starknet_domain: StarknetDomain,
    is_buy: bool,
):
    quote_asset = quote_asset_model.to_settlement_asset()
    base_asset = base_asset_model.to_settlement_asset()

    quote_amount_internal = InternalAmount(
        asset=quote_asset,
        value=-quote_amount if is_buy else quote_amount,
    )
    base_amount_internal = InternalAmount(
        asset=base_asset,
        value=base_amount if is_buy else -base_amount,
    )

    quote_amount_stark = quote_amount_internal.to_stark_amount(decimal.Context(rounding=decimal.ROUND_UP))
    base_amount_stark = base_amount_internal.to_stark_amount(decimal.Context(rounding=decimal.ROUND_UP))

    nonce = generate_nonce()
    expire_time = utc_now() + timedelta(hours=1)
    order_hash = hash_limit_order(
        amount_base=base_amount_stark,
        amount_quote=quote_amount_stark,
        max_fee=StarkAmount(0, quote_asset),
        nonce=nonce,
        position_id=position_id,
        expiration_timestamp=expire_time,
        public_key=starknet_account.public_key,
        starknet_domain=starknet_domain,
    )
    order_signature = starknet_account.sign(order_hash)

    settlement = LimitOrderSettlementModel(
        base_amount=base_amount_stark.value,
        quote_amount=quote_amount_stark.value,
        fee_amount=0,
        base_asset_id=int(base_asset.starkex_id, 16),
        quote_asset_id=int(quote_asset.starkex_id, 16),
        fee_asset_id=int(quote_asset.starkex_id, 16),
        expiration_timestamp=calc_settlement_expiration(SETTLEMENT_EXPIRATION_BUFFER_DAYS, expire_time),
        nonce=nonce,
        receiver_position_id=position_id,
        sender_position_id=position_id,
        signature=SettlementSignatureModel(r=order_signature[0], s=order_signature[1]),
    )

    return settlement, quote_amount_internal, base_amount_internal
