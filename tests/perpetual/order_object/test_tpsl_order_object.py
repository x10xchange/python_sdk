from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.models.order import (
    OrderPriceType,
    OrderSide,
    OrderTpslType,
    OrderTriggerPriceType,
    OrderType,
    SelfTradeProtectionLevel,
)
from x10.config import TESTNET_CONFIG
from x10.utils.date import utc_now

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_partial_tpsl_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import OrderTpslTriggerParam, create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        order_type=OrderType.TPSL,
        amount_of_synthetic=btc_usd_market.trading_config.min_order_size,
        price=Decimal("0"),
        side=OrderSide.SELL,
        reduce_only=True,
        expire_time=utc_now() + timedelta(days=14),
        self_trade_protection_level=SelfTradeProtectionLevel.CLIENT,
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
        taker_fee=TESTNET_CONFIG.defaults.taker_fee,
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
                "id": "2302927936354168859785231329337424926774195696889032018790365367779325970821",
                "market": "BTC-USD",
                "type": "TPSL",
                "side": "SELL",
                "qty": "0.0001",
                "price": "0",
                "reduceOnly": True,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "CLIENT",
                "cancelId": None,
                "settlement": None,
                "trigger": None,
                "tpSlType": "ORDER",
                "takeProfit": {
                    "triggerPrice": "49000",
                    "triggerPriceType": "MARK",
                    "price": "50000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x513b8c6540b171c6e85e2992046ce697b6056793ace2ea0e46c04cba1b72aa0",
                            "s": "0x25684458e72e276bbaa87a6787bfab11ed4b117c4f6ffa7cea2781c13648667",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {"collateralAmount": "5000000", "feeAmount": "2500", "syntheticAmount": "-100"},
                },
                "stopLoss": {
                    "triggerPrice": "40000",
                    "triggerPriceType": "MARK",
                    "price": "39000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x30227b00607a0f671db245c734a9d9152c58af0ec0fbc83ac8c50d41b6dc2e5",
                            "s": "0xb355fcce280b7c82c8e6b23106df57d98aba5b3616a791a4db226063693b5d",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {"collateralAmount": "3900000", "feeAmount": "1950", "syntheticAmount": "-100"},
                },
                "debuggingAmounts": {"collateralAmount": "0", "feeAmount": "0", "syntheticAmount": "-100"},
                "builderFee": None,
                "builderId": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_position_tpsl_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.perpetual.order_object import OrderTpslTriggerParam, create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        order_type=OrderType.TPSL,
        amount_of_synthetic=Decimal("0"),
        price=Decimal("0"),
        side=OrderSide.SELL,
        reduce_only=True,
        expire_time=utc_now() + timedelta(days=14),
        self_trade_protection_level=SelfTradeProtectionLevel.CLIENT,
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
        taker_fee=TESTNET_CONFIG.defaults.taker_fee,
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
                "id": "2740618205716882280724217633173981437193188033910023585411792989580464995593",
                "market": "BTC-USD",
                "type": "TPSL",
                "side": "SELL",
                "qty": "0",
                "price": "0",
                "reduceOnly": True,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "CLIENT",
                "cancelId": None,
                "settlement": None,
                "trigger": None,
                "tpSlType": "POSITION",
                "takeProfit": {
                    "triggerPrice": "49000",
                    "triggerPriceType": "MARK",
                    "price": "50000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x9ec78c951d0397e31873bb1f5ede330dffc05a6be918007fac3299a122bc37",
                            "s": "0x1962207a67b6b6d77216d363af31ca5ea37d371ac762aa13bd5366634337b86",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "500000000000000",
                        "feeAmount": "250000000000",
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
                            "r": "0x4b5a05de5d0c07956398de50b846037250dee8cd85c35944fd97f0b3dad3e5b",
                            "s": "0x76aa8c382b73c0f516c8398e4d648d2dad411e8b6a9a7e81fbae3656bed6d78",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {
                        "collateralAmount": "499999999980000",
                        "feeAmount": "249999999990",
                        "syntheticAmount": "-12820512820",
                    },
                },
                "debuggingAmounts": {"collateralAmount": "0", "feeAmount": "0", "syntheticAmount": "0"},
                "builderFee": None,
                "builderId": None,
            }
        ),
    )
