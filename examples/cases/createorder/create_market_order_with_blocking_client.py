import asyncio
import logging

from examples.utils import BTC_USD_MARKET, create_blocking_client
from x10.config import TESTNET_CONFIG
from x10.models.order import OrderSide, OrderType, TimeInForce
from x10.perpetual.orderbook import OrderBook
from x10.utils.order import get_price_with_slippage

LOGGER = logging.getLogger()
ENDPOINT_CONFIG = TESTNET_CONFIG
MARKET_NAME = BTC_USD_MARKET


async def get_orderbook_best_ask(market_name: str):
    best_ask_condition = asyncio.Condition()

    async def best_ask_initialised(_best_ask):
        async with best_ask_condition:
            best_ask_condition.notify_all()

    orderbook = await OrderBook.create(
        ENDPOINT_CONFIG,
        market_name=market_name,
        start=True,
        best_ask_change_callback=best_ask_initialised,
        best_bid_change_callback=None,
    )

    async with best_ask_condition:
        await best_ask_condition.wait()

    result = orderbook.best_ask()

    await orderbook.close()

    return result


async def run_example():
    blocking_client = create_blocking_client(ENDPOINT_CONFIG)
    markets = await blocking_client.get_markets()
    market = markets[MARKET_NAME]

    LOGGER.info("Waiting for the orderbook best ASK price for market: %s", market.name)

    best_ask_entry = await get_orderbook_best_ask(market.name)

    if best_ask_entry is None:
        raise ValueError("Best ASK orderbook entry is empty")

    order_side = OrderSide.BUY
    order_size = market.trading_config.min_order_size
    order_price = get_price_with_slippage(
        side=order_side,
        price=best_ask_entry.price,
        min_price_change=market.trading_config.min_price_change,
        slippage=blocking_client.config.defaults.market_price_slippage,
    )

    LOGGER.info("Creating MARKET order for market %s: %s@%s", market.name, order_size, order_price)

    placed_order = await blocking_client.create_and_place_order(
        market_name=market.name,
        order_type=OrderType.MARKET,
        side=order_side,
        amount_of_synthetic=order_size,
        price=order_price,
        time_in_force=TimeInForce.IOC,
        reduce_only=False,
        post_only=False,
        taker_fee=blocking_client.config.defaults.taker_fee,
    )

    await blocking_client.close()

    LOGGER.info("Order is placed: %s", placed_order.to_pretty_json())
    LOGGER.warning("Don't forget to reduce/close your position!")


if __name__ == "__main__":
    asyncio.run(main=run_example())
