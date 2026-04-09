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
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.transfer_object import create_transfer_object

    trading_account = create_trading_account()
    accounts = create_accounts()
    transfer_obj = create_transfer_object(
        from_vault=trading_account.vault,
        to_vault=int(accounts[1].l2_vault),
        to_l2_key=accounts[1].l2_key,
        amount=Decimal("1.1"),
        stark_account=trading_account,
        config=TESTNET_CONFIG,
        nonce=FROZEN_NONCE,
    )
    assert_that(
        transfer_obj.to_api_request_json(),
        equal_to(
            {
                "fromVault": 10002,
                "toVault": 10002,
                "amount": "1.1",
                "settlement": {
                    "amount": 1100000,
                    "assetId": "0x1",
                    "expirationTimestamp": 1706231337,
                    "nonce": 1473459052,
                    "receiverPositionId": 10002,
                    "receiverPublicKey": "0x3895139a98a6168dc8b0db251bcd0e6dcf97fd1e96f7a87d9bd3f341753a844",
                    "senderPositionId": 10002,
                    "senderPublicKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "signature": {
                        "r": "0x21f353080b04ab862474d0d2985f4d223087a89193a3a8bdea3de320f845cf8",
                        "s": "0x6f70daa9e65037d97ccf0667cc6f1368b7b01a93d0ededf929b53be3f177d96",
                    },
                },
                "transferredAsset": "0x1",
            }
        ),
    )
