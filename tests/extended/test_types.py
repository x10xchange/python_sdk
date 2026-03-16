"""
Unit tests for Extended SDK type definitions.

Tests type enums and dataclasses in extended.types.
"""

import pytest
from decimal import Decimal
from hamcrest import assert_that, equal_to

from x10.perpetual.orders import OrderSide, TimeInForce as X10TimeInForce
from x10.perpetual.positions import PositionSide

from extended.types import (
    Side,
    TimeInForce,
    LimitOrderType,
    OrderTypeSpec,
    BuilderInfo,
)


class TestSideEnum:
    """Tests for Side enum."""

    def test_side_values(self):
        """Test Side enum values."""
        assert_that(Side.BUY.value, equal_to("B"))
        assert_that(Side.SELL.value, equal_to("A"))

    def test_from_is_buy_true(self):
        """Test converting is_buy=True to BUY."""
        assert_that(Side.from_is_buy(True), equal_to(Side.BUY))

    def test_from_is_buy_false(self):
        """Test converting is_buy=False to SELL."""
        assert_that(Side.from_is_buy(False), equal_to(Side.SELL))

    def test_from_x10_side_buy(self):
        """Test converting x10 BUY side."""
        assert_that(Side.from_x10_side(OrderSide.BUY), equal_to(Side.BUY))
        assert_that(Side.from_x10_side("BUY"), equal_to(Side.BUY))
        assert_that(Side.from_x10_side("buy"), equal_to(Side.BUY))

    def test_from_x10_side_sell(self):
        """Test converting x10 SELL side."""
        assert_that(Side.from_x10_side(OrderSide.SELL), equal_to(Side.SELL))
        assert_that(Side.from_x10_side("SELL"), equal_to(Side.SELL))
        assert_that(Side.from_x10_side("sell"), equal_to(Side.SELL))

    def test_from_x10_side_long(self):
        """Test converting LONG position side to BUY."""
        assert_that(Side.from_x10_side(PositionSide.LONG), equal_to(Side.BUY))
        assert_that(Side.from_x10_side("LONG"), equal_to(Side.BUY))

    def test_from_x10_side_short(self):
        """Test converting SHORT position side to SELL."""
        assert_that(Side.from_x10_side(PositionSide.SHORT), equal_to(Side.SELL))
        assert_that(Side.from_x10_side("SHORT"), equal_to(Side.SELL))

    def test_to_is_buy(self):
        """Test converting Side to is_buy boolean."""
        assert_that(Side.BUY.to_is_buy(), equal_to(True))
        assert_that(Side.SELL.to_is_buy(), equal_to(False))


class TestTimeInForceEnum:
    """Tests for TimeInForce enum."""

    def test_tif_values(self):
        """Test TimeInForce enum values."""
        assert_that(TimeInForce.GTC.value, equal_to("Gtc"))
        assert_that(TimeInForce.IOC.value, equal_to("Ioc"))
        assert_that(TimeInForce.ALO.value, equal_to("Alo"))

    def test_to_x10_tif_gtc(self):
        """Test converting GTC to x10 GTT."""
        assert_that(TimeInForce.GTC.to_x10_tif(), equal_to(X10TimeInForce.GTT))

    def test_to_x10_tif_ioc(self):
        """Test converting IOC to x10 IOC."""
        assert_that(TimeInForce.IOC.to_x10_tif(), equal_to(X10TimeInForce.IOC))

    def test_to_x10_tif_alo(self):
        """Test converting ALO to x10 GTT (ALO uses GTT with post_only)."""
        assert_that(TimeInForce.ALO.to_x10_tif(), equal_to(X10TimeInForce.GTT))

    def test_is_post_only(self):
        """Test is_post_only property."""
        assert_that(TimeInForce.GTC.is_post_only, equal_to(False))
        assert_that(TimeInForce.IOC.is_post_only, equal_to(False))
        assert_that(TimeInForce.ALO.is_post_only, equal_to(True))


class TestOrderTypeSpec:
    """Tests for OrderTypeSpec dataclass."""

    def test_from_dict_gtc(self):
        """Test creating GTC order type from dict."""
        data = {"limit": {"tif": "Gtc"}}
        spec = OrderTypeSpec.from_dict(data)

        assert_that(spec.limit.tif, equal_to(TimeInForce.GTC))

    def test_from_dict_ioc(self):
        """Test creating IOC order type from dict."""
        data = {"limit": {"tif": "Ioc"}}
        spec = OrderTypeSpec.from_dict(data)

        assert_that(spec.limit.tif, equal_to(TimeInForce.IOC))

    def test_from_dict_alo(self):
        """Test creating ALO order type from dict."""
        data = {"limit": {"tif": "Alo"}}
        spec = OrderTypeSpec.from_dict(data)

        assert_that(spec.limit.tif, equal_to(TimeInForce.ALO))

    def test_from_dict_default_tif(self):
        """Test default TIF when not specified."""
        data = {"limit": {}}
        spec = OrderTypeSpec.from_dict(data)

        assert_that(spec.limit.tif, equal_to(TimeInForce.GTC))

    def test_from_dict_no_limit_key(self):
        """Test default when no limit key."""
        data = {}
        spec = OrderTypeSpec.from_dict(data)

        assert_that(spec.limit.tif, equal_to(TimeInForce.GTC))

    def test_to_dict(self):
        """Test converting OrderTypeSpec to dict."""
        spec = OrderTypeSpec(limit=LimitOrderType(tif=TimeInForce.IOC))
        result = spec.to_dict()

        assert_that(result, equal_to({"limit": {"tif": "Ioc"}}))


class TestBuilderInfo:
    """Tests for BuilderInfo dataclass."""

    def test_from_dict_none(self):
        """Test from_dict with None input."""
        result = BuilderInfo.from_dict(None)
        assert_that(result, equal_to(None))

    def test_from_dict_valid(self):
        """Test from_dict with valid input."""
        data = {"b": "123", "f": 10}
        info = BuilderInfo.from_dict(data)

        assert_that(info.b, equal_to("123"))
        assert_that(info.f, equal_to(10))

    def test_from_dict_numeric_builder_id(self):
        """Test from_dict converts numeric builder_id to string."""
        data = {"b": 456, "f": 20}
        info = BuilderInfo.from_dict(data)

        assert_that(info.b, equal_to("456"))

    def test_to_dict(self):
        """Test converting BuilderInfo to dict."""
        info = BuilderInfo(b="789", f=50)
        result = info.to_dict()

        assert_that(result, equal_to({"b": "789", "f": 50}))

    def test_builder_id_property(self):
        """Test builder_id property returns int."""
        info = BuilderInfo(b="123", f=10)
        assert_that(info.builder_id, equal_to(123))

    def test_fee_decimal_conversion(self):
        """Test fee_decimal property converts correctly."""
        # f=1 -> 0.1 bps -> 0.00001
        info1 = BuilderInfo(b="1", f=1)
        assert_that(info1.fee_decimal, equal_to(Decimal("0.00001")))

        # f=10 -> 1 bps -> 0.0001
        info2 = BuilderInfo(b="1", f=10)
        assert_that(info2.fee_decimal, equal_to(Decimal("0.0001")))

        # f=50 -> 5 bps -> 0.0005
        info3 = BuilderInfo(b="1", f=50)
        assert_that(info3.fee_decimal, equal_to(Decimal("0.0005")))

        # f=100 -> 10 bps -> 0.001
        info4 = BuilderInfo(b="1", f=100)
        assert_that(info4.fee_decimal, equal_to(Decimal("0.001")))
