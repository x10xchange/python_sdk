from decimal import Decimal

from hamcrest import assert_that, equal_to
from perpetual.orders import OrderSide

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


def test_get_price_with_slippage(create_btc_usd_market):
    # given
    market = create_btc_usd_market()
    slippage = Decimal("0.0075")
    best_ask = Decimal("66841.6")
    best_bid = Decimal("66774.7")

    # then
    assert_that(
        get_price_with_slippage(
            OrderSide.BUY,
            best_ask,
            market,
            slippage,
        ),
        equal_to(Decimal("67343")),
    )
    assert_that(
        get_price_with_slippage(
            OrderSide.SELL,
            best_bid,
            market,
            slippage,
        ),
        equal_to(Decimal("66273.8")),
    )
    assert_that(
        get_price_with_slippage(
            OrderSide.SELL,
            market.trading_config.min_price_change,
            market,
            slippage,
        ),
        equal_to(market.trading_config.min_price_change),
    )
