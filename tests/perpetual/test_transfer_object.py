from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.perpetual.configuration import TESTNET_CONFIG

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_transfer(mocker: MockerFixture, create_trading_account, create_accounts, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.transfer_object import create_transfer_object

    trading_account = create_trading_account()
    accounts = create_accounts()

    transfer_obj = create_transfer_object(
        from_vault=int(accounts[0].l2_vault),
        from_l2_key=accounts[0].l2_key,
        to_vault=int(accounts[1].l2_vault),
        to_l2_key=accounts[1].l2_key,
        amount=Decimal("1.1"),
        stark_account=trading_account,
        config=TESTNET_CONFIG,
    )

    assert_that(
        transfer_obj.to_api_request_json(),
        equal_to(
            {
                "fromVault": 10001,
                "toVault": 10002,
                "amount": "1.1",
                "transferredAsset": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                "settlement": {
                    "amount": 1100000,
                    "assetId": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                    "expirationTimestamp": 473954,
                    "nonce": 1473459052,
                    "receiverPositionId": 10002,
                    "receiverPublicKey": "0x3895139a98a6168dc8b0db251bcd0e6dcf97fd1e96f7a87d9bd3f341753a844",
                    "senderPositionId": 10001,
                    "senderPublicKey": "0x6970ac7180192cb58070d639064408610d0fbfd3b16c6b2c6219b9d91aa456f",
                    "signature": {
                        "r": "0x6840d40d8a7e190caa9bf823e9d8ee08462148b30cfdaff306302d686b22fa9",
                        "s": "0x4bd52731c5549f4e0781e8ffa7c5aea9be0aa01ca502a50ca7fc7cc46ccdb2f",
                    },
                },
            }
        ),
    )
