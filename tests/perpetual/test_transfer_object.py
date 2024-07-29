from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.perpetual.accounts import AccountModel

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_transfer(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.transfer_object import create_transfer_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    accounts = [
        AccountModel(
            status="ACTIVE",
            l2_key="0x6970ac7180192cb58070d639064408610d0fbfd3b16c6b2c6219b9d91aa456f",
            l2_vault="10001",
            account_index=0,
            account_id=1001,
            description="Main Account",
            api_keys=[],
        ),
        AccountModel(
            status="ACTIVE",
            l2_key="0x6970ac7180192cb58070d639064408610d0fbfd3b16c6b2c6219b9d91aa456f",
            l2_vault="10002",
            account_index=0,
            account_id=1002,
            description="Main Account",
            api_keys=[],
        ),
    ]
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
                    "receiverPublicKey": "0x6970ac7180192cb58070d639064408610d0fbfd3b16c6b2c6219b9d91aa456f",
                    "senderPositionId": 10001,
                    "senderPublicKey": "0x6970ac7180192cb58070d639064408610d0fbfd3b16c6b2c6219b9d91aa456f",
                    "signature": {
                        "r": "0x1603de2462480569344dddb57fa5c4c9d960d3d163aedc157c628792419eca4",
                        "s": "0x6cd0c3f58f63eeb7a2f21bb8d4a2903e933a52c1fb3c1f38cd019a9e32b26",
                    },
                },
            }
        ),
    )
