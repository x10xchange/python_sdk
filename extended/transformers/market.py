"""
Market data transformers.

Converts Extended market data to Hyperliquid format.
"""

import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from x10.perpetual.candles import CandleModel
from x10.perpetual.markets import MarketModel, MarketStatsModel
from x10.perpetual.orderbooks import OrderbookUpdateModel

from extended.utils.constants import INTERVAL_MS
from extended.utils.helpers import (
    calculate_sz_decimals,
    to_hyperliquid_market_name,
)


class MarketTransformer:
    """Transform Extended market data to Hyperliquid format."""

    @staticmethod
    def transform_meta(markets: List[MarketModel]) -> Dict[str, Any]:
        """
        Transform Extended markets list to Hyperliquid meta format.

        Args:
            markets: List of Extended MarketModel

        Returns:
            Dict in Hyperliquid meta format with universe list
        """
        universe = []
        for market in markets:
            if not market.active:
                continue

            trading_config = market.trading_config
            sz_decimals = calculate_sz_decimals(trading_config.min_order_size_change)

            universe.append({
                "name": to_hyperliquid_market_name(market.name),
                "szDecimals": sz_decimals,
                "maxLeverage": int(trading_config.max_leverage),
                "onlyIsolated": False,  # Extended only supports cross margin
            })

        return {"universe": universe}

    @staticmethod
    def transform_all_mids(markets: List[MarketModel]) -> Dict[str, str]:
        """
        Transform Extended markets to mid prices dict.

        Args:
            markets: List of Extended MarketModel (with stats)

        Returns:
            Dict mapping coin name to mid price string
        """
        mids = {}
        for market in markets:
            stats = market.market_stats
            bid = stats.bid_price
            ask = stats.ask_price
            mid = (bid + ask) / 2

            coin = to_hyperliquid_market_name(market.name)
            mids[coin] = str(mid)

        return mids

    @staticmethod
    def transform_l2_snapshot(
        orderbook: OrderbookUpdateModel,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Transform Extended orderbook to Hyperliquid l2_snapshot format.

        Args:
            orderbook: Extended OrderbookUpdateModel
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Dict in Hyperliquid l2_snapshot format
        """
        def transform_levels(levels: List[Any]) -> List[Dict[str, Any]]:
            return [
                {"px": str(level.price), "sz": str(level.qty), "n": 1}
                for level in levels
            ]

        return {
            "coin": to_hyperliquid_market_name(orderbook.market),
            "levels": [
                transform_levels(orderbook.bid),  # bids (index 0)
                transform_levels(orderbook.ask),  # asks (index 1)
            ],
            "time": timestamp or int(time.time() * 1000),
        }

    @staticmethod
    def transform_candles(
        candles: List[CandleModel],
        coin: str,
        interval: str,
    ) -> List[Dict[str, Any]]:
        """
        Transform Extended candles to Hyperliquid format.

        Args:
            candles: List of Extended CandleModel
            coin: Coin name in Hyperliquid format (e.g., "BTC")
            interval: Interval in Hyperliquid format (e.g., "1m")

        Returns:
            List of candles in Hyperliquid format
        """
        interval_ms = INTERVAL_MS.get(interval, 60000)

        return [
            {
                "t": candle.timestamp,
                "T": candle.timestamp + interval_ms,
                "s": coin,
                "i": interval,
                "o": str(candle.open),
                "c": str(candle.close),
                "h": str(candle.high),
                "l": str(candle.low),
                "v": str(candle.volume) if candle.volume else "0",
                "n": 0,  # Number of trades (not available from Extended)
            }
            for candle in candles
        ]

    @staticmethod
    def transform_market_stats(stats: MarketStatsModel) -> Dict[str, Any]:
        """
        Transform Extended market stats to a dict.

        Args:
            stats: Extended MarketStatsModel

        Returns:
            Dict with market statistics
        """
        return {
            "last_price": str(stats.last_price),
            "mark_price": str(stats.mark_price),
            "index_price": str(stats.index_price),
            "bid_price": str(stats.bid_price),
            "ask_price": str(stats.ask_price),
            "funding_rate": str(stats.funding_rate),
            "open_interest": str(stats.open_interest),
            "daily_volume": str(stats.daily_volume),
            "daily_price_change": str(stats.daily_price_change),
        }
