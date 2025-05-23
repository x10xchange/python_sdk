import math
from datetime import timedelta
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.withdrawals import PerpetualSlowWithdrawal
from x10.utils.date import utc_now

SECONDS_IN_HOUR = 60 * 60


def calc_expiration_timestamp():
    expire_time = utc_now() + timedelta(days=15)
    expire_time_with_buffer = expire_time + timedelta(days=14)
    expire_time_with_buffer_as_hours = math.ceil(expire_time_with_buffer.timestamp() / SECONDS_IN_HOUR)

    return expire_time_with_buffer_as_hours


def create_withdrawal_object(
    amount: Decimal,
    eth_address: str,
    stark_account: StarkPerpetualAccount,
    config: EndpointConfig,
    description: str | None = None,
    nonce: int | None = None,
) -> PerpetualSlowWithdrawal:
    raise NotImplementedError("This function is not implemented yet.")
