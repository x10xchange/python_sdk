import logging
from asyncio import run
from decimal import Decimal

from examples.utils import create_trading_client

LOGGER = logging.getLogger()


async def run_example():
    trading_client = create_trading_client()
    shares_amount = Decimal("5")

    LOGGER.info("Creating withdrawal of %s shares from vault...", shares_amount)

    await trading_client.vault.withdraw_from_vault(shares_amount)

    LOGGER.info("Withdrawal created")


if __name__ == "__main__":
    run(main=run_example())
