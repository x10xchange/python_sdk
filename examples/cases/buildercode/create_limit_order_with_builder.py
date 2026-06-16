import logging.handlers
from asyncio import run

from examples.utils import (
    BTC_USD_MARKET,
    create_rest_client,
    find_order_and_cancel,
    get_adjust_price_by_pct,
    init_env,
)
from x10.models.order import OrderSide, TimeInForce
from x10.signing.order_object import create_order_object

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def run_example():
    env_config = init_env()
    builder_id = env_config.builder_id
    rest_client = create_rest_client()

    assert builder_id, "`builder_id` is not set"

    markets_dict = await rest_client.info.get_markets_dict()
    fees = await rest_client.account.get_fees(market_names=[MARKET_NAME], builder_id=builder_id)
    builder_fee = fees.data[0].builder_fee_rate

    market = markets_dict[MARKET_NAME]
    adjust_price_by_pct = get_adjust_price_by_pct(market.trading_config)

    order_size = market.trading_config.min_order_size
    order_price = adjust_price_by_pct(market.market_stats.bid_price, -10.0)

    LOGGER.info("Builder: id=%s, fee=%s", builder_id, builder_fee)
    LOGGER.info("Creating LIMIT order object for market: %s", market.name)

    new_order = create_order_object(
        account=rest_client.stark_account,
        starknet_domain=rest_client.config.signing.starknet_domain,
        market=market,
        side=OrderSide.BUY,
        amount_of_synthetic=order_size,
        price=market.trading_config.round_price(order_price),
        time_in_force=TimeInForce.GTT,
        reduce_only=False,
        post_only=True,
        builder_fee=builder_fee,
        builder_id=builder_id,
    )

    LOGGER.info("Placing order...")

    placed_order = await rest_client.orders.place_order(order=new_order)

    LOGGER.info("Order is placed: %s", placed_order.to_pretty_json())

    await find_order_and_cancel(rest_client=rest_client, logger=LOGGER, order_id=placed_order.data.id)


if __name__ == "__main__":
    run(main=run_example())
