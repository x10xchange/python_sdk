from decimal import Decimal
from typing import Optional

from x10.models.base import X10BaseModel


class BalanceModel(X10BaseModel):
    collateral_name: str
    balance: Decimal
    equity: Decimal
    available_for_trade: Decimal
    available_for_withdrawal: Decimal
    unrealised_pnl: Decimal
    initial_margin: Decimal
    margin_ratio: Decimal
    updated_time: int
    spot_equity: Decimal = Decimal(0)
    spot_equity_for_available_for_trade: Decimal = Decimal(0)
    collateral_reserved_for_spot_orders: Decimal = Decimal(0)


class SpotBalanceModel(X10BaseModel):
    account_id: int
    asset: str
    balance: Decimal
    index_price: Decimal
    notional_value: Decimal
    contribution_factor: Decimal
    equity_contribution: Decimal
    available_to_withdraw: Decimal
    updated_at: int
    absolute_pnl: Optional[Decimal] = None
    pnl_percentage: Optional[Decimal] = None
    average_entry_price: Optional[Decimal] = None
