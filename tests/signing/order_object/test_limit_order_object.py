from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.config import TESTNET_CONFIG
from x10.models.order import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
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

    from x10.signing.order_object import create_order_object

    frozen_time.move_to("2024-01-05 01:08:57")
    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.SELL,
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
    )
    freezer.stop()
    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "2232188746727335862816603489303653270852715601463961134919314346761104492787",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1704420537000,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x5fce9121830ce5d52ebd67cbe3c26c887c90ea167847a13fcd9941131259632",
                        "s": "0x2dce7889bf3180fe5b6a8000694d9caf4ad8700178bf95c386f23f4a94f15f7",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "43445116", "feeAmount": "23895", "syntheticAmount": "-1000"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_sell_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.SELL,
        expire_time=utc_now() + timedelta(days=14),
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
        nonce=FROZEN_NONCE,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "72965300737557143680432668562257471458173947931488845841217525623203620988",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x3f46da6e065078f977a03f2f06344233d35c4e24c59ad1bdcedfb4e4decc7d5",
                        "s": "0x28f0ff5691836871618e3f8ace4f2afd49a25859d225438bbdb978dc740a8f1",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "43445116", "feeAmount": "23895", "syntheticAmount": "-1000"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import create_order_object

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
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "1907762952461311671923583391607095874251325290575862033081301647075361782959",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "CLIENT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x491ff843ef9e616db627d20cc372a05bcfb7e5dfa85ce0691eab871bf4c783d",
                        "s": "0x204ca78c316b29e7d05070ce115fe281422f870409cba03b5163fba455a7c63",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "-43445117", "feeAmount": "23895", "syntheticAmount": "1000"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order_with_order_tpsl(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import OrderTpslTriggerParam, create_order_object

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
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
        tp_sl_type=OrderTpslType.ORDER,
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
                "id": "1907762952461311671923583391607095874251325290575862033081301647075361782959",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "CLIENT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x491ff843ef9e616db627d20cc372a05bcfb7e5dfa85ce0691eab871bf4c783d",
                        "s": "0x204ca78c316b29e7d05070ce115fe281422f870409cba03b5163fba455a7c63",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": "ORDER",
                "takeProfit": {
                    "triggerPrice": "49000",
                    "triggerPriceType": "MARK",
                    "price": "50000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x3f93be474562d4ea31aad80205e846315155346691a863a286c51985ac57dca",
                            "s": "0x5483832334dc8b86304ddbdf887483a9bd6dfd78c7ad49c802a697a9bc01ad4",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "50000000",
                        "feeAmount": "27500",
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
                            "r": "0x75cbbf7495af1b2eec8fb8427f0610d157aebbb9910aae551b36f4f53638e50",
                            "s": "0x71b2a6611bb0a31c1944730050e38678067c025894410a5211f23658e80dad2",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "39000000",
                        "feeAmount": "21450",
                        "syntheticAmount": "-1000",
                    },
                },
                "debuggingAmounts": {"collateralAmount": "-43445117", "feeAmount": "23895", "syntheticAmount": "1000"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order_with_position_tpsl(
    mocker: MockerFixture, create_trading_account, create_btc_usd_market
):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import OrderTpslTriggerParam, create_order_object

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
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
        tp_sl_type=OrderTpslType.POSITION,
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
                "id": "1907762952461311671923583391607095874251325290575862033081301647075361782959",
                "market": "BTC-USD",
                "type": "LIMIT",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "CLIENT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x491ff843ef9e616db627d20cc372a05bcfb7e5dfa85ce0691eab871bf4c783d",
                        "s": "0x204ca78c316b29e7d05070ce115fe281422f870409cba03b5163fba455a7c63",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": "POSITION",
                "takeProfit": {
                    "triggerPrice": "49000",
                    "triggerPriceType": "MARK",
                    "price": "50000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x45491d177ba68c2a02c5b9dba4a696d80e3f357640b8add0077a0e9d66a879f",
                            "s": "0x77f8d743353eb24d429bfd36ebefa58564507dd2c11cca4bcfc25c7f56f3908",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "500000000000000",
                        "feeAmount": "275000000000",
                        "syntheticAmount": "-10000000000",
                    },
                },
                "stopLoss": {
                    "triggerPrice": "40000",
                    "triggerPriceType": "MARK",
                    "price": "39000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x274696d776e044ad4f85a23a26c02d1d367dc56a88e1ef777e4a886680d873f",
                            "s": "0x317051bcb37dd5adc02ba8f98ee3e427aa9ccd3df59019f62c39b0f855ee6dc",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "499999999980000",
                        "feeAmount": "274999999989",
                        "syntheticAmount": "-12820512820",
                    },
                },
                "debuggingAmounts": {"collateralAmount": "-43445117", "feeAmount": "23895", "syntheticAmount": "1000"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )
