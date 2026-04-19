import logging
import logging.config
import logging.handlers
import os
from dataclasses import dataclass
from decimal import Decimal
from logging import Logger
from pathlib import Path

import yaml
from dotenv import load_dotenv

from x10.core.stark_account import StarkPerpetualAccount
from x10.models.market import TradingConfigModel
from x10.perpetual.configuration import TESTNET_CONFIG, EndpointConfig
from x10.perpetual.simple_client.simple_trading_client import BlockingTradingClient
from x10.perpetual.stream_client import PerpetualStreamClient
from x10.perpetual.trading_client import PerpetualTradingClient
from x10.utils.string import is_hex_string


@dataclass
class EnvConfig:
    api_key: str | None = None
    public_key: str | None = None
    private_key: str | None = None
    vault_id: int | None = None
    builder_id: int | None = None


def init_env(require_private_api: bool = True):
    load_dotenv()

    config_as_str = Path(__file__).parent.joinpath("./logger.yml").read_text()
    config = yaml.safe_load(config_as_str)
    logging.config.dictConfig(config)

    api_key = os.getenv("X10_API_KEY")
    public_key = os.getenv("X10_PUBLIC_KEY")
    private_key = os.getenv("X10_PRIVATE_KEY")
    vault_id = os.getenv("X10_VAULT_ID")
    builder_id = os.getenv("X10_BUILDER_ID")

    if require_private_api:
        assert api_key, "X10_API_KEY is not set"
        assert public_key, "X10_PUBLIC_KEY is not set"
        assert private_key, "X10_PRIVATE_KEY is not set"
        assert vault_id, "X10_VAULT_ID is not set"

        assert is_hex_string(public_key), "X10_PUBLIC_KEY must be a hex string"
        assert is_hex_string(private_key), "X10_PRIVATE_KEY must be a hex string"

    return EnvConfig(
        api_key=api_key,
        public_key=public_key.lower() if public_key else None,
        private_key=private_key.lower() if private_key else None,
        vault_id=int(vault_id) if vault_id else None,
        builder_id=int(builder_id) if builder_id else None,
    )


def create_trading_client(endpoint_config: EndpointConfig = TESTNET_CONFIG):
    env_config = init_env()

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return PerpetualTradingClient(endpoint_config, stark_account)


def create_blocking_client(endpoint_config: EndpointConfig = TESTNET_CONFIG):
    env_config = init_env()

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return BlockingTradingClient(endpoint_config, stark_account)


def create_stream_client(endpoint_config: EndpointConfig = TESTNET_CONFIG):
    return PerpetualStreamClient(api_url=endpoint_config.stream_url)


def get_adjust_price_by_pct(config: TradingConfigModel):
    def adjust_price_by_pct(price: Decimal, pct: Decimal | int):
        return config.round_price(price + price * Decimal(pct) / 100)

    return adjust_price_by_pct


async def find_order_and_cancel(*, trading_client: PerpetualTradingClient, logger: Logger, order_id: str):
    open_order = await trading_client.account.get_order_by_id(order_id)

    logger.info("Found placed order: %s", open_order.to_pretty_json())
    logger.info("Cancelling placed order...")

    await trading_client.orders.cancel_order(order_id)

    logger.info("Placed order is cancelled")
