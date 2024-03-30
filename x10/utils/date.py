from datetime import datetime, timezone


def utc_now():
    return datetime.now(tz=timezone.utc)


def to_epoch_millis(value: datetime):
    assert value.tzinfo == timezone.utc, "`value` must be in UTC"

    return int(value.timestamp() * 1000)
