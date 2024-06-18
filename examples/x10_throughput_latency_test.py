import asyncio
import dataclasses
import logging
import logging.config
import logging.handlers
import os
from asyncio import run
from decimal import Decimal
from multiprocessing import Process, Queue
from typing import Optional

from dotenv import load_dotenv

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG, EndpointConfig
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient
from x10.perpetual.trading_client import PerpetualTradingClient

NUM_PRICE_LEVELS = 1

@dataclasses.dataclass(frozen=True)
class TimedOperation:
    name: str
    start_nanos: int
    end_nanos: int
    operation_ms: float


async def clean_it(trading_client: PerpetualTradingClient, market_name: str | None = None):
    logger = logging.getLogger("placed_order_example")
    positions = await trading_client.account.get_positions()
    logger.info("Positions: %s", positions.to_pretty_json())
    balance = await trading_client.account.get_balance()
    logger.info("Balance: %s", balance.to_pretty_json())
    open_orders = await trading_client.account.get_open_orders(market_names=[market_name] if market_name else None)
    await trading_client.orders.mass_cancel(order_ids=[order.id for order in open_orders.data])


async def setup_and_run(base: str = "BTC", queue: Optional[Queue] = None):
    market_name = f"{base}-USD"
    print("Running for market: ", market_name)
    load_dotenv(f"/workspaces/python_trading_clone/env/{base}.env")
    API_KEY = os.getenv("X10_API_KEY")
    PUBLIC_KEY = os.getenv("X10_PUBLIC_KEY")
    PRIVATE_KEY = os.getenv("X10_PRIVATE_KEY")
    VAULT_ID = int(os.environ["X10_VAULT_ID"])

    stark_account = StarkPerpetualAccount(
        vault=VAULT_ID,
        private_key=PRIVATE_KEY,
        public_key=PUBLIC_KEY,
        api_key=API_KEY,
    )
    trading_client = PerpetualTradingClient.create(
        endpoint_config=EndpointConfig(
            api_base_url=TESTNET_CONFIG.api_base_url,
            stream_url=TESTNET_CONFIG.stream_url,
        ),
        trading_account=stark_account,
    )

    positions = await trading_client.account.get_positions()
    for position in positions.data:
        print(
            f"market: {position.market} \
            side: {position.side} \
            size: {position.size} \
            mark_price: ${position.mark_price} \
            leverage: {position.leverage}"
        )
        print(f"consumed im: ${round((position.size * position.mark_price) / position.leverage, 2)}")

    await clean_it(trading_client)

    blocking_client = BlockingTradingClient(
        endpoint_config=EndpointConfig(
            api_base_url=TESTNET_CONFIG.api_base_url,
            stream_url=TESTNET_CONFIG.stream_url,
        ),
        account=stark_account,
    )

    markets = await blocking_client.get_markets()
    market = markets[market_name]

    orderbook = await OrderBook.create(
        endpoint_config=EndpointConfig(
            api_base_url=TESTNET_CONFIG.api_base_url,
            stream_url=TESTNET_CONFIG.stream_url,
        ),
        market_name=market_name,
    )

    await orderbook.start_orderbook()

    def order_loop(idx: int, side: OrderSide, outbound_queue: Optional[Queue] = None) -> asyncio.Task:
        side_adjustment = Decimal("-1") if side == OrderSide.BUY else Decimal("1")
        base_offset = side_adjustment * Decimal("0.02")

        async def inner():
            while True:
                baseline_price = orderbook.best_bid() if side == OrderSide.BUY else orderbook.best_ask()
                if baseline_price:
                    order_price = round(
                        (baseline_price.price + baseline_price.price * base_offset)
                        + side_adjustment * market.trading_config.min_price_change * idx,
                        market.trading_config.price_precision,
                    )
                    timed_place = await blocking_client.create_and_place_order(
                        market_name=market_name,
                        amount_of_synthetic=market.trading_config.min_order_size,
                        price=order_price,
                        side=side,
                        post_only=True,
                    )
                    queue.put(TimedOperation("place", timed_place.start_nanos, timed_place.end_nanos, timed_place.operation_ms))
                    timed_cancel = await blocking_client.cancel_order(order_id=timed_place.id)
                    queue.put(TimedOperation("cancel", timed_cancel.start_nanos, timed_cancel.end_nanos, timed_cancel.operation_ms))
                else:
                    print("No baseline price for market", market_name)
                    await asyncio.sleep(1)

        return asyncio.get_running_loop().create_task(inner())

    sell_tasks = list(map(lambda idx: order_loop(idx, OrderSide.SELL, outbound_queue=queue), range(NUM_PRICE_LEVELS)))
    buy_tasks = list(map(lambda idx: order_loop(idx, OrderSide.BUY, outbound_queue=queue), range(NUM_PRICE_LEVELS)))

    for task in sell_tasks:
        print(await task)
    for task in buy_tasks:
        print(await task)


def entry_point(base: str, queue: Queue):
    run(main=setup_and_run(base=base, queue=queue))


if __name__ == "__main__":
    markets = ["ARB", "AVAX", "BTC", "DOGE", "ETH", "LINK", "SOL", "WLD"]

    q = Queue()
    subprocesses = map(lambda market: Process(target=entry_point, args=[market, q]), markets)

    for p in subprocesses:
        p.start()

    import threading

    def read_queue():
        while True:
            print(q.get())

    threading.Thread(target=read_queue).start()

    import signal
    import sys

    def signal_handler(sig, frame):
        print("You pressed Ctrl+C!")
        for p in subprocesses:
            p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print("Press Ctrl+C to exit")
    signal.pause()

    # entry_point("ARB", None)
