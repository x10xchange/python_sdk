import logging
from asyncio import run
from decimal import Decimal

from examples.utils import create_trading_client
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.utils.nonce import generate_nonce

LOGGER = logging.getLogger()


async def run_example():
    """
    Example works on MAINNET only with STARKNET wallets.
    """

    trading_client = create_trading_client(MAINNET_CONFIG)

    amount_usdc = Decimal("5")
    target_wallet_address = "<STARKNET_WALLET_ADDRESS>"
    nonce = generate_nonce()

    assert target_wallet_address.startswith("0x"), "`target_wallet_address` must be a hex string"

    LOGGER.info("Creating withdrawal of %s USDC to %s...", amount_usdc, target_wallet_address)

    withdrawal_id = (
        await trading_client.account.withdraw(
            amount=amount_usdc,
            stark_address=target_wallet_address.lower(),
            nonce=nonce,
        )
    ).data

    LOGGER.info("Withdrawal created: %s", withdrawal_id)


if __name__ == "__main__":
    run(main=run_example())
