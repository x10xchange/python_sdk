import logging
from asyncio import run
from decimal import Decimal

from examples.init_env import init_env
from examples.utils import find_order_and_cancel, get_adjust_price_by_pct
from x10.config import ETH_USD_MARKET
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OrderSide, TimeInForce
from x10.perpetual.trading_client import PerpetualTradingClient

LOGGER = logging.getLogger()
MARKET_NAME = ETH_USD_MARKET
ENDPOINT_CONFIG = MAINNET_CONFIG  # replace with TESTNET_CONFIG for testnet


async def run_example():
    env_config = init_env()
    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )
    trading_client = PerpetualTradingClient(ENDPOINT_CONFIG, stark_account)
    await trading_client.vault.deposit_to_vault(amount=Decimal(5))


if __name__ == "__main__":
    run(main=run_example())
