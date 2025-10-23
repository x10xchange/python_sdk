import logging
from asyncio import run

from examples.init_env import init_env

LOGGER = logging.getLogger()


async def run_example():
    LOGGER.info("Create limit order")


if __name__ == "__main__":
    init_env()
    run(main=run_example())
