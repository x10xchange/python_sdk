import logging
from asyncio import run

from examples.utils import (
    create_trading_client,
    find_order_and_cancel,
    get_adjust_price_by_pct,
)
from x10.config import BTC_USD_MARKET
from x10.perpetual.order_object import OrderConditionalTriggerParam, create_order_object
from x10.perpetual.orders import (
    OrderPriceType,
    OrderSide,
    OrderTriggerDirection,
    OrderTriggerPriceType,
    OrderType,
    TimeInForce,
)

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def run_example():
    trading_client = create_trading_client()
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    order_size = market.trading_config.min_order_size
    order_price = adjust_price_by_pct(market.market_stats.bid_price, -15.0)
    order_trigger_price = adjust_price_by_pct(market.market_stats.bid_price, -10.0)

    LOGGER.info("Creating CONDITIONAL order object for market: %s", market.name)

    new_order = create_order_object(
        account=trading_client.stark_account,
        order_type=OrderType.CONDITIONAL,
        starknet_domain=trading_client.config.starknet_domain,
        market=market,
        side=OrderSide.BUY,
        amount_of_synthetic=order_size,
        price=market.trading_config.round_price(order_price),
        time_in_force=TimeInForce.GTT,
        reduce_only=False,
        post_only=True,
        trigger=OrderConditionalTriggerParam(
            trigger_price=order_trigger_price,
            trigger_price_type=OrderTriggerPriceType.LAST,
            direction=OrderTriggerDirection.DOWN,
            execution_price_type=OrderPriceType.LIMIT,
        ),
    )

    LOGGER.info("Placing order...")

    placed_order = await trading_client.orders.place_order(order=new_order)

    LOGGER.info("Order is placed: %s", placed_order.to_pretty_json())

    await find_order_and_cancel(trading_client=trading_client, logger=LOGGER, order_id=placed_order.data.id)


if __name__ == "__main__":
    run(main=run_example())
