"""
Native Sync Info API for Extended Exchange SDK.

Provides read-only operations matching Hyperliquid's Info class interface.
Uses direct HTTP calls with requests - no async dependencies.
"""

import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from extended.api.base_native_sync import BaseNativeSyncClient
from extended.auth_sync import SimpleSyncAuth
from extended.config_sync import SimpleSyncConfig
from extended.transformers_sync import (
    SyncAccountTransformer,
    SyncMarketTransformer,
    SyncOrderTransformer,
    normalize_market_name,
    to_hyperliquid_market_name,
)

# Interval mapping (Hyperliquid -> Extended)
INTERVAL_MAPPING = {
    "1m": "PT1M",
    "5m": "PT5M",
    "15m": "PT15M",
    "30m": "PT30M",
    "1h": "PT1H",
    "2h": "PT2H",
    "4h": "PT4H",
    "1d": "P1D",
}

DEFAULT_CANDLE_TYPE = "trades"


class NativeSyncInfoAPI(BaseNativeSyncClient):
    """
    Extended Exchange Native Sync Info API with Hyperliquid-compatible interface.

    Uses requests directly for pure synchronous operation.

    Note: Unlike Hyperliquid, Extended requires authentication for
    user-specific data. The `address` parameter is accepted for
    interface compatibility but ignored (uses authenticated user).

    Example:
        info = NativeSyncInfoAPI(auth, config)
        state = info.user_state()
        orders = info.open_orders()
    """

    def __init__(self, auth: SimpleSyncAuth, config: SimpleSyncConfig):
        """
        Initialize the native sync Info API.

        Args:
            auth: SimpleSyncAuth instance with credentials
            config: SimpleSyncConfig configuration
        """
        super().__init__(auth, config)

    def user_state(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user's account state (balance + positions) - NATIVE SYNC.

        Args:
            address: Ignored (Extended requires auth, uses authenticated user)

        Returns:
            Dict with Hyperliquid-compatible structure containing:
            - assetPositions: List of position info
            - crossMarginSummary: Account value and margin info
            - marginSummary: Margin details
            - withdrawable: Available for withdrawal
        """
        if address is not None and address != self.auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        # Endpoints from x10/perpetual/trading_client/account_module.py
        balance_response = self.get("/user/balance", authenticated=True)
        positions_response = self.get("/user/positions", authenticated=True)

        return SyncAccountTransformer.transform_user_state(
            balance_response.get("data", {}),
            positions_response.get("data", []) or [],
        )

    def open_orders(self, address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's open orders - NATIVE SYNC.

        Args:
            address: Ignored (uses authenticated user)

        Returns:
            List of orders in Hyperliquid format
        """
        if address is not None and address != self.auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        # Endpoint: /user/orders
        response = self.get("/user/orders", authenticated=True)
        return SyncOrderTransformer.transform_open_orders(response.get("data", []) or [])

    def meta(self) -> Dict[str, Any]:
        """
        Get exchange metadata (markets info) - NATIVE SYNC.

        Returns:
            Dict with Hyperliquid-compatible structure with universe list
        """
        # Endpoint: /info/markets
        response = self.get("/info/markets", authenticated=False)
        return SyncMarketTransformer.transform_meta(response.get("data", []) or [])

    def all_mids(self) -> Dict[str, str]:
        """
        Get mid prices for all markets - NATIVE SYNC.

        Returns:
            Dict mapping coin name to mid price string
        """
        # Endpoint: /info/markets (includes stats)
        response = self.get("/info/markets", authenticated=False)
        return SyncMarketTransformer.transform_all_mids(response.get("data", []) or [])

    def l2_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Get order book snapshot - NATIVE SYNC.

        Args:
            name: Market name (e.g., "BTC-USD" or "BTC")

        Returns:
            Dict in Hyperliquid format with coin, levels, and time
        """
        market_name = normalize_market_name(name)
        # Endpoint: /info/markets/<market>/orderbook
        response = self.get(f"/info/markets/{market_name}/orderbook", authenticated=False)
        return SyncMarketTransformer.transform_l2_snapshot(response.get("data", {}))

    def candles_snapshot(
        self,
        name: str,
        interval: str,
        startTime: int,
        endTime: int,
        candle_type: str = DEFAULT_CANDLE_TYPE,
    ) -> List[Dict[str, Any]]:
        """
        Get historical candles - NATIVE SYNC.

        Args:
            name: Market name (e.g., "BTC" or "BTC-USD")
            interval: "1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"
            startTime: Start timestamp (ms)
            endTime: End timestamp (ms)
            candle_type: Type of candle data (default "trades")

        Returns:
            List of candles in Hyperliquid format
        """
        market_name = normalize_market_name(name)
        extended_interval = INTERVAL_MAPPING.get(interval, "PT1M")

        # Convert endTime to milliseconds for API
        params = {
            "interval": extended_interval,
            "endTime": endTime,
            "limit": 1000,
        }

        # Endpoint: /info/candles/<market>/<candle_type>
        response = self.get(
            f"/info/candles/{market_name}/{candle_type}",
            params=params,
            authenticated=False
        )

        # Filter candles by startTime
        candles = response.get("data", []) or []
        filtered_candles = [c for c in candles if c.get("timestamp", 0) >= startTime]

        coin = to_hyperliquid_market_name(name)
        return SyncMarketTransformer.transform_candles(filtered_candles, coin, interval)

    def user_fills(
        self,
        coin: Optional[str] = None,
        address: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get user's trade fills - NATIVE SYNC.

        Args:
            coin: Market name (optional - if None, returns fills for all markets)
            address: Ignored (uses authenticated user)
            start_time: Optional start timestamp (ms)
            end_time: Optional end timestamp (ms)

        Returns:
            List of fills in Hyperliquid format (up to 1000 most recent)
        """
        if address is not None and address != self.auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        params = {}
        if coin:
            params["market"] = normalize_market_name(coin)

        # Endpoint: /user/trades
        response = self.get("/user/trades", params=params, authenticated=True)
        trades = response.get("data", []) or []

        # Filter by time if provided
        if start_time is not None:
            trades = [t for t in trades if t.get("createdTime", t.get("created_time", 0)) >= start_time]
        if end_time is not None:
            trades = [t for t in trades if t.get("createdTime", t.get("created_time", 0)) <= end_time]

        return SyncOrderTransformer.transform_user_fills(trades)

    def get_position_leverage(
        self,
        symbol: str,
        address: Optional[str] = None,
    ) -> Optional[int]:
        """
        Get current leverage for a position - NATIVE SYNC.

        Args:
            symbol: Market name (e.g., "BTC" or "BTC-USD")
            address: Ignored (uses authenticated user)

        Returns:
            Current leverage as integer, or None if not found
        """
        if address is not None and address != self.auth.address:
            warnings.warn(
                "Extended Exchange does not support querying other users. "
                f"Ignoring address={address}, using authenticated user.",
                UserWarning,
            )

        market_name = normalize_market_name(symbol)
        params = {"market": [market_name]}

        # Endpoint: /user/leverage
        response = self.get("/user/leverage", params=params, authenticated=True)

        leverage_data = response.get("data", []) or []
        if leverage_data:
            for lev in leverage_data:
                if lev.get("market") == market_name:
                    return int(lev.get("leverage", 0))

        return None
