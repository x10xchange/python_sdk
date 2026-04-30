import logging
from asyncio import run
from decimal import Decimal

from examples.utils import create_rest_client

LOGGER = logging.getLogger()


async def run_example():
    rest_client = create_rest_client()
    shares_amount = Decimal("5")

    LOGGER.info("Creating withdrawal of %s shares from vault...", shares_amount)

    await rest_client.vault.withdraw_from_vault(shares_amount)

    LOGGER.info("Withdrawal created")


if __name__ == "__main__":
    run(main=run_example())
