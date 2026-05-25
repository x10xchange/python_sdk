import math
from datetime import datetime, timedelta, timezone


def utc_now():
    return datetime.now(tz=timezone.utc)


def to_epoch_millis(value: datetime):
    assert value.tzinfo == timezone.utc, "`value` must be in UTC"

    # Use ceiling to match the hash_order logic which uses math.ceil
    return int(math.ceil(value.timestamp() * 1000))


def calc_settlement_expiration(buffer_days: int, expiration_timestamp: datetime | None = None) -> int:
    if expiration_timestamp is None:
        expiration_timestamp = utc_now()

    expire_time_with_buffer = expiration_timestamp + timedelta(days=buffer_days)
    expire_time_as_seconds = math.ceil(expire_time_with_buffer.timestamp())

    return expire_time_as_seconds
