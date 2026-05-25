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
                "id": "2580220688642480426946040763258220762106230673118492731878319591751617419967",
                "market": "BTC-USD",
                "type": "MARKET",
                "side": "SELL",
                "qty": "0.00100000",
                "price": "49625.0",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "IOC",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x28af719b8c9619fadd151a0f9c269058b3240ae2e08ab14e6fa15b8ea081dc6",
                        "s": "0x78c518768fe71c8583aee78e756de66ffed2170171fec10da03edc5e9a3d241",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "49625000", "feeAmount": "24813", "syntheticAmount": "-1000"},
                "builderFee": None,
                "builderId": None,
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
                "id": "3168487898969135762904713190835173941926260364920267758857147425797045990747",
                "market": "BTC-USD",
                "type": "MARKET",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "50375.0",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "IOC",
                "expiryEpochMillis": 1705626536861,
                "fee": "0.0005",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x4baa519bdf416e3563eb9c6d52d48d6adaf8926e4840a76d242c1ba62be6587",
                        "s": "0x87342653d415d4f47f876bcc34d11b2a16c9220b6a8e1dc7fb9225d9e7e9f9",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": None,
                "tpSlType": None,
                "takeProfit": None,
                "stopLoss": None,
                "debuggingAmounts": {"collateralAmount": "-50375000", "feeAmount": "25188", "syntheticAmount": "1000"},
                "builderFee": None,
                "builderId": None,
            }
        ),
    )
