import asyncio
import logging
from asyncio import run
from signal import SIGINT, SIGTERM

from examples.utils import BTC_USD_MARKET, create_stream_rpc_client, init_env
from x10.clients.streamrpc.subscription import TradesParams
from x10.config import get_config_by_name
from x10.models.stream_rpc import StreamMessageEnvelope
from x10.models.trade import PublicTradeModel

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


def on_trade(env: StreamMessageEnvelope[list[PublicTradeModel]]) -> None:
    for t in env.data:
        print(f"[trade] {t.market} {t.side.value} {t.qty} @ {t.price} (seq={env.seq})")


async def subscribe_to_rpc_stream(stop_event: asyncio.Event):
    env_config = init_env()
    client_config = get_config_by_name(env_config.client_config_name)

    async with create_stream_rpc_client(client_config) as client:
        await client.subscribe(params=TradesParams(market="BTC-USD"), handler=on_trade)
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
