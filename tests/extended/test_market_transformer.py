"""
Unit tests for MarketTransformer.

Tests transformation of Extended market data to Hyperliquid format.
"""

import pytest
from decimal import Decimal
from hamcrest import assert_that, equal_to, has_key, has_length, has_entries, contains_inanyorder

from extended.transformers.market import MarketTransformer
from tests.extended.fixtures import (
    create_mock_market,
    create_mock_markets,
    create_mock_orderbook,
    create_mock_candles,
)


class TestMarketTransformerMeta:
    """Tests for transform_meta method."""

    def test_transform_meta_single_market(self):
        """Test transforming a single market to meta format."""
        market = create_mock_market("BTC-USD")
        result = MarketTransformer.transform_meta([market])

        assert_that(result, has_key("universe"))
        assert_that(result["universe"], has_length(1))

        btc_entry = result["universe"][0]
        assert_that(btc_entry["name"], equal_to("BTC"))  # Stripped -USD
        assert_that(btc_entry["szDecimals"], equal_to(5))  # From min_order_size_change
        assert_that(btc_entry["maxLeverage"], equal_to(50))
        assert_that(btc_entry["onlyIsolated"], equal_to(False))

    def test_transform_meta_multiple_markets(self):
        """Test transforming multiple markets to meta format."""
        markets = create_mock_markets()
        result = MarketTransformer.transform_meta(markets)

        assert_that(result, has_key("universe"))
        assert_that(result["universe"], has_length(3))

        names = [m["name"] for m in result["universe"]]
        assert_that(names, contains_inanyorder("BTC", "ETH", "SOL"))

    def test_transform_meta_excludes_inactive_markets(self):
        """Test that inactive markets are excluded from meta."""
        active_market = create_mock_market("BTC-USD", active=True)
        inactive_market = create_mock_market("ETH-USD", active=False)

        result = MarketTransformer.transform_meta([active_market, inactive_market])

        assert_that(result["universe"], has_length(1))
        assert_that(result["universe"][0]["name"], equal_to("BTC"))

    def test_transform_meta_empty_list(self):
        """Test transforming empty markets list."""
        result = MarketTransformer.transform_meta([])

        assert_that(result, equal_to({"universe": []}))


class TestMarketTransformerAllMids:
    """Tests for transform_all_mids method."""

    def test_transform_all_mids(self):
        """Test transforming markets to mid prices dict."""
        markets = create_mock_markets()
        result = MarketTransformer.transform_all_mids(markets)

        # Should have all markets
        assert_that(len(result), equal_to(3))

        # Check BTC mid price (bid=50490, ask=50510, mid=50500)
        assert_that("BTC" in result, equal_to(True))
        assert_that(result["BTC"], equal_to("50500.00"))

    def test_transform_all_mids_market_name_conversion(self):
        """Test that market names are converted to Hyperliquid format."""
        markets = create_mock_markets()
        result = MarketTransformer.transform_all_mids(markets)

        # All names should be without -USD suffix
        for name in result.keys():
            assert_that("-USD" in name, equal_to(False))


class TestMarketTransformerL2Snapshot:
    """Tests for transform_l2_snapshot method."""

    def test_transform_l2_snapshot_structure(self):
        """Test L2 snapshot has correct structure."""
        orderbook = create_mock_orderbook()
        result = MarketTransformer.transform_l2_snapshot(orderbook)

        assert_that(result, has_key("coin"))
        assert_that(result, has_key("levels"))
        assert_that(result, has_key("time"))

    def test_transform_l2_snapshot_coin_name(self):
        """Test coin name is converted to Hyperliquid format."""
        orderbook = create_mock_orderbook()
        result = MarketTransformer.transform_l2_snapshot(orderbook)

        assert_that(result["coin"], equal_to("BTC"))

    def test_transform_l2_snapshot_levels(self):
        """Test levels are correctly transformed."""
        orderbook = create_mock_orderbook()
        result = MarketTransformer.transform_l2_snapshot(orderbook)

        # levels[0] = bids, levels[1] = asks
        assert_that(len(result["levels"]), equal_to(2))

        bids = result["levels"][0]
        asks = result["levels"][1]

        assert_that(len(bids), equal_to(3))
        assert_that(len(asks), equal_to(3))

        # Check first bid
        assert_that(bids[0]["px"], equal_to("50490.00"))
        assert_that(bids[0]["sz"], equal_to("1.5"))
        assert_that(bids[0]["n"], equal_to(1))

        # Check first ask
        assert_that(asks[0]["px"], equal_to("50510.00"))
        assert_that(asks[0]["sz"], equal_to("1.2"))

    def test_transform_l2_snapshot_custom_timestamp(self):
        """Test custom timestamp is used when provided."""
        orderbook = create_mock_orderbook()
        custom_ts = 1234567890000
        result = MarketTransformer.transform_l2_snapshot(orderbook, timestamp=custom_ts)

        assert_that(result["time"], equal_to(custom_ts))


class TestMarketTransformerCandles:
    """Tests for transform_candles method."""

    def test_transform_candles_structure(self):
        """Test candles have correct Hyperliquid structure."""
        candles = create_mock_candles()
        result = MarketTransformer.transform_candles(candles, "BTC", "1m")

        assert_that(len(result), equal_to(3))

        first_candle = result[0]
        assert_that(first_candle, has_key("t"))  # open timestamp
        assert_that(first_candle, has_key("T"))  # close timestamp
        assert_that(first_candle, has_key("s"))  # symbol
        assert_that(first_candle, has_key("i"))  # interval
        assert_that(first_candle, has_key("o"))  # open
        assert_that(first_candle, has_key("c"))  # close
        assert_that(first_candle, has_key("h"))  # high
        assert_that(first_candle, has_key("l"))  # low
        assert_that(first_candle, has_key("v"))  # volume
        assert_that(first_candle, has_key("n"))  # num trades

    def test_transform_candles_values(self):
        """Test candle values are correctly transformed."""
        candles = create_mock_candles()
        result = MarketTransformer.transform_candles(candles, "BTC", "1m")

        first_candle = result[0]
        assert_that(first_candle["s"], equal_to("BTC"))
        assert_that(first_candle["i"], equal_to("1m"))
        assert_that(first_candle["o"], equal_to("50000.00"))
        assert_that(first_candle["c"], equal_to("50050.00"))
        assert_that(first_candle["h"], equal_to("50100.00"))
        assert_that(first_candle["l"], equal_to("49900.00"))
        assert_that(first_candle["v"], equal_to("100.5"))

    def test_transform_candles_close_timestamp(self):
        """Test close timestamp is calculated correctly for 1m interval."""
        candles = create_mock_candles()
        result = MarketTransformer.transform_candles(candles, "BTC", "1m")

        first_candle = result[0]
        # Close timestamp = open + 60000ms (1 minute)
        assert_that(first_candle["T"], equal_to(first_candle["t"] + 60000))

    def test_transform_candles_empty_list(self):
        """Test transforming empty candles list."""
        result = MarketTransformer.transform_candles([], "BTC", "1m")
        assert_that(result, equal_to([]))
