import asyncio
import logging
from asyncio import run
from signal import SIGINT, SIGTERM

from examples.init_env import init_env
from x10.config import ETH_USD_MARKET
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.stream_client import PerpetualStreamClient

LOGGER = logging.getLogger()
MARKET_NAME = ETH_USD_MARKET
ENDPOINT_CONFIG = MAINNET_CONFIG


async def subscribe_to_streams(stop_event: asyncio.Event):
    env_config = init_env()
    stream_client = PerpetualStreamClient(api_url=ENDPOINT_CONFIG.stream_url)

    async def subscribe_to_orderbook():
        async with stream_client.subscribe_to_orderbooks(MARKET_NAME) as orderbook_stream:
            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(orderbook_stream.recv(), timeout=1)
                    LOGGER.info("Orderbook: %s#%s", msg.type, msg.seq)
                except asyncio.TimeoutError:
                    pass

    async def subscribe_to_account():
        async with stream_client.subscribe_to_account_updates(env_config.api_key) as account_stream:
            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(account_stream.recv(), timeout=1)
                    LOGGER.info("Account: %s#%s", msg.type, msg.seq)
                except asyncio.TimeoutError:
                    pass

    LOGGER.info("Press Ctrl+C to stop")

    await asyncio.gather(subscribe_to_orderbook(), subscribe_to_account())


async def run_example():
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def signal_handler():
        LOGGER.info("Signal received, stopping...")
        stop_event.set()

    loop.add_signal_handler(SIGINT, signal_handler)
    loop.add_signal_handler(SIGTERM, signal_handler)

    await subscribe_to_streams(stop_event)


if __name__ == "__main__":
    run(main=run_example())
