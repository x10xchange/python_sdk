import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional, Tuple

from fast_stark_crypto import get_order_msg_hash

from x10.perpetual.amounts import (
    ROUNDING_BUY_CONTEXT,
    ROUNDING_FEE_CONTEXT,
    ROUNDING_SELL_CONTEXT,
    HumanReadableAmount,
    StarkAmount,
)
from x10.perpetual.configuration import StarknetDomain
from x10.perpetual.fees import TradingFeeModel
from x10.perpetual.markets import MarketModel
from x10.perpetual.orders import (
    OrderSide,
    StarkDebuggingOrderAmountsModel,
    StarkSettlementModel,
)
from x10.utils.model import SettlementSignatureModel


@dataclass(kw_only=True)
class OrderSettlementData:
    synthetic_amount_human: HumanReadableAmount
    order_hash: int
    settlement: StarkSettlementModel
    debugging_amounts: StarkDebuggingOrderAmountsModel


@dataclass(kw_only=True)
class SettlementDataCtx:
    market: MarketModel
    fees: TradingFeeModel
    builder_fee: Optional[Decimal]
    nonce: int
    collateral_position_id: int
    expire_time: datetime
    signer: Callable[[int], Tuple[int, int]]
    public_key: int
    starknet_domain: StarknetDomain


def __calc_settlement_expiration(expiration_timestamp: datetime):
    expire_time_with_buffer = expiration_timestamp + timedelta(days=14)
    expire_time_as_seconds = math.ceil(expire_time_with_buffer.timestamp())

    return expire_time_as_seconds


def hash_order(
    amount_synthetic: StarkAmount,
    amount_collateral: StarkAmount,
    max_fee: StarkAmount,
    nonce: int,
    position_id: int,
    expiration_timestamp: datetime,
    public_key: int,
    starknet_domain: StarknetDomain,
) -> int:
    synthetic_asset = amount_synthetic.asset
    collateral_asset = amount_collateral.asset

    return get_order_msg_hash(
        position_id=position_id,
        base_asset_id=int(synthetic_asset.settlement_external_id, 16),
        base_amount=amount_synthetic.value,
        quote_asset_id=int(collateral_asset.settlement_external_id, 16),
        quote_amount=amount_collateral.value,
        fee_amount=max_fee.value,
        fee_asset_id=int(collateral_asset.settlement_external_id, 16),
        expiration=__calc_settlement_expiration(expiration_timestamp),
        salt=nonce,
        user_public_key=public_key,
        domain_name=starknet_domain.name,
        domain_version=starknet_domain.version,
        domain_chain_id=starknet_domain.chain_id,
        domain_revision=starknet_domain.revision,
    )


def create_order_settlement_data(
    *,
    side: OrderSide,
    synthetic_amount: Decimal,
    price: Decimal,
    ctx: SettlementDataCtx,
):
    is_buying_synthetic = side == OrderSide.BUY
    rounding_context = ROUNDING_BUY_CONTEXT if is_buying_synthetic else ROUNDING_SELL_CONTEXT

    synthetic_amount_human = HumanReadableAmount(synthetic_amount, ctx.market.synthetic_asset)
    collateral_amount_human = HumanReadableAmount(synthetic_amount * price, ctx.market.collateral_asset)
    total_fee = ctx.fees.taker_fee_rate + (ctx.builder_fee if ctx.builder_fee is not None else 0)
    fee_amount_human = HumanReadableAmount(
        total_fee * collateral_amount_human.value,
        ctx.market.collateral_asset,
    )

    stark_collateral_amount: StarkAmount = collateral_amount_human.to_stark_amount(rounding_context=rounding_context)
    stark_synthetic_amount: StarkAmount = synthetic_amount_human.to_stark_amount(rounding_context=rounding_context)
    stark_fee_amount: StarkAmount = fee_amount_human.to_stark_amount(rounding_context=ROUNDING_FEE_CONTEXT)

    if is_buying_synthetic:
        stark_collateral_amount = stark_collateral_amount.negate()
    else:
        stark_synthetic_amount = stark_synthetic_amount.negate()

    debugging_amounts = StarkDebuggingOrderAmountsModel(
        collateral_amount=Decimal(stark_collateral_amount.value),
        fee_amount=Decimal(stark_fee_amount.value),
        synthetic_amount=Decimal(stark_synthetic_amount.value),
    )

    order_hash = hash_order(
        amount_synthetic=stark_synthetic_amount,
        amount_collateral=stark_collateral_amount,
        max_fee=stark_fee_amount,
        nonce=ctx.nonce,
        position_id=ctx.collateral_position_id,
        expiration_timestamp=ctx.expire_time,
        public_key=ctx.public_key,
        starknet_domain=ctx.starknet_domain,
    )

    (order_signature_r, order_signature_s) = ctx.signer(order_hash)
    settlement = StarkSettlementModel(
        signature=SettlementSignatureModel(r=order_signature_r, s=order_signature_s),
        stark_key=ctx.public_key,
        collateral_position=Decimal(ctx.collateral_position_id),
    )

    return OrderSettlementData(
        synthetic_amount_human=synthetic_amount_human,
        order_hash=order_hash,
        settlement=settlement,
        debugging_amounts=debugging_amounts,
    )
