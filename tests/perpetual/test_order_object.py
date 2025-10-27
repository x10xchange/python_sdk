from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to, has_entries
from pytest_mock import MockerFixture

from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orders import (
    OrderPriceType,
    OrderSide,
    OrderTriggerPriceType,
    SelfTradeProtectionLevel,
)
from x10.utils.date import utc_now

FROZEN_NONCE = 1473459052


@pytest.mark.asyncio
async def test_create_sell_order_with_default_expiration(
    mocker: MockerFixture, create_trading_account, create_btc_usd_market
):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)
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
        starknet_domain=TESTNET_CONFIG.starknet_domain,
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
                "builderFee": None,
                "builderId": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_sell_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

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
        starknet_domain=TESTNET_CONFIG.starknet_domain,
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
                "expiryEpochMillis": 1705626536861,
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
                "builderFee": None,
                "builderId": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

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
        starknet_domain=TESTNET_CONFIG.starknet_domain,
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
                "expiryEpochMillis": 1705626536861,
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
                "builderFee": None,
                "builderId": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order_with_tpsl(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import OrderTpslTriggerParam, create_order_object

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
        starknet_domain=TESTNET_CONFIG.starknet_domain,
        take_profit=OrderTpslTriggerParam(
            trigger_price=Decimal("49000"),
            trigger_price_type=OrderTriggerPriceType.MARK,
            price=Decimal("50000"),
            price_type=OrderPriceType.LIMIT,
        ),
        stop_loss=OrderTpslTriggerParam(
            trigger_price=Decimal("40000"),
            trigger_price_type=OrderTriggerPriceType.MARK,
            price=Decimal("39000"),
            price_type=OrderPriceType.LIMIT,
        ),
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
                "expiryEpochMillis": 1705626536861,
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
                "takeProfit": {
                    "triggerPrice": "49000",
                    "triggerPriceType": "MARK",
                    "price": "50000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x19a043716e5b47bdfa8743e1cad471da3a86dc5a4044a87fb51bea4d61d788c",
                            "s": "0x70db738d6d4896b757e062fec0f3eb8fdcf7d5de23ace3d3c44c1fc9c9c66d4",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "50000000",
                        "feeAmount": "25000",
                        "syntheticAmount": "-1000",
                    },
                },
                "stopLoss": {
                    "triggerPrice": "40000",
                    "triggerPriceType": "MARK",
                    "price": "39000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0xa1d28df388fb5038c2475527667b726ccec821d8362a803702b3a0428ba647",
                            "s": "0x511a2c6a9dc215d965ca08fe2c1533923b2470b1625e1144c70c63b26671086",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "39000000",
                        "feeAmount": "19500",
                        "syntheticAmount": "-1000",
                    },
                },
                "debuggingAmounts": {"collateralAmount": "-43445117", "feeAmount": "21723", "syntheticAmount": "1000"},
                "builderFee": None,
                "builderId": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_cancel_previous_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

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
        previous_order_external_id="previous_custom_id",
        starknet_domain=TESTNET_CONFIG.starknet_domain,
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
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

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
        starknet_domain=TESTNET_CONFIG.starknet_domain,
    )

    assert_that(
        order_obj.to_api_request_json(),
        has_entries(
            {
                "id": equal_to("custom_id"),
            }
        ),
    )
