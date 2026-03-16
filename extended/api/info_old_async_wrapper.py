"""
Sync Info API for Extended Exchange SDK.

Provides read-only operations matching Hyperliquid's Info class interface.
Wraps AsyncInfoAPI to provide synchronous interface.
"""

from typing import Any, Dict, List, Optional

from x10.perpetual.configuration import EndpointConfig

from extended.api.base import BaseSyncAPI
from extended.api.info_async import AsyncInfoAPI
from extended.auth import ExtendedAuth
from extended.utils.helpers import run_sync


class InfoAPI(BaseSyncAPI):
    """
    Extended Exchange Info API with Hyperliquid-compatible interface.

    Synchronous wrapper around AsyncInfoAPI.

    Note: Unlike Hyperliquid, Extended requires authentication for
    user-specific data. The `address` parameter is accepted for
    interface compatibility but ignored (uses authenticated user).

    Example:
        info = InfoAPI(auth, config)
        state = info.user_state()
        orders = info.open_orders()
    """

    def __init__(self, auth: ExtendedAuth, config: EndpointConfig):
        """
        Initialize the sync Info API.

        Args:
            auth: ExtendedAuth instance with credentials
            config: Endpoint configuration
        """
        super().__init__(auth, config)
        self._async = AsyncInfoAPI(auth, config)

    def user_state(self, address: Optional[str] = None) -> Dict[str, Any]:
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
        """
        return run_sync(lambda: self._async.user_state(address))

    def open_orders(self, address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's open orders.

        Args:
            address: Ignored (uses authenticated user)

        Returns:
            List of orders in Hyperliquid format
        """
        return run_sync(lambda: self._async.open_orders(address))

    def meta(self) -> Dict[str, Any]:
        """
        Get exchange metadata (markets info).

        Returns:
            Dict with Hyperliquid-compatible structure with universe list
        """
        return run_sync(lambda: self._async.meta())

    def all_mids(self) -> Dict[str, str]:
        """
        Get mid prices for all markets.

        Returns:
            Dict mapping coin name to mid price string
        """
        return run_sync(lambda: self._async.all_mids())

    def l2_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Get order book snapshot.

        Args:
            name: Market name (e.g., "BTC-USD" or "BTC")

        Returns:
            Dict in Hyperliquid format with coin, levels, and time
        """
        return run_sync(lambda: self._async.l2_snapshot(name))

    def candles_snapshot(
        self,
        name: str,
        interval: str,
        startTime: int,
        endTime: int,
        candle_type: str = "trades",
    ) -> List[Dict[str, Any]]:
        """
        Get historical candles.

        Args:
            name: Market name (e.g., "BTC" or "BTC-USD")
            interval: "1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"
            startTime: Start timestamp (ms)
            endTime: End timestamp (ms)
            candle_type: Type of candle data (default "trades")

        Returns:
            List of candles in Hyperliquid format
        """
        return run_sync(
            lambda: self._async.candles_snapshot(name, interval, startTime, endTime, candle_type)
        )

    def user_fills(
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
            The `cloid` field will be null in responses.
        """
        return run_sync(lambda: self._async.user_fills(coin, address, start_time, end_time))

    def get_position_leverage(
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
        return run_sync(lambda: self._async.get_position_leverage(symbol, address))

    def close(self):
        """Close the API and release resources."""
        run_sync(lambda: self._async.close())
