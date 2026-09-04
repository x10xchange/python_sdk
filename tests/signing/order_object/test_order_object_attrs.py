from datetime import timedelta
from decimal import Decimal

import pytest
from freezegun import freeze_time
from hamcrest import assert_that, equal_to, has_entries
from pytest_mock import MockerFixture

from x10.config import TESTNET_CONFIG
from x10.errors import ValidationError
from x10.models.order import CreateOrderRfqModel, OrderSide, OrderType, TimeInForce
from x10.utils.date import utc_now

FROZEN_NONCE = 1473459052


@freeze_time("2024-01-05 01:08:56.860694")
@pytest.mark.asyncio
async def test_cancel_previous_order(mocker: MockerFixture, create_trading_account, create_btc_usd_market):
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
        previous_order_external_id="previous_custom_id",
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
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
        order_external_id="custom_id",
        starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
    )

    assert_that(
        order_obj.to_api_request_json(),
        has_entries(
            {
                "id": equal_to("custom_id"),
            }
        ),
    )


@pytest.mark.asyncio
async def test_rfq_not_allowed_for_non_rfq_market(create_trading_account, create_btc_usd_market):
    from x10.signing.order_object import create_order_object

    with pytest.raises(ValidationError, match="only supported for RFQ markets"):
        create_order_object(
            account=create_trading_account(),
            market=create_btc_usd_market(),
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.IOC,
            amount_of_synthetic=Decimal("0.00100000"),
            price=Decimal("43445.11680000"),
            side=OrderSide.BUY,
            starknet_domain=TESTNET_CONFIG.signing.starknet_domain,
            rfq=CreateOrderRfqModel(start_price=Decimal("43000"), max_reprice_steps=3),
        )
