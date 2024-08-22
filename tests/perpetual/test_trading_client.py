import dataclasses
from typing import List

import pytest
from aiohttp import web
from hamcrest import assert_that, equal_to, has_length

from x10.perpetual.assets import AssetOperationModel
from x10.perpetual.configuration import TESTNET_CONFIG
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

    endpoint_config = dataclasses.replace(TESTNET_CONFIG, api_base_url=url)
    trading_client = PerpetualTradingClient(endpoint_config=endpoint_config)
    markets = await trading_client.markets_info.get_markets()

    assert_that(markets.status, equal_to("OK"))
    assert_that(markets.data, has_length(1))
    assert_that(
        markets.data[0].to_api_request_json(),
        equal_to(
            {
                "name": "BTC-USD",
                "assetName": "BTC",
                "assetPrecision": 5,
                "collateralAssetName": "USD",
                "collateralAssetPrecision": 6,
                "active": True,
                "marketStats": {
                    "dailyVolume": "2410800.768021",
                    "dailyVolumeBase": "37.94502",
                    "dailyPriceChange": "969.9",
                    "dailyLow": "62614.8",
                    "dailyHigh": "64421.1",
                    "lastPrice": "64280.0",
                    "askPrice": "64268.2",
                    "bidPrice": "64235.9",
                    "markPrice": "64267.380482593245",
                    "indexPrice": "64286.409493065992",
                    "fundingRate": "-0.000034",
                    "nextFundingRate": 1715072400000,
                    "openInterest": "150629.886375",
                    "openInterestBase": "2.34380",
                },
                "tradingConfig": {
                    "minOrderSize": "0.0001",
                    "minOrderSizeChange": "0.00001",
                    "minPriceChange": "0.1",
                    "maxMarketOrderValue": "1000000",
                    "maxLimitOrderValue": "5000000",
                    "maxPositionValue": "10000000",
                    "maxLeverage": "50.00",
                    "maxNumOrders": 200,
                    "limitPriceCap": "0.05",
                    "limitPriceFloor": "0.05",
                    "riskFactorConfig": [
                        {"upperBound": "400000", "riskFactor": "0.02"},
                        {"upperBound": "800000", "riskFactor": "0.04"},
                        {"upperBound": "1200000", "riskFactor": "0.06"},
                        {"upperBound": "1600000", "riskFactor": "0.08"},
                        {"upperBound": "2000000", "riskFactor": "0.1"},
                        {"upperBound": "2400000", "riskFactor": "0.12"},
                        {"upperBound": "2800000", "riskFactor": "0.14"},
                        {"upperBound": "3200000", "riskFactor": "0.16"},
                        {"upperBound": "3600000", "riskFactor": "0.18"},
                        {"upperBound": "4000000", "riskFactor": "0.2"},
                        {"upperBound": "4400000", "riskFactor": "0.22"},
                        {"upperBound": "4800000", "riskFactor": "0.24"},
                        {"upperBound": "5200000", "riskFactor": "0.26"},
                        {"upperBound": "5600000", "riskFactor": "0.28"},
                        {"upperBound": "6000000", "riskFactor": "0.3"},
                        {"upperBound": "6400000", "riskFactor": "0.32"},
                        {"upperBound": "6800000", "riskFactor": "0.34"},
                        {"upperBound": "7200000", "riskFactor": "0.36"},
                        {"upperBound": "7600000", "riskFactor": "0.38"},
                        {"upperBound": "8000000", "riskFactor": "0.4"},
                        {"upperBound": "8400000", "riskFactor": "0.42"},
                        {"upperBound": "8800000", "riskFactor": "0.44"},
                        {"upperBound": "9200000", "riskFactor": "0.46"},
                        {"upperBound": "9600000", "riskFactor": "0.48"},
                        {"upperBound": "10000000", "riskFactor": "0.5"},
                        {"upperBound": "1000000000", "riskFactor": "1"},
                    ],
                },
                "l2Config": {
                    "type": "STARKX",
                    "collateralId": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                    "collateralResolution": 1000000,
                    "syntheticId": "0x4254432d3600000000000000000000",
                    "syntheticResolution": 1000000,
                },
            }
        ),
    )


@pytest.mark.asyncio
async def test_get_asset_operations(aiohttp_server, create_asset_operations, create_trading_account):
    from x10.perpetual.trading_client import PerpetualTradingClient

    expected_operations = create_asset_operations()
    expected_response = WrappedApiResponse[List[AssetOperationModel]].model_validate(
        {"status": "OK", "data": [op.model_dump() for op in expected_operations]}
    )

    app = web.Application()
    app.router.add_get("/user/assetOperations", serve_data(expected_response.model_dump_json()))

    server = await aiohttp_server(app)
    url = f"http://{server.host}:{server.port}"

    stark_account = create_trading_account()
    endpoint_config = endpoint_config = dataclasses.replace(TESTNET_CONFIG, api_base_url=url)
    trading_client = PerpetualTradingClient(endpoint_config=endpoint_config, stark_account=stark_account)
    operations = await trading_client.account.asset_operations()

    assert_that(operations.status, equal_to("OK"))
    assert_that(operations.data, has_length(2))
    assert_that(
        [op.to_api_request_json() for op in operations.data],
        equal_to(
            [
                {
                    "id": "1816814506626514944",
                    "type": "TRANSFER",
                    "status": "COMPLETED",
                    "amount": "-100.0000000000000000",
                    "fee": "0",
                    "asset": 1,
                    "time": 1721997307818,
                    "accountId": 3004,
                    "counterpartyAccountId": 7349,
                    "transactionHash": None,
                },
                {
                    "id": "1813548171448147968",
                    "type": "CLAIM",
                    "status": "COMPLETED",
                    "amount": "100000.0000000000000000",
                    "fee": "0",
                    "asset": 1,
                    "time": 1721218552833,
                    "accountId": 3004,
                    "counterpartyAccountId": None,
                    "transactionHash": None,
                },
            ]
        ),
    )
