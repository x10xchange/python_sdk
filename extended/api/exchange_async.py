"""
Async Exchange API for Extended Exchange SDK.

Provides trading operations matching Hyperliquid's Exchange class interface.
"""

import warnings
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.orders import OrderSide, TimeInForce as X10TimeInForce

from extended.api.base_async import BaseAsyncAPI
from extended.auth import ExtendedAuth
from extended.exceptions import ExtendedAPIError, ExtendedValidationError
from extended.transformers import OrderTransformer
from extended.utils.async_helpers import thread_safe_gather
from extended.utils.constants import (
    DEFAULT_SLIPPAGE,
    MARKET_ORDER_PRICE_CAP,
    MARKET_ORDER_PRICE_FLOOR,
    SIDE_MAPPING,
)
from extended.utils.helpers import normalize_market_name, parse_builder, parse_order_type


class AsyncExchangeAPI(BaseAsyncAPI):
    """
    Extended Exchange trading API with Hyperliquid-compatible interface.

    Handles order placement, cancellation, and account management.

    Example:
        async_exchange = AsyncExchangeAPI(auth, config)
        result = await async_exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)
        await async_exchange.cancel("BTC", oid=12345)
    """

    def __init__(self, auth: ExtendedAuth, config: EndpointConfig):
        """
        Initialize the async Exchange API.

        Args:
            auth: ExtendedAuth instance with credentials
            config: Endpoint configuration
        """
        super().__init__(auth, config)

    async def order(
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
            Hyperliquid-format response:
            {"status": "ok", "response": {"type": "order", "data": {"statuses": [...]}}}
        """
        if order_type is None:
            order_type = {"limit": {"tif": "Gtc"}}

        market_name = normalize_market_name(name)
        side = OrderSide.BUY if is_buy else OrderSide.SELL
        tif, post_only = parse_order_type(order_type)
        builder_id, builder_fee = parse_builder(builder)

        try:
            response = await self._client.place_order(
                market_name=market_name,
                amount_of_synthetic=Decimal(str(sz)),
                price=Decimal(str(limit_px)),
                side=side,
                post_only=post_only,
                time_in_force=tif,
                external_id=cloid,
                builder_id=builder_id,
                builder_fee=builder_fee,
                reduce_only=reduce_only,
            )

            return OrderTransformer.transform_order_response(response.data)

        except Exception as e:
            return OrderTransformer.transform_error_response(str(e))

    async def bulk_orders(
        self,
        order_requests: List[Dict[str, Any]],
        builder: Optional[Dict[str, Any]] = None,
        grouping: str = "na",
    ) -> Dict[str, Any]:
        """
        Place multiple orders in parallel.

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
        async def place_single(request: Dict[str, Any]) -> Dict[str, Any]:
            try:
                result = await self.order(
                    name=request["coin"],
                    is_buy=request["is_buy"],
                    sz=request["sz"],
                    limit_px=request["limit_px"],
                    order_type=request.get("order_type", {"limit": {"tif": "Gtc"}}),
                    reduce_only=request.get("reduce_only", False),
                    cloid=request.get("cloid"),
                    builder=builder or request.get("builder"),
                )

                # Extract the placed order data from the response
                if result.get("status") == "ok":
                    statuses = result.get("response", {}).get("data", {}).get("statuses", [])
                    if statuses and "resting" in statuses[0]:
                        return {
                            "status": "ok",
                            "data": {
                                "id": statuses[0]["resting"]["oid"],
                                "external_id": statuses[0]["resting"]["cloid"],
                            }
                        }
                return {"status": "error", "error": result.get("response", "Unknown error")}

            except Exception as e:
                return {"status": "error", "error": str(e)}

        # Execute all orders in parallel
        results = await thread_safe_gather(
            *[place_single(req) for req in order_requests],
            return_exceptions=True,
        )

        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({"status": "error", "error": str(result)})
            else:
                processed_results.append(result)

        return OrderTransformer.transform_bulk_orders_response(processed_results)

    async def cancel(
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
            Hyperliquid-format response:
            {"status": "ok", "response": {"type": "cancel", "data": {"statuses": [...]}}}
        """
        if oid is None and cloid is None:
            raise ExtendedValidationError("Either oid or cloid must be provided")

        try:
            if oid is not None:
                await self._client.orders.cancel_order(order_id=oid)
            else:
                await self._client.orders.cancel_order_by_external_id(
                    order_external_id=cloid  # type: ignore
                )

            return OrderTransformer.transform_cancel_response(success=True, order_id=oid)

        except Exception as e:
            return OrderTransformer.transform_error_response(str(e))

    async def cancel_by_cloid(self, name: str, cloid: str) -> Dict[str, Any]:
        """
        Cancel order by client order ID.

        Args:
            name: Market name
            cloid: Client order ID

        Returns:
            Cancel response in Hyperliquid format
        """
        return await self.cancel(name, cloid=cloid)

    async def bulk_cancel(
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
        # Group by oids and cloids for mass cancel
        oids = []
        cloids = []

        for req in cancel_requests:
            if "oid" in req and req["oid"] is not None:
                oids.append(req["oid"])
            elif "cloid" in req and req["cloid"] is not None:
                cloids.append(req["cloid"])

        try:
            await self._client.orders.mass_cancel(
                order_ids=oids if oids else None,
                external_order_ids=cloids if cloids else None,
            )

            return {
                "status": "ok",
                "response": {
                    "type": "cancel",
                    "data": {
                        "statuses": ["success"] * len(cancel_requests)
                    },
                },
            }

        except Exception as e:
            return OrderTransformer.transform_error_response(str(e))

    async def update_leverage(
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
            Hyperliquid-format response:
            {"status": "ok", "response": {"type": "leverage"}}
        """
        if not is_cross:
            warnings.warn(
                "Extended Exchange only supports cross margin. "
                "is_cross=False will be ignored.",
                UserWarning,
            )

        market_name = normalize_market_name(name)

        try:
            await self._client.account.update_leverage(
                market_name=market_name,
                leverage=Decimal(leverage),
            )

            return OrderTransformer.transform_leverage_response()

        except Exception as e:
            return OrderTransformer.transform_error_response(str(e))

    async def _calculate_market_order_price(
        self,
        name: str,
        is_buy: bool,
        slippage: float,
    ) -> Decimal:
        """
        Calculate limit price for simulated market order.

        Extended constraints:
        - Buy: price <= mark_price * 1.05
        - Sell: price >= mark_price * 0.95

        Args:
            name: Market name
            is_buy: True for buy
            slippage: Max slippage (e.g., 0.05 for 5%)

        Returns:
            Calculated limit price (rounded to market precision)
        """
        from decimal import ROUND_CEILING, ROUND_FLOOR

        market_name = normalize_market_name(name)

        # Get orderbook, market stats, and market config in parallel
        orderbook_task = self._client.markets_info.get_orderbook_snapshot(
            market_name=market_name
        )
        stats_task = self._client.markets_info.get_market_statistics(
            market_name=market_name
        )
        markets_task = self._client.markets_info.get_markets_dict()

        orderbook_response, stats_response, markets_dict = await thread_safe_gather(
            orderbook_task, stats_task, markets_task
        )

        orderbook = orderbook_response.data
        stats = stats_response.data
        mark_price = stats.mark_price
        market = markets_dict[market_name]

        if is_buy:
            # Use best ask with slippage, capped at mark * 1.05
            best_ask = (
                orderbook.ask[0].price
                if orderbook.ask
                else mark_price
            )
            target_price = best_ask * Decimal(1 + slippage)
            max_price = mark_price * Decimal(str(MARKET_ORDER_PRICE_CAP))
            price = min(target_price, max_price)
            # Round up for buys to ensure fill
            return market.trading_config.round_price(price, ROUND_CEILING)
        else:
            # Use best bid with slippage, floored at mark * 0.95
            best_bid = (
                orderbook.bid[0].price
                if orderbook.bid
                else mark_price
            )
            target_price = best_bid * Decimal(1 - slippage)
            min_price = mark_price * Decimal(str(MARKET_ORDER_PRICE_FLOOR))
            price = max(target_price, min_price)
            # Round down for sells to ensure fill
            return market.trading_config.round_price(price, ROUND_FLOOR)

    async def market_open(
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
        if px is not None:
            limit_price = Decimal(str(px))
        else:
            limit_price = await self._calculate_market_order_price(
                name, is_buy, slippage
            )

        return await self.order(
            name=name,
            is_buy=is_buy,
            sz=sz,
            limit_px=float(limit_price),
            order_type={"limit": {"tif": "Ioc"}},
            reduce_only=False,
            cloid=cloid,
            builder=builder,
        )

    async def market_close(
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
        market_name = normalize_market_name(coin)

        # Get current position to determine size and side
        positions_response = await self._client.account.get_positions(
            market_names=[market_name]
        )

        positions = positions_response.data or []
        if not positions:
            return OrderTransformer.transform_error_response(
                f"No open position found for {coin}"
            )

        position = positions[0]

        # Determine size to close
        close_sz = float(sz) if sz is not None else float(position.size)

        # Close is opposite side (side can be str or PositionSide enum)
        side = position.side.value if hasattr(position.side, 'value') else position.side
        is_buy = side == "SHORT"

        if px is not None:
            limit_price = Decimal(str(px))
        else:
            limit_price = await self._calculate_market_order_price(
                coin, is_buy, slippage
            )

        return await self.order(
            name=coin,
            is_buy=is_buy,
            sz=close_sz,
            limit_px=float(limit_price),
            order_type={"limit": {"tif": "Ioc"}},
            reduce_only=True,
            cloid=cloid,
            builder=builder,
        )
