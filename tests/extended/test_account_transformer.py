"""
Unit tests for AccountTransformer.

Tests transformation of Extended account data to Hyperliquid format.
"""

import pytest
from decimal import Decimal
from hamcrest import assert_that, equal_to, has_key, has_length, has_entries

from extended.transformers.account import AccountTransformer
from tests.extended.fixtures import (
    create_mock_balance,
    create_mock_position,
    create_mock_positions,
)


class TestAccountTransformerUserState:
    """Tests for transform_user_state method."""

    def test_transform_user_state_structure(self):
        """Test user_state has correct Hyperliquid structure."""
        balance = create_mock_balance()
        positions = create_mock_positions()

        result = AccountTransformer.transform_user_state(balance, positions)

        assert_that(result, has_key("assetPositions"))
        assert_that(result, has_key("crossMaintenanceMarginUsed"))
        assert_that(result, has_key("crossMarginSummary"))
        assert_that(result, has_key("marginSummary"))
        assert_that(result, has_key("withdrawable"))

    def test_transform_user_state_balance_values(self):
        """Test balance values are correctly transformed."""
        balance = create_mock_balance()
        positions = []

        result = AccountTransformer.transform_user_state(balance, positions)

        assert_that(result["withdrawable"], equal_to("8000.00"))  # available_for_trade
        assert_that(result["crossMaintenanceMarginUsed"], equal_to("2000.00"))

        margin_summary = result["marginSummary"]
        assert_that(margin_summary["accountValue"], equal_to("10500.00"))  # equity
        assert_that(margin_summary["totalMarginUsed"], equal_to("2000.00"))
        assert_that(margin_summary["totalRawUsd"], equal_to("10000.00"))  # balance
        assert_that(margin_summary["withdrawable"], equal_to("8000.00"))

    def test_transform_user_state_with_positions(self):
        """Test user_state with positions."""
        balance = create_mock_balance()
        positions = create_mock_positions()

        result = AccountTransformer.transform_user_state(balance, positions)

        assert_that(result["assetPositions"], has_length(2))

        # Total position value should be sum of all positions
        cross_summary = result["crossMarginSummary"]
        expected_total = str(Decimal("25000.00") + Decimal("15000.00"))
        assert_that(cross_summary["totalNtlPos"], equal_to(expected_total))

    def test_transform_user_state_empty_positions(self):
        """Test user_state with no positions."""
        balance = create_mock_balance()
        positions = []

        result = AccountTransformer.transform_user_state(balance, positions)

        assert_that(result["assetPositions"], equal_to([]))
        assert_that(result["crossMarginSummary"]["totalNtlPos"], equal_to("0"))


class TestAccountTransformerPosition:
    """Tests for transform_position method."""

    def test_transform_position_structure(self):
        """Test position has correct Hyperliquid structure."""
        position = create_mock_position()
        result = AccountTransformer.transform_position(position)

        assert_that(result, has_key("position"))
        assert_that(result, has_key("type"))
        assert_that(result["type"], equal_to("oneWay"))

        pos = result["position"]
        assert_that(pos, has_key("coin"))
        assert_that(pos, has_key("szi"))
        assert_that(pos, has_key("leverage"))
        assert_that(pos, has_key("entryPx"))
        assert_that(pos, has_key("positionValue"))
        assert_that(pos, has_key("unrealizedPnl"))
        assert_that(pos, has_key("liquidationPx"))
        assert_that(pos, has_key("marginUsed"))
        assert_that(pos, has_key("returnOnEquity"))

    def test_transform_position_long(self):
        """Test LONG position has positive szi."""
        position = create_mock_position(
            market="BTC-USD",
            side="LONG",
            size=Decimal("0.5"),
        )
        result = AccountTransformer.transform_position(position)

        assert_that(result["position"]["coin"], equal_to("BTC"))
        assert_that(result["position"]["szi"], equal_to("0.5"))  # Positive for LONG

    def test_transform_position_short(self):
        """Test SHORT position has negative szi."""
        position = create_mock_position(
            market="ETH-USD",
            side="SHORT",
            size=Decimal("5.0"),
        )
        result = AccountTransformer.transform_position(position)

        assert_that(result["position"]["coin"], equal_to("ETH"))
        assert_that(result["position"]["szi"], equal_to("-5.0"))  # Negative for SHORT

    def test_transform_position_leverage(self):
        """Test leverage is correctly formatted."""
        position = create_mock_position(leverage=10)
        result = AccountTransformer.transform_position(position)

        leverage = result["position"]["leverage"]
        assert_that(leverage["type"], equal_to("cross"))
        assert_that(leverage["value"], equal_to(10))

    def test_transform_position_values(self):
        """Test position values are correctly transformed."""
        position = create_mock_position(
            open_price=Decimal("50000.00"),
            value=Decimal("25000.00"),
            unrealised_pnl=Decimal("500.00"),
        )
        result = AccountTransformer.transform_position(position)

        pos = result["position"]
        assert_that(pos["entryPx"], equal_to("50000.00"))
        assert_that(pos["positionValue"], equal_to("25000.00"))
        assert_that(pos["unrealizedPnl"], equal_to("500.00"))
        assert_that(pos["liquidationPx"], equal_to("45000.00"))

    def test_transform_position_margin_used_calculation(self):
        """Test margin used is calculated from value/leverage."""
        position = create_mock_position(
            value=Decimal("25000.00"),
            leverage=10,
        )
        result = AccountTransformer.transform_position(position)

        # marginUsed = value / leverage = 25000 / 10 = 2500
        assert_that(result["position"]["marginUsed"], equal_to("2500.00"))

    def test_transform_position_roe_calculation(self):
        """Test return on equity is calculated correctly."""
        position = create_mock_position(
            value=Decimal("25000.00"),
            unrealised_pnl=Decimal("500.00"),
            leverage=10,
        )
        result = AccountTransformer.transform_position(position)

        # marginUsed = 25000 / 10 = 2500
        # ROE = 500 / 2500 = 0.2
        assert_that(result["position"]["returnOnEquity"], equal_to("0.2"))


class TestAccountTransformerBalance:
    """Tests for transform_balance method."""

    def test_transform_balance_structure(self):
        """Test balance has all expected fields."""
        balance = create_mock_balance()
        result = AccountTransformer.transform_balance(balance)

        assert_that(result, has_key("balance"))
        assert_that(result, has_key("equity"))
        assert_that(result, has_key("available_for_trade"))
        assert_that(result, has_key("available_for_withdrawal"))
        assert_that(result, has_key("unrealised_pnl"))
        assert_that(result, has_key("initial_margin"))
        assert_that(result, has_key("margin_ratio"))

    def test_transform_balance_values(self):
        """Test balance values are correctly transformed."""
        balance = create_mock_balance()
        result = AccountTransformer.transform_balance(balance)

        assert_that(result["balance"], equal_to("10000.00"))
        assert_that(result["equity"], equal_to("10500.00"))
        assert_that(result["available_for_trade"], equal_to("8000.00"))
        assert_that(result["available_for_withdrawal"], equal_to("7500.00"))
        assert_that(result["unrealised_pnl"], equal_to("500.00"))
        assert_that(result["initial_margin"], equal_to("2000.00"))
        assert_that(result["margin_ratio"], equal_to("0.20"))
