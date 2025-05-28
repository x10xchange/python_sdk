from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to, has_entries
from pytest_mock import MockerFixture

from x10.perpetual.configuration import STARKNET_TESTNET_CONFIG
from x10.perpetual.orders import OrderSide, SelfTradeProtectionLevel
from x10.utils.date import utc_now

FROZEN_NONCE = 1473459052


@pytest.mark.asyncio
async def test_create_sell_order_with_default_expiration(
    mocker: MockerFixture, create_trading_account, create_btc_usd_market
):
    mocker.patch("x10.utils.generate_nonce", return_value=FROZEN_NONCE)
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
        starknet_domain=STARKNET_TESTNET_CONFIG.starknet_domain,
    )
    freezer.stop()
    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "529621978301228831750156704671293558063128025271079340676658105549022202327",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1704420537000,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x3d17d8b9652e5f60d40d079653cfa92b1065ea8cf159609a3c390070dcd44f7",
                        "s": "0x76a6deccbc84ac324f695cfbde80e0ed62443e95f5dcd8722d12650ccc122e5",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "43445116", "feeAmount": "21723", "syntheticAmount": "-1000"},
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_sell_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.generate_nonce", return_value=FROZEN_NONCE)

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
        starknet_domain=STARKNET_TESTNET_CONFIG.starknet_domain,
        nonce=FROZEN_NONCE,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "2969335148777495210033041829700798003994871688044444919524700744667647811801",
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
                        "r": "0x604ef07147d4251385eaaa630e6a71db8f0a8c7cb33021c98698047db80edfa",
                        "s": "0x6c707d9a06604d3f8ffd34378bf4fce7c0aaf50cba4cf37c3525c323106cda5",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "43445116", "feeAmount": "21723", "syntheticAmount": "-1000"},
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.generate_nonce", return_value=FROZEN_NONCE)

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
        starknet_domain=STARKNET_TESTNET_CONFIG.starknet_domain,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "2495374044666992118771096772295242242651427695217815113349321039194683172848",
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
                        "r": "0xa55625c7d5f1b85bed22556fc805224b8363074979cf918091d9ddb1403e13",
                        "s": "0x504caf634d859e643569743642ccf244434322859b2421d76f853af43ae7a46",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "-43445117", "feeAmount": "21723", "syntheticAmount": "1000"},
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_cancel_previous_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.generate_nonce", return_value=FROZEN_NONCE)

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
        starknet_domain=STARKNET_TESTNET_CONFIG.starknet_domain,
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
    mocker.patch("x10.utils.generate_nonce", return_value=FROZEN_NONCE)

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
        starknet_domain=STARKNET_TESTNET_CONFIG.starknet_domain,
    )

    assert_that(
        order_obj.to_api_request_json(),
        has_entries(
            {
                "id": equal_to("custom_id"),
            }
        ),
    )
