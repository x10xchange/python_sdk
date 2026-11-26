from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to
from pytest_mock import MockerFixture

from x10.config import TESTNET_CONFIG
from x10.models.order import (
    OrderPriceType,
    OrderSide,
    OrderTriggerDirection,
    OrderTriggerPriceType,
    OrderType,
)

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_create_buy_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
    mocker.patch("x10.utils.nonce.generate_nonce", return_value=FROZEN_NONCE)

    from x10.signing.order_object import (
        OrderConditionalTriggerParam,
        create_order_object,
    )

    trading_account = create_trading_account()
    btc_usd_market = create_btc_usd_market()
    order_obj = create_order_object(
        account=trading_account,
        order_type=OrderType.CONDITIONAL,
        market=btc_usd_market,
        amount_of_synthetic=Decimal("0.00100000"),
        price=Decimal("43445.11680000"),
        side=OrderSide.BUY,
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
        trigger=OrderConditionalTriggerParam(
            trigger_price=Decimal("43400"),
            trigger_price_type=OrderTriggerPriceType.INDEX,
            direction=OrderTriggerDirection.UP,
            execution_price_type=OrderPriceType.MARKET,
        ),
    )

    assert_that(
        order_obj.to_api_request_json(),
        equal_to(
            {
                "id": "434417434510465193432755032994326999013617650871787329211165981097474900314",
                "market": "BTC-USD",
                "type": "CONDITIONAL",
                "side": "BUY",
                "qty": "0.00100000",
                "price": "43445.11680000",
                "reduceOnly": False,
                "postOnly": False,
                "timeInForce": "GTT",
                "expiryEpochMillis": 1704420536861,
                "fee": "0.00055",
                "nonce": "1473459052",
                "selfTradeProtectionLevel": "ACCOUNT",
                "cancelId": None,
                "settlement": {
                    "signature": {
                        "r": "0x70cd275fcff48aacfdb5c31c566a00cbebea85f15f01ce3221efcc7cd3144df",
                        "s": "0x2e9a704b178064150b12e193d25747a39b68f5de83c4a694cb93b3d1bdd0636",
                    },
                    "starkKey": "0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
                    "collateralPosition": "10002",
                },
                "trigger": {
                    "triggerPrice": "43400",
                    "triggerPriceType": "INDEX",
                    "direction": "UP",
                    "executionPriceType": "MARKET",
                },
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
