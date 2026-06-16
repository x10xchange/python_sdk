import logging
import logging.config
import logging.handlers
from decimal import Decimal
from logging import Logger
from pathlib import Path

import yaml
from dotenv import load_dotenv

from x10.clients.blocking import BlockingTradingClient
from x10.clients.rest import RestApiClient
from x10.clients.stream import StreamClient
from x10.config import get_config_by_name
from x10.core.client_config import ClientConfig
from x10.core.env_config import EnvConfig
from x10.core.stark_account import StarkPerpetualAccount
from x10.models.market import TradingConfigModel

BTC_USD_MARKET = "BTC-USD"


def init_env(require_private_api: bool = True):
    load_dotenv()

    config_as_str = Path(__file__).parent.joinpath("./logger.yml").read_text()
    config = yaml.safe_load(config_as_str)
    logging.config.dictConfig(config)

    env_config = EnvConfig.parse()

    if require_private_api:
        assert env_config.api_key, "X10_API_KEY is not set"
        assert env_config.public_key, "X10_PUBLIC_KEY is not set"
        assert env_config.private_key, "X10_PRIVATE_KEY is not set"
        assert env_config.vault_id, "X10_VAULT_ID is not set"

    return env_config


def create_rest_client():
    env_config = init_env()

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return RestApiClient(
        get_config_by_name(env_config.client_config_name),
        stark_account,
    )


def create_blocking_client(config: ClientConfig | None = None):
    env_config = init_env()

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return BlockingTradingClient(
        config or get_config_by_name(env_config.client_config_name),
        stark_account,
    )


def create_stream_client(config: ClientConfig):
    return StreamClient(api_url=config.endpoints.stream_url)


def get_adjust_price_by_pct(config: TradingConfigModel):
    def adjust_price_by_pct(price: Decimal, pct: Decimal | int):
        return config.round_price(price + price * Decimal(pct) / 100)

    return adjust_price_by_pct


async def find_order_and_cancel(*, rest_client: RestApiClient, logger: Logger, order_id: str):
    open_order = await rest_client.account.get_order_by_id(order_id)

    logger.info("Found placed order: %s", open_order.to_pretty_json())
    logger.info("Cancelling placed order...")

    await rest_client.orders.cancel_order(order_id)

    logger.info("Placed order is cancelled")
