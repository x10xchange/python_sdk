from decimal import ROUND_CEILING, Decimal
from functools import cached_property
from typing import List

from x10.perpetual.assets import Asset
from x10.utils.model import X10BaseModel


class RiskFactorConfig(X10BaseModel):
    upper_bound: Decimal
    risk_factor: Decimal

    @cached_property
    def max_leverage(self) -> Decimal:
        return round(Decimal(1) / self.risk_factor, 2)


class MarketStatsModel(X10BaseModel):
    daily_volume: Decimal
    daily_volume_base: Decimal
    daily_price_change: Decimal
    daily_low: Decimal
    daily_high: Decimal
    last_price: Decimal
    ask_price: Decimal
    bid_price: Decimal
    mark_price: Decimal
    index_price: Decimal
    funding_rate: Decimal
    next_funding_rate: int
    open_interest: Decimal
    open_interest_base: Decimal


class TradingConfigModel(X10BaseModel):
    min_order_size: Decimal
    min_order_size_change: Decimal
    min_price_change: Decimal
    max_market_order_value: Decimal
    max_limit_order_value: Decimal
    max_position_value: Decimal
    max_leverage: Decimal
    max_num_orders: int
    limit_price_cap: Decimal
    limit_price_floor: Decimal
    risk_factor_config: List[RiskFactorConfig]

    @cached_property
    def price_precision(self) -> int:
        return abs(int(self.min_price_change.log10().to_integral_exact(ROUND_CEILING)))

    @cached_property
    def quantity_precision(self) -> int:
        return abs(int(self.min_order_size_change.log10().to_integral_exact(ROUND_CEILING)))

    def max_leverage_for_position_value(self, position_value: Decimal) -> Decimal:
        filtered = [x for x in self.risk_factor_config if x.upper_bound >= position_value]
        return filtered[0].max_leverage if filtered else Decimal(0)

    def max_position_value_for_leverage(self, leverage: Decimal) -> Decimal:
        filtered = [x for x in self.risk_factor_config if x.max_leverage >= leverage]
        return filtered[-1].upper_bound if filtered else Decimal(0)


class L2ConfigModel(X10BaseModel):
    type: str
    collateral_id: str
    collateral_resolution: int
    synthetic_id: str
    synthetic_resolution: int


class MarketModel(X10BaseModel):
    name: str
    asset_name: str
    asset_precision: int
    collateral_asset_name: str
    collateral_asset_precision: int
    active: bool
    market_stats: MarketStatsModel
    trading_config: TradingConfigModel
    l2_config: L2ConfigModel

    @cached_property
    def synthetic_asset(self) -> Asset:
        return Asset(
            id=1,
            name=self.asset_name,
            precision=self.asset_precision,
            active=self.active,
            is_collateral=False,
            settlement_external_id=self.l2_config.synthetic_id,
            settlement_resolution=self.l2_config.synthetic_resolution,
            l1_external_id="",
            l1_resolution=0,
        )

    @cached_property
    def collateral_asset(self) -> Asset:
        return Asset(
            id=2,
            name=self.collateral_asset_name,
            precision=self.collateral_asset_precision,
            active=self.active,
            is_collateral=True,
            settlement_external_id=self.l2_config.collateral_id,
            settlement_resolution=self.l2_config.collateral_resolution,
            l1_external_id="",
            l1_resolution=0,
        )
