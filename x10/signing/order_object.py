from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional, Tuple

from x10.config import StarknetDomain
from x10.core.stark_account import StarkPerpetualAccount
from x10.errors import NotSupportedError, ValidationError
from x10.models.market import MarketModel
from x10.models.order import (
    CreateOrderConditionalTriggerModel,
    CreateOrderTpslTriggerModel,
    NewOrderModel,
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerDirection,
    OrderTriggerPriceType,
    OrderType,
    SelfTradeProtectionLevel,
    TimeInForce,
)
from x10.signing.order_object_settlement import (
    SettlementDataCtx,
    create_order_settlement_data,
)
from x10.utils.date import to_epoch_millis, utc_now
from x10.utils.nonce import generate_nonce
from x10.utils.order import calc_entire_position_size

DEFAULT_TAKER_FEE = Decimal("0.0005")


@dataclass(kw_only=True, frozen=True)
class OrderConditionalTriggerParam:
    trigger_price: Decimal
    trigger_price_type: OrderTriggerPriceType
    direction: OrderTriggerDirection
    execution_price_type: OrderPriceType


@dataclass(kw_only=True, frozen=True)
class OrderTpslTriggerParam:
    trigger_price: Decimal
    trigger_price_type: OrderTriggerPriceType
    price: Decimal
    price_type: OrderPriceType


def create_order_object(
    *,
    account: StarkPerpetualAccount,
    market: MarketModel,
    amount_of_synthetic: Decimal,
    price: Decimal,
    rfq_start_price: Optional[Decimal] = None,
    side: OrderSide,
    starknet_domain: StarknetDomain,
    order_type: OrderType = OrderType.LIMIT,
    post_only: bool = False,
    previous_order_external_id: Optional[str] = None,
    expire_time: Optional[datetime] = None,
    order_external_id: Optional[str] = None,
    time_in_force: TimeInForce = TimeInForce.GTT,
    self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
    nonce: Optional[int] = None,
    taker_fee: Optional[Decimal] = None,
    builder_fee: Optional[Decimal] = None,
    builder_id: Optional[int] = None,
    reduce_only: bool = False,
    trigger: Optional[OrderConditionalTriggerParam] = None,
    tp_sl_type: Optional[OrderTpslType] = None,
    take_profit: Optional[OrderTpslTriggerParam] = None,
    stop_loss: Optional[OrderTpslTriggerParam] = None,
) -> NewOrderModel:
    """
    Creates an order object to be placed on the exchange using the `place_order` method.
    """

    if expire_time is None:
        expire_time = utc_now() + timedelta(hours=1)

    return __create_order_object(
        market=market,
        order_type=order_type,
        synthetic_amount=amount_of_synthetic,
        price=price,
        rfq_start_price=rfq_start_price,
        side=side,
        collateral_position_id=account.vault,
        signer=account.sign,
        public_key=account.public_key,
        exact_only=False,
        expire_time=expire_time,
        post_only=post_only,
        previous_order_external_id=previous_order_external_id,
        order_external_id=order_external_id,
        time_in_force=time_in_force,
        self_trade_protection_level=self_trade_protection_level,
        starknet_domain=starknet_domain,
        nonce=nonce,
        taker_fee=taker_fee,
        builder_fee=builder_fee,
        builder_id=builder_id,
        reduce_only=reduce_only,
        trigger=trigger,
        tp_sl_type=tp_sl_type,
        take_profit=take_profit,
        stop_loss=stop_loss,
    )


def __create_order_tpsl_trigger_model(
    *,
    trigger_param: OrderTpslTriggerParam,
    order_type: OrderType,
    side: OrderSide,
    synthetic_amount: Decimal,
    tp_sl_type: OrderTpslType,
    market: MarketModel,
    settlement_data_ctx: SettlementDataCtx,
):
    settlement_synthetic_amount = (
        synthetic_amount
        if tp_sl_type == OrderTpslType.ORDER
        else calc_entire_position_size(
            price=trigger_param.price,
            quantity_precision=market.trading_config.quantity_precision,
            max_position_value=market.trading_config.max_position_value,
        )
    )
    settlement_data = create_order_settlement_data(
        side=side if order_type == OrderType.TPSL else __get_opposite_side(side),
        synthetic_amount=settlement_synthetic_amount,
        price=trigger_param.price,
        ctx=settlement_data_ctx,
    )

    return CreateOrderTpslTriggerModel(
        trigger_price=trigger_param.trigger_price,
        trigger_price_type=trigger_param.trigger_price_type,
        price=trigger_param.price,
        price_type=trigger_param.price_type,
        settlement=settlement_data.settlement,
        debugging_amounts=settlement_data.debugging_amounts,
    )


def __get_opposite_side(side: OrderSide) -> OrderSide:
    return OrderSide.BUY if side == OrderSide.SELL else OrderSide.SELL


