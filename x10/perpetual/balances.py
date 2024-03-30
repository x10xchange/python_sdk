from decimal import Decimal

from x10.utils.model import X10BaseModel


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
