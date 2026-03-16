"""
Sync Exchange API for Extended Exchange SDK.

Provides trading operations matching Hyperliquid's Exchange class interface.
Wraps AsyncExchangeAPI to provide synchronous interface.
"""

from typing import Any, Dict, List, Optional

from x10.perpetual.configuration import EndpointConfig

from extended.api.base import BaseSyncAPI
from extended.api.exchange_async import AsyncExchangeAPI
from extended.auth import ExtendedAuth
from extended.utils.constants import DEFAULT_SLIPPAGE
from extended.utils.helpers import run_sync


class ExchangeAPI(BaseSyncAPI):
    """
    Extended Exchange trading API with Hyperliquid-compatible interface.

    Synchronous wrapper around AsyncExchangeAPI.

    Example:
        exchange = ExchangeAPI(auth, config)
        result = exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)
        exchange.cancel("BTC", oid=12345)
    """

    def __init__(self, auth: ExtendedAuth, config: EndpointConfig):
        """
        Initialize the sync Exchange API.

        Args:
            auth: ExtendedAuth instance with credentials
            config: Endpoint configuration
        """
        super().__init__(auth, config)
        self._async = AsyncExchangeAPI(auth, config)

    def order(
        self,
        name: str,
        is_buy: bool,
        sz: float,
        limit_px: float,
        order_type: Optional[Dict[str, Any]] = None,
        reduce_only: bool = False,
        cloid: Optional[str] = None,
        builder: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Place a limit order.

        Args:
            name: Market name (e.g., "BTC" or "BTC-USD")
            is_buy: True for buy, False for sell
            sz: Size in base asset
            limit_px: Limit price
            order_type: {"limit": {"tif": "Gtc"}} or {"limit": {"tif": "Ioc"}}
                       or {"limit": {"tif": "Alo"}} (post-only)
            reduce_only: Only reduce position
            cloid: Client order ID (maps to external_id)
            builder: {"b": builder_id, "f": fee_bps_tenths}

        Returns:
            Hyperliquid-format response
        """
        return run_sync(
            self._async.order(
                name=name,
                is_buy=is_buy,
                sz=sz,
                limit_px=limit_px,
                order_type=order_type,
                reduce_only=reduce_only,
                cloid=cloid,
                builder=builder,
            )
        )

    def bulk_orders(
        self,
        order_requests: List[Dict[str, Any]],
        builder: Optional[Dict[str, Any]] = None,
        grouping: str = "na",
    ) -> Dict[str, Any]:
        """
        Place multiple orders.

        WARNING: Unlike Hyperliquid, Extended does not support atomic
        bulk orders. Orders are sent in parallel and may partially fail.

        Args:
            order_requests: List of order dicts with keys:
                - coin, is_buy, sz, limit_px, order_type, reduce_only, cloid
            builder: Builder info applied to all orders
            grouping: Ignored (no native support)

        Returns:
            Combined results from all orders
        """
        return run_sync(
            self._async.bulk_orders(
                order_requests=order_requests,
                builder=builder,
                grouping=grouping,
            )
        )

    def cancel(
        self,
        name: str,
        oid: Optional[int] = None,
        cloid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel an order by oid or cloid.

        Args:
            name: Market name (required for Hyperliquid compat, may be ignored)
            oid: Internal order ID
            cloid: Client order ID (external_id)

        Returns:
            Cancel response in Hyperliquid format
        """
        return run_sync(self._async.cancel(name=name, oid=oid, cloid=cloid))

    def cancel_by_cloid(self, name: str, cloid: str) -> Dict[str, Any]:
        """
        Cancel order by client order ID.

        Args:
            name: Market name
            cloid: Client order ID

        Returns:
            Cancel response in Hyperliquid format
        """
        return run_sync(self._async.cancel_by_cloid(name=name, cloid=cloid))

    def bulk_cancel(
        self,
        cancel_requests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Cancel multiple orders.

        Args:
            cancel_requests: List of {"coin": str, "oid": int}
                            or {"coin": str, "cloid": str}

        Returns:
            Combined cancel results
        """
        return run_sync(self._async.bulk_cancel(cancel_requests=cancel_requests))

    def update_leverage(
        self,
        leverage: int,
        name: str,
        is_cross: bool = True,
    ) -> Dict[str, Any]:
        """
        Update leverage for a market.

        Args:
            leverage: Target leverage (1-50)
            name: Market name
            is_cross: Ignored (Extended only supports cross margin)

        Returns:
            Leverage update response in Hyperliquid format
        """
        return run_sync(
            self._async.update_leverage(
                leverage=leverage,
                name=name,
                is_cross=is_cross,
            )
        )

    def market_open(
        self,
        name: str,
        is_buy: bool,
        sz: float,
        px: Optional[float] = None,
        slippage: float = DEFAULT_SLIPPAGE,
        cloid: Optional[str] = None,
        builder: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Open a position with a market order.

        Note: Extended simulates market orders as IOC limit orders.

        Args:
            name: Market name
            is_buy: True for long, False for short
            sz: Size in base asset
            px: Optional price hint (uses orderbook if not provided)
            slippage: Max slippage (default 5%)
            cloid: Client order ID
            builder: Builder info

        Returns:
            Order response in Hyperliquid format
        """
        return run_sync(
            self._async.market_open(
                name=name,
                is_buy=is_buy,
                sz=sz,
                px=px,
                slippage=slippage,
                cloid=cloid,
                builder=builder,
            )
        )

    def market_close(
        self,
        coin: str,
        sz: Optional[float] = None,
        px: Optional[float] = None,
        slippage: float = DEFAULT_SLIPPAGE,
        cloid: Optional[str] = None,
        builder: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Close a position with a market order.

        Args:
            coin: Market name
            sz: Size to close (None = close entire position)
            px: Optional price hint
            slippage: Max slippage
            cloid: Client order ID
            builder: Builder info

        Returns:
            Order response in Hyperliquid format
        """
        return run_sync(
            self._async.market_close(
                coin=coin,
                sz=sz,
                px=px,
                slippage=slippage,
                cloid=cloid,
                builder=builder,
            )
        )

    def close(self):
        """Close the API and release resources."""
        run_sync(self._async.close())
