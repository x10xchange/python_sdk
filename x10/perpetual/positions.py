from decimal import Decimal
from enum import Enum
from typing import Optional

from x10.utils.model import X10BaseModel


class ExitType(Enum):
    TRADE = "TRADE"
    LIQUIDATION = "LIQUIDATION"
    ADL = "ADL"


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class PositionModel(X10BaseModel):
    id: int
    account_id: int
    market: str
    side: PositionSide
    leverage: Decimal
    size: Decimal
    value: Decimal
    open_price: Decimal
    mark_price: Decimal
    liquidation_price: Optional[Decimal] = None
    unrealised_pnl: Decimal
    realised_pnl: Decimal
    tp_price: Optional[Decimal] = None
    sl_price: Optional[Decimal] = None
    adl: Optional[int] = None
    created_at: int
    updated_at: int


class PositionHistoryModel(X10BaseModel):
    id: int
    account_id: int
    market: str
    side: PositionSide
    leverage: Decimal
    size: Decimal
    open_price: Decimal
    exit_type: Optional[ExitType]
    exit_price: Optional[Decimal]
    realised_pnl: Decimal
    created_time: int
    closed_time: Optional[int]
