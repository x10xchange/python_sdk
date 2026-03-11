import datetime

from hamcrest import assert_that, equal_to
from eth_account import Account
from decimal import Decimal

from hamcrest import equal_to

from x10.perpetual.user_client.onboarding import get_l2_keys_from_l1_account
from x10.perpetual.withdrawals import Withdrawal


def test_withdrawal_object_generation():
    known_private_key = "50c8e358cc974aaaa6e460641e53f78bdc550fd372984aa78ef8fd27c751e6f4"

    l1_account = Account.from_key(known_private_key)

    payload = Withdrawal(
        account_id=12,
        target_wallet="0x1234",
        amount=Decimal("1"),
        expiration=datetime.datetime.fromtimestamp(1710176400,tz=datetime.timezone.utc),
        asset_id="0x1",
    )
    result = l1_account.sign_message(payload.to_signable_message("x10.exchange")).signature.hex()
    assert_that(
        result,
        equal_to('f1d965cc6c3d020c103e2bd295a0416ab50b0f6c67b01312bf09ea883788df2027a7dad3666c7cca618063b9eda37854642c02dc7842679ccc07e4ea0d0ec0ec1c')
    )
