"""
Native Sync Exchange API for Extended Exchange SDK.

Provides trading operations matching Hyperliquid's Exchange class interface.
Uses direct HTTP calls with requests and X10 signing infrastructure.
"""

import time
import warnings
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Any, Dict, List, Optional

from extended.api.base_native_sync import BaseNativeSyncClient, ExtendedAPIError
from extended.auth_sync import SimpleSyncAuth
from extended.config_sync import SimpleSyncConfig
from extended.transformers_sync import (
    SyncOrderTransformer,
    normalize_market_name,
    to_hyperliquid_market_name,
)

# Import X10 signing infrastructure (all sync!)
from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import StarknetDomain
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OrderSide, TimeInForce

# Constants
DEFAULT_SLIPPAGE = 0.05
MARKET_ORDER_PRICE_CAP = 1.05
MARKET_ORDER_PRICE_FLOOR = 0.95

# Time in force mapping (Hyperliquid -> X10)
TIF_MAPPING = {
    "Gtc": TimeInForce.GTT,
    "Ioc": TimeInForce.IOC,
    "Alo": TimeInForce.GTT,  # ALO uses GTT with post_only=True
}


class ExtendedValidationError(Exception):
    """Validation error for Exchange API."""
    pass


def parse_order_type(order_type: Optional[Dict[str, Any]]) -> tuple:
    """
    Parse Hyperliquid order_type to Extended params.

    Returns:
        Tuple of (TimeInForce, post_only)
    """
    if order_type is None:
        return TimeInForce.GTT, False

    if "limit" in order_type:
        tif = order_type["limit"].get("tif", "Gtc")
        post_only = tif == "Alo"
        return TIF_MAPPING.get(tif, TimeInForce.GTT), post_only

    return TimeInForce.GTT, False


def parse_builder(builder: Optional[Dict[str, Any]]) -> tuple:
    """
    Parse Hyperliquid builder format to Extended params.

    Returns:
        Tuple of (builder_id, builder_fee)
    """
    if builder is None:
        return None, None

    builder_id = int(builder["b"])
    fee_tenths_bps = builder.get("f", 0)
    builder_fee = Decimal(fee_tenths_bps) / Decimal(100000)

    return builder_id, builder_fee


