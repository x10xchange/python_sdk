import asyncio
import logging
import logging.config
import logging.handlers
import os
import random
from asyncio import run
from decimal import Decimal

from dotenv import load_dotenv

from examples.utils import create_blocking_client, create_trading_client
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orders import OrderSide
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient
from x10.perpetual.trading_client import PerpetualTradingClient

LOGGER = logging.getLogger()
ENDPOINT_CONFIG = TESTNET_CONFIG
# NUM_PRICE_LEVELS = 1
#
# load_dotenv()
#
# API_KEY = os.getenv("X10_API_KEY")
# PUBLIC_KEY = os.getenv("X10_PUBLIC_KEY")
# PRIVATE_KEY = os.getenv("X10_PRIVATE_KEY")
# VAULT_ID = int(os.environ["X10_VAULT_ID"])
#
#
# async def clean_it(trading_client: PerpetualTradingClient):
#     logger = logging.getLogger("placed_order_example")
#     positions = await trading_client.account.get_positions()
#     logger.info("Positions: %s", positions.to_pretty_json())
#     balance = await trading_client.account.get_balance()
#     logger.info("Balance: %s", balance.to_pretty_json())
#     open_orders = await trading_client.account.get_open_orders()
#     await trading_client.orders.mass_cancel(order_ids=[order.id for order in open_orders.data])


async def show_positions_and_cancel_open_orders():
    trading_client = create_trading_client(ENDPOINT_CONFIG)
    positions = await trading_client.account.get_positions()

    if len(positions.data) > 0:
        LOGGER.info("Positions:")

        for position in positions.data:
            pass
            # LOGGER.info(
            #     f"{position.market}\t\
            #     side: {position.side} \
            #     size: {position.size} \
            #     mark_price: ${position.mark_price} \
            #     leverage: {position.leverage}"
            # )
            # LOGGER.info(f"consumed im: ${round((position.size * position.mark_price) / position.leverage, 2)}")
    else:
        LOGGER.info("No open positions")
    # for position in positions.data:
    #     print(
    #         f"market: {position.market} \
    #         side: {position.side} \
    #         size: {position.size} \
    #         mark_price: ${position.mark_price} \
    #         leverage: {position.leverage}"
    #     )
    #     print(f"consumed im: ${round((position.size * position.mark_price) / position.leverage, 2)}")
    #
    # await clean_it(trading_client)


async def run_example():
    blocking_client = create_blocking_client(ENDPOINT_CONFIG)

    await show_positions_and_cancel_open_orders()

    orderbook = await OrderBook.create(endpoint_config=TESTNET_CONFIG, market_name="BTC-USD", start=True)

    # def order_loop(idx: int, side: OrderSide) -> asyncio.Task:
    #     offset = (Decimal("-1") if side == OrderSide.BUY else Decimal("1")) * Decimal(idx + 1)
    #
    #     async def inner():
    #         while True:
    #             baseline_price = orderbook.best_bid() if side == OrderSide.BUY else orderbook.best_ask()
    #             if baseline_price:
    #                 order_price = round(
    #                     baseline_price.price + offset * baseline_price.price * Decimal("0.002"),
    #                     1,
    #                 )
    #                 external_id = str(random.randint(1, 10000000000000000000000000000000000000000000000000000000000))
    #                 placed_order = await blocking_client.create_and_place_order(
    #                     market_name="BTC-USD",
    #                     amount_of_synthetic=Decimal("0.01"),
    #                     price=order_price,
    #                     side=side,
    #                     post_only=True,
    #                     external_id=external_id,
    #                 )
    #                 print(f"baseline: {baseline_price.price}, order: {order_price}, id: {placed_order.id}")
    #                 await blocking_client.cancel_order(order_external_id=external_id)
    #                 await asyncio.sleep(0)
    #             else:
    #                 await asyncio.sleep(1)
    #
    #     return asyncio.get_running_loop().create_task(inner())
    #
    # sell_tasks = list(map(lambda idx: order_loop(idx, OrderSide.SELL), range(NUM_PRICE_LEVELS)))
    # buy_tasks = list(map(lambda idx: order_loop(idx, OrderSide.BUY), range(NUM_PRICE_LEVELS)))
    #
    # for task in sell_tasks:
    #     print(await task)
    # for task in buy_tasks:
    #     print(await task)


if __name__ == "__main__":
    run(main=run_example())
