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


class PositionStatus(StrEnum):
    OPENED = "OPENED"
    CLOSED = "CLOSED"


class PositionModel(X10BaseModel):
    id: int
    account_id: int
    market: str
    status: PositionStatus
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


class RealisedPnlBreakdownModel(X10BaseModel):
    trade_pnl: Decimal
    funding_fees: Decimal
    open_fees: Decimal
    close_fees: Decimal


class PositionHistoryModel(X10BaseModel):
    id: int
    account_id: int
    market: str
    side: PositionSide
    size: Decimal
    max_position_size: Decimal
    leverage: Decimal
    open_price: Decimal
    exit_price: Optional[Decimal] = None
    realised_pnl: Decimal
    realised_pnl_breakdown: RealisedPnlBreakdownModel
    created_time: int
    exit_type: Optional[ExitType] = None
    closed_time: Optional[int] = None
