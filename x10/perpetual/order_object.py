import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Tuple

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
    SignatureModel,
    StarkDebuggingOrderAmountsModel,
    StarkSettlementModel,
    TimeInForce,
)
from x10.utils.date import to_epoch_millis, utc_now
from x10.utils.starkex import generate_nonce, hash_order

order_executor = ThreadPoolExecutor(thread_name_prefix="order_builder")


async def create_order_object(
    account: StarkPerpetualAccount,
    market: MarketModel,
    amount_of_synthetic: Decimal,
    price: Decimal,
    side: OrderSide,
) -> PerpetualOrderModel:
    """
    Creates an order object to be placed on the exchange using the `place_order` method.
    """
    expire_time = utc_now() + timedelta(days=7)
    fees = account.trading_fee.get(market.name, DEFAULT_FEES)
    pool = asyncio.get_event_loop()
    return await pool.run_in_executor(
        order_executor,
        __create_order_object,
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
    )


def create_order_object_sync(
    account: StarkPerpetualAccount,
    market: MarketModel,
    amount_of_synthetic: Decimal,
    price: Decimal,
    side: OrderSide,
) -> PerpetualOrderModel:
    """
    Creates an order object to be placed on the exchange using the `place_order` method.
    """
    expire_time = utc_now() + timedelta(days=7)
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
    expire_time: datetime = utc_now() + timedelta(days=7),
) -> PerpetualOrderModel:
    if exact_only:
        raise NotImplementedError("`exact_only` option is not supported yet")

    nonce = generate_nonce()
    is_buying_synthetic = side == OrderSide.BUY
    rounding_context = ROUNDING_BUY_CONTEXT if is_buying_synthetic else ROUNDING_SELL_CONTEXT

    collateral_amount_human = HumanReadableAmount(synthetic_amount * price, market.collateral_asset)
    synthetic_amount_human = HumanReadableAmount(synthetic_amount, market.synthetic_asset)

    fee = HumanReadableAmount(
        fees.taker_fee * collateral_amount_human.value,
        market.collateral_asset,
    )

    amounts = StarkOrderAmounts(
        collateral_amount_internal=collateral_amount_human,
        synthetic_amount_internal=synthetic_amount_human,
        fee_amount_internal=fee,
        fee_rate=fees.taker_fee,
        rounding_context=rounding_context,
    )

    order_hash = hash_order(
        amounts=amounts,
        is_buying_synthetic=is_buying_synthetic,
        nonce=nonce,
        position_id=collateral_position_id,
        expiration_timestamp=expire_time,
    )

    (order_signature_r, order_signature_s) = signer(order_hash)

    order = PerpetualOrderModel(
        id=str(order_hash),
        market=market.name,
        type=OrderType.LIMIT,
        side=side,
        qty=synthetic_amount_human.value,
        price=price,
        reduce_only=False,
        post_only=False,
        time_in_force=TimeInForce.GTT,
        fee=amounts.fee_rate,
        expiry_epoch_millis=to_epoch_millis(expire_time),
        settlement=StarkSettlementModel(
            signature=SignatureModel(r=order_signature_r, s=order_signature_s),
            stark_key=public_key,
            collateral_position=Decimal(collateral_position_id),
        ),
        nonce=Decimal(nonce),
        take_profit_signature=None,
        stop_loss_signature=None,
        cancel_id=None,
        trigger_price=None,
        take_profit_price=None,
        take_profit_limit_price=None,
        stop_loss_price=None,
        stop_loss_limit_price=None,
        debugging_amounts=StarkDebuggingOrderAmountsModel(
            collateral_amount=Decimal(
                amounts.collateral_amount_internal.to_stark_amount(amounts.rounding_context).value
            ),
            fee_amount=Decimal(amounts.fee_amount_internal.to_stark_amount(ROUNDING_FEE_CONTEXT).value),
            synthetic_amount=Decimal(amounts.synthetic_amount_internal.to_stark_amount(amounts.rounding_context).value),
        ),
    )

    return order
