import logging
from asyncio import run
from decimal import Decimal

from examples.utils import (
    create_trading_client,
    find_order_and_cancel,
    get_adjust_price_by_pct,
)
from x10.config import BTC_USD_MARKET
from x10.models.order import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    OrderType,
    TimeInForce,
)
from x10.perpetual.order_object import OrderTpslTriggerParam, create_order_object

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def run_example():
    trading_client = create_trading_client()
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    order_size = market.trading_config.min_order_size

    last_price = market.market_stats.last_price
    tp_trigger_price = adjust_price_by_pct(last_price, -5)
    tp_price = adjust_price_by_pct(tp_trigger_price, -5)
    sl_trigger_price = adjust_price_by_pct(last_price, 5)
    sl_price = adjust_price_by_pct(sl_trigger_price, 5)

    LOGGER.info("Creating partial TPSL order object for market: %s", market.name)

    new_order = create_order_object(
        account=trading_client.stark_account,
        starknet_domain=trading_client.config.starknet_domain,
        market=market,
        order_type=OrderType.TPSL,
        side=OrderSide.SELL,
        amount_of_synthetic=order_size,
        price=Decimal(0),
        time_in_force=TimeInForce.GTT,
        reduce_only=True,
        post_only=False,
        tp_sl_type=OrderTpslType.ORDER,
        take_profit=OrderTpslTriggerParam(
            trigger_price=tp_trigger_price,
            trigger_price_type=OrderTriggerPriceType.LAST,
            price=tp_price,
            price_type=OrderPriceType.LIMIT,
        ),
        stop_loss=OrderTpslTriggerParam(
            trigger_price=sl_trigger_price,
            trigger_price_type=OrderTriggerPriceType.LAST,
            price=sl_price,
            price_type=OrderPriceType.LIMIT,
        ),
    )

    LOGGER.info("Placing order...")

    placed_order = await trading_client.orders.place_order(order=new_order)

    LOGGER.info(f"Order is placed: {placed_order.to_pretty_json()}")

    await find_order_and_cancel(trading_client=trading_client, logger=LOGGER, order_id=placed_order.data.id)


if __name__ == "__main__":
    run(main=run_example())
