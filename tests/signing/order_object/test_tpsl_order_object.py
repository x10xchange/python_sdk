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
    OrderType,
    SelfTradeProtectionLevel,
)
from x10.utils.date import utc_now

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_partial_tpsl_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import OrderTpslTriggerParam, create_order_object

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
                "fee": "0.00055",
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
                            "r": "0xb31988d118bc6632e609e101a3d60c23f7c4de9f03486ae206dacef365e55d",
                            "s": "0x4c85c696a325e6f395942124d435e680174398f9b959f0dbc4032e77794a4d7",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {"collateralAmount": "5000000", "feeAmount": "2750", "syntheticAmount": "-100"},
                },
                "stopLoss": {
                    "triggerPrice": "40000",
                    "triggerPriceType": "MARK",
                    "price": "39000",
                    "priceType": "LIMIT",
                    "settlement": {
                        "signature": {
                            "r": "0x4274ec25be494f9115f156dba70cebda52cd7945769486061a08ee37fde705a",
                            "s": "0x1e1f389746d7100cc33c9f5587ec98631475cae35978cf52f8a8cea3815241a",
                        },
                        "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                        "collateralPosition": "10002",
                    },
                    "debuggingAmounts": {"collateralAmount": "3900000", "feeAmount": "2145", "syntheticAmount": "-100"},
                },
                "debuggingAmounts": {"collateralAmount": "0", "feeAmount": "0", "syntheticAmount": "-100"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_position_tpsl_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import OrderTpslTriggerParam, create_order_object

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
                "fee": "0.00055",
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
                "debuggingAmounts": {"collateralAmount": "0", "feeAmount": "0", "syntheticAmount": "0"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )
