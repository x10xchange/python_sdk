from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.perpetual.orders import OrderSide

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_sell_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = await create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.SELL,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "3280850248231586971858312197993273142004261856737545220604391622653484552257",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "fee": "0.0005",
                "expiryEpochMillis": 1705021736860,
                "nonce": "1473459052",
                "takeProfitSignature": None,
                "stopLossSignature": None,
                "cancelId": None,
                "triggerPrice": None,
                "takeProfitPrice": None,
                "takeProfitLimitPrice": None,
                "stopLossPrice": None,
                "stopLossLimitPrice": None,
                "settlement": {
                    "signature": {
                        "r": "0x6036ac4ade5f5dfb1d293450fbf3a6864be35d3d90f78c61a6e97ed08af60ad",
                        "s": "0x6d2b1e8e4ce023cb4c85864ac042d865c4e5a455b1916606bbde9386357a9ee",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "debuggingAmounts": {
                    "collateralAmount": "43445116",
                    "feeAmount": "21723",
                    "syntheticAmount": "1000",
                },
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = await create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.BUY,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "3341877135169230217913846589832056830347340581639748919090243450434880694177",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "fee": "0.0005",
                "expiryEpochMillis": 1705021736860,
                "nonce": "1473459052",
                "takeProfitSignature": None,
                "stopLossSignature": None,
                "cancelId": None,
                "triggerPrice": None,
                "takeProfitPrice": None,
                "takeProfitLimitPrice": None,
                "stopLossPrice": None,
                "stopLossLimitPrice": None,
                "settlement": {
                    "signature": {
                        "r": "0xc68d574e2e92138f799068506a5e2840083ff1a6e3d65498f38e3bf7dd1c95",
                        "s": "0x5b51dd5664176164dcff0fb7a7eff7db748d920bbc1be4dc42b433286139bfa",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "debuggingAmounts": {
                    "collateralAmount": "43445117",
                    "feeAmount": "21723",
                    "syntheticAmount": "1000",
                },
            }
        ),
    )
