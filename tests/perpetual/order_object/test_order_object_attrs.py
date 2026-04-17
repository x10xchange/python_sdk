from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to, has_entries
from pytest_mock import MockerFixture

from x10.configuration import TESTNET_CONFIG
from x10.models.order import OrderSide
from x10.utils.date import utc_now

FROZEN_NONCE = 1473459052


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
