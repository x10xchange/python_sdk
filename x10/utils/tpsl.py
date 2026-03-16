from decimal import ROUND_FLOOR, Decimal


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
