import logging
from asyncio import run
from decimal import Decimal

from examples.utils import create_trading_client

LOGGER = logging.getLogger()


async def run_example():
    trading_client = create_trading_client()
    collateral_amount = Decimal("5")

    LOGGER.info("Creating deposit of %s USDC to vault...", collateral_amount)

    await trading_client.vault.deposit_to_vault(collateral_amount)

    LOGGER.info("Deposit created")


if __name__ == "__main__":
    run(main=run_example())
