from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_limit_order_settlement_data(
    mocker: MockerFixture, create_trading_account, get_asset_usd, get_asset_xvs
):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.config import MAINNET_CONFIG
    from x10.perpetual.limit_order_object_settlement import create_order_settlement_data

    trading_account = create_trading_account()
    collateral_asset = get_asset_usd()
    vault_asset = get_asset_xvs()

    settlement, quote_amount_human, base_amount_human = create_order_settlement_data(
        quote_amount=Decimal("10"),
        base_amount=Decimal("7"),
        position_id=trading_account.vault,
        quote_asset_model=collateral_asset,
        base_asset_model=vault_asset,
        starknet_account=trading_account,
        starknet_domain=MAINNET_CONFIG.signing.starknet_domain,
        is_buy=True,
    )

    assert_that(quote_amount_human.value, equal_to(Decimal("-10")))
    assert_that(base_amount_human.value, equal_to(Decimal("7")))
    assert_that(
        settlement.to_api_request_json(),
        equal_to(
            {
                "baseAmount": 7000000,
                "quoteAmount": -10000000,
                "feeAmount": 0,
                "baseAssetId": "0x7db365513df1ee2eb8fc2d157d4d1cba3d4a2ef59b44dd3d61124c88b4f6084",
                "quoteAssetId": "0x1",
                "feeAssetId": "0x1",
                "expirationTimestamp": 1705630137,
                "nonce": 1473459052,
                "receiverPositionId": 10002,
                "senderPositionId": 10002,
                "signature": {
                    "r": "0x77c1a73e45bf4d7934f7deb04fbd4a3c9d3261baf2007e5f25b0fc681dd3183",
                    "s": "0x26f4fbcf7b3dbb2bf14c438bed1c482eb3a65dc9f73b305e56345c8a3e393cd",
                },
            }
        ),
    )
