import asyncio
import logging
from asyncio import run
from signal import SIGINT, SIGTERM

from x10_rpc.params import FundingRatesParams

from examples.utils import BTC_USD_MARKET, create_stream_rpc_client, init_env
from x10.clients.streamrpc.subscription_params import (
    CandlesParams,
    FundingRatesParams,
    OrderbooksParams,
    PricesParams,
    TradesParams,
)
from x10.config import get_config_by_name
from x10.models.account import AccountStreamDataModel
from x10.models.stream_rpc import StreamRpcResponseModel
from x10.models.trade import PublicTradeModel

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


def on_message(message: StreamRpcResponseModel) -> None:
    print(message)


# FIXME: Cleanup
async def subscribe_to_rpc_stream(stop_event: asyncio.Event):
    env_config = init_env()
    client_config = get_config_by_name(env_config.client_config_name)

    async with create_stream_rpc_client(client_config) as client:
        # await client.subscribe(params=TradesParams(market="BTC-USD"), handler=on_trade)
        # await client.subscribe(params=TradesParams(market="ETH-USD"), handler=on_trade)
        # await client.subscribe(params=OrderBookParams(market="ETH-USD"), handler=on_message)
        # await client.subscribe(params=PricesParams(price_type="index", market="ETH-USD"), handler=on_message)
        print(await client.list_subscriptions())
        await client.subscribe(
            params=CandlesParams(candle_type="index", market="ETH-USD", interval="PT1M"), handler=on_message
        )
        print(await client.list_subscriptions())
        # FIXME: Change account
        # await client.subscribe(params=AccountParams(account="3375", api_key=env_config.api_key), handler=on_account)
        # await asyncio.sleep(5)
        # await client.unsubscribe(TradesParams(market="ETH-USD").topic_id)
        await stop_event.wait()


#         await c.ping()
#         print("Ping OK")
#         await c.subscribe(TradesParams(market="BTC-USD"), on_trade)
#         await c.subscribe(TradesParams(market="ETH-USD"), on_trade)
#         subs = await c.list_subscriptions()
#         print(f"Active subscriptions: {subs}")
#         await asyncio.sleep(10)
#         await c.unsubscribe(TradesParams(market="BTC-USD").topic_id)
#         await c.unsubscribe(TradesParams(market="ETH-USD").topic_id)
#         print("Unsubscribed from trades")


async def run_example():
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def signal_handler():
        LOGGER.info("Signal received, stopping...")
        stop_event.set()

    loop.add_signal_handler(SIGINT, signal_handler)
    loop.add_signal_handler(SIGTERM, signal_handler)

    await subscribe_to_rpc_stream(stop_event)


if __name__ == "__main__":
    run(main=run_example())
