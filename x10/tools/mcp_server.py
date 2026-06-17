import logging
from typing import Any, Optional

from config import get_config_by_name
from core.env_config import EnvConfig
from mcp.server.fastmcp import FastMCP

from x10.clients.rest.rest_api_client import RestApiClient
from x10.core.stark_account import StarkPerpetualAccount
from x10.models.candle import CandleInterval, CandleType

LOGGER = logging.getLogger()

mcp = FastMCP("Extended DEX MCP Server")


def _create_public_rest_api_client() -> RestApiClient:
    env_config = EnvConfig.parse()
    client_config = get_config_by_name(env_config.client_config_name)

    return RestApiClient(client_config)


def _create_private_rest_api_client() -> RestApiClient:
    env_config = EnvConfig.parse()
    env_config.validate_private_api_credentials()
    client_config = get_config_by_name(env_config.client_config_name)

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )

    return RestApiClient(client_config, stark_account)


@mcp.tool()
async def get_markets(market_names: Optional[list[str]] = None) -> list[dict]:
    """
    List available trading markets. Optionally filter by name.

    Args:
        market_names: Optional list of market names to filter (e.g. ["BTC-USD", "ETH-USD"]).
    """
    async with _create_public_rest_api_client() as client:
        result = await client.info.get_markets(market_names=market_names)
        return _serialize_tool_result(result.data)


@mcp.tool()
async def get_market_statistics(market_name: str) -> dict:
    """
    Get 24h statistics for a market (price, volume, open interest, funding rate).

    Args:
        market_name: Market identifier, e.g. "BTC-USD".
    """
    async with _create_public_rest_api_client() as client:
        result = await client.info.get_market_statistics(market_name=market_name)
        return _serialize_tool_result(result.data)


@mcp.tool()
async def get_orderbook_snapshot(market_name: str) -> dict:
    """
    Get current orderbook (bids and asks) for a market.

    Args:
        market_name: Market identifier, e.g. "BTC-USD".
    """
    async with _create_public_rest_api_client() as client:
        result = await client.info.get_orderbook_snapshot(market_name=market_name)
        return _serialize_tool_result(result.data)


@mcp.tool()
async def get_asset_price(asset_name: str) -> str:
    """
    Get current price for an asset.

    Args:
        asset_name: Asset name, e.g. "BTC".
    """
    async with _create_public_rest_api_client() as client:
        result = await client.info.get_asset_price(asset_name=asset_name)
        return str(result.data)


@mcp.tool()
async def get_candles_history(
    market_name: str,
    candle_type: CandleType,
    interval: CandleInterval,
    limit: int = 100,
) -> list[dict]:
    """
    Get OHLCV candle history for a market.

    Args:
        market_name: Market identifier, e.g. "BTC-USD".
        candle_type: One of "trades", "mark-prices", "index-prices".
        interval: One of "PT1M", "PT5M", "PT15M", "PT30M", "PT1H", "PT2H", "PT4H", "P1D".
        limit: Number of candles to return (default 100).
    """
    async with _create_public_rest_api_client() as client:
        result = await client.info.get_candles_history(
            market_name=market_name,
            candle_type=candle_type,
            interval=interval,
            limit=limit,
        )
        return _serialize_tool_result(result.data)


@mcp.tool()
async def get_balance() -> dict:
    """
    Get account balance. Requires authentication env vars.
    """
    async with _create_private_rest_api_client() as client:
        result = await client.account.get_balance()
        return _serialize_tool_result(result.data)


@mcp.tool()
async def get_positions(market_names: Optional[list[str]] = None) -> list[dict]:
    """
    Get open positions. Requires authentication env vars.

    Args:
        market_names: Optional list of market names to filter.
    """
    async with _create_private_rest_api_client() as client:
        result = await client.account.get_positions(market_names=market_names)
        return _serialize_tool_result(result.data)


@mcp.tool()
async def get_open_orders(market_names: Optional[list[str]] = None) -> list[dict]:
    """
    Get open orders. Requires authentication env vars.

    Args:
        market_names: Optional list of market names to filter.
    """
    async with _create_private_rest_api_client() as client:
        result = await client.account.get_open_orders(market_names=market_names)
        return _serialize_tool_result(result.data)


def _serialize_tool_result(obj: Any) -> Any:
    if obj is None:
        return None

    if hasattr(obj, "to_api_request_json"):
        return obj.to_api_request_json()

    if isinstance(obj, list):
        return [_serialize_tool_result(item) for item in obj]

    return obj


if __name__ == "__main__":
    mcp.run()
