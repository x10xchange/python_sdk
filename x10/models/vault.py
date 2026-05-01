from decimal import Decimal

from x10.models.base import X10BaseModel
from x10.models.order import LimitOrderSettlementModel


class DepositRequestModel(X10BaseModel):
    from_account_id: int
    to_account_id: int
    collateral: Decimal
    shares: Decimal
    settlement: LimitOrderSettlementModel


class WithdrawRequestModel(X10BaseModel):
    from_account_id: int
    to_account_id: int
    collateral: Decimal
    shares: Decimal
    settlement: LimitOrderSettlementModel
