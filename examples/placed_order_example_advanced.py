import asyncio
import logging
import logging.config
import logging.handlers
from asyncio import run
from collections.abc import Awaitable
from decimal import Decimal
from typing import Dict, Optional, Tuple

from x10.config import ADA_USD_MARKET
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OrderSide, PlacedOrderModel
from x10.perpetual.stream_client.perpetual_stream_connection import (
    PerpetualStreamConnection,
)
from x10.perpetual.stream_client.stream_client import PerpetualStreamClient
from x10.perpetual.trading_client import PerpetualTradingClient
from x10.utils.http import WrappedApiResponse
from x10.utils.model import EmptyModel

NUM_ORDERS_PER_PRICE_LEVEL = 100
NUM_PRICE_LEVELS = 80

API_KEY = "<API_KEY>"
PRIVATE_KEY = "<PRIVATE_KEY>"
PUBLIC_KEY = "<PUBLIC_KEY"
VAULT_ID = 12345677890

order_condtions: Dict[str, asyncio.Condition] = {}
socket_connect_condition = asyncio.Condition()
socket_connected = False
order_loop_finished = False
stream: Optional[PerpetualStreamConnection] = None


stark_account = StarkPerpetualAccount(vault=VAULT_ID, private_key=PRIVATE_KEY, public_key=PUBLIC_KEY, api_key=API_KEY)


async def build_markets_cache(trading_client: PerpetualTradingClient):
    markets = await trading_client.markets_info.get_markets()
    assert markets.data is not None
    return {m.name: m for m in markets.data}


async def order_stream():
    stream_client = PerpetualStreamClient(api_url=TESTNET_CONFIG.stream_url)
    global stream
    stream = await stream_client.subscribe_to_account_updates(API_KEY)

    global socket_connected
    socket_connected = True

    async with socket_connect_condition:
        socket_connect_condition.notify_all()

    async for event in stream:
        if order_loop_finished:
            break
        if not (event.data and event.data.orders):
            continue
        else:
            pass
        for order in event.data.orders:
            print(f"processing order {order.external_id}")
            condition = order_condtions.get(order.external_id)
            if not condition:
                continue
            if condition:
                async with condition:
                    condition.notify_all()
                    del order_condtions[order.external_id]


async def order_loop(
    i: int,
    trading_client: PerpetualTradingClient,
    markets_cache: dict[str, MarketModel],
):
    if not socket_connected:
        async with socket_connect_condition:
            await socket_connect_condition.wait()

    for _ in range(NUM_ORDERS_PER_PRICE_LEVEL):
        (external_id, order_response) = await place_order(i, trading_client, markets_cache)
        print(f"placed order {external_id}")
        condition = order_condtions.get(external_id)
        if condition:
            async with condition:
                await condition.wait()
        if order_response and order_response.data:
            print(f"cancelling order {external_id}")
            await trading_client.orders.cancel_order(order_id=order_response.data.id)
            print(f"cancelled order {external_id}")


async def place_order(
    i: int,
    trading_client: PerpetualTradingClient,
    markets_cache: dict[str, MarketModel],
) -> Tuple[str, WrappedApiResponse[PlacedOrderModel]]:
    should_buy = i % 2 == 0
    price = Decimal("0.660") - Decimal("0.00" + str(i)) if should_buy else Decimal("0.6601") + Decimal("0.00" + str(i))
    order_side = OrderSide.BUY if should_buy else OrderSide.SELL
    market = markets_cache[ADA_USD_MARKET]
    new_order = create_order_object(stark_account, market, Decimal("100"), price, order_side)
    order_condtions[new_order.id] = asyncio.Condition()
    return new_order.id, await trading_client.orders.place_order(order=new_order)


async def clean_it():
    logger = logging.getLogger("placed_order_example")
    trading_client = PerpetualTradingClient(TESTNET_CONFIG, stark_account)
    positions = await trading_client.account.get_positions()
    logger.info("Positions: %s", positions.to_pretty_json())
    balance = await trading_client.account.get_balance()
    logger.info("Balance: %s", balance.to_pretty_json())
    open_orders = await trading_client.account.get_open_orders(market_names=[ADA_USD_MARKET])

    def __cancel_order(order_id: int) -> Awaitable[WrappedApiResponse[EmptyModel]]:
        return trading_client.orders.cancel_order(order_id=order_id)

    cancel_futures = list(map(__cancel_order, [order.id for order in open_orders.data]))
    await asyncio.gather(*cancel_futures)


async def setup_and_run():
    await clean_it()
    print("Press enter to start load test")
    input()

    trading_client = PerpetualTradingClient(TESTNET_CONFIG, stark_account)
    markets_cache = await build_markets_cache(trading_client)
    stream_future = asyncio.create_task(order_stream())

    def __create_order_loop(i: int):
        return asyncio.create_task(
            order_loop(
                i,
                trading_client=trading_client,
                markets_cache=markets_cache,
            )
        )

    order_loop_futures = map(__create_order_loop, range(NUM_PRICE_LEVELS))
    await asyncio.gather(*order_loop_futures)
    print("Load Test Complete")
    global order_loop_finished
    order_loop_finished = True
    if stream:
        await stream.close()
    await stream_future
    await clean_it()


if __name__ == "__main__":
    run(main=setup_and_run())
