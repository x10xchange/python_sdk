from decimal import Decimal

from hamcrest import assert_that, equal_to

from x10.perpetual.orders import OrderSide
from x10.utils.order import calc_entire_position_size, get_price_with_slippage


def test_calc_entire_position_size():
    assert_that(
        calc_entire_position_size(
            price=Decimal("24580.3412"),
            quantity_precision=4,
            max_position_value=Decimal("10000000"),
        ),
        equal_to(Decimal("20341.4588")),
    )


def test_get_price_with_slippage():
    # given
    best_ask = Decimal("66841.6")
    best_bid = Decimal("66774.7")
    min_price_change = Decimal("0.1")
    slippage = Decimal("0.0075")

    # then
    assert_that(
        get_price_with_slippage(
            side=OrderSide.BUY,
            price=best_ask,
            min_price_change=min_price_change,
            slippage=slippage,
        ),
        equal_to(Decimal("67343")),
    )
    assert_that(
        get_price_with_slippage(
            side=OrderSide.SELL,
            price=best_bid,
            min_price_change=min_price_change,
            slippage=slippage,
        ),
        equal_to(Decimal("66273.8")),
    )
    assert_that(
        get_price_with_slippage(
            side=OrderSide.SELL,
            price=min_price_change,
            min_price_change=min_price_change,
            slippage=slippage,
        ),
        equal_to(min_price_change),
    )
