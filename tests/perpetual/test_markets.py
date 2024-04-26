# from decimal import Decimal
# from typing import List

# from hamcrest import assert_that, equal_to

# from x10.perpetual.markets import Asset, MarketModel, TradingConfigModel
# from x10.utils.http import WrappedApiResponse


# def test_computed_assets(valid_btc_usd_market_json):
#     result = WrappedApiResponse[List[MarketModel]].model_validate_json(valid_btc_usd_market_json)

#     markets = result.data
#     market = markets[0]

#     assert_that(market.name, equal_to("BTC-USD"))

#     assert_that(
#         market.collateral_asset,
#         equal_to(
#             Asset(
#                 id=2,
#                 name="USD",
#                 precision=2,
#                 active=True,
#                 is_collateral=True,
#                 settlement_external_id="0x35596841893e0d17079c27b2d72db1694f26a1932a7429144b439ba0807d29c",
#                 settlement_resolution=1000000,
#                 l1_external_id="",
#                 l1_resolution=0,
#             )
#         ),
#     )
#     assert_that(
#         market.synthetic_asset,
#         equal_to(
#             Asset(
#                 id=1,
#                 name="BTC",
#                 precision=8,
#                 active=True,
#                 is_collateral=False,
#                 settlement_external_id="0x4254432d3130000000000000000000",
#                 settlement_resolution=10000000000,
#                 l1_external_id="",
#                 l1_resolution=0,
#             )
#         ),
#     )


# def test_trading_config_properties(valid_btc_usd_market_json):
#     result = WrappedApiResponse[List[MarketModel]].model_validate_json(valid_btc_usd_market_json)

#     markets = result.data
#     market = markets[0]

#     trading_config = market.trading_config

#     assert_that(
#         trading_config,
#         equal_to(
#             TradingConfigModel(
#                 min_order_size=Decimal("0.001"),
#                 min_order_size_change=Decimal("0.001"),
#                 min_price_change=Decimal("0.001"),
#                 max_market_order_size=Decimal("70"),
#                 max_limit_order_size=Decimal("100"),
#                 max_position_size=Decimal("220"),
#                 max_leverage=Decimal("50"),
#                 base_risk_limit=Decimal("120000"),
#                 risk_step=Decimal("60000"),
#                 initial_margin_fraction=Decimal("0.1"),
#                 incremental_initial_margin_fraction=Decimal("0.01"),
#                 max_num_orders=200,
#                 limit_price_cap=Decimal("0.05"),
#                 limit_price_floor=Decimal("0.05"),
#             )
#         ),
#     )
