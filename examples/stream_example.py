import asyncio
import logging
import signal

from examples.utils import init_logging
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.stream_client import PerpetualStreamClient

API_KEY = "<API_KEY>"


async def iterator_example():
    logger = logging.getLogger("stream_example[iterator_example]")
    stream_client = PerpetualStreamClient(api_url=TESTNET_CONFIG.stream_url)
    stream = await stream_client.subscribe_to_account_updates(API_KEY)

    async for event in stream:
        logger.info(event)


async def manual_example():
    logger = logging.getLogger("stream_example[manual_example]")
    stream_client = PerpetualStreamClient(api_url=TESTNET_CONFIG.stream_url)
    stream = await stream_client.subscribe_to_account_updates(API_KEY)

    event1 = await stream.recv()
    event2 = await stream.recv()

    logger.info("Event #1: %s", event1)
    logger.info("Event #2: %s", event2)

    # etc

    await stream.close()


async def context_manager_example():
    logger = logging.getLogger("stream_example[context_manager_example]")
    stream_client = PerpetualStreamClient(api_url=TESTNET_CONFIG.stream_url)

    async with stream_client.subscribe_to_orderbooks("BTC-USD") as stream:
        msg1 = await stream.recv()
        msg2 = await stream.recv()

        logger.info("Message #1: %s", msg1)
        logger.info("Message #2: %s", msg2)

        # etc


async def merge_streams_example():
    logger = logging.getLogger("stream_example[merge_streams_example]")
    stop_event = asyncio.Event()

    def sigint_handler(sig, frame):
        logger.info("Interrupted by the user, stopping...")
        stop_event.set()

    signal.signal(signal.SIGINT, sigint_handler)

    stream_client = PerpetualStreamClient(api_url=TESTNET_CONFIG.stream_url)
    queue = asyncio.Queue()

    async def run_producer_stream1():
        async with stream_client.subscribe_to_orderbooks("BTC-USD") as stream1:
            while not stop_event.is_set():
                msg = await asyncio.wait_for(stream1.recv(), timeout=5)
                await queue.put(("stream1", msg))

                if stream1.msgs_count == 5:
                    logger.info("Stream #1 produced 5 messages, stopping...")
                    break

    async def run_producer_stream2():
        async with stream_client.subscribe_to_account_updates(API_KEY) as stream2:
            while not stop_event.is_set():
                msg = await asyncio.wait_for(stream2.recv(), timeout=5)
                await queue.put(("stream2", msg))

                if stream2.msgs_count == 3:
                    logger.info("Stream #2 produced 3 messages, stopping...")
                    break

    async def run_consumer():
        while not stop_event.is_set():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=5)
                logger.info("Message: %s", msg)
                queue.task_done()
            except asyncio.TimeoutError:
                logger.info("No messages received in the last 5 seconds, stopping...")
                break

    await asyncio.gather(run_producer_stream1(), run_producer_stream2(), run_consumer())


async def main():
    await iterator_example()


if __name__ == "__main__":
    init_logging()
    asyncio.run(main=main())
