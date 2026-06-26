import asyncio
import logging
from asyncio import run
from signal import SIGINT, SIGTERM

from examples.utils import BTC_USD_MARKET, create_stream_rpc_client, init_env
from x10.config import get_config_by_name

LOGGER = logging.getLogger()
MARKET_NAME = BTC_USD_MARKET


# def on_trade(env: StreamEnvelope[PublicTrade]) -> None:
#     for t in env.data:
#         print(f"[trade] {t.market} {t.side.value} {t.qty} @ {t.price} (seq={env.seq})")


async def subscribe_to_rpc_stream(stop_event: asyncio.Event):
    env_config = init_env()
    client_config = get_config_by_name(env_config.client_config_name)

    async with create_stream_rpc_client(client_config) as client:
        pass


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

#     async def subscribe_to_orderbook():
#         async with stream_client.subscribe_to_orderbooks(MARKET_NAME) as orderbook_stream:
#             while not stop_event.is_set():
#                 try:
#                     msg = await asyncio.wait_for(orderbook_stream.recv(), timeout=1)
#                     LOGGER.info("Orderbook update %s#%s: %s", msg.type, msg.seq, msg.data.market)
#                 except asyncio.TimeoutError:
#                     pass
#
#     async def subscribe_to_account():
#         async with stream_client.subscribe_to_account_updates(env_config.api_key) as account_stream:
#             while not stop_event.is_set():
#                 try:
#                     msg = await asyncio.wait_for(account_stream.recv(), timeout=1)
#                     if msg.type == "BALANCE":
#                         LOGGER.info(
#                             "Account balance update %s#%s: %s%s",
#                             msg.type,
#                             msg.seq,
#                             msg.data.balance.collateral_name,
#                             msg.data.balance.balance,
#                         )
#                     else:
#                         LOGGER.info("Account update %s#%s", msg.type, msg.seq)
#                 except asyncio.TimeoutError:
#                     pass
#
#     LOGGER.info("Press Ctrl+C to stop")
#
#     await asyncio.gather(subscribe_to_orderbook(), subscribe_to_account())


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
