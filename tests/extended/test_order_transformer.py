"""
Unit tests for OrderTransformer.

Tests transformation of Extended order/trade data to Hyperliquid format.
"""

import pytest
from decimal import Decimal
from hamcrest import assert_that, equal_to, has_key, has_length

from extended.transformers.order import OrderTransformer
from tests.extended.fixtures import (
    create_mock_open_order,
    create_mock_open_orders,
    create_mock_placed_order,
    create_mock_trade,
    create_mock_trades,
)


class TestOrderTransformerOpenOrders:
    """Tests for transform_open_orders method."""

    def test_transform_open_orders_list(self):
        """Test transforming a list of open orders."""
        orders = create_mock_open_orders()
        result = OrderTransformer.transform_open_orders(orders)

        assert_that(len(result), equal_to(2))

    def test_transform_open_orders_empty_list(self):
        """Test transforming empty orders list."""
        result = OrderTransformer.transform_open_orders([])
        assert_that(result, equal_to([]))


class TestOrderTransformerOpenOrder:
    """Tests for transform_open_order method."""

    def test_transform_open_order_structure(self):
        """Test open order has correct Hyperliquid structure."""
        order = create_mock_open_order()
        result = OrderTransformer.transform_open_order(order)

        assert_that(result, has_key("coin"))
        assert_that(result, has_key("side"))
        assert_that(result, has_key("limitPx"))
        assert_that(result, has_key("sz"))
        assert_that(result, has_key("oid"))
        assert_that(result, has_key("timestamp"))
        assert_that(result, has_key("origSz"))
        assert_that(result, has_key("cloid"))

    def test_transform_open_order_values(self):
        """Test open order values are correctly transformed."""
        order = create_mock_open_order(
            order_id=12345,
            market="BTC-USD",
            side="BUY",
            price=Decimal("50000.00"),
            qty=Decimal("0.1"),
            external_id="test-order-001",
        )
        result = OrderTransformer.transform_open_order(order)

        assert_that(result["coin"], equal_to("BTC"))  # Converted from BTC-USD
        assert_that(result["side"], equal_to("B"))  # BUY -> B
        assert_that(result["limitPx"], equal_to("50000.00"))
        assert_that(result["sz"], equal_to("0.1"))
        assert_that(result["oid"], equal_to(12345))
        assert_that(result["origSz"], equal_to("0.1"))
        assert_that(result["cloid"], equal_to("test-order-001"))

    def test_transform_open_order_sell_side(self):
        """Test SELL order is transformed to 'A'."""
        order = create_mock_open_order(side="SELL")
        result = OrderTransformer.transform_open_order(order)

        assert_that(result["side"], equal_to("A"))

    def test_transform_open_order_remaining_size(self):
        """Test remaining size is calculated correctly."""
        order = create_mock_open_order(
            qty=Decimal("1.0"),
            filled_qty=Decimal("0.3"),
        )
        result = OrderTransformer.transform_open_order(order)

        assert_that(result["sz"], equal_to("0.7"))  # 1.0 - 0.3
        assert_that(result["origSz"], equal_to("1.0"))

    def test_transform_open_order_empty_external_id(self):
        """Test order with empty external_id has None cloid."""
        order = create_mock_open_order(external_id="")
        result = OrderTransformer.transform_open_order(order)

        # Empty string should be converted to None
        assert_that(result["cloid"], equal_to(None))


class TestOrderTransformerUserFills:
    """Tests for transform_user_fills method."""

    def test_transform_user_fills_list(self):
        """Test transforming a list of fills."""
        trades = create_mock_trades()
        result = OrderTransformer.transform_user_fills(trades)

        assert_that(len(result), equal_to(2))

    def test_transform_user_fills_empty_list(self):
        """Test transforming empty trades list."""
        result = OrderTransformer.transform_user_fills([])
        assert_that(result, equal_to([]))


