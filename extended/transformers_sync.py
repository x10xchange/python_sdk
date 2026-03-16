"""
Native Sync Transformers for Extended Exchange SDK.

Converts raw API JSON responses (dict data) to Hyperliquid format.
No X10 model dependencies - works entirely with raw dicts.
"""

import time
from decimal import Decimal
from typing import Any, Dict, List, Optional


# ============================================================================
# CONSTANTS (duplicated to avoid X10 dependencies)
# ============================================================================

SIDE_TO_HL = {
    "BUY": "B",
    "SELL": "A",
    "LONG": "B",
    "SHORT": "A",
}

INTERVAL_MS = {
    "1m": 60000,
    "5m": 300000,
    "15m": 900000,
    "30m": 1800000,
    "1h": 3600000,
    "2h": 7200000,
    "4h": 14400000,
    "1d": 86400000,
}


def normalize_market_name(name: str) -> str:
    """Convert market name to Extended format (BTC -> BTC-USD)."""
    if "-" not in name:
        return f"{name}-USD"
    return name


def to_hyperliquid_market_name(name: str) -> str:
    """Convert Extended market name to Hyperliquid format (BTC-USD -> BTC)."""
    return name.replace("-USD", "")


def calculate_sz_decimals(min_order_size_change) -> int:
    """Calculate size decimals from minimum order size change."""
    if not min_order_size_change:
        return 0
    val = Decimal(str(min_order_size_change))
    if val <= 0:
        return 0
    return abs(int(val.log10()))


# ============================================================================
# ACCOUNT TRANSFORMERS
# ============================================================================

