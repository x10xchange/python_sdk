import asyncio
import datetime
import random
from decimal import Decimal
from typing import Dict

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient


async def build_markets_cache(trading_client: PerpetualTradingClient):
    markets = await trading_client.markets_info.get_markets()
    assert markets.data is not None
    return {m.name: m for m in markets.data}


# flake8: noqa
async def on_board_example():
    environment_config = MAINNET_CONFIG

    root_trading_client = PerpetualTradingClient(
        environment_config,
        StarkPerpetualAccount(
            vault=200027,
            private_key="<>",
            public_key="<>",
            api_key="<>",
        ),
    )

    markets = await build_markets_cache(root_trading_client)
    market = markets["APEX-USD"]

    best_ask_condition = asyncio.Condition()
    best_bid_condition = asyncio.Condition()

    async def react_to_best_ask_change(best_ask):
        async with best_ask_condition:
            print(f"Best ask changed: {best_ask}")
            best_ask_condition.notify_all()

    async def react_to_best_bid_change(best_bid):
        async with best_bid_condition:
            print(f"Best bid changed: {best_bid}")
            best_bid_condition.notify_all()

    order_book = await OrderBook.create(
        MAINNET_CONFIG,
        market.name,
        start=True,
        best_ask_change_callback=react_to_best_ask_change,
        best_bid_change_callback=react_to_best_bid_change,
    )

    tasks = []
    price_offset_per_level_percent = Decimal("0.3")
    num_of_price_levels = 2

    cancelled_orders: Dict[str, datetime.datetime] = {}

    for i in range(num_of_price_levels):

        async def task(i: int, side: OrderSide):
            price_offset_for_level_percent = price_offset_per_level_percent * Decimal(i + 1)
            prev_order_id: int | None = None
            prev_order_price: Decimal | None = None

            while True:
                if side == OrderSide.SELL.value:
                    async with best_ask_condition:
                        await best_ask_condition.wait()
                        current_best = order_book.best_ask()
                else:
                    async with best_bid_condition:
                        await best_bid_condition.wait()
                        current_best = order_book.best_bid()

                if current_best is None:
                    continue

                offset_direction = Decimal(1 if side == OrderSide.SELL else -1)

                current_price = current_best.price
                target_price = market.trading_config.round_price(
                    current_price + offset_direction * current_price * (price_offset_for_level_percent / Decimal("100"))
                )

                actual_delta = (
                    abs(((prev_order_price - current_price) / current_price)) if prev_order_price is not None else 0
                )

                target_delta = price_offset_for_level_percent / Decimal("100")

                max_delta_allowed = target_delta + target_delta * price_offset_per_level_percent / (
                    Decimal(1) + Decimal(i) / Decimal(num_of_price_levels)
                )

                min_delta_required = target_delta - target_delta * price_offset_per_level_percent * (
                    Decimal(1) + Decimal(i) / Decimal(num_of_price_levels)
                )

                if prev_order_price is None or (actual_delta < min_delta_required or actual_delta > max_delta_allowed):
                    print(f"Repricing {side} order from {prev_order_price} to {target_price}, price level {i}")
                    if prev_order_id is not None:
                        print(f"Cancelling previous order {prev_order_id}")
                        asyncio.create_task(
                            root_trading_client.orders.cancel_order_by_external_id(order_external_id=str(prev_order_id))
                        )
                    new_id = random.randint(0, 10000000000000000000000000)
                    print(f"Placing {side} order {new_id} at {target_price}, price level {i}")
                    try:
                        await root_trading_client.place_order(
                            market_name=market.name,
                            amount_of_synthetic=market.trading_config.min_order_size,
                            price=target_price,
                            side=side,
                            external_id=str(new_id),
                            post_only=True,
                        )
                    except Exception as e:
                        print(f"Error placing order {new_id} at {target_price}, price level {i}: {e}")
                        continue
                    prev_order_id = new_id
                    prev_order_price = target_price
                else:
                    pass

        tasks.append(asyncio.create_task(task(i=i, side=OrderSide.SELL)))
        tasks.append(asyncio.create_task(task(i=i, side=OrderSide.BUY)))

    while True:
        try:
            await asyncio.gather(*tasks)
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Error: {e}")


asyncio.run(on_board_example())
