from datetime import datetime

from hamcrest import assert_that, equal_to, raises

from x10.utils.date import to_epoch_millis


def test_convert_datetime_to_epoch_millis():
    dt = datetime.fromisoformat("2024-01-08 11:35:20.447+00:00")

    assert_that(to_epoch_millis(dt), equal_to(1704713720447))


def test_throw_on_non_utc_timezone():
    dt1 = datetime.fromisoformat("2024-01-08 11:35:20.447")
    dt2 = datetime.fromisoformat("2024-01-08 11:35:20.447+02:00")

    assert_that(lambda: to_epoch_millis(dt1), raises(AssertionError, "`value` must be in UTC"))
    assert_that(lambda: to_epoch_millis(dt2), raises(AssertionError, "`value` must be in UTC"))
