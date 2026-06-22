import logging
from asyncio import run
from decimal import Decimal

from examples.utils import create_rest_client
from x10.config import MAINNET_CONFIG
from x10.errors import ValidationError
from x10.utils.nonce import generate_nonce
from x10.utils.string import is_hex_string

LOGGER = logging.getLogger()


async def run_example():
    rest_client = create_rest_client()

    if rest_client.config != MAINNET_CONFIG:
        raise ValidationError("Example works on MAINNET only with EVM wallets")

    amount_usdc = Decimal("5")
    target_wallet_address = "<STARKNET_WALLET_ADDRESS>"
    nonce = generate_nonce()

    assert is_hex_string(target_wallet_address), "`target_wallet_address` must be a hex string"

    LOGGER.info("Creating withdrawal of %s USDC to %s...", amount_usdc, target_wallet_address)

    withdrawal_id = (
        await rest_client.account.withdraw(
            amount=amount_usdc,
            stark_address=target_wallet_address.lower(),
            nonce=nonce,
        )
    ).data

    LOGGER.info("Withdrawal created: %s", withdrawal_id)


if __name__ == "__main__":
    run(main=run_example())
