"""
Async Info API for Extended Exchange SDK.

Provides read-only operations matching Hyperliquid's Info class interface.
"""

import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from x10.perpetual.candles import CandleType
from x10.perpetual.configuration import EndpointConfig

from extended.api.base_async import BaseAsyncAPI
from extended.auth import ExtendedAuth
from extended.transformers import AccountTransformer, MarketTransformer, OrderTransformer
from extended.utils.async_helpers import thread_safe_gather
from extended.utils.constants import INTERVAL_MAPPING, DEFAULT_CANDLE_TYPE
from extended.utils.helpers import normalize_market_name, to_hyperliquid_market_name


class AsyncInfoAPI(BaseAsyncAPI):
    """
    Extended Exchange Info API with Hyperliquid-compatible interface.

    Note: Unlike Hyperliquid, Extended requires authentication for
    user-specific data. The `address` parameter is accepted for
    interface compatibility but ignored (uses authenticated user).

    Example:
        async_info = AsyncInfoAPI(auth, config)
        state = await async_info.user_state()
        orders = await async_info.open_orders()
    """

    def __init__(self, auth: ExtendedAuth, config: EndpointConfig):
        """
        Initialize the async Info API.

        Args:
            auth: ExtendedAuth instance with credentials
            config: Endpoint configuration
        """
        super().__init__(auth, config)

    async def user_state(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user's account state (balance + positions).

        Args:
            address: Ignored (Extended requires auth, uses authenticated user)

        Returns:
            Dict with Hyperliquid-compatible structure containing:
            - assetPositions: List of position info
            - crossMarginSummary: Account value and margin info
            - marginSummary: Margin details
            - withdrawable: Available for withdrawal

        Note:
            Unlike Hyperliquid, Extended requires authentication.
            The `address` parameter is accepted for interface compatibility
            but is ignored. Data is always for the authenticated user.
        """
        if address is not None and address != self._auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        # Fetch balance and positions in parallel
        balance_task = self._client.account.get_balance()
        positions_task = self._client.account.get_positions()

        balance_response, positions_response = await thread_safe_gather(
            balance_task, positions_task
        )

        return AccountTransformer.transform_user_state(
            balance_response.data,
            positions_response.data or [],
        )

    async def open_orders(self, address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's open orders.

        Args:
            address: Ignored (uses authenticated user)

        Returns:
            List of orders in Hyperliquid format with keys:
            - coin: Market name (e.g., "BTC")
            - side: "B" for buy, "A" for sell
            - limitPx: Limit price
            - sz: Remaining size
            - oid: Order ID
            - timestamp: Creation timestamp
            - origSz: Original size
            - cloid: Client order ID (external_id)
        """
        if address is not None and address != self._auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        response = await self._client.account.get_open_orders()
        return OrderTransformer.transform_open_orders(response.data or [])

    async def meta(self) -> Dict[str, Any]:
        """
        Get exchange metadata (markets info).

        Returns:
            Dict with Hyperliquid-compatible structure:
            {
                "universe": [
                    {
                        "name": "BTC",
                        "szDecimals": 5,
                        "maxLeverage": 50,
                        "onlyIsolated": False,
                    }
                ]
            }
        """
        response = await self._client.markets_info.get_markets()
        return MarketTransformer.transform_meta(response.data or [])

    async def all_mids(self) -> Dict[str, str]:
        """
        Get mid prices for all markets.

        Returns:
            Dict mapping coin name to mid price string:
            {"BTC": "50000.5", "ETH": "3000.25", ...}
        """
        response = await self._client.markets_info.get_markets()
        return MarketTransformer.transform_all_mids(response.data or [])

    async def l2_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Get order book snapshot.

        Args:
            name: Market name (e.g., "BTC-USD" or "BTC")

        Returns:
            Dict in Hyperliquid format:
            {
                "coin": "BTC",
                "levels": [
                    [{"px": "50000.0", "sz": "1.5", "n": 3}],  # bids
                    [{"px": "50001.0", "sz": "2.0", "n": 5}],  # asks
                ],
                "time": 1234567890000
            }
        """
        market_name = normalize_market_name(name)
        response = await self._client.markets_info.get_orderbook_snapshot(
            market_name=market_name
        )
        return MarketTransformer.transform_l2_snapshot(response.data)

    async def candles_snapshot(
        self,
        name: str,
        interval: str,
        startTime: int,
        endTime: int,
        candle_type: str = DEFAULT_CANDLE_TYPE,
    ) -> List[Dict[str, Any]]:
        """
        Get historical candles.

        Args:
            name: Market name (e.g., "BTC" or "BTC-USD")
            interval: "1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"
            startTime: Start timestamp (ms)
            endTime: End timestamp (ms)
            candle_type: Type of candle data (default "trades")
                - "trades": Trade-based candles
                - "mark-prices": Mark price candles
                - "index-prices": Index price candles

        Returns:
            List of candles in Hyperliquid format:
            [{"t": ts, "T": close_ts, "s": symbol, "i": interval,
              "o": open, "h": high, "l": low, "c": close, "v": vol, "n": 0}]
        """
        market_name = normalize_market_name(name)
        extended_interval = INTERVAL_MAPPING.get(interval, "PT1M")

        # Calculate limit based on time range and interval
        # Extended API uses limit parameter, not startTime
        end_dt = datetime.fromtimestamp(endTime / 1000, tz=timezone.utc)

        response = await self._client.markets_info.get_candles_history(
            market_name=market_name,
            candle_type=candle_type,  # type: ignore
            interval=extended_interval,  # type: ignore
            end_time=end_dt,
            limit=1000,  # Fetch max and filter by startTime
        )

        # Filter candles by startTime
        candles = [c for c in (response.data or []) if c.timestamp >= startTime]

        coin = to_hyperliquid_market_name(name)
        return MarketTransformer.transform_candles(candles, coin, interval)

    async def user_fills(
        self,
        coin: Optional[str] = None,
        address: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get user's trade fills.

        Args:
            coin: Market name (optional - if None, returns fills for all markets)
            address: Ignored (uses authenticated user)
            start_time: Optional start timestamp (ms)
            end_time: Optional end timestamp (ms)

        Returns:
            List of fills in Hyperliquid format (up to 1000 most recent)

        Note:
            The `cloid` field will be null in responses (not available from trades endpoint).
        """
        if address is not None and address != self._auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        market_names = [normalize_market_name(coin)] if coin else None
        response = await self._client.account.get_trades(
            market_names=market_names,
        )

        # Filter by time if provided
        trades = response.data or []
        if start_time is not None:
            trades = [t for t in trades if t.created_time >= start_time]
        if end_time is not None:
            trades = [t for t in trades if t.created_time <= end_time]

        return OrderTransformer.transform_user_fills(trades)

    async def get_position_leverage(
        self,
        symbol: str,
        address: Optional[str] = None,
    ) -> Optional[int]:
        """
        Get current leverage for a position.

        Args:
            symbol: Market name (e.g., "BTC" or "BTC-USD")
            address: Ignored (uses authenticated user)

        Returns:
            Current leverage as integer, or None if not found
        """
        if address is not None and address != self._auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        market_name = normalize_market_name(symbol)
        response = await self._client.account.get_leverage(
            market_names=[market_name]
        )

        if response.data:
            for lev in response.data:
                if lev.market == market_name:
                    return int(lev.leverage)

        return None
