import logging.handlers
from asyncio import run
from decimal import Decimal

from eth_account import Account
from eth_account.signers.local import LocalAccount

from examples.init_env import init_env
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient

LOGGER = logging.getLogger()
ENDPOINT_CONFIG = TESTNET_CONFIG


# Bridged withdrawal example. Bridge disabled on sepolia, example works only on mainnet
async def run_example():
    env_config = init_env()
    amount = 1
    to_vault = -1
    to_l2_key = "<target l2 key>"
    signing_account = Account.from_key("<your private key>")
    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )
    trading_client = PerpetualTradingClient(ENDPOINT_CONFIG, stark_account)
    LOGGER.info("Sending transfer")
    await trading_client.account.transfer(
        to_vault=to_vault,
        to_l2_key=to_l2_key,
        amount=Decimal(amount),
        signing_account=signing_account
    )
    LOGGER.info("Transfer sent")


if __name__ == "__main__":
    run(main=run_example())
