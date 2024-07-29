from typing import List


def get_btc_usd_market_json_data():
    return """
    {
        "status": "OK",
        "data": [
            {
                "name": "BTC-USD",
                "category": "L1",
                "assetName": "BTC",
                "assetPrecision": 5,
                "collateralAssetName": "USD",
                "collateralAssetPrecision": 6,
                "active": true,
                "marketStats": {
                    "dailyVolume": "2410800.768021",
                    "dailyVolumeBase": "37.94502",
                    "dailyPriceChange": "969.9",
                    "dailyPriceChangePercentage": "0.02",
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
                    "deleverageLevels": {
                        "shortPositions": [
                            {
                                "level": 1,
                                "rankingLowerBound": "-5919.3176"
                            },
                            {
                                "level": 2,
                                "rankingLowerBound": "-1.8517"
                            }
                        ],
                        "longPositions": [
                            {
                                "level": 1,
                                "rankingLowerBound": "0.0000"
                            },
                            {
                                "level": 2,
                                "rankingLowerBound": "0.0000"
                            }
                        ]
                    }
                },
                "tradingConfig": {
                    "minOrderSize": "0.0001",
                    "minOrderSizeChange": "0.00001",
                    "minPriceChange": "0.1",
                    "maxMarketOrderValue": "1000000",
                    "maxLimitOrderValue": "5000000",
                    "maxPositionValue": "10000000",
                    "maxLeverage": "50.00",
                    "maxNumOrders": "200",
                    "limitPriceCap": "0.05",
                    "limitPriceFloor": "0.05",
                    "riskFactorConfig": [
                        {
                            "upperBound": "400000",
                            "riskFactor": "0.02"
                        },
                        {
                            "upperBound": "800000",
                            "riskFactor": "0.04"
                        },
                        {
                            "upperBound": "1200000",
                            "riskFactor": "0.06"
                        },
                        {
                            "upperBound": "1600000",
                            "riskFactor": "0.08"
                        },
                        {
                            "upperBound": "2000000",
                            "riskFactor": "0.1"
                        },
                        {
                            "upperBound": "2400000",
                            "riskFactor": "0.12"
                        },
                        {
                            "upperBound": "2800000",
                            "riskFactor": "0.14"
                        },
                        {
                            "upperBound": "3200000",
                            "riskFactor": "0.16"
                        },
                        {
                            "upperBound": "3600000",
                            "riskFactor": "0.18"
                        },
                        {
                            "upperBound": "4000000",
                            "riskFactor": "0.2"
                        },
                        {
                            "upperBound": "4400000",
                            "riskFactor": "0.22"
                        },
                        {
                            "upperBound": "4800000",
                            "riskFactor": "0.24"
                        },
                        {
                            "upperBound": "5200000",
                            "riskFactor": "0.26"
                        },
                        {
                            "upperBound": "5600000",
                            "riskFactor": "0.28"
                        },
                        {
                            "upperBound": "6000000",
                            "riskFactor": "0.3"
                        },
                        {
                            "upperBound": "6400000",
                            "riskFactor": "0.32"
                        },
                        {
                            "upperBound": "6800000",
                            "riskFactor": "0.34"
                        },
                        {
                            "upperBound": "7200000",
                            "riskFactor": "0.36"
                        },
                        {
                            "upperBound": "7600000",
                            "riskFactor": "0.38"
                        },
                        {
                            "upperBound": "8000000",
                            "riskFactor": "0.4"
                        },
                        {
                            "upperBound": "8400000",
                            "riskFactor": "0.42"
                        },
                        {
                            "upperBound": "8800000",
                            "riskFactor": "0.44"
                        },
                        {
                            "upperBound": "9200000",
                            "riskFactor": "0.46"
                        },
                        {
                            "upperBound": "9600000",
                            "riskFactor": "0.48"
                        },
                        {
                            "upperBound": "10000000",
                            "riskFactor": "0.5"
                        },
                        {
                            "upperBound": "1000000000",
                            "riskFactor": "1"
                        }
                    ]
                },
                "l2Config": {
                    "type": "STARKX",
                    "collateralId": "0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
                    "syntheticId": "0x4254432d3600000000000000000000",
                    "syntheticResolution": 1000000,
                    "collateralResolution": 1000000
                }
            }
        ]
    }
    """


def create_btc_usd_market(json_data: str):
    from x10.perpetual.markets import MarketModel
    from x10.utils.http import WrappedApiResponse

    result = WrappedApiResponse[List[MarketModel]].model_validate_json(json_data)

    assert result.data

    return result.data[0]
