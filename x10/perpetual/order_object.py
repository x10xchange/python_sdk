from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional, Tuple

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import StarknetDomain
from x10.perpetual.fees import DEFAULT_FEES, TradingFeeModel
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object_settlement import (
    SettlementDataCtx,
    create_order_settlement_data,
)
from x10.perpetual.orders import (
    CreateOrderTpslTriggerModel,
    NewOrderModel,
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    OrderType,
    SelfTradeProtectionLevel,
    TimeInForce,
)
from x10.utils.date import to_epoch_millis, utc_now
from x10.utils.nonce import generate_nonce
from x10.utils.order import calc_entire_position_size


@dataclass(kw_only=True)
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
    builder_fee: Optional[Decimal] = None,
    builder_id: Optional[int] = None,
    reduce_only: bool = False,
    tp_sl_type: Optional[OrderTpslType] = None,
    take_profit: Optional[OrderTpslTriggerParam] = None,
    stop_loss: Optional[OrderTpslTriggerParam] = None,
) -> NewOrderModel:
    """
    Creates an order object to be placed on the exchange using the `place_order` method.
    """

    if expire_time is None:
        expire_time = utc_now() + timedelta(hours=1)

    fees = account.trading_fee.get(market.name, DEFAULT_FEES)

    return __create_order_object(
        market=market,
        order_type=order_type,
        synthetic_amount=amount_of_synthetic,
        price=price,
        side=side,
        collateral_position_id=account.vault,
        fees=fees,
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
        builder_fee=builder_fee,
        builder_id=builder_id,
        reduce_only=reduce_only,
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
    side: OrderSide,
    collateral_position_id: int,
    fees: TradingFeeModel,
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
    builder_fee: Optional[Decimal] = None,
    builder_id: Optional[int] = None,
    reduce_only: bool = False,
    tp_sl_type: Optional[OrderTpslType] = None,
    take_profit: Optional[OrderTpslTriggerParam] = None,
    stop_loss: Optional[OrderTpslTriggerParam] = None,
) -> NewOrderModel:
    def validate_market_order():
        if post_only:
            raise ValueError("MARKET orders must not be post-only")

        if time_in_force != TimeInForce.IOC:
            raise ValueError("MARKET orders must have `time_in_force` set to IOC")

    def validate_tpsl_order():
        if not reduce_only:
            raise ValueError("TPSL orders must be reduce-only")

        if post_only:
            raise ValueError("TPSL orders must not be post-only")

        if tp_sl_type == OrderTpslType.POSITION and synthetic_amount != Decimal(0):
            raise ValueError("`synthetic_amount` must be 0 for entire position TPSL orders")

        if price != Decimal(0):
            raise ValueError("`price` must be 0 for TPSL orders")

    if order_type not in [OrderType.LIMIT, OrderType.MARKET, OrderType.TPSL]:
        raise NotImplementedError(f"{order_type} order type is not supported yet")

    if exact_only:
        raise NotImplementedError("`exact_only` option is not supported yet")

    if time_in_force == TimeInForce.FOK:
        raise ValueError("FOK `time_in_force` value is deprecated")

    if expire_time is None:
        raise ValueError("`expire_time` must be provided")

    if order_type == OrderType.MARKET:
        validate_market_order()
    elif order_type == OrderType.TPSL:
        validate_tpsl_order()

    if nonce is None:
        nonce = generate_nonce()

    fee_rate = fees.taker_fee_rate

    settlement_data_ctx = SettlementDataCtx(
        market=market,
        fees=fees,
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
            raise ValueError("`tp_sl_type` must be provided if `take_profit` or `stop_loss` is specified")

        if trigger_param.price_type == OrderPriceType.MARKET:
            raise NotImplementedError("TPSL `MARKET` price type is not supported yet")

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
        post_only=post_only,
        time_in_force=time_in_force,
        expiry_epoch_millis=to_epoch_millis(expire_time),
        fee=fee_rate,
        self_trade_protection_level=self_trade_protection_level,
        nonce=Decimal(nonce),
        cancel_id=previous_order_external_id,
        settlement=settlement_data.settlement if order_type != OrderType.TPSL else None,
        tp_sl_type=tp_sl_type,
        take_profit=create_tpsl_trigger_model(take_profit),
        stop_loss=create_tpsl_trigger_model(stop_loss),
        debugging_amounts=settlement_data.debugging_amounts,
        builderFee=builder_fee,
        builderId=builder_id,
        reduce_only=reduce_only,
    )

    return order
