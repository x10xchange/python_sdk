from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_withdrawal(mocker: MockerFixture, create_trading_account, create_accounts, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.withdrawal_object import create_withdrawal_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    accounts = create_accounts()
    withdrawal_obj = create_withdrawal_object(
        accounts[0].account_id,
        Decimal("1.1"),
        "USD",
        "0x6c5a62e584D0289def8Fe3c9C8194a07246a2C52",
        trading_account,
        accounts,
        btc_usd_market,
    )

    assert_that(
        withdrawal_obj.to_api_request_json(),
        equal_to(
            {
                "accountId": 1001,
                "amount": "1100000",
                "asset": "USD",
                "settlement": {
                    "amount": 1100000,
                    "collateralAssetId": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                    "ethAddress": "0x6c5a62e584d0289def8fe3c9c8194a07246a2c52",
                    "expirationTimestamp": 473786,
                    "nonce": 1473459052,
                    "positionId": 10001,
                    "publicKey": "0x6970ac7180192cb58070d639064408610d0fbfd3b16c6b2c6219b9d91aa456f",
                    "signature": {
                        "r": "0x50f64858e6a5dc102e66a9a4a3f26a831dd8134914ddc783b962dadefaf10e4",
                        "s": "0x439465e93fefd9f0473ce35d21cf1f31f3c30dad51fe9efc190b09702ed75c",
                    },
                },
            }
        ),
    )