class TestOrderTransformerFill:
    """Tests for transform_fill method."""

    def test_transform_fill_structure(self):
        """Test fill has correct Hyperliquid structure."""
        trade = create_mock_trade()
        result = OrderTransformer.transform_fill(trade)

        assert_that(result, has_key("coin"))
        assert_that(result, has_key("px"))
        assert_that(result, has_key("sz"))
        assert_that(result, has_key("side"))
        assert_that(result, has_key("time"))
        assert_that(result, has_key("startPosition"))
        assert_that(result, has_key("dir"))
        assert_that(result, has_key("closedPnl"))
        assert_that(result, has_key("hash"))
        assert_that(result, has_key("oid"))
        assert_that(result, has_key("crossed"))
        assert_that(result, has_key("fee"))
        assert_that(result, has_key("tid"))
        assert_that(result, has_key("liquidation"))
        assert_that(result, has_key("cloid"))

    def test_transform_fill_values(self):
        """Test fill values are correctly transformed."""
        trade = create_mock_trade(
            trade_id=98765,
            order_id=12345,
            market="BTC-USD",
            side="BUY",
            price=Decimal("50000.00"),
            qty=Decimal("0.1"),
            fee=Decimal("2.50"),
            is_taker=True,
        )
        result = OrderTransformer.transform_fill(trade)

        assert_that(result["coin"], equal_to("BTC"))
        assert_that(result["px"], equal_to("50000.00"))
        assert_that(result["sz"], equal_to("0.1"))
        assert_that(result["side"], equal_to("B"))
        assert_that(result["oid"], equal_to(12345))
        assert_that(result["fee"], equal_to("2.50"))
        assert_that(result["tid"], equal_to(98765))
        assert_that(result["hash"], equal_to("98765"))
        assert_that(result["crossed"], equal_to(True))  # is_taker

    def test_transform_fill_sell_side(self):
        """Test SELL fill is transformed to 'A'."""
        trade = create_mock_trade(side="SELL")
        result = OrderTransformer.transform_fill(trade)

        assert_that(result["side"], equal_to("A"))

    def test_transform_fill_cloid_is_none(self):
        """Test cloid is always None (not available from Extended)."""
        trade = create_mock_trade()
        result = OrderTransformer.transform_fill(trade)

        assert_that(result["cloid"], equal_to(None))

    def test_transform_fill_not_liquidation(self):
        """Test normal trade is not a liquidation."""
        trade = create_mock_trade()
        result = OrderTransformer.transform_fill(trade)

        assert_that(result["liquidation"], equal_to(False))


class TestOrderTransformerOrderResponse:
    """Tests for transform_order_response method."""

    def test_transform_order_response_structure(self):
        """Test order response has correct Hyperliquid structure."""
        placed_order = create_mock_placed_order(order_id=12345, external_id="test-001")
        result = OrderTransformer.transform_order_response(placed_order)

        assert_that(result["status"], equal_to("ok"))
        assert_that(result["response"]["type"], equal_to("order"))
        assert_that(result["response"]["data"], has_key("statuses"))

    def test_transform_order_response_values(self):
        """Test order response values."""
        placed_order = create_mock_placed_order(order_id=12345, external_id="test-001")
        result = OrderTransformer.transform_order_response(placed_order)

        statuses = result["response"]["data"]["statuses"]
        assert_that(len(statuses), equal_to(1))
        assert_that(statuses[0]["resting"]["oid"], equal_to(12345))
        assert_that(statuses[0]["resting"]["cloid"], equal_to("test-001"))


class TestOrderTransformerCancelResponse:
    """Tests for transform_cancel_response method."""

    def test_transform_cancel_response_success(self):
        """Test successful cancel response."""
        result = OrderTransformer.transform_cancel_response(success=True)

        assert_that(result["status"], equal_to("ok"))
        assert_that(result["response"]["type"], equal_to("cancel"))
        assert_that(result["response"]["data"]["statuses"][0], equal_to("success"))

    def test_transform_cancel_response_failure(self):
        """Test failed cancel response."""
        result = OrderTransformer.transform_cancel_response(success=False)

        assert_that(result["status"], equal_to("err"))
        assert_that(result["response"], equal_to("Cancel failed"))


class TestOrderTransformerErrorResponse:
    """Tests for transform_error_response method."""

    def test_transform_error_response(self):
        """Test error response formatting."""
        result = OrderTransformer.transform_error_response("Order rejected: insufficient margin")

        assert_that(result["status"], equal_to("err"))
        assert_that(result["response"], equal_to("Order rejected: insufficient margin"))


class TestOrderTransformerBulkOrdersResponse:
    """Tests for transform_bulk_orders_response method."""

    def test_transform_bulk_orders_response_all_success(self):
        """Test bulk orders response with all successes."""
        results = [
            {"status": "ok", "data": {"id": 12345, "external_id": "order-1"}},
            {"status": "ok", "data": {"id": 12346, "external_id": "order-2"}},
        ]
        result = OrderTransformer.transform_bulk_orders_response(results)

        assert_that(result["status"], equal_to("ok"))
        assert_that(result["response"]["type"], equal_to("order"))

        statuses = result["response"]["data"]["statuses"]
        assert_that(len(statuses), equal_to(2))
        assert_that(statuses[0]["resting"]["oid"], equal_to(12345))
        assert_that(statuses[1]["resting"]["oid"], equal_to(12346))

    def test_transform_bulk_orders_response_mixed(self):
        """Test bulk orders response with mixed results."""
        results = [
            {"status": "ok", "data": {"id": 12345, "external_id": "order-1"}},
            {"status": "err", "error": "Insufficient margin"},
        ]
        result = OrderTransformer.transform_bulk_orders_response(results)

        statuses = result["response"]["data"]["statuses"]
        assert_that(len(statuses), equal_to(2))
        assert_that(statuses[0]["resting"]["oid"], equal_to(12345))
        assert_that(statuses[1]["error"], equal_to("Insufficient margin"))


class TestOrderTransformerLeverageResponse:
    """Tests for transform_leverage_response method."""

    def test_transform_leverage_response(self):
        """Test leverage response formatting."""
        result = OrderTransformer.transform_leverage_response()

        assert_that(result["status"], equal_to("ok"))
        assert_that(result["response"]["type"], equal_to("leverage"))
