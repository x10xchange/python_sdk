import decimal
from decimal import Decimal

from hamcrest import assert_that, equal_to

from x10.core.amount import InternalAmount, L1Amount, StarkAmount


def test_internal_amount_operations(get_asset_usd):
    asset = get_asset_usd().to_settlement_asset()
    rounding_ctx = decimal.Context(rounding=decimal.ROUND_UP)

    internal_amount = InternalAmount(Decimal("1.499"), asset)
    l1_amount = internal_amount.to_l1_amount()
    stark_amount = internal_amount.to_stark_amount(rounding_ctx)

    assert_that(internal_amount.value, equal_to(Decimal("1.499")))
    assert_that(l1_amount.value, equal_to(1_499_000))
    assert_that(stark_amount.value, equal_to(1_499_000))


def test_stark_amount_operations(get_asset_usd):
    asset = get_asset_usd().to_settlement_asset()

    stark_amount = StarkAmount(1_499_000, asset)
    internal_amount = stark_amount.to_internal_amount()

    assert_that(stark_amount.value, equal_to(1_499_000))
    assert_that(internal_amount.value, equal_to(Decimal("1.499")))


def test_l1_amount_operations(get_asset_usd):
    asset = get_asset_usd().to_settlement_asset()

    l1_amount = L1Amount(1_499_000, asset)
    internal_amount = l1_amount.to_internal_amount()

    assert_that(l1_amount.value, equal_to(1_499_000))
    assert_that(internal_amount.value, equal_to(Decimal("1.499")))
