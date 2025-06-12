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
    mocker.patch("x10.utils.generate_nonce", return_value=FROZEN_NONCE)

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
                "fromVault": trading_account.vault,
                "toVault": int(accounts[1].l2_vault),
                "amount": "1.1",
                "transferredAsset": "0x1",
                "settlement": {
                    "amount": 1100000,
                    "assetId": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                    "expirationTimestamp": 1706231337,
                    "nonce": 1473459052,
                    "receiverPositionId": int(accounts[1].l2_vault),
                    "receiverPublicKey": accounts[1].l2_key,
                    "senderPositionId": trading_account.vault,
                    "senderPublicKey": f"{hex(trading_account.public_key)}",
                    "signature": {
                        "r": "0x23d69eafa600b088844ecd6d413f0858a9f66ce5521a5de2836d97809521af2",
                        "s": "0x67eb0ec88db83455721e8a628fa6fca23085ea42e5d00a6cd2260f8fa5d1ce",
                    },
                },
            }
        ),
    )
