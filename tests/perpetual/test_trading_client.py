from typing import List

import pytest
from aiohttp import web
from hamcrest import assert_that, equal_to, has_length

from x10.perpetual.markets import MarketModel
from x10.utils.http import WrappedApiResponse


def serve_data(data):
    async def _serve_data(_request):
        return web.Response(text=data)

    return _serve_data


@pytest.mark.asyncio
async def test_get_markets(aiohttp_server, create_btc_usd_market):
    from x10.perpetual.trading_client import PerpetualTradingClient

    expected_market = create_btc_usd_market()
    expected_markets = WrappedApiResponse[List[MarketModel]].model_validate(
        {"status": "OK", "data": [expected_market.model_dump()]}
    )

    app = web.Application()
    app.router.add_get("/info/markets", serve_data(expected_markets.model_dump_json()))

    server = await aiohttp_server(app)
    url = f"http://{server.host}:{server.port}"

    trading_client = PerpetualTradingClient(api_url=url, api_key="api_key")
    markets = await trading_client.markets_info.get_markets()

    assert_that(markets.status, equal_to("OK"))
    assert_that(markets.data, has_length(1))
    assert_that(
        markets.data[0].to_api_request_json(),
        equal_to(
            {
                "name": expected_market.name,
                "assetName": "BTC",
                "assetPrecision": 8,
                "collateralAssetName": "USD",
                "collateralAssetPrecision": 2,
                "active": True,
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
                    "openInterestBase": "1245.2",
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
                    "limitPriceFloor": "0.05",
                },
                "l2Config": {
                    "type": "STARKX",
                    "collateralId": "0x35596841893e0d17079c27b2d72db1694f26a1932a7429144b439ba0807d29c",
                    "collateralResolution": 1000000,
                    "syntheticId": "0x4254432d3130000000000000000000",
                    "syntheticResolution": 10000000000,
                },
            }
        ),
    )
