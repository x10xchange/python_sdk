"""
Unit tests for Extended SDK helper functions.

Tests utility functions in extended.utils.helpers.
"""

import pytest
from decimal import Decimal
from hamcrest import assert_that, equal_to

from x10.perpetual.orders import TimeInForce as X10TimeInForce

from extended.utils.helpers import (
    normalize_market_name,
    to_hyperliquid_market_name,
    parse_order_type,
    parse_builder,
    calculate_sz_decimals,
)


class TestNormalizeMarketName:
    """Tests for normalize_market_name function."""

    def test_normalize_without_suffix(self):
        """Test adding -USD suffix to bare coin name."""
        assert_that(normalize_market_name("BTC"), equal_to("BTC-USD"))
        assert_that(normalize_market_name("ETH"), equal_to("ETH-USD"))
        assert_that(normalize_market_name("SOL"), equal_to("SOL-USD"))

    def test_normalize_with_suffix(self):
        """Test preserving existing -USD suffix."""
        assert_that(normalize_market_name("BTC-USD"), equal_to("BTC-USD"))
        assert_that(normalize_market_name("ETH-USD"), equal_to("ETH-USD"))

    def test_normalize_special_coins(self):
        """Test normalizing special coin names."""
        assert_that(normalize_market_name("1000PEPE"), equal_to("1000PEPE-USD"))
        assert_that(normalize_market_name("1000SHIB"), equal_to("1000SHIB-USD"))


class TestToHyperliquidMarketName:
    """Tests for to_hyperliquid_market_name function."""

    def test_strip_usd_suffix(self):
        """Test stripping -USD suffix."""
        assert_that(to_hyperliquid_market_name("BTC-USD"), equal_to("BTC"))
        assert_that(to_hyperliquid_market_name("ETH-USD"), equal_to("ETH"))
        assert_that(to_hyperliquid_market_name("SOL-USD"), equal_to("SOL"))

    def test_already_stripped(self):
        """Test names without -USD suffix are unchanged."""
        assert_that(to_hyperliquid_market_name("BTC"), equal_to("BTC"))
        assert_that(to_hyperliquid_market_name("ETH"), equal_to("ETH"))

    def test_special_coins(self):
        """Test stripping suffix from special coin names."""
        assert_that(to_hyperliquid_market_name("1000PEPE-USD"), equal_to("1000PEPE"))
        assert_that(to_hyperliquid_market_name("1000SHIB-USD"), equal_to("1000SHIB"))


class TestParseOrderType:
    """Tests for parse_order_type function."""

    def test_parse_gtc_order_type(self):
        """Test parsing GTC order type."""
        order_type = {"limit": {"tif": "Gtc"}}
        tif, post_only = parse_order_type(order_type)

        assert_that(tif, equal_to(X10TimeInForce.GTT))
        assert_that(post_only, equal_to(False))

    def test_parse_ioc_order_type(self):
        """Test parsing IOC order type."""
        order_type = {"limit": {"tif": "Ioc"}}
        tif, post_only = parse_order_type(order_type)

        assert_that(tif, equal_to(X10TimeInForce.IOC))
        assert_that(post_only, equal_to(False))

    def test_parse_alo_order_type(self):
        """Test parsing ALO (post-only) order type."""
        order_type = {"limit": {"tif": "Alo"}}
        tif, post_only = parse_order_type(order_type)

        assert_that(tif, equal_to(X10TimeInForce.GTT))
        assert_that(post_only, equal_to(True))

    def test_parse_order_type_default_tif(self):
        """Test default TIF when not specified."""
        order_type = {"limit": {}}
        tif, post_only = parse_order_type(order_type)

        assert_that(tif, equal_to(X10TimeInForce.GTT))
        assert_that(post_only, equal_to(False))

    def test_parse_order_type_unknown_format(self):
        """Test handling unknown order type format."""
        order_type = {"market": {}}
        tif, post_only = parse_order_type(order_type)

        assert_that(tif, equal_to(X10TimeInForce.GTT))
        assert_that(post_only, equal_to(False))


class TestParseBuilder:
    """Tests for parse_builder function."""

    def test_parse_builder_none(self):
        """Test parsing None builder."""
        builder_id, builder_fee = parse_builder(None)

        assert_that(builder_id, equal_to(None))
        assert_that(builder_fee, equal_to(None))

    def test_parse_builder_basic(self):
        """Test parsing basic builder info."""
        builder = {"b": "123", "f": 10}  # 1 bps = 0.0001
        builder_id, builder_fee = parse_builder(builder)

        assert_that(builder_id, equal_to(123))
        assert_that(builder_fee, equal_to(Decimal("0.0001")))

    def test_parse_builder_fee_conversion(self):
        """Test fee conversion from tenths of bps to decimal."""
        # f=1 -> 0.1 bps -> 0.000001
        builder1 = {"b": "1", "f": 1}
        _, fee1 = parse_builder(builder1)
        assert_that(fee1, equal_to(Decimal("0.00001")))

        # f=10 -> 1 bps -> 0.0001
        builder2 = {"b": "1", "f": 10}
        _, fee2 = parse_builder(builder2)
        assert_that(fee2, equal_to(Decimal("0.0001")))

        # f=50 -> 5 bps -> 0.0005
        builder3 = {"b": "1", "f": 50}
        _, fee3 = parse_builder(builder3)
        assert_that(fee3, equal_to(Decimal("0.0005")))

    def test_parse_builder_no_fee(self):
        """Test parsing builder without fee."""
        builder = {"b": "456"}
        builder_id, builder_fee = parse_builder(builder)

        assert_that(builder_id, equal_to(456))
        assert_that(builder_fee, equal_to(Decimal("0")))


class TestCalculateSzDecimals:
    """Tests for calculate_sz_decimals function."""

    def test_calculate_sz_decimals_five_places(self):
        """Test calculating 5 decimal places."""
        result = calculate_sz_decimals(Decimal("0.00001"))
        assert_that(result, equal_to(5))

    def test_calculate_sz_decimals_three_places(self):
        """Test calculating 3 decimal places."""
        result = calculate_sz_decimals(Decimal("0.001"))
        assert_that(result, equal_to(3))

    def test_calculate_sz_decimals_one_place(self):
        """Test calculating 1 decimal place."""
        result = calculate_sz_decimals(Decimal("0.1"))
        assert_that(result, equal_to(1))

    def test_calculate_sz_decimals_zero_places(self):
        """Test calculating 0 decimal places."""
        result = calculate_sz_decimals(Decimal("1"))
        assert_that(result, equal_to(0))

    def test_calculate_sz_decimals_zero_input(self):
        """Test handling zero input."""
        result = calculate_sz_decimals(Decimal("0"))
        assert_that(result, equal_to(0))

    def test_calculate_sz_decimals_negative_input(self):
        """Test handling negative input."""
        result = calculate_sz_decimals(Decimal("-0.001"))
        assert_that(result, equal_to(0))
