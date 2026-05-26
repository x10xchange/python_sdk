from datetime import datetime

from freezegun import freeze_time
from hamcrest import assert_that, equal_to, raises

from x10.utils.date import to_epoch_millis


@freeze_time("2024-01-05 01:08:56.860694")
def test_utc_now():
    from x10.utils.date import utc_now

    expected_dt = datetime.fromisoformat("2024-01-05 01:08:56.860694+00:00")
    assert_that(utc_now(), equal_to(expected_dt))


def test_convert_datetime_to_epoch_millis():
    dt = datetime.fromisoformat("2024-01-08 11:35:20.447+00:00")

    assert_that(to_epoch_millis(dt), equal_to(1704713720447))


def test_throw_on_non_utc_timezone():
    dt1 = datetime.fromisoformat("2024-01-08 11:35:20.447")
    dt2 = datetime.fromisoformat("2024-01-08 11:35:20.447+02:00")

    assert_that(lambda: to_epoch_millis(dt1), raises(AssertionError, "`value` must be in UTC"))  # type: ignore[misc]
    assert_that(lambda: to_epoch_millis(dt2), raises(AssertionError, "`value` must be in UTC"))  # type: ignore[misc]


@freeze_time("2024-01-05 01:08:56.860694")
def test_calc_settlement_expiration():
    from x10.utils.date import calc_settlement_expiration

    custom_dt = datetime.fromisoformat("2024-01-08 11:35:20.447+00:00")

    assert_that(calc_settlement_expiration(10), equal_to(1705280937))
    assert_that(calc_settlement_expiration(10, custom_dt), equal_to(1705577721))
