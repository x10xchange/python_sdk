import asyncio
import dataclasses
import logging
import logging.config
import logging.handlers
import os
from asyncio import run
from decimal import Decimal
from multiprocessing import Process, Queue
from typing import List, Optional

from dotenv import load_dotenv

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient
from x10.perpetual.trading_client import PerpetualTradingClient

NUM_PRICE_LEVELS = 1

PLACE = "PLACE"
CANCEL = "CANCEL"
NANOS_IN_SECOND = 1000 * 1000 * 1000


@dataclasses.dataclass(frozen=True)
class TimedOperation:
    name: str
    start_nanos: int
    end_nanos: int
    operation_ms: float


@dataclasses.dataclass(frozen=True)
class TimeSeriesChunk:
    start_ns: int
    end_ns: int
    mean_operation_latency_ms: float
    std_dev_operation_latency_ms: float
    throughput: float


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
    load_dotenv(f"./env/{base}.env")
    API_KEY = os.environ["X10_API_KEY"]
    PUBLIC_KEY = os.environ["X10_PUBLIC_KEY"]
    PRIVATE_KEY = os.environ["X10_PRIVATE_KEY"]
    VAULT_ID = int(os.environ["X10_VAULT_ID"])

    stark_account = StarkPerpetualAccount(
        vault=VAULT_ID,
        private_key=PRIVATE_KEY,
        public_key=PUBLIC_KEY,
        api_key=API_KEY,
    )
    trading_client = PerpetualTradingClient(
        endpoint_config=TESTNET_CONFIG,
        stark_account=stark_account,
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
        endpoint_config=TESTNET_CONFIG,
        account=stark_account,
    )

    markets = await blocking_client.get_markets()
    market = markets[market_name]

    orderbook = await OrderBook.create(
        endpoint_config=TESTNET_CONFIG,
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
                    queue.put(
                        TimedOperation(
                            PLACE,
                            timed_place.start_nanos,
                            timed_place.end_nanos,
                            timed_place.operation_ms,
                        )
                    )
                    timed_cancel = await blocking_client.cancel_order(order_id=timed_place.id)
                    queue.put(
                        TimedOperation(
                            CANCEL,
                            timed_cancel.start_nanos,
                            timed_cancel.end_nanos,
                            timed_cancel.operation_ms,
                        )
                    )
                else:
                    print("No baseline price for market", market_name)
                    await asyncio.sleep(1)

        return asyncio.get_running_loop().create_task(inner())

    sell_tasks = list(
        map(
            lambda idx: order_loop(idx, OrderSide.SELL, outbound_queue=queue),
            range(NUM_PRICE_LEVELS),
        )
    )
    buy_tasks = list(
        map(
            lambda idx: order_loop(idx, OrderSide.BUY, outbound_queue=queue),
            range(NUM_PRICE_LEVELS),
        )
    )

    for task in sell_tasks:
        print(await task)
    for task in buy_tasks:
        print(await task)


def entry_point(base: str, queue: Queue):
    run(main=setup_and_run(base=base, queue=queue))


if __name__ == "__main__":
    markets = ["BTC", "ETH"]
    cancels: List[TimedOperation] = []
    cancels_chunks: List[TimeSeriesChunk] = []
    places: List[TimedOperation] = []
    place_chunks: List[TimeSeriesChunk] = []

    q: "Queue[TimedOperation]" = Queue()
    subprocesses = map(lambda market: Process(target=entry_point, args=[market, q]), markets)

    for p in subprocesses:
        p.start()

    import csv
    import threading

    cancel_file = open("cancel.csv", "w")
    place_file = open("place.csv", "w")
    cancels_csv = csv.DictWriter(cancel_file, fieldnames=list(TimeSeriesChunk.__annotations__.keys()))
    places_csv = csv.DictWriter(place_file, fieldnames=list(TimeSeriesChunk.__annotations__.keys()))

    poison_pill = None

    def handle_operation(
        new_operation: TimedOperation, list: List[TimedOperation], chunks: List[TimeSeriesChunk]
    ) -> TimeSeriesChunk | None:
        list.append(new_operation)
        newest = new_operation.end_nanos
        oldest = list[0].start_nanos
        if newest - oldest > NANOS_IN_SECOND:
            latencies = [operation.operation_ms for operation in list]
            mean_latency = round(sum(latencies) / len(latencies), 1)
            latency_std_dev = round((sum((x - mean_latency) ** 2 for x in latencies) / len(latencies)) ** 0.5, 1)
            throughput_per_second = round(len(list) / ((newest - oldest) / NANOS_IN_SECOND), 1)
            chunk = TimeSeriesChunk(
                start_ns=oldest,
                end_ns=newest,
                mean_operation_latency_ms=mean_latency,
                std_dev_operation_latency_ms=latency_std_dev,
                throughput=throughput_per_second,
            )
            chunks.append(chunk)
            list.clear()
            return chunk
        return None

    def read_queue():
        cancels_csv.writeheader()
        places_csv.writeheader()
        while True:
            element: TimedOperation = q.get()
            if element == poison_pill:
                break
            if element.name == PLACE:
                chunk = handle_operation(element, places, place_chunks)
                if chunk:
                    places_csv.writerow(dataclasses.asdict(chunk))
                    place_file.flush()
            elif element.name == CANCEL:
                chunk = handle_operation(element, cancels, cancels_chunks)
                if chunk:
                    cancels_csv.writerow(dataclasses.asdict(chunk))
                    cancel_file.flush()
        cancel_file.close()
        place_file.close()
        print("Exiting queue reader")

    queue_reader = threading.Thread(target=read_queue)
    queue_reader.start()

    import signal
    import sys

    def signal_handler(sig, frame):
        print("You pressed Ctrl+C!")
        q.put(None)
        for p in subprocesses:
            p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print("Press Ctrl+C to exit")
    signal.pause()
