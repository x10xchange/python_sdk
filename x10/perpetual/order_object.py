from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional, Tuple

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.amounts import (
    ROUNDING_BUY_CONTEXT,
    ROUNDING_FEE_CONTEXT,
    ROUNDING_SELL_CONTEXT,
    HumanReadableAmount,
    StarkOrderAmounts,
)
from x10.perpetual.fees import DEFAULT_FEES, TradingFeeModel
from x10.perpetual.markets import MarketModel
from x10.perpetual.orders import (
    OrderSide,
    OrderType,
    PerpetualOrderModel,
    SelfTradeProtectionLevel,
    SettlementSignatureModel,
    StarkDebuggingOrderAmountsModel,
    StarkSettlementModel,
    TimeInForce,
)
from x10.utils.date import to_epoch_millis, utc_now
from x10.utils.starkex import generate_nonce, hash_order


def create_order_object(
    account: StarkPerpetualAccount,
    market: MarketModel,
    amount_of_synthetic: Decimal,
    price: Decimal,
    side: OrderSide,
    post_only: bool = False,
    previous_order_id: Optional[str] = None,
    expire_time: Optional[datetime] = None,
    order_external_id: Optional[str] = None,
    time_in_force: TimeInForce = TimeInForce.GTT,
    self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
) -> PerpetualOrderModel:
    """
    Creates an order object to be placed on the exchange using the `place_order` method.
    """
    fees = account.trading_fee.get(market.name, DEFAULT_FEES)

    return __create_order_object(
        market,
        amount_of_synthetic,
        price,
        side,
        account.vault,
        fees,
        account.sign,
        account.public_key,
        False,
        expire_time,
        post_only=post_only,
        previous_order_external_id=previous_order_id,
        order_external_id=order_external_id,
        time_in_force=time_in_force,
        self_trade_protection_level=self_trade_protection_level,
    )


def __create_order_object(
    market: MarketModel,
    synthetic_amount: Decimal,
    price: Decimal,
    side: OrderSide,
    collateral_position_id: int,
    fees: TradingFeeModel,
    signer: Callable[[int], Tuple[int, int]],
    public_key: int,
    exact_only: bool = False,
    expire_time: Optional[datetime] = None,
    post_only: bool = False,
    previous_order_external_id: Optional[str] = None,
    order_external_id: Optional[str] = None,
    time_in_force: TimeInForce = TimeInForce.GTT,
    self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
) -> PerpetualOrderModel:
    if exact_only:
        raise NotImplementedError("`exact_only` option is not supported yet")

    if expire_time is None:
        expire_time = utc_now() + timedelta(hours=8)

    nonce = generate_nonce()
    is_buying_synthetic = side == OrderSide.BUY
    rounding_context = ROUNDING_BUY_CONTEXT if is_buying_synthetic else ROUNDING_SELL_CONTEXT

    collateral_amount_human = HumanReadableAmount(synthetic_amount * price, market.collateral_asset)
    synthetic_amount_human = HumanReadableAmount(synthetic_amount, market.synthetic_asset)

    fee = HumanReadableAmount(
        fees.taker_fee_rate * collateral_amount_human.value,
        market.collateral_asset,
    )

    amounts = StarkOrderAmounts(
        collateral_amount_internal=collateral_amount_human,
        synthetic_amount_internal=synthetic_amount_human,
        fee_amount_internal=fee,
        fee_rate=fees.taker_fee_rate,
        rounding_context=rounding_context,
    )
    debugging_amounts = StarkDebuggingOrderAmountsModel(
        collateral_amount=Decimal(amounts.collateral_amount_internal.to_stark_amount(amounts.rounding_context).value),
        fee_amount=Decimal(amounts.fee_amount_internal.to_stark_amount(ROUNDING_FEE_CONTEXT).value),
        synthetic_amount=Decimal(amounts.synthetic_amount_internal.to_stark_amount(amounts.rounding_context).value),
    )

    order_hash = hash_order(
        amounts=amounts,
        is_buying_synthetic=is_buying_synthetic,
        nonce=nonce,
        position_id=collateral_position_id,
        expiration_timestamp=expire_time,
    )

    (order_signature_r, order_signature_s) = signer(order_hash)
    settlement = StarkSettlementModel(
        signature=SettlementSignatureModel(r=order_signature_r, s=order_signature_s),
        stark_key=public_key,
        collateral_position=Decimal(collateral_position_id),
    )

    order_id = str(order_hash) if order_external_id is None else order_external_id
    order = PerpetualOrderModel(
        id=order_id,
        market=market.name,
        type=OrderType.LIMIT,
        side=side,
        qty=synthetic_amount_human.value,
        price=price,
        post_only=post_only,
        time_in_force=time_in_force,
        expiry_epoch_millis=to_epoch_millis(expire_time),
        fee=amounts.fee_rate,
        self_trade_protection_level=self_trade_protection_level,
        nonce=Decimal(nonce),
        cancel_id=previous_order_external_id,
        settlement=settlement,
        debugging_amounts=debugging_amounts,
    )

    return order
