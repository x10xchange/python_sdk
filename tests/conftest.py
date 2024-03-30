from decimal import Decimal
from typing import List

import pytest


@pytest.fixture
def create_trading_account():
    def _create_trading_account():
        from x10.perpetual.accounts import StarkPerpetualAccount

        return StarkPerpetualAccount(
            vault=10002,
            private_key="0x7a7ff6fd3cab02ccdcd4a572563f5976f8976899b03a39773795a3c486d4986",
            public_key="0x61c5e7e8339b7d56f197f54ea91b776776690e3232313de0f2ecbd0ef76f466",
        )

    return _create_trading_account


@pytest.fixture
def valid_btc_usd_market_json():
    return """
{
  "status": "OK",
  "data": [
    {
      "name": "BTC-USD",
      "assetName": "BTC",
      "assetPrecision": 8,
      "collateralAssetName": "USD",
      "collateralAssetPrecision": 2,
      "active": true,
      "marketStats": {
        "dailyVolume": "39659164065",
        "dailyVolumeBase": "39659164065",
        "dailyPriceChange": "5.57",
        "dailyLow": "39512",
        "dailyHigh": "42122",
        "lastPrice": "42000",
        "askPrice": "42005",
        "bidPrice": "39998",
        "markPrice": "39950",
        "indexPrice": "39940",
        "fundingRate": "0.001",
        "nextFundingRate": 1701563440,
        "openInterest": "1245.2",
        "openInterestBase": "1245.2"
      },
      "tradingConfig": {
        "minOrderSize": "0.001",
        "minOrderSizeChange": "0.001",
        "minPriceChange": "0.001",
        "maxMarketOrderSize": "70",
        "maxLimitOrderSize": "100",
        "maxPositionSize": "220",
        "maxLeverage": "50",
        "baseRiskLimit": "120000",
        "riskStep": "60000",
        "initialMarginFraction": "0.1",
        "incrementalInitialMarginFraction": "0.01",
        "maxNumOrders": 200,
        "limitPriceCap": "0.05",
        "limitPriceFloor": "0.05"
      },
      "l2Config": {
        "type": "STARKX",
        "collateralId": "0x35596841893e0d17079c27b2d72db1694f26a1932a7429144b439ba0807d29c",
        "collateralResolution": 1000000,
        "syntheticId": "0x4254432d3130000000000000000000",
        "syntheticResolution": 10000000000
      }
    }
  ]
}
"""


@pytest.fixture
def create_btc_usd_market(valid_btc_usd_market_json):
    def _create_btc_usd_market():
        from x10.perpetual.markets import MarketModel
        from x10.utils.http import WrappedApiResponse

        result = WrappedApiResponse[List[MarketModel]].model_validate_json(valid_btc_usd_market_json)

        return result.data[0]

    return _create_btc_usd_market


@pytest.fixture
def create_orderbook_message():
    def _create_orderbook_message():
        from x10.perpetual.orderbooks import (
            OrderbookQuantityModel,
            OrderbookUpdateModel,
        )
        from x10.utils.http import WrappedStreamResponse

        return WrappedStreamResponse[OrderbookUpdateModel](
            type="SNAPSHOT",
            data=OrderbookUpdateModel(
                market="BTC-USD",
                bid=[
                    OrderbookQuantityModel(qty=Decimal("0.008"), price=Decimal("43547.00")),
                    OrderbookQuantityModel(qty=Decimal("0.007000"), price=Decimal("43548.00")),
                ],
                ask=[OrderbookQuantityModel(qty=Decimal("0.008"), price=Decimal("43546.00"))],
            ),
            ts=1704798222748,
            seq=570,
        )

    return _create_orderbook_message