def __create_order_object(
    *,
    market: MarketModel,
    order_type: OrderType,
    synthetic_amount: Decimal,
    price: Decimal,
    rfq_start_price: Optional[Decimal] = None,
    side: OrderSide,
    collateral_position_id: int,
    signer: Callable[[int], Tuple[int, int]],
    public_key: int,
    starknet_domain: StarknetDomain,
    exact_only: bool = False,
    expire_time: Optional[datetime] = None,
    post_only: bool = False,
    previous_order_external_id: Optional[str] = None,
    order_external_id: Optional[str] = None,
    time_in_force: TimeInForce = TimeInForce.GTT,
    self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
    nonce: Optional[int] = None,
    taker_fee: Optional[Decimal] = None,
    builder_fee: Optional[Decimal] = None,
    builder_id: Optional[int] = None,
    reduce_only: bool = False,
    trigger: Optional[OrderConditionalTriggerParam] = None,
    tp_sl_type: Optional[OrderTpslType] = None,
    take_profit: Optional[OrderTpslTriggerParam] = None,
    stop_loss: Optional[OrderTpslTriggerParam] = None,
) -> NewOrderModel:
    def validate_market_order():
        if post_only:
            raise ValidationError("MARKET orders must not be post-only")

        if time_in_force != TimeInForce.IOC:
            raise ValidationError("MARKET orders must have `time_in_force` set to IOC")

    def validate_conditional_order():
        if not trigger:
            raise ValidationError("CONDITIONAL orders must have `trigger` specified")

    def validate_rfq_start_price():
        if rfq_start_price and not market.is_rfq:
            raise ValidationError("`rfq_start_price` must not be provided for non-RFQ markets")

        if rfq_start_price and order_type != OrderType.MARKET:
            raise ValidationError("`rfq_start_price` must not be provided for non-MARKET orders")

    def validate_tpsl_order():
        if not reduce_only:
            raise ValidationError("TPSL orders must be reduce-only")

        if post_only:
            raise ValidationError("TPSL orders must not be post-only")

        if tp_sl_type == OrderTpslType.POSITION and synthetic_amount != Decimal(0):
            raise ValidationError("`synthetic_amount` must be 0 for entire position TPSL orders")

        if price != Decimal(0):
            raise ValidationError("`price` must be 0 for TPSL orders")

    if order_type not in [OrderType.LIMIT, OrderType.MARKET, OrderType.CONDITIONAL, OrderType.TPSL]:
        raise NotSupportedError(f"{order_type} order type is not supported yet")

    if exact_only:
        raise NotSupportedError("`exact_only` option is not supported yet")

    if time_in_force == TimeInForce.FOK:
        raise ValidationError("FOK `time_in_force` value is deprecated")

    if time_in_force == TimeInForce.TOB and not post_only:
        raise ValidationError("`post_only` must be true for TOB `time_in_force`")

    if expire_time is None:
        raise ValidationError("`expire_time` must be provided")

    if order_type == OrderType.MARKET:
        validate_market_order()
    elif order_type == OrderType.CONDITIONAL:
        validate_conditional_order()
    elif order_type == OrderType.TPSL:
        validate_tpsl_order()

    validate_rfq_start_price()

    if nonce is None:
        nonce = generate_nonce()

    if taker_fee is None:
        taker_fee = DEFAULT_TAKER_FEE

    settlement_data_ctx = SettlementDataCtx(
        market=market,
        taker_fee=taker_fee,
        builder_fee=builder_fee,
        nonce=nonce,
        collateral_position_id=collateral_position_id,
        expire_time=expire_time,
        signer=signer,
        public_key=public_key,
        starknet_domain=starknet_domain,
    )
    settlement_data = create_order_settlement_data(
        side=side, synthetic_amount=synthetic_amount, price=price, ctx=settlement_data_ctx
    )

    def create_tpsl_trigger_model(trigger_param: OrderTpslTriggerParam | None):
        if not trigger_param:
            return None

        if tp_sl_type is None:
            raise ValidationError("`tp_sl_type` must be provided if `take_profit` and/or `stop_loss` is specified")

        return __create_order_tpsl_trigger_model(
            trigger_param=trigger_param,
            order_type=order_type,
            side=side,
            synthetic_amount=synthetic_amount,
            tp_sl_type=tp_sl_type,
            market=market,
            settlement_data_ctx=settlement_data_ctx,
        )

    order_id = str(settlement_data.order_hash) if order_external_id is None else order_external_id
    order = NewOrderModel(
        id=order_id,
        market=market.name,
        type=order_type,
        side=side,
        qty=settlement_data.synthetic_amount_human.value,
        price=price,
        rfq_start_price=rfq_start_price,
        post_only=post_only,
        time_in_force=time_in_force,
        expiry_epoch_millis=to_epoch_millis(expire_time),
        fee=taker_fee,
        self_trade_protection_level=self_trade_protection_level,
        nonce=Decimal(nonce),
        cancel_id=previous_order_external_id,
        settlement=settlement_data.settlement if order_type != OrderType.TPSL else None,
        trigger=CreateOrderConditionalTriggerModel(
            trigger_price=trigger.trigger_price,
            trigger_price_type=trigger.trigger_price_type,
            direction=trigger.direction,
            execution_price_type=trigger.execution_price_type,
        )
        if trigger
        else None,
        tp_sl_type=tp_sl_type,
        take_profit=create_tpsl_trigger_model(take_profit),
        stop_loss=create_tpsl_trigger_model(stop_loss),
        debugging_amounts=settlement_data.debugging_amounts,
        builder_fee=builder_fee,
        builder_id=builder_id,
        reduce_only=reduce_only,
    )

    return order
