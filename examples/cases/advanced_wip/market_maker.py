import asyncio
import datetime
import logging
import random
from decimal import Decimal
from typing import Any, Awaitable, Callable, Coroutine, Dict

from examples.utils import create_trading_client
from x10.config import BTC_USD_MARKET
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG, TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook, OrderBookEntry
from x10.perpetual.orders import OrderSide
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient

LOGGER = logging.getLogger()
ENDPOINT_CONFIG = MAINNET_CONFIG
MARKET_NAME = BTC_USD_MARKET
NUM_PRICE_LEVELS = 2
PRICE_OFFSET_PER_LEVEL_PCT = Decimal("0.3")


async def create_orders_task(
    *,
    level: int,
    side: OrderSide,
    get_best_price: Callable[[], Awaitable[OrderBookEntry | None]],
):
    trading_client = create_trading_client(ENDPOINT_CONFIG)
    markets_dict = await trading_client.markets_info.get_markets_dict()

    market = markets_dict[MARKET_NAME]

    prev_order_id: int | None = None
    prev_order_price: Decimal | None = None

    price_offset_for_level_percent = PRICE_OFFSET_PER_LEVEL_PCT * (level + 1)

    while True:
        best_price = await get_best_price()

        if best_price is None:
            continue

        LOGGER.info("Creating %s orders task for level %s (best price is %s)", side, level, best_price)

        offset_direction = Decimal(1 if side == OrderSide.SELL else -1)

        current_price = best_price.price
        target_price = market.trading_config.round_price(
            current_price + offset_direction * current_price * (price_offset_for_level_percent / Decimal("100"))
        )

        current_delta = abs(((prev_order_price - current_price) / current_price)) if prev_order_price is not None else 0
        target_delta = price_offset_for_level_percent / Decimal("100")

        min_delta_required = target_delta - target_delta * PRICE_OFFSET_PER_LEVEL_PCT * (
            Decimal(1) + Decimal(level) / Decimal(NUM_PRICE_LEVELS)
        )
        max_delta_allowed = target_delta + target_delta * PRICE_OFFSET_PER_LEVEL_PCT / (
            Decimal(1) + Decimal(level) / Decimal(NUM_PRICE_LEVELS)
        )

        if prev_order_price is not None and (min_delta_required <= current_delta <= max_delta_allowed):
            continue

        LOGGER.info("Repricing %s order for level %s: %s -> %s",side, level, current_price, target_price)
#                 print(f"Repricing {side} order from {prev_order_price} to {target_price}, price level {i}")
#                 if prev_order_id is not None:
#                     print(f"Cancelling previous order {prev_order_id}")
#                     asyncio.create_task(
#                         root_trading_client.orders.cancel_order_by_external_id(order_external_id=str(prev_order_id))
#                     )
#                 new_id = random.randint(0, 10000000000000000000000000)
#                 print(f"Placing {side} order {new_id} at {target_price}, price level {i}")
#                 try:
#                     await root_trading_client.place_order(
#                         market_name=market.name,
#                         amount_of_synthetic=market.trading_config.min_order_size,
#                         price=target_price,
#                         side=side,
#                         external_id=str(new_id),
#                         post_only=True,
#                     )
#                 except Exception as e:
#                     print(f"Error placing order {new_id} at {target_price}, price level {i}: {e}")
#                     continue
#                 prev_order_id = new_id
#                 prev_order_price = target_price


async def run_example():
    trading_client = create_trading_client(ENDPOINT_CONFIG)
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
        ENDPOINT_CONFIG,
        market.name,
        start=True,
        best_ask_change_callback=on_best_ask_change,
        best_bid_change_callback=on_best_bid_change,
    )

    async def get_best_ask():
        async with best_ask_condition:
            await best_ask_condition.wait()
            return orderbook.best_ask()

    async def get_best_bid():
        async with best_bid_condition:
            await best_bid_condition.wait()
            return orderbook.best_bid()

    create_orders_tasks = []

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

    # FIXME
    # while True:
    try:
        await asyncio.gather(*create_orders_tasks)
        await asyncio.sleep(30)
    except Exception as e:
        LOGGER.error(e)


if __name__ == "__main__":
    asyncio.run(run_example())
