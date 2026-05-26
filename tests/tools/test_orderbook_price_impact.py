import asyncio
from decimal import Decimal

import pytest
from hamcrest import assert_that, equal_to, none, not_none

from x10.config import TESTNET_CONFIG
from x10.models.orderbook import OrderbookQuantityModel, OrderbookUpdateModel
from x10.tools.orderbook import OrderBook


async def populate_dummy_data(market_name: str, orderbook: OrderBook):
    dummy_data = OrderbookUpdateModel(
        market=market_name,
        bid=[
            OrderbookQuantityModel(price=Decimal("100"), qty=Decimal("1")),
            OrderbookQuantityModel(price=Decimal("99"), qty=Decimal("2")),
            OrderbookQuantityModel(price=Decimal("98"), qty=Decimal("1")),
        ],
        ask=[
            OrderbookQuantityModel(price=Decimal("101"), qty=Decimal("1")),
            OrderbookQuantityModel(price=Decimal("102"), qty=Decimal("2")),
            OrderbookQuantityModel(price=Decimal("103"), qty=Decimal("1")),
        ],
    )
    await orderbook.update_orderbook(dummy_data)


@pytest.fixture(scope="module")
def orderbook():
    market_name = "dummy-market"
    orderbook = OrderBook(
        TESTNET_CONFIG,
        market_name,
        best_ask_change_callback=None,
        best_bid_change_callback=None,
    )
    asyncio.run(populate_dummy_data(market_name, orderbook))

    return orderbook


def test_calculate_impact_partial_buy(orderbook):
    notional = Decimal("105")
    expected_amount = Decimal("1") + Decimal("4") / Decimal("102")
    expected_average_price = notional / expected_amount
    result = orderbook.calculate_price_impact_notional(notional, "BUY")

    assert_that(result.amount, equal_to(expected_amount))
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_impact_partial_sell(orderbook):
    notional = Decimal("110")
    expected_amount = Decimal(1) + Decimal("10") / Decimal("99")
    expected_average_price = notional / expected_amount
    result = orderbook.calculate_price_impact_notional(notional, "SELL")

    assert_that(result.amount, equal_to(expected_amount))
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_price_impact_total_match_sell(orderbook):
    notional = Decimal("199")
    expected_amount = Decimal("2")
    expected_average_price = notional / expected_amount
    result = orderbook.calculate_price_impact_notional(notional, "SELL")

    assert_that(result.amount, equal_to(expected_amount))
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_price_impact_total_match_buy(orderbook):
    notional = Decimal("101") + Decimal("2") * Decimal("102") + Decimal("103")
    expected_amount = Decimal("4")
    expected_average_price = notional / expected_amount
    result = orderbook.calculate_price_impact_notional(notional, "BUY")

    assert_that(result.amount, equal_to(expected_amount))
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_price_impact_insufficient_liquidity_bid(orderbook):
    notional = Decimal("1000")
    result = orderbook.calculate_price_impact_notional(notional, "SELL")

    assert_that(result, none())


def test_calculate_price_impact_insufficient_liquidity_ask(orderbook):
    notional = Decimal("1000")
    result = orderbook.calculate_price_impact_notional(notional, "BUY")

    assert_that(result, none())


def test_calculate_price_impact_invalid_notional(orderbook):
    notional = Decimal("-10")
    result = orderbook.calculate_price_impact_notional(notional, "SELL")

    assert_that(result, none())


def test_calculate_price_impact_invalid_side(orderbook):
    notional = Decimal("100")
    result = orderbook.calculate_price_impact_notional(notional, "invalid")

    assert_that(result, none())


def test_calculate_qty_impact_partial_buy(orderbook):
    """
    Buy a partial quantity that spans multiple ask levels.
    For example: buying 2 units:
      - 1 unit at price 101
      - 1 unit at price 102
    total cost = 101 + 102 = 203
    average price = 203 / 2 = 101.5
    """
    qty = Decimal("2")
    result = orderbook.calculate_price_impact_qty(qty, "BUY")

    assert_that(result, not_none(), "Result should not be None for partial fill.")
    assert_that(result.amount, equal_to(qty), "Filled amount should match requested qty.")

    expected_average_price = Decimal("101.5")
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_qty_impact_partial_sell(orderbook):
    """
    Sell a partial quantity that spans multiple bid levels.
    For example: selling 2 units:
      - 1 unit at price 100
      - 1 unit at price 99
    total received = 100 + 99 = 199
    average price = 199 / 2 = 99.5
    """
    qty = Decimal("2")
    result = orderbook.calculate_price_impact_qty(qty, "SELL")

    assert_that(result, not_none(), "Result should not be None for partial fill.")
    assert_that(result.amount, equal_to(qty), "Filled amount should match requested qty.")

    expected_average_price = Decimal("99.5")
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_qty_impact_total_match_buy(orderbook):
    """
    Buy all available ask liquidity: total ask qty = 1 + 2 + 1 = 4
    Fill:
      - 1 @101 => cost 101
      - 2 @102 => cost 204
      - 1 @103 => cost 103
    total = 101 + 204 + 103 = 408
    average = 408 / 4 = 102
    """
    qty = Decimal("4")
    result = orderbook.calculate_price_impact_qty(qty, "BUY")

    assert_that(result, not_none(), "Result should not be None when liquidity matches exactly.")
    assert_that(result.amount, equal_to(qty), "Filled amount should match requested qty.")

    expected_average_price = Decimal("102")
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_qty_impact_total_match_sell(orderbook):
    """
    Sell all available bid liquidity: total bid qty = 1 + 2 + 1 = 4
    Fill:
      - 1 @100 => 100
      - 2 @99 => 198
      - 1 @98 => 98
    total = 100 + 198 + 98 = 396
    average = 396 / 4 = 99
    """
    qty = Decimal("4")
    result = orderbook.calculate_price_impact_qty(qty, "SELL")

    assert_that(result, not_none(), "Result should not be None when liquidity matches exactly.")
    assert_that(result.amount, equal_to(qty))

    expected_average_price = Decimal("99")
    assert_that(result.price, equal_to(expected_average_price))


def test_calculate_qty_impact_insufficient_liquidity_buy(orderbook):
    """
    Request a qty larger than available on the ask side (4 total).
    Asking for 5 => insufficient => should return None.
    """
    qty = Decimal("5")
    result = orderbook.calculate_price_impact_qty(qty, "BUY")

    assert_that(result, none(), "Result should be None when there's insufficient ask liquidity.")


def test_calculate_qty_impact_insufficient_liquidity_sell(orderbook):
    """
    Request a qty larger than available on the bid side (4 total).
    Asking for 5 => insufficient => should return None.
    """
    qty = Decimal("5")
    result = orderbook.calculate_price_impact_qty(qty, "SELL")

    assert_that(result, none(), "Result should be None when there's insufficient bid liquidity.")


def test_calculate_qty_impact_invalid_qty(orderbook):
    """
    Negative or zero qty should return None.
    """
    qty = Decimal("-1")
    result = orderbook.calculate_price_impact_qty(qty, "BUY")

    assert_that(result, none(), "Result should be None for invalid qty (negative).")

    qty_zero = Decimal("0")
    result_zero = orderbook.calculate_price_impact_qty(qty_zero, "SELL")

    assert_that(result_zero, none(), "Result should be None for invalid qty (zero).")


def test_calculate_qty_impact_invalid_side(orderbook):
    """
    Any side not 'BUY' or 'SELL' should yield None.
    """
    qty = Decimal("1")
    result = orderbook.calculate_price_impact_qty(qty, "INVALID_SIDE")

    assert_that(result, none(), "Result should be None for invalid side.")
