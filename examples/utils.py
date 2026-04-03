from decimal import Decimal
from logging import Logger

from examples.init_env import init_env
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG, EndpointConfig
from x10.perpetual.markets import TradingConfigModel
from x10.perpetual.trading_client import PerpetualTradingClient


def create_trading_client(endpoint_config: EndpointConfig = TESTNET_CONFIG):
    env_config = init_env()
    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return PerpetualTradingClient(endpoint_config, stark_account)


def get_adjust_price_by_pct(config: TradingConfigModel):
    def adjust_price_by_pct(price: Decimal, pct: int):
        return config.round_price(price + price * Decimal(pct) / 100)

    return adjust_price_by_pct


async def find_order_and_cancel(*, trading_client: PerpetualTradingClient, logger: Logger, order_id: str):
    open_order = await trading_client.account.get_order_by_id(order_id)

    logger.info("Found placed order: %s", open_order.to_pretty_json())
    logger.info("Cancelling placed order...")

    await trading_client.orders.cancel_order(order_id)

    logger.info("Placed order is cancelled")
