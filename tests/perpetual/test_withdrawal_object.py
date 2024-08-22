from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.perpetual.configuration import TESTNET_CONFIG

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_withdrawal(mocker: MockerFixture, create_trading_account, create_accounts, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.withdrawal_object import create_withdrawal_object

    trading_account = create_trading_account()
    withdrawal_obj = create_withdrawal_object(
        amount=Decimal("1.1"),
        eth_address="0x6c5a62e584D0289def8Fe3c9C8194a07246a2C52",
        description="withdraw my gains",
        config=TESTNET_CONFIG,
        stark_account=trading_account,
    )

    assert_that(
        withdrawal_obj.to_api_request_json(),
        equal_to(
            {
                "amount": "1.1",
                "settlement": {
                    "amount": 1100000,
                    "collateralAssetId": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                    "ethAddress": "0x6c5a62e584d0289def8fe3c9c8194a07246a2c52",
                    "expirationTimestamp": 474146,
                    "nonce": 1473459052,
                    "positionId": 10002,
                    "publicKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "signature": {
                        "r": "0x3f3aa8b0c2f2a8953aef42dd79d7c1003a98df241b7a989bb0ed122ae9e99dd",
                        "s": "0x789b22f03b13df2e95d5bffd472f1c8abb325291a142e55b7bd61a6cc998b46",
                    },
                },
                "description": "withdraw my gains",
            }
        ),
    )
