from decimal import Decimal
from enum import Enum
from typing import Optional

from x10.utils.model import HexValue, X10BaseModel


class TimeInForce(Enum):
    GTT = "GTT"
    IOC = "IOC"
    FOK = "FOK"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    LIMIT = "LIMIT"
    CONDITIONAL = "CONDITIONAL"
    TPSL = "TPSL"
    MARKET = "MARKET"


class OrderStatus(Enum):
    UNKNOWN = "UNKNOWN"
    NEW = "NEW"
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class SignatureModel(X10BaseModel):
    r: HexValue
    s: HexValue


class StarkSettlementModel(X10BaseModel):
    signature: SignatureModel
    stark_key: HexValue
    collateral_position: Decimal


class StarkDebuggingOrderAmountsModel(X10BaseModel):
    collateral_amount: Decimal
    fee_amount: Decimal
    synthetic_amount: Decimal


class PerpetualOrderModel(X10BaseModel):
    id: str
    market: str
    type: OrderType
    side: OrderSide
    qty: Decimal
    price: Decimal
    reduce_only: bool
    post_only: bool
    time_in_force: TimeInForce
    fee: Decimal
    expiry_epoch_millis: int
    nonce: Decimal
    take_profit_signature: Optional[str] = None
    stop_loss_signature: Optional[str] = None
    cancel_id: Optional[int] = None
    trigger_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None
    take_profit_limit_price: Optional[Decimal] = None
    stop_loss_price: Optional[Decimal] = None
    stop_loss_limit_price: Optional[Decimal] = None
    settlement: Optional[StarkSettlementModel] = None
    debugging_amounts: Optional[StarkDebuggingOrderAmountsModel] = None


class PlacedOrderModel(X10BaseModel):
    id: int
    external_id: str


class OpenOrderModel(X10BaseModel):
    id: int
    account_id: int
    external_id: str
    market: str
    type: OrderType
    side: OrderSide
    status: OrderStatus
    price: Decimal
    average_price: Optional[Decimal] = None
    qty: Decimal
    filled_qty: Optional[Decimal] = None
    reduce_only: bool
    post_only: bool
    created_time: int
    expiry_time: Optional[int] = None
