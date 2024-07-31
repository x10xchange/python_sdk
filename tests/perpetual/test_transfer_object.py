from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_transfer(mocker: MockerFixture, create_trading_account, create_accounts, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.transfer_object import create_transfer_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    accounts = create_accounts()
    transfer_obj = create_transfer_object(
        accounts[0].account_id,
        accounts[1].account_id,
        Decimal("1.1"),
        "USD",
        stark_account=trading_account,
        accounts=accounts,
        market=btc_usd_market,
    )

    assert_that(
        transfer_obj.to_api_request_json(),
        equal_to(
            {
                "fromAccount": 1001,
                "toAccount": 1002,
                "amount": "1.1",
                "transferredAsset": "USD",
                "settlement": {
                    "amount": 1100000,
                    "assetId": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                    "expirationTimestamp": 473786,
                    "nonce": 1473459052,
                    "receiverPositionId": 10002,
                    "receiverPublicKey": "0x3895139a98a6168dc8b0db251bcd0e6dcf97fd1e96f7a87d9bd3f341753a844",
                    "senderPositionId": 10001,
                    "senderPublicKey": "0x6970ac7180192cb58070d639064408610d0fbfd3b16c6b2c6219b9d91aa456f",
                    "signature": {
                        "r": "0x199d37ea69c2b4604430ca2588843827995d01a85537a90244659268d9995ba",
                        "s": "0x4c65838c77e31bb6d464a1d9cc5d560cd091ddb75cb7d64963b4e28db2c381",
                    },
                },
            }
        ),
    )
