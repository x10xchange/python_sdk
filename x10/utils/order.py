from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

from perpetual.markets import MarketModel
from perpetual.orders import OrderSide


def calc_entire_position_size(
    *,
    price: Decimal,
    quantity_precision: int,
    max_position_value: Decimal,
):
    """
    This calculation is required to avoid a case when the position at
    the time of TPSL execution has a bigger size than a signed TPSL order size.
    """

    assert price > 0, "`price` must be greater than 0"

    return (max_position_value * 50 / price).quantize(Decimal(10) ** -quantity_precision, rounding=ROUND_FLOOR)


def get_price_with_slippage(side: OrderSide, price: Decimal, market: MarketModel, slippage: Decimal) -> Decimal:
    slippage_collateral = price * slippage
    price_with_slippage = price + slippage_collateral if side == OrderSide.BUY else price - slippage_collateral
    rounding_direction = ROUND_CEILING if side == OrderSide.BUY else ROUND_FLOOR

    return Decimal.max(
        market.trading_config.min_price_change,
        market.trading_config.round_price(price_with_slippage, rounding_direction=rounding_direction),
    )
