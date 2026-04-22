import asyncio
import logging
from asyncio import run
from signal import SIGINT, SIGTERM

from examples.utils import BTC_USD_MARKET, create_stream_client, init_env

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


async def subscribe_to_streams(stop_event: asyncio.Event):
    env_config = init_env()
    stream_client = create_stream_client()

    async def subscribe_to_orderbook():
        async with stream_client.subscribe_to_orderbooks(MARKET_NAME) as orderbook_stream:
            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(orderbook_stream.recv(), timeout=1)
                    LOGGER.info("Orderbook update %s#%s: %s", msg.type, msg.seq, msg.data.market)
                except asyncio.TimeoutError:
                    pass

    async def subscribe_to_account():
        async with stream_client.subscribe_to_account_updates(env_config.api_key) as account_stream:
            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(account_stream.recv(), timeout=1)
                    if msg.type == "BALANCE":
                        LOGGER.info(
                            "Account balance update %s#%s: %s%s",
                            msg.type,
                            msg.seq,
                            msg.data.balance.collateral_name,
                            msg.data.balance.balance,
                        )
                    else:
                        LOGGER.info("Account update %s#%s", msg.type, msg.seq)
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
