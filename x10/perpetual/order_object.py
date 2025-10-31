from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional, Tuple

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import StarknetDomain
from x10.perpetual.fees import DEFAULT_FEES, TradingFeeModel
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object_settlement import (
    OrderSettlementData,
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


@dataclass(kw_only=True)
class OrderTpslTriggerParam:
    trigger_price: Decimal
    trigger_price_type: OrderTriggerPriceType
    price: Decimal
    price_type: OrderPriceType


def create_order_object(
    account: StarkPerpetualAccount,
    market: MarketModel,
    amount_of_synthetic: Decimal,
    price: Decimal,
    side: OrderSide,
    starknet_domain: StarknetDomain,
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


def __create_order_tpsl_trigger_model(trigger_param: OrderTpslTriggerParam, settlement_data: OrderSettlementData):
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
    if side not in OrderSide:
        raise ValueError(f"Unexpected order side value: {side}")

    if time_in_force not in TimeInForce or time_in_force == TimeInForce.FOK:
        raise ValueError(f"Unexpected time in force value: {time_in_force}")

    if expire_time is None:
        raise ValueError("`expire_time` must be provided")

    if exact_only:
        raise NotImplementedError("`exact_only` option is not supported yet")

    if tp_sl_type == OrderTpslType.POSITION:
        raise NotImplementedError("`POSITION` TPSL type is not supported yet")

    if (take_profit and take_profit.price_type == OrderPriceType.MARKET) or (
        stop_loss and stop_loss.price_type == OrderPriceType.MARKET
    ):
        raise NotImplementedError("TPSL `MARKET` price type is not supported yet")

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
    tp_trigger_model = (
        __create_order_tpsl_trigger_model(
            take_profit,
            create_order_settlement_data(
                side=__get_opposite_side(side),
                synthetic_amount=synthetic_amount,
                price=take_profit.price,
                ctx=settlement_data_ctx,
            ),
        )
        if take_profit
        else None
    )
    sl_trigger_model = (
        __create_order_tpsl_trigger_model(
            stop_loss,
            create_order_settlement_data(
                side=__get_opposite_side(side),
                synthetic_amount=synthetic_amount,
                price=stop_loss.price,
                ctx=settlement_data_ctx,
            ),
        )
        if stop_loss
        else None
    )

    order_id = str(settlement_data.order_hash) if order_external_id is None else order_external_id
    order = NewOrderModel(
        id=order_id,
        market=market.name,
        type=OrderType.LIMIT,
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
        settlement=settlement_data.settlement,
        tp_sl_type=tp_sl_type,
        take_profit=tp_trigger_model,
        stop_loss=sl_trigger_model,
        debugging_amounts=settlement_data.debugging_amounts,
        builderFee=builder_fee,
        builderId=builder_id,
        reduce_only=reduce_only,
    )

    return order