class NativeSyncExchangeAPI(BaseNativeSyncClient):
    """
    Extended Exchange Native Sync trading API with Hyperliquid-compatible interface.

    Uses requests for HTTP and X10 signing infrastructure for order signing.
    All operations are synchronous.

    Example:
        exchange = NativeSyncExchangeAPI(auth, config)
        result = exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)
        exchange.cancel("BTC", oid=12345)
    """

    def __init__(self, auth: SimpleSyncAuth, config: SimpleSyncConfig):
        """
        Initialize the native sync Exchange API.

        Args:
            auth: SimpleSyncAuth instance with credentials
            config: SimpleSyncConfig configuration
        """
        super().__init__(auth, config)

        # Create StarkPerpetualAccount for signing (sync!)
        self._stark_account = StarkPerpetualAccount(
            vault=auth.vault,
            private_key=auth.stark_private_key,
            public_key=auth.stark_public_key,
            api_key=auth.api_key,
        )

        # Create StarknetDomain from config
        self._starknet_domain = StarknetDomain(
            name="Perpetuals",
            version="v0",
            chain_id="SN_MAIN" if "sepolia" not in config.api_base_url else "SN_SEPOLIA",
            revision="1",
        )

        # Cache for market models
        self._markets_cache: Dict[str, MarketModel] = {}

    def _get_market(self, market_name: str) -> MarketModel:
        """
        Get MarketModel for a market, with caching.

        Args:
            market_name: Market name in Extended format (e.g., "BTC-USD")

        Returns:
            MarketModel instance
        """
        if market_name not in self._markets_cache:
            # Fetch markets from API
            response = self.get("/info/markets", authenticated=False)
            markets_data = response.get("data", [])

            for market_data in markets_data:
                try:
                    market = MarketModel.model_validate(market_data)
                    self._markets_cache[market.name] = market
                except Exception:
                    # Skip markets that fail to parse
                    pass

        if market_name not in self._markets_cache:
            raise ExtendedValidationError(f"Market {market_name} not found")

        return self._markets_cache[market_name]

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
        Place a limit order - NATIVE SYNC with proper signing.

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
        market_name = normalize_market_name(name)
        side = OrderSide.BUY if is_buy else OrderSide.SELL
        tif, post_only = parse_order_type(order_type)
        builder_id, builder_fee = parse_builder(builder)

        try:
            # Get market model for order creation
            market = self._get_market(market_name)

            # Create signed order using X10 infrastructure (all sync!)
            order = create_order_object(
                account=self._stark_account,
                market=market,
                amount_of_synthetic=Decimal(str(sz)),
                price=Decimal(str(limit_px)),
                side=side,
                starknet_domain=self._starknet_domain,
                post_only=post_only,
                time_in_force=tif,
                order_external_id=cloid,
                builder_fee=builder_fee,
                builder_id=builder_id,
                reduce_only=reduce_only,
            )

            # Send order via HTTP
            order_data = order.to_api_request_json(exclude_none=True)
            response = self.post("/user/order", data=order_data, authenticated=True)

            # Transform response
            data = response.get("data", {})
            return {
                "status": "ok",
                "response": {
                    "type": "order",
                    "data": {
                        "statuses": [
                            {
                                "resting": {
                                    "oid": data.get("id", data.get("orderId", 0)),
                                    "cloid": data.get("externalId", cloid),
                                }
                            }
                        ]
                    },
                },
            }

        except ExtendedAPIError as e:
            return SyncOrderTransformer.transform_error_response(str(e.message))
        except Exception as e:
            return SyncOrderTransformer.transform_error_response(str(e))

    def bulk_orders(
        self,
        order_requests: List[Dict[str, Any]],
        builder: Optional[Dict[str, Any]] = None,
        grouping: str = "na",
    ) -> Dict[str, Any]:
        """
        Place multiple orders sequentially - NATIVE SYNC.

        WARNING: Unlike Hyperliquid, Extended does not support atomic
        bulk orders. Orders are sent sequentially and may partially fail.

        Args:
            order_requests: List of order dicts with keys:
                - coin, is_buy, sz, limit_px, order_type, reduce_only, cloid
            builder: Builder info applied to all orders
            grouping: Ignored (no native support)

        Returns:
            Combined results from all orders
        """
        results = []

        for request in order_requests:
            try:
                result = self.order(
                    name=request["coin"],
                    is_buy=request["is_buy"],
                    sz=request["sz"],
                    limit_px=request["limit_px"],
                    order_type=request.get("order_type", {"limit": {"tif": "Gtc"}}),
                    reduce_only=request.get("reduce_only", False),
                    cloid=request.get("cloid"),
                    builder=builder or request.get("builder"),
                )

                if result.get("status") == "ok":
                    statuses = result.get("response", {}).get("data", {}).get("statuses", [])
                    if statuses and "resting" in statuses[0]:
                        results.append({
                            "status": "ok",
                            "data": {
                                "id": statuses[0]["resting"]["oid"],
                                "external_id": statuses[0]["resting"]["cloid"],
                            }
                        })
                    else:
                        results.append({"status": "error", "error": result.get("response", "Unknown error")})
                else:
                    results.append({"status": "error", "error": result.get("response", "Unknown error")})

            except Exception as e:
                results.append({"status": "error", "error": str(e)})

        return SyncOrderTransformer.transform_bulk_orders_response(results)

    def cancel(
        self,
        name: str,
        oid: Optional[int] = None,
        cloid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel an order by oid or cloid - NATIVE SYNC.

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
                # Endpoint: /user/order/<order_id> (DELETE)
                response = self.delete(f"/user/order/{oid}", authenticated=True)
            else:
                # Endpoint: /user/order?externalId=<cloid> (DELETE)
                response = self.delete("/user/order", params={"externalId": cloid}, authenticated=True)

            return SyncOrderTransformer.transform_cancel_response(success=True, order_id=oid)

        except ExtendedAPIError as e:
            return SyncOrderTransformer.transform_error_response(str(e.message))
        except Exception as e:
            return SyncOrderTransformer.transform_error_response(str(e))

    def cancel_by_cloid(self, name: str, cloid: str) -> Dict[str, Any]:
        """
        Cancel order by client order ID - NATIVE SYNC.

        Args:
            name: Market name
            cloid: Client order ID

        Returns:
            Cancel response in Hyperliquid format
        """
        return self.cancel(name, cloid=cloid)

    def bulk_cancel(
        self,
        cancel_requests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Cancel multiple orders - NATIVE SYNC.

        Args:
            cancel_requests: List of {"coin": str, "oid": int}
                            or {"coin": str, "cloid": str}

        Returns:
            Combined cancel results
        """
        oids = []
        cloids = []

        for req in cancel_requests:
            if "oid" in req and req["oid"] is not None:
                oids.append(req["oid"])
            elif "cloid" in req and req["cloid"] is not None:
                cloids.append(req["cloid"])

        try:
            cancel_data = {}
            if oids:
                cancel_data["orderIds"] = oids
            if cloids:
                cancel_data["externalOrderIds"] = cloids

            # Endpoint: /user/order/massCancel (POST)
            response = self.post("/user/order/massCancel", data=cancel_data, authenticated=True)

            return {
                "status": "ok",
                "response": {
                    "type": "cancel",
                    "data": {
                        "statuses": ["success"] * len(cancel_requests)
                    },
                },
            }

        except ExtendedAPIError as e:
            return SyncOrderTransformer.transform_error_response(str(e.message))
        except Exception as e:
            return SyncOrderTransformer.transform_error_response(str(e))

    def update_leverage(
        self,
        leverage: int,
        name: str,
        is_cross: bool = True,
    ) -> Dict[str, Any]:
        """
        Update leverage for a market - NATIVE SYNC.

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
            leverage_data = {
                "market": market_name,
                "leverage": str(leverage)
            }

            # Endpoint: /user/leverage (PATCH)
            response = self.patch("/user/leverage", data=leverage_data, authenticated=True)
            return SyncOrderTransformer.transform_leverage_response()

        except ExtendedAPIError as e:
            return SyncOrderTransformer.transform_error_response(str(e.message))
        except Exception as e:
            return SyncOrderTransformer.transform_error_response(str(e))

    def _calculate_market_order_price(
        self,
        name: str,
        is_buy: bool,
        slippage: float,
    ) -> Decimal:
        """
        Calculate limit price for simulated market order - NATIVE SYNC.

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
        market_name = normalize_market_name(name)

        # Get market for tick size
        market = self._get_market(market_name)
        tick_size = market.trading_config.min_price_change

        # Get orderbook and stats
        orderbook_response = self.get(f"/info/markets/{market_name}/orderbook", authenticated=False)
        stats_response = self.get(f"/info/markets/{market_name}/stats", authenticated=False)

        orderbook = orderbook_response.get("data", {})
        stats = stats_response.get("data", {})
        mark_price = Decimal(str(stats.get("markPrice", stats.get("mark_price", "0"))))

        if is_buy:
            asks = orderbook.get("ask", orderbook.get("asks", []))
            best_ask = Decimal(str(asks[0].get("price", mark_price))) if asks else mark_price

            target_price = best_ask * Decimal(1 + slippage)
            max_price = mark_price * Decimal(str(MARKET_ORDER_PRICE_CAP))
            price = min(target_price, max_price)

            return (price / tick_size).quantize(Decimal('1'), rounding=ROUND_CEILING) * tick_size
        else:
            bids = orderbook.get("bid", orderbook.get("bids", []))
            best_bid = Decimal(str(bids[0].get("price", mark_price))) if bids else mark_price

            target_price = best_bid * Decimal(1 - slippage)
            min_price = mark_price * Decimal(str(MARKET_ORDER_PRICE_FLOOR))
            price = max(target_price, min_price)

            return (price / tick_size).quantize(Decimal('1'), rounding=ROUND_FLOOR) * tick_size

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
        Open a position with a market order - NATIVE SYNC.

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
            limit_price = self._calculate_market_order_price(name, is_buy, slippage)

        return self.order(
            name=name,
            is_buy=is_buy,
            sz=sz,
            limit_px=float(limit_price),
            order_type={"limit": {"tif": "Ioc"}},
            reduce_only=False,
            cloid=cloid,
            builder=builder,
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
        Close a position with a market order - NATIVE SYNC.

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

        # Get current position
        params = {"market": [market_name]}
        positions_response = self.get("/user/positions", params=params, authenticated=True)

        positions = positions_response.get("data", [])
        if not positions:
            return SyncOrderTransformer.transform_error_response(
                f"No open position found for {coin}"
            )

        position = positions[0]

        # Determine size to close
        close_sz = float(sz) if sz is not None else abs(float(position.get("size", 0)))

        # Close is opposite side
        side = position.get("side", "LONG")
        is_buy = side == "SHORT"

        if px is not None:
            limit_price = Decimal(str(px))
        else:
            limit_price = self._calculate_market_order_price(coin, is_buy, slippage)

        return self.order(
            name=coin,
            is_buy=is_buy,
            sz=close_sz,
            limit_px=float(limit_price),
            order_type={"limit": {"tif": "Ioc"}},
            reduce_only=True,
            cloid=cloid,
            builder=builder,
        )
