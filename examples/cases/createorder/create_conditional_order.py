import logging
from asyncio import run

from examples.utils import (
    BTC_USD_MARKET,
    create_rest_client,
    find_order_and_cancel,
    get_adjust_price_by_pct,
)
from x10.models.order import (
    OrderPriceType,
    OrderSide,
    OrderTriggerDirection,
    OrderTriggerPriceType,
    OrderType,
    TimeInForce,
)
from x10.perpetual.order_object import OrderConditionalTriggerParam, create_order_object

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def run_example():
    rest_client = create_rest_client()
    markets_dict = await rest_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    order_size = market.trading_config.min_order_size
    order_trigger_price = adjust_price_by_pct(market.market_stats.bid_price, -10.0)
    order_price = adjust_price_by_pct(order_trigger_price, -5.0)

    LOGGER.info("Creating CONDITIONAL order object for market: %s", market.name)

    new_order = create_order_object(
        account=rest_client.stark_account,
        order_type=OrderType.CONDITIONAL,
        starknet_domain=rest_client.config.signing.starknet_domain,
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

    placed_order = await rest_client.orders.place_order(order=new_order)

    LOGGER.info("Order is placed: %s", placed_order.to_pretty_json())

    await find_order_and_cancel(rest_client=rest_client, logger=LOGGER, order_id=placed_order.data.id)


if __name__ == "__main__":
    run(main=run_example())
