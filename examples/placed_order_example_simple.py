import asyncio
import logging
import logging.config
import logging.handlers
import os
from asyncio import run
from decimal import Decimal

from dotenv import load_dotenv

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient
from x10.perpetual.trading_client import PerpetualTradingClient

NUM_PRICE_LEVELS = 1

load_dotenv()

API_KEY = os.getenv("X10_API_KEY")
PUBLIC_KEY = os.getenv("X10_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("X10_PRIVATE_KEY")
VAULT_ID = int(os.environ["X10_VAULT_ID"])


async def clean_it(trading_client: PerpetualTradingClient):
    logger = logging.getLogger("placed_order_example")
    positions = await trading_client.account.get_positions()
    logger.info("Positions: %s", positions.to_pretty_json())
    balance = await trading_client.account.get_balance()
    logger.info("Balance: %s", balance.to_pretty_json())
    open_orders = await trading_client.account.get_open_orders()
    await trading_client.orders.mass_cancel(order_ids=[order.id for order in open_orders.data])


async def setup_and_run():
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

    orderbook = await OrderBook.create(
        endpoint_config=TESTNET_CONFIG,
        market_name="BTC-USD",
    )

    await orderbook.start_orderbook()

    def order_loop(idx: int, side: OrderSide) -> asyncio.Task:
        offset = (Decimal("-1") if side == OrderSide.BUY else Decimal("1")) * Decimal(idx + 1)

        async def inner():
            while True:
                baseline_price = orderbook.best_bid() if side == OrderSide.BUY else orderbook.best_ask()
                if baseline_price:
                    order_price = round(
                        baseline_price.price + offset * baseline_price.price * Decimal("0.002"),
                        1,
                    )
                    placed_order = await blocking_client.create_and_place_order(
                        market_name="BTC-USD",
                        amount_of_synthetic=Decimal("0.01"),
                        price=order_price,
                        side=side,
                        post_only=True,
                    )
                    print(f"baseline: {baseline_price.price}, order: {order_price}, id: {placed_order.id}")
                    await blocking_client.cancel_order(order_id=placed_order.id)
                    await asyncio.sleep(0)
                else:
                    await asyncio.sleep(1)

        return asyncio.get_running_loop().create_task(inner())

    sell_tasks = list(map(lambda idx: order_loop(idx, OrderSide.SELL), range(NUM_PRICE_LEVELS)))
    buy_tasks = list(map(lambda idx: order_loop(idx, OrderSide.BUY), range(NUM_PRICE_LEVELS)))

    for task in sell_tasks:
        print(await task)
    for task in buy_tasks:
        print(await task)


if __name__ == "__main__":
    run(main=setup_and_run())