class SyncAccountTransformer:
    """Transform raw API account data to Hyperliquid format."""

    @staticmethod
    def transform_user_state(
        balance_data: Dict[str, Any],
        positions_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Transform raw balance + positions to Hyperliquid user_state format.

        Args:
            balance_data: Raw balance dict from API
            positions_data: Raw positions list from API

        Returns:
            Dict in Hyperliquid user_state format
        """
        # Extract balance fields with defaults
        equity = balance_data.get("equity", "0")
        balance = balance_data.get("balance", "0")
        initial_margin = balance_data.get("initialMargin", balance_data.get("initial_margin", "0"))
        available_for_trade = balance_data.get("availableForTrade", balance_data.get("available_for_trade", "0"))

        # Calculate total position value
        total_position_value = Decimal("0")
        for pos in positions_data:
            val = pos.get("value", "0")
            total_position_value += Decimal(str(val)) if val else Decimal("0")

        # Transform positions
        asset_positions = [
            SyncAccountTransformer.transform_position(pos)
            for pos in positions_data
        ]

        return {
            "assetPositions": asset_positions,
            "crossMaintenanceMarginUsed": str(initial_margin),
            "crossMarginSummary": {
                "accountValue": str(equity),
                "totalMarginUsed": str(initial_margin),
                "totalNtlPos": str(total_position_value),
                "totalRawUsd": str(balance),
            },
            "marginSummary": {
                "accountValue": str(equity),
                "totalMarginUsed": str(initial_margin),
                "totalNtlPos": str(total_position_value),
                "totalRawUsd": str(balance),
                "withdrawable": str(available_for_trade),
            },
            "withdrawable": str(available_for_trade),
        }

    @staticmethod
    def transform_position(position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw position to Hyperliquid assetPosition format.

        Args:
            position: Raw position dict from API

        Returns:
            Dict in Hyperliquid assetPosition format
        """
        market = position.get("market", "")
        size = Decimal(str(position.get("size", "0")))
        side = position.get("side", "LONG")
        leverage = int(position.get("leverage", 1))
        value = Decimal(str(position.get("value", "0")))
        open_price = position.get("openPrice", position.get("open_price", "0"))
        unrealised_pnl = Decimal(str(position.get("unrealisedPnl", position.get("unrealised_pnl", "0"))))
        liquidation_price = position.get("liquidationPrice", position.get("liquidation_price"))

        # Signed size: positive for LONG, negative for SHORT
        szi = str(size) if side == "LONG" else str(-size)

        # Calculate margin and ROE
        margin_used = value / leverage if leverage > 0 else Decimal("0")
        roe = unrealised_pnl / margin_used if margin_used > 0 else Decimal("0")

        return {
            "position": {
                "coin": to_hyperliquid_market_name(market),
                "szi": szi,
                "leverage": {"type": "cross", "value": leverage},
                "entryPx": str(open_price),
                "positionValue": str(value),
                "unrealizedPnl": str(unrealised_pnl),
                "liquidationPx": str(liquidation_price) if liquidation_price else None,
                "marginUsed": str(margin_used),
                "returnOnEquity": str(roe),
            },
            "type": "oneWay",
        }


# ============================================================================
# MARKET TRANSFORMERS
# ============================================================================

class SyncMarketTransformer:
    """Transform raw API market data to Hyperliquid format."""

    @staticmethod
    def transform_meta(markets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform raw markets list to Hyperliquid meta format.

        Args:
            markets_data: Raw markets list from API

        Returns:
            Dict in Hyperliquid meta format with universe list
        """
        universe = []
        for market in markets_data:
            if not market.get("active", True):
                continue

            trading_config = market.get("tradingConfig", market.get("trading_config", {}))
            min_order_size_change = trading_config.get("minOrderSizeChange", trading_config.get("min_order_size_change", "0.001"))
            max_leverage = trading_config.get("maxLeverage", trading_config.get("max_leverage", "50"))
            sz_decimals = calculate_sz_decimals(min_order_size_change)

            # Handle max_leverage as string with decimal (e.g., "50.00")
            try:
                max_lev_int = int(float(str(max_leverage)))
            except (ValueError, TypeError):
                max_lev_int = 50

            universe.append({
                "name": to_hyperliquid_market_name(market.get("name", "")),
                "szDecimals": sz_decimals,
                "maxLeverage": max_lev_int,
                "onlyIsolated": False,
            })

        return {"universe": universe}

    @staticmethod
    def transform_all_mids(markets_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Transform raw markets to mid prices dict.

        Args:
            markets_data: Raw markets list from API (with stats)

        Returns:
            Dict mapping coin name to mid price string
        """
        mids = {}
        for market in markets_data:
            stats = market.get("marketStats", market.get("market_stats", {}))
            bid = Decimal(str(stats.get("bidPrice", stats.get("bid_price", "0"))))
            ask = Decimal(str(stats.get("askPrice", stats.get("ask_price", "0"))))
            mid = (bid + ask) / 2 if (bid and ask) else Decimal("0")

            coin = to_hyperliquid_market_name(market.get("name", ""))
            mids[coin] = str(mid)

        return mids

    @staticmethod
    def transform_l2_snapshot(
        orderbook_data: Dict[str, Any],
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Transform raw orderbook to Hyperliquid l2_snapshot format.

        Args:
            orderbook_data: Raw orderbook dict from API
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Dict in Hyperliquid l2_snapshot format
        """
        def transform_levels(levels: List[Dict]) -> List[Dict[str, Any]]:
            return [
                {"px": str(level.get("price", "0")), "sz": str(level.get("qty", "0")), "n": 1}
                for level in levels
            ]

        market = orderbook_data.get("market", "")
        bids = orderbook_data.get("bid", orderbook_data.get("bids", []))
        asks = orderbook_data.get("ask", orderbook_data.get("asks", []))

        return {
            "coin": to_hyperliquid_market_name(market),
            "levels": [
                transform_levels(bids),
                transform_levels(asks),
            ],
            "time": timestamp or int(time.time() * 1000),
        }

    @staticmethod
    def transform_candles(
        candles_data: List[Dict[str, Any]],
        coin: str,
        interval: str,
    ) -> List[Dict[str, Any]]:
        """
        Transform raw candles to Hyperliquid format.

        Args:
            candles_data: Raw candles list from API
            coin: Coin name in Hyperliquid format (e.g., "BTC")
            interval: Interval in Hyperliquid format (e.g., "1m")

        Returns:
            List of candles in Hyperliquid format
        """
        interval_ms = INTERVAL_MS.get(interval, 60000)

        return [
            {
                "t": candle.get("timestamp", 0),
                "T": candle.get("timestamp", 0) + interval_ms,
                "s": coin,
                "i": interval,
                "o": str(candle.get("open", "0")),
                "c": str(candle.get("close", "0")),
                "h": str(candle.get("high", "0")),
                "l": str(candle.get("low", "0")),
                "v": str(candle.get("volume", "0")),
                "n": 0,
            }
            for candle in candles_data
        ]


# ============================================================================
# ORDER TRANSFORMERS
# ============================================================================

class SyncOrderTransformer:
    """Transform raw API order data to Hyperliquid format."""

    @staticmethod
    def transform_open_orders(orders_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw orders to Hyperliquid open_orders format.

        Args:
            orders_data: Raw orders list from API

        Returns:
            List of orders in Hyperliquid format
        """
        return [
            SyncOrderTransformer.transform_open_order(order)
            for order in orders_data
        ]

    @staticmethod
    def transform_open_order(order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw order to Hyperliquid format.

        Args:
            order: Raw order dict from API

        Returns:
            Dict in Hyperliquid open order format
        """
        qty = Decimal(str(order.get("qty", "0")))
        filled_qty = Decimal(str(order.get("filledQty", order.get("filled_qty", "0"))))
        remaining_sz = qty - filled_qty

        side = order.get("side", "BUY")
        market = order.get("market", "")
        price = order.get("price", "0")
        order_id = order.get("id", 0)
        created_time = order.get("createdTime", order.get("created_time", 0))
        external_id = order.get("externalId", order.get("external_id"))

        return {
            "coin": to_hyperliquid_market_name(market),
            "side": SIDE_TO_HL.get(side, "B"),
            "limitPx": str(price),
            "sz": str(remaining_sz),
            "oid": order_id,
            "timestamp": created_time,
            "origSz": str(qty),
            "cloid": external_id,
        }

    @staticmethod
    def transform_user_fills(trades_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw trades to Hyperliquid user_fills format.

        Args:
            trades_data: Raw trades list from API

        Returns:
            List of fills in Hyperliquid format
        """
        return [
            SyncOrderTransformer.transform_fill(trade)
            for trade in trades_data
        ]

    @staticmethod
    def transform_fill(trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single raw trade to Hyperliquid fill format.

        Args:
            trade: Raw trade dict from API

        Returns:
            Dict in Hyperliquid fill format
        """
        market = trade.get("market", "")
        side = trade.get("side", "BUY")
        trade_type = trade.get("tradeType", trade.get("trade_type", "TRADE"))
        is_taker = trade.get("isTaker", trade.get("is_taker", False))

        return {
            "coin": to_hyperliquid_market_name(market),
            "px": str(trade.get("price", "0")),
            "sz": str(trade.get("qty", "0")),
            "side": SIDE_TO_HL.get(side, "B"),
            "time": trade.get("createdTime", trade.get("created_time", 0)),
            "startPosition": "0",
            "dir": "Trade",
            "closedPnl": "0",
            "hash": str(trade.get("id", "")),
            "oid": trade.get("orderId", trade.get("order_id", 0)),
            "crossed": is_taker,
            "fee": str(trade.get("fee", "0")),
            "tid": trade.get("id", 0),
            "liquidation": trade_type == "LIQUIDATION",
            "cloid": None,
        }

    @staticmethod
    def transform_order_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw order placement response to Hyperliquid format.

        Args:
            response_data: Raw response dict from API

        Returns:
            Dict in Hyperliquid order response format
        """
        order_id = response_data.get("id", response_data.get("orderId", 0))
        external_id = response_data.get("externalId", response_data.get("external_id"))

        return {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": [
                        {
                            "resting": {
                                "oid": order_id,
                                "cloid": external_id,
                            }
                        }
                    ]
                },
            },
        }

    @staticmethod
    def transform_cancel_response(success: bool = True, order_id: Optional[int] = None) -> Dict[str, Any]:
        """Transform cancel response to Hyperliquid format."""
        if success:
            return {
                "status": "ok",
                "response": {
                    "type": "cancel",
                    "data": {"statuses": ["success"]},
                },
            }
        return {"status": "err", "response": "Cancel failed"}

    @staticmethod
    def transform_error_response(message: str) -> Dict[str, Any]:
        """Transform an error to Hyperliquid error format."""
        return {"status": "err", "response": message}

    @staticmethod
    def transform_bulk_orders_response(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform bulk order results to Hyperliquid format."""
        statuses = []
        for result in results:
            if result.get("status") == "ok":
                data = result.get("data", {})
                statuses.append({
                    "resting": {
                        "oid": data.get("id"),
                        "cloid": data.get("external_id"),
                    }
                })
            else:
                statuses.append({"error": result.get("error", "Unknown error")})

        return {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {"statuses": statuses},
            },
        }

    @staticmethod
    def transform_leverage_response() -> Dict[str, Any]:
        """Transform leverage update response to Hyperliquid format."""
        return {"status": "ok", "response": {"type": "leverage"}}
