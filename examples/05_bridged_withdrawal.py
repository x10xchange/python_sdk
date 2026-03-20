import logging.handlers
from asyncio import run
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient

from examples.init_env import init_env

LOGGER = logging.getLogger()
ENDPOINT_CONFIG = MAINNET_CONFIG


# Bridged withdrawal example. Bridge disabled on sepolia, example works only on mainnet
async def run_example():
    env_config = init_env()
    amount = 5
    target_chain = "ETH"

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )
    trading_client = PerpetualTradingClient(ENDPOINT_CONFIG, stark_account)
    LOGGER.info("Getting quote")
    quote = (await trading_client.account.get_bridge_quote(chain_in="STRK", chain_out=target_chain, amount=amount)).data
    if quote.fee > Decimal(2):
        LOGGER.info("Fee %s is too high", quote.fee)
        return
    LOGGER.info("Commiting quote")
    await trading_client.account.commit_bridge_quote(quote.id)
    LOGGER.info("Requesting withdrawal")
    withdrawal_id = (
        await trading_client.account.withdraw(
            amount=Decimal(amount),
            chain_id=target_chain,
            quote_id=quote.id,
        )
    ).data

    LOGGER.info("Withdrawal %s requested", withdrawal_id)


if __name__ == "__main__":
    run(main=run_example())
