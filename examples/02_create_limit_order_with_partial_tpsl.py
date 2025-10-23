import logging
from asyncio import run

from config import ETH_USD_MARKET
from perpetual.accounts import StarkPerpetualAccount
from perpetual.configuration import TESTNET_CONFIG
from perpetual.trading_client import PerpetualTradingClient

from examples.init_env import init_env

LOGGER = logging.getLogger()
SDK_CONFIG = TESTNET_CONFIG
ETH_USD_MARKET = 'ETH-USD'


async def build_markets_cache(trading_client: PerpetualTradingClient):
    markets = await trading_client.markets_info.get_markets()
    assert markets.data is not None
    return {m.name: m for m in markets.data}


async def run_example():
    LOGGER.info("Create limit order with partial TPSL")

    env_config = init_env()
    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id
    )
    trading_client = PerpetualTradingClient(SDK_CONFIG, stark_account)
    markets_cache = await build_markets_cache(trading_client)

    market = markets_cache[ETH_USD_MARKET]

    LOGGER.info(f"Market: {market}")

    # new_order = create_order_object(
    #     stark_account,
    #     market,
    #     Decimal("100"),
    #     price,
    #     order_side,
    #     starknet_domain=TESTNET_CONFIG.starknet_domain
    # )


if __name__ == "__main__":
    run(main=run_example())
