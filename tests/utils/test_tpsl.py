from decimal import Decimal

from hamcrest import assert_that, equal_to

from x10.utils.tpsl import calc_entire_position_size


def test_calc_entire_position_size():
    assert_that(
        calc_entire_position_size(
            price=Decimal("24580.3412"),
            quantity_precision=4,
            max_position_value=Decimal("10000000"),
        ),
        equal_to(Decimal("20341.4588")),
    )
