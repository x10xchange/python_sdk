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
                "id": "2057177517787449460689138427731484839396065306136765792011752882862551327344",
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
                        "r": "0x4a8c8928a5bd63bf11ed6570d25078ff67a14dfba6a75855cc3b3d19e26621e",
                        "s": "0x11afcfac10aea315b88f774836e980d81738317156d59d20abf9cd4c374fd77",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "debuggingAmounts": {
                    "collateralAmount": "43445116",
                    "feeAmount": "21723",
                    "syntheticAmount": "10000000",
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
                "id": "3155583690180525934046012843594580395696986309866824276323868753991017198384",
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
                        "r": "0x702fb315701838342b120267a1b0ca62c2dd79ea4fbf5b2faf23985aaf962b2",
                        "s": "0x388e459d7e04c187d1635fcc3529e139a41e1c9c1364c8707060c3b97adfee",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "debuggingAmounts": {
                    "collateralAmount": "43445117",
                    "feeAmount": "21723",
                    "syntheticAmount": "10000000",
                },
            }
        ),
    )
