import logging
from asyncio import run
from decimal import Decimal

from examples.utils import create_rest_client
from x10.config import MAINNET_CONFIG

LOGGER = logging.getLogger()
FEE_THRESHOLD_USDC = 2


async def run_example():
    """
    Example works on MAINNET only with EVM wallets.
    """

    rest_client = create_rest_client(MAINNET_CONFIG)

    amount_usdc = Decimal("5")
    chain_in = "STRK"
    chain_out = "ARB"

    LOGGER.info("Getting quote...")

    quote = (
        await rest_client.account.get_bridge_quote(
            chain_in=chain_in,
            chain_out=chain_out,
            amount=amount_usdc,
        )
    ).data

    if quote.fee > FEE_THRESHOLD_USDC:
        LOGGER.warning("Fee is too high: %s USDC", quote.fee)
        return

    LOGGER.info("Expected fee: %s USDC", quote.fee)
    LOGGER.info("Commiting quote: %s", quote.id)

    await rest_client.account.commit_bridge_quote(quote.id)

    LOGGER.info("Creating withdrawal of %s USDC to %s...", amount_usdc, chain_in)

    withdrawal_id = (
        await rest_client.account.withdraw(
            amount=amount_usdc,
            chain_id=chain_out,
            quote_id=quote.id,
        )
    ).data

    LOGGER.info("Withdrawal created: %s", withdrawal_id)


if __name__ == "__main__":
    run(main=run_example())
