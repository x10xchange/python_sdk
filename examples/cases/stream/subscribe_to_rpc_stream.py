import asyncio
import logging
from asyncio import run
from signal import SIGINT, SIGTERM

from examples.utils import BTC_USD_MARKET, create_rest_client, create_stream_rpc_client
from x10.clients.streamrpc.subscription_params import (
    AccountParams,
    CandlesParams,
    PricesParams,
    TradesParams,
)
from x10.models.stream_rpc import StreamRpcResponseModel

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


def on_message(message: StreamRpcResponseModel) -> None:
    LOGGER.info("Received message: %s", message)


async def subscribe_to_rpc_stream(stop_event: asyncio.Event):
    rest_client = create_rest_client()
    main_account = await rest_client.account.get_account()

    async with create_stream_rpc_client(rest_client.config) as client:
        await client.ping()

        subscriptions_before = await client.list_subscriptions()

        LOGGER.info("Active subscriptions: %s", subscriptions_before)

        btc_usd_trades_topic_id = await client.subscribe(params=TradesParams(market="BTC-USD"), handler=on_message)
        await client.subscribe(params=TradesParams(market="ETH-USD"), handler=on_message)
        await client.subscribe(params=PricesParams(price_type="index", market="ETH-USD"), handler=on_message)
        await client.subscribe(
            params=CandlesParams(candle_type="index", market="ETH-USD", interval="PT1M"), handler=on_message
        )
        await client.subscribe(
            params=AccountParams(
                account=str(main_account.data.id),
                api_key=rest_client.stark_account.api_key,
            ),
            handler=on_message,
        )
        await client.unsubscribe(topic_id=btc_usd_trades_topic_id)

        subscriptions_after = await client.list_subscriptions()

        LOGGER.info("Active subscriptions: %s", subscriptions_after)

        await stop_event.wait()


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
