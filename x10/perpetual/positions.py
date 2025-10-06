from decimal import Decimal
from typing import Optional

from strenum import StrEnum

from x10.utils.model import X10BaseModel


class ExitType(StrEnum):
    TRADE = "TRADE"
    LIQUIDATION = "LIQUIDATION"
    ADL = "ADL"


class PositionSide(StrEnum):
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
    exit_type: Optional[ExitType] = None
    exit_price: Optional[Decimal] = None
    realised_pnl: Decimal
    created_time: int
    closed_time: Optional[int] = None
