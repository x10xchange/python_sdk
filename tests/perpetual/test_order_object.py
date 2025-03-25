from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to, has_entries
from pytest_mock import MockerFixture

from x10.perpetual.orders import OrderSide, SelfTradeProtectionLevel
from x10.utils.date import utc_now

FROZEN_NONCE = 1473459052


@pytest.mark.asyncio
async def test_create_sell_order_with_default_expiration(
    mocker: MockerFixture, create_trading_account, create_btc_usd_market
):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    freezer = freeze_time("2024-01-05 01:08:56.860694")
    frozen_time = freezer.start()

    from x10.perpetual.order_object import create_order_object

    frozen_time.move_to("2024-01-05 01:08:57")

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.SELL,
    )

    freezer.stop()

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "2096045681239655445582070517240411138302380632690430411530650608228763263945",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1704445737000,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x39ff8493e8e26c9a588a7046e1380b6e1201287a179e10831b7040d3efc26d",
                        "s": "0x5c9acd1879bf8d43e4ccd14648186d2a9edf387fe1b61e491fe0a539de3272b",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "43445116", "feeAmount": "21723", "syntheticAmount": "1000"},
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_sell_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.SELL,
        expire_time=utc_now() + timedelta(days=14),
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "2656406151911156282898770907232061209407892373872976831396563134482995247110",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536860,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x5766fe0420270feadb55cd6d89cedba0bb8cbd3847fca73d27fe78b0c499b48",
                        "s": "0xc8456b2db2060d25990471f22cae59bed86d51e508812455458f0464cc5867",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "43445116", "feeAmount": "21723", "syntheticAmount": "1000"},
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
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.BUY,
        expire_time=utc_now() + timedelta(days=14),
        self_trade_protection_level=SelfTradeProtectionLevel.CLIENT,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "1166889461421716582054747865777410838520755143669870072976787470981175645302",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536860,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "CLIENT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x52a42b6cb980b552c08d5d01b86852b64f7468f5ed7430133f0e2ea1b53df0",
                        "s": "0x67287f8aca9f96bc0fa58e5f0f6875e52f869fc392d912145ff9cb16b73a666",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "43445117", "feeAmount": "21723", "syntheticAmount": "1000"},
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_cancel_previous_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.BUY,
        expire_time=utc_now() + timedelta(days=14),
        previous_order_id="previous_custom_id",
    )

    assert_that(
        order_obj.to_api_request_json(),
        has_entries(
            {
                "cancelId": equal_to("previous_custom_id"),
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_external_order_id(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.starkex.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.BUY,
        expire_time=utc_now() + timedelta(days=14),
        order_external_id="custom_id",
    )

    assert_that(
        order_obj.to_api_request_json(),
        has_entries(
            {
                "id": equal_to("custom_id"),
            }
        ),
    )
