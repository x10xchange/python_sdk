from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.config import TESTNET_CONFIG
from x10.models.order import OrderSide, OrderType, TimeInForce
from x10.utils.date import utc_now
from x10.utils.order import get_price_with_slippage

FROZEN_NONCE = 1473459052
SLIPPAGE = Decimal("0.0075")


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_sell_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import create_order_object

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_side = OrderSide.SELL
    order_price = get_price_with_slippage(
        side=order_side,
        price=Decimal("50000"),
        min_price_change=btc_usd_market.trading_config.min_price_change,
        slippage=SLIPPAGE,
    )
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        order_type=OrderType.MARKET,
        amount_of_synthetic=Decimal("0.00100000"),
        price=order_price,
        side=order_side,
        expire_time=utc_now() + timedelta(days=14),
        time_in_force=TimeInForce.IOC,
        nonce=FROZEN_NONCE,
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "1329959279920778787835850141943406014399403016268035909645039439710012370742",
                "market": "BTC-USD",
                "type": "MARKET",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "49625.0",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "IOC",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x1846200186d1c56fa3125a214bdb4ba02ccc3b9315276ed2e9746c8e155c1c6",
                        "s": "0x437a29282fa06c63c79e132183de169048445477b9becab0300868ec81eebd0",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "49625000", "feeAmount": "27294", "syntheticAmount": "-1000"},
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
    order_side = OrderSide.BUY
    order_price = get_price_with_slippage(
        side=order_side,
        price=Decimal("50000"),
        min_price_change=btc_usd_market.trading_config.min_price_change,
        slippage=SLIPPAGE,
    )
    order_obj = create_order_object(
        account=trading_account,
        market=btc_usd_market,
        order_type=OrderType.MARKET,
        amount_of_synthetic=Decimal("0.00100000"),
        price=order_price,
        side=order_side,
        expire_time=utc_now() + timedelta(days=14),
        time_in_force=TimeInForce.IOC,
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
        nonce=FROZEN_NONCE,
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "2409879577479083341107955215307387093936416851088622563162890616308575179078",
                "market": "BTC-USD",
                "type": "MARKET",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "50375.0",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "IOC",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x5840ba1994d394ec83d9897b3b5c341444d8feac9dd4060f63b7d28edd4a412",
                        "s": "0x7780d481663cbe8ed64dfb7d81fc46d8cf244bb58cb0fee39c3a2949fbf255",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "-50375000", "feeAmount": "27707", "syntheticAmount": "1000"},
                "builderFee": None,
                "builderId": None,
                "rfq": None,
            }
        ),
    )
