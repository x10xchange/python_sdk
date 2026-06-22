from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from x10.clients.rest.rest_api_client import RestApiClient
from x10.config import get_config_by_name
from x10.core.env_config import EnvConfig
from x10.models.asset import AssetType
from x10.models.candle import CandleInterval, CandleType
from x10.tools.mcp.utils import serialize_tool_result


def _create_public_rest_api_client() -> RestApiClient:
    env_config = EnvConfig.parse()
    client_config = get_config_by_name(env_config.client_config_name)

    return RestApiClient(client_config)


def register_tools(mcp: FastMCP):
    @mcp.tool()
    async def get_assets(asset_type: Optional[AssetType] = None) -> list[dict]:
        """
        List available assets. Optionally filter by type.

        Args:
            asset_type: Optional asset type to filter by. One of "SPOT", "PERPETUAL".
        """
        async with _create_public_rest_api_client() as client:
            result = await client.info.get_assets(asset_type=asset_type)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_markets(market_names: Optional[list[str]] = None) -> list[dict]:
        """
        List available trading markets. Optionally filter by name.

        Args:
            market_names: Optional list of market names to filter (e.g. ["BTC-USD", "ETH-USD"]).
        """
        async with _create_public_rest_api_client() as client:
            result = await client.info.get_markets(market_names=market_names)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_market_statistics(market_name: str) -> dict:
        """
        Get 24h statistics for a market (price, volume, open interest, funding rate).

        Args:
            market_name: Market identifier, e.g. "BTC-USD".
        """
        async with _create_public_rest_api_client() as client:
            result = await client.info.get_market_statistics(market_name=market_name)
            return serialize_tool_result(result.data)

    @mcp.tool()
    async def get_orderbook_snapshot(market_name: str) -> dict:
        """
        Get current orderbook (bids and asks) for a market.

        Args:
            market_name: Market identifier, e.g. "BTC-USD".
        """
        async with _create_public_rest_api_client() as client:
            result = await client.info.get_orderbook_snapshot(market_name=market_name)
            return serialize_tool_result(result.data)

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
            return serialize_tool_result(result.data)
