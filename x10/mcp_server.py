"""
MCP server exposing X10 DEX SDK capabilities as tools.

Public tools (no credentials needed):
  get_markets, get_market_statistics, get_orderbook_snapshot,
  get_asset_price, get_candles_history

Authenticated tools (require env vars):
  get_balance, get_positions, get_open_orders,
  place_order, cancel_order

Environment variables:
  X10_NETWORK      "mainnet" or "testnet" (default: testnet)
  X10_API_KEY      API key
  X10_PUBLIC_KEY   Stark public key (hex)
  X10_PRIVATE_KEY  Stark private key (hex)
  X10_VAULT_ID     Vault ID (integer)
"""

import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from config import get_config_by_name, TESTNET_CONFIG
from core.env_config import EnvConfig
from x10.clients.rest.rest_api_client import RestApiClient
from x10.core.stark_account import StarkPerpetualAccount
from x10.models.candle import CandleInterval, CandleType
from x10.models.order import OrderSide


def _get_public_client() -> RestApiClient:
    env_config = EnvConfig.parse()
    client_config = get_config_by_name(env_config.client_config_name)

    return RestApiClient(client_config)


def _get_auth_client() -> RestApiClient:
    env_config = EnvConfig.parse()

    assert env_config.api_key, "X10_API_KEY is not set"
    assert env_config.public_key, "X10_PUBLIC_KEY is not set"
    assert env_config.private_key, "X10_PRIVATE_KEY is not set"
    assert env_config.vault_id, "X10_VAULT_ID is not set"

    stark_account = StarkPerpetualAccount(
        api_key=env_config.api_key,
        public_key=env_config.public_key,
        private_key=env_config.private_key,
        vault=env_config.vault_id,
    )
    client_config = get_config_by_name(env_config.client_config_name)

    return RestApiClient(client_config, stark_account)


def _serialize(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    return obj


mcp = FastMCP("x10-dex")


# ---------------------------------------------------------------------------
# Public tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_markets(market_names: Optional[list[str]] = None) -> list[dict]:
    """
    List available trading markets. Optionally filter by name.

    Args:
        market_names: Optional list of market names to filter (e.g. ["BTC-USD", "ETH-USD"]).
    """
    async with _get_public_client() as client:
        result = await client.info.get_markets(market_names=market_names)
        return _serialize(result.data)


@mcp.tool()
async def get_market_statistics(market_name: str) -> dict:
    """
    Get 24h statistics for a market (price, volume, open interest, funding rate).

    Args:
        market_name: Market identifier, e.g. "BTC-USD".
    """
    async with _get_public_client() as client:
        result = await client.info.get_market_statistics(market_name=market_name)
        return _serialize(result.data)


@mcp.tool()
async def get_orderbook_snapshot(market_name: str) -> dict:
    """
    Get current orderbook (bids and asks) for a market.

    Args:
        market_name: Market identifier, e.g. "BTC-USD".
    """
    async with _get_public_client() as client:
        result = await client.info.get_orderbook_snapshot(market_name=market_name)
        return _serialize(result.data)


@mcp.tool()
async def get_asset_price(asset_name: str) -> str:
    """
    Get current price for an asset.

    Args:
        asset_name: Asset name, e.g. "BTC".
    """
    async with _get_public_client() as client:
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
    async with _get_public_client() as client:
        result = await client.info.get_candles_history(
            market_name=market_name,
            candle_type=candle_type,
            interval=interval,
            limit=limit,
        )
        return _serialize(result.data)


# ---------------------------------------------------------------------------
# Authenticated tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_balance() -> dict:
    """
    Get account balance. Requires authentication env vars.
    """
    async with _get_auth_client() as client:
        result = await client.account.get_balance()
        return _serialize(result.data)


@mcp.tool()
async def get_positions(market_names: Optional[list[str]] = None) -> list[dict]:
    """
    Get open positions. Requires authentication env vars.

    Args:
        market_names: Optional list of market names to filter.
    """
    async with _get_auth_client() as client:
        result = await client.account.get_positions(market_names=market_names)
        return _serialize(result.data)


@mcp.tool()
async def get_open_orders(market_names: Optional[list[str]] = None) -> list[dict]:
    """
    Get open orders. Requires authentication env vars.

    Args:
        market_names: Optional list of market names to filter.
    """
    async with _get_auth_client() as client:
        result = await client.account.get_open_orders(market_names=market_names)
        return _serialize(result.data)


@mcp.tool()
async def place_order(
    market_name: str,
    side: str,
    amount: str,
    price: str,
    taker_fee: str,
    post_only: bool = False,
    reduce_only: bool = False,
    external_id: Optional[str] = None,
) -> dict:
    """
    Place a limit order. Requires authentication env vars.

    Args:
        market_name: Market identifier, e.g. "BTC-USD".
        side: "BUY" or "SELL".
        amount: Amount of synthetic asset (e.g. "0.01" for 0.01 BTC).
        price: Limit price (e.g. "50000").
        taker_fee: Taker fee rate (e.g. "0.0005" for 0.05%).
        post_only: If True, order will be cancelled if it would take liquidity.
        reduce_only: If True, order can only reduce an existing position.
        external_id: Optional client-assigned order ID.
    """
    async with _get_auth_client() as client:
        result = await client.place_order(
            market_name=market_name,
            side=OrderSide(side.upper()),
            amount_of_synthetic=Decimal(amount),
            price=Decimal(price),
            taker_fee=Decimal(taker_fee),
            post_only=post_only,
            reduce_only=reduce_only,
            external_id=external_id,
        )
        return _serialize(result.data)


@mcp.tool()
async def cancel_order(order_id: int) -> dict:
    """
    Cancel an open order by its ID. Requires authentication env vars.

    Args:
        order_id: Numeric order ID returned when the order was placed.
    """
    async with _get_auth_client() as client:
        result = await client.orders.cancel_order(order_id)
        return _serialize(result.data)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
