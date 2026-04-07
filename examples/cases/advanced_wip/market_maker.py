import asyncio
import logging
import random
from decimal import Decimal
from signal import SIGINT, SIGTERM
from typing import Awaitable, Callable

from examples.utils import create_trading_client
from x10.config import BTC_USD_MARKET
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook, OrderBookEntry
from x10.perpetual.orders import OrderSide

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET
NUM_PRICE_LEVELS = 5
PRICE_OFFSET_PER_LEVEL_PCT = Decimal("0.3")


def generate_external_id():
    return str(random.randint(0, 10000000000000000000000000))


async def create_orders_task(
    *,
    level: int,
    side: OrderSide,
    get_best_price: Callable[[], Awaitable[Decimal | None]],
):
    trading_client = create_trading_client()
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]

    prev_order_external_id: str | None = None
    prev_order_price: Decimal | None = None

    price_offset_for_level_percent = PRICE_OFFSET_PER_LEVEL_PCT * (level + 1)

    try:
        while True:
            best_price = await get_best_price()

            if best_price is None:
                continue

            LOGGER.info("Creating %s orders task for level %s (best price is %s)", side, level, best_price)

            offset_direction = Decimal(1 if side == OrderSide.SELL else -1)

            current_price = best_price
            target_price = market.trading_config.round_price(
                current_price + offset_direction * current_price * (price_offset_for_level_percent / Decimal("100"))
            )

            current_delta = (
                abs(((prev_order_price - current_price) / current_price)) if prev_order_price is not None else 0
            )
            target_delta = price_offset_for_level_percent / Decimal("100")

            min_delta_required = target_delta - target_delta * PRICE_OFFSET_PER_LEVEL_PCT * (
                Decimal(1) + Decimal(level) / Decimal(NUM_PRICE_LEVELS)
            )
            max_delta_allowed = target_delta + target_delta * PRICE_OFFSET_PER_LEVEL_PCT / (
                Decimal(1) + Decimal(level) / Decimal(NUM_PRICE_LEVELS)
            )

            if prev_order_price is not None and (min_delta_required <= current_delta <= max_delta_allowed):
                continue

            LOGGER.info("Re-pricing %s order for level %s: %s -> %s", side, level, current_price, target_price)

            if prev_order_external_id is not None:
                LOGGER.info("Cancelling previous order with external id %s", prev_order_external_id)

                asyncio.create_task(
                    trading_client.orders.cancel_order_by_external_id(order_external_id=prev_order_external_id)
                )

            new_order_external_id = generate_external_id()
            new_order_size = market.trading_config.min_order_size

            try:
                await trading_client.place_order(
                    market_name=market.name,
                    amount_of_synthetic=new_order_size,
                    price=target_price,
                    side=side,
                    external_id=new_order_external_id,
                    post_only=True,
                )

                LOGGER.info(
                    "Placed %s %s@%s order for level %s",
                    side,
                    new_order_size,
                    target_price,
                    level,
                )

                prev_order_external_id = new_order_external_id
                prev_order_price = target_price
            except Exception as e:
                LOGGER.error(
                    "Error placing %s %s@%s order for level %s",
                    side,
                    new_order_size,
                    target_price,
                    level,
                    e,
                )
    except asyncio.CancelledError:
        LOGGER.info("Orders task for %s level %s cancelled, stopping...", side, level)
        raise


async def run_example():
    loop = asyncio.get_running_loop()
    create_orders_tasks = []

    def signal_handler():
        LOGGER.info("Signal received, stopping...")

        for task in create_orders_tasks:
            task.cancel()

    loop.add_signal_handler(SIGINT, signal_handler)
    loop.add_signal_handler(SIGTERM, signal_handler)

    trading_client = create_trading_client()
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]

    best_ask_condition = asyncio.Condition()
    best_bid_condition = asyncio.Condition()

    async def on_best_ask_change(best_ask: OrderBookEntry | None):
        async with best_ask_condition:
            LOGGER.info("Best ask changed: %s", best_ask)
            best_ask_condition.notify_all()

    async def on_best_bid_change(best_bid: OrderBookEntry | None):
        async with best_bid_condition:
            LOGGER.info("Best bid changed: %s", best_bid)
            best_bid_condition.notify_all()

    orderbook = await OrderBook.create(
        trading_client.config,
        market.name,
        start=True,
        best_ask_change_callback=on_best_ask_change,
        best_bid_change_callback=on_best_bid_change,
    )

    async def get_best_ask():
        async with best_ask_condition:
            await best_ask_condition.wait()
            best_entry = orderbook.best_bid()
            return best_entry.price if best_entry else None

    async def get_best_bid():
        async with best_bid_condition:
            await best_bid_condition.wait()
            best_entry = orderbook.best_bid()
            return best_entry.price if best_entry else None

    for level in range(NUM_PRICE_LEVELS):
        buy_task = create_orders_task(
            level=level,
            side=OrderSide.BUY,
            get_best_price=get_best_bid,
        )
        sell_task = create_orders_task(
            level=level,
            side=OrderSide.SELL,
            get_best_price=get_best_ask,
        )

        create_orders_tasks.append(asyncio.create_task(buy_task))
        create_orders_tasks.append(asyncio.create_task(sell_task))

    await asyncio.gather(*create_orders_tasks, return_exceptions=True)
    await orderbook.close()


if __name__ == "__main__":
    asyncio.run(run_example())
