import asyncio
import logging.handlers
import random
from asyncio import run
from typing import Set

from examples.utils import create_trading_client
from x10.config import BTC_USD_MARKET
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OrderSide
from x10.perpetual.stream_client.stream_client import PerpetualStreamClient
from x10.perpetual.trading_client import PerpetualTradingClient

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET
NUM_ORDERS_PER_PRICE_LEVEL = 10
NUM_PRICE_LEVELS = 20

stop_event = asyncio.Event()
unconfirmed_order_lock = asyncio.Lock()
unconfirmed_order_external_ids: Set[str] = set()


def generate_external_id():
    return str(random.randint(0, 10000000000000000000000000))


async def create_orders_loop(*, trading_client: PerpetualTradingClient, market: MarketModel, level: int):
    market_mid_price = market.trading_config.round_price(
        (market.market_stats.bid_price + market.market_stats.ask_price) / 2
    )

    for _ in range(NUM_ORDERS_PER_PRICE_LEVEL):
        should_buy = level % 2 == 0

        price_delta = market.trading_config.min_price_change * (level + 1) * (-1 if should_buy else 1)

        new_order_side = OrderSide.BUY if should_buy else OrderSide.SELL
        new_order_price = market.trading_config.round_price(market_mid_price + price_delta)
        new_order_external_id = generate_external_id()
        new_order_size = market.trading_config.min_order_size

        new_order = create_order_object(
            account=trading_client.stark_account,
            market=market,
            amount_of_synthetic=new_order_size,
            price=new_order_price,
            side=new_order_side,
            starknet_domain=trading_client.config.starknet_domain,
            order_external_id=new_order_external_id,
            post_only=True,
        )

        async with unconfirmed_order_lock:
            unconfirmed_order_external_ids.add(new_order_external_id)

        await trading_client.orders.place_order(order=new_order)


async def order_confirmation_loop(*, stream_url: str, api_key: str):
    stream_client = PerpetualStreamClient(api_url=stream_url)

    async with stream_client.subscribe_to_account_updates(api_key) as account_stream:
        while not stop_event.is_set():
            try:
                msg = await asyncio.wait_for(account_stream.recv(), timeout=1)

                if msg.type == "ORDER":
                    async with unconfirmed_order_lock:
                        for order in msg.data.orders:
                            if order.external_id in unconfirmed_order_external_ids:
                                unconfirmed_order_external_ids.remove(order.external_id)

                        unconfirmed_orders_count = len(unconfirmed_order_external_ids)

                        if unconfirmed_orders_count == 0:
                            stop_event.set()
                        else:
                            LOGGER.info("Waiting for confirmation of %s orders", unconfirmed_orders_count)
            except asyncio.TimeoutError:
                pass


async def cancel_open_orders(trading_client: PerpetualTradingClient):
    positions = await trading_client.account.get_positions(market_names=[MARKET_NAME])
    balance = await trading_client.account.get_balance()

    LOGGER.info("Balance: %s", balance.to_pretty_json())
    LOGGER.info("Positions: %s", positions.to_pretty_json())

    await trading_client.orders.mass_cancel(markets=[MARKET_NAME])


async def run_example():
    trading_client = create_trading_client()

    markets_dict = await trading_client.markets_info.get_markets_dict()
    market = markets_dict[MARKET_NAME]

    LOGGER.info("Starting load testing:")
    LOGGER.info("- Market: %s", MARKET_NAME)
    LOGGER.info("- Levels: %s", NUM_PRICE_LEVELS)
    LOGGER.info("- Orders per level: %s", NUM_ORDERS_PER_PRICE_LEVEL)

    await cancel_open_orders(trading_client)

    orders_confirmation_task = asyncio.create_task(
        order_confirmation_loop(
            stream_url=trading_client.config.stream_url,
            api_key=trading_client.stark_account.api_key,
        )
    )
    orders_creation_tasks = []

    for level in range(NUM_PRICE_LEVELS):
        task = create_orders_loop(trading_client=trading_client, market=market, level=level)
        orders_creation_tasks.append(asyncio.create_task(task))

    await asyncio.gather(*orders_creation_tasks)
    await orders_confirmation_task
    await cancel_open_orders(trading_client)

    LOGGER.info("Load testing finished")


if __name__ == "__main__":
    run(main=run_example())
