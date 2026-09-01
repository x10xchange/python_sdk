from decimal import Decimal
from typing import List, Optional

from strenum import StrEnum

from x10.models.base import HexValue, SettlementSignatureModel, X10BaseModel


class TimeInForce(StrEnum):
    GTT = "GTT"
    IOC = "IOC"
    FOK = "FOK"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderSortBy(StrEnum):
    ID = "ID"
    UPDATED_AT = "UPDATED_AT"


class OrderType(StrEnum):
    LIMIT = "LIMIT"
    CONDITIONAL = "CONDITIONAL"
    MARKET = "MARKET"
    TPSL = "TPSL"
    TWAP = "TWAP"


class OrderTpslType(StrEnum):
    ORDER = "ORDER"
    POSITION = "POSITION"


class OrderStatus(StrEnum):
    # Technical status
    UNKNOWN = "UNKNOWN"

    NEW = "NEW"
    UNTRIGGERED = "UNTRIGGERED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class OrderStatusReason(StrEnum):
    # Technical status
    UNKNOWN = "UNKNOWN"

    NONE = "NONE"
    UNKNOWN_MARKET = "UNKNOWN_MARKET"
    DISABLED_MARKET = "DISABLED_MARKET"
    NOT_ENOUGH_FUNDS = "NOT_ENOUGH_FUNDS"
    NO_LIQUIDITY = "NO_LIQUIDITY"
    INVALID_FEE = "INVALID_FEE"
    INVALID_QTY = "INVALID_QTY"
    INVALID_PRICE = "INVALID_PRICE"
    INVALID_VALUE = "INVALID_VALUE"
    UNKNOWN_ACCOUNT = "UNKNOWN_ACCOUNT"
    SELF_TRADE_PROTECTION = "SELF_TRADE_PROTECTION"
    POST_ONLY_FAILED = "POST_ONLY_FAILED"
    REDUCE_ONLY_FAILED = "REDUCE_ONLY_FAILED"
    INVALID_EXPIRE_TIME = "INVALID_EXPIRE_TIME"
    POSITION_TPSL_CONFLICT = "POSITION_TPSL_CONFLICT"
    INVALID_LEVERAGE = "INVALID_LEVERAGE"
    PREV_ORDER_NOT_FOUND = "PREV_ORDER_NOT_FOUND"
    PREV_ORDER_TRIGGERED = "PREV_ORDER_TRIGGERED"
    TPSL_OTHER_SIDE_FILLED = "TPSL_OTHER_SIDE_FILLED"
    PREV_ORDER_CONFLICT = "PREV_ORDER_CONFLICT"
    ORDER_REPLACED = "ORDER_REPLACED"
    POST_ONLY_MODE = "POST_ONLY_MODE"
    REDUCE_ONLY_MODE = "REDUCE_ONLY_MODE"
    TRADING_OFF_MODE = "TRADING_OFF_MODE"


class OrderTriggerPriceType(StrEnum):
    # Technical status
    UNKNOWN = "UNKNOWN"

    MARK = "MARK"
    INDEX = "INDEX"
    LAST = "LAST"


class OrderTriggerDirection(StrEnum):
    # Technical status
    UNKNOWN = "UNKNOWN"

    UP = "UP"
    DOWN = "DOWN"


class OrderPriceType(StrEnum):
    # Technical status
    UNKNOWN = "UNKNOWN"

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class SelfTradeProtectionLevel(StrEnum):
    DISABLED = "DISABLED"
    ACCOUNT = "ACCOUNT"
    CLIENT = "CLIENT"


class StarkSettlementModel(X10BaseModel):
    signature: SettlementSignatureModel
    stark_key: HexValue
    collateral_position: Decimal


class LimitOrderSettlementModel(X10BaseModel):
    base_amount: int
    quote_amount: int
    fee_amount: int
    base_asset_id: HexValue
    quote_asset_id: HexValue
    fee_asset_id: HexValue
    expiration_timestamp: int
    nonce: int
    receiver_position_id: int
    sender_position_id: int
    signature: SettlementSignatureModel


class StarkDebuggingOrderAmountsModel(X10BaseModel):
    collateral_amount: Decimal
    fee_amount: Decimal
    synthetic_amount: Decimal


class CreateOrderConditionalTriggerModel(X10BaseModel):
    trigger_price: Decimal
    trigger_price_type: OrderTriggerPriceType
    direction: OrderTriggerDirection
    execution_price_type: OrderPriceType


class CreateOrderTpslTriggerModel(X10BaseModel):
    trigger_price: Decimal
    trigger_price_type: OrderTriggerPriceType
    price: Decimal
    price_type: OrderPriceType
    settlement: StarkSettlementModel
    debugging_amounts: Optional[StarkDebuggingOrderAmountsModel] = None


class CreateOrderRfqModel(X10BaseModel):
    start_price: Optional[Decimal] = None
    max_reprice_steps: Optional[int] = None


class NewOrderModel(X10BaseModel):
    id: str
    market: str
    type: OrderType
    side: OrderSide
    qty: Decimal
    price: Decimal
    reduce_only: bool = False
    post_only: bool = False
    time_in_force: TimeInForce
    expiry_epoch_millis: int
    fee: Decimal
    nonce: Decimal
    self_trade_protection_level: SelfTradeProtectionLevel
    cancel_id: Optional[str] = None
    settlement: Optional[StarkSettlementModel] = None
    trigger: Optional[CreateOrderConditionalTriggerModel] = None
    tp_sl_type: Optional[OrderTpslType] = None
    take_profit: Optional[CreateOrderTpslTriggerModel] = None
    stop_loss: Optional[CreateOrderTpslTriggerModel] = None
    debugging_amounts: Optional[StarkDebuggingOrderAmountsModel] = None
    builder_fee: Optional[Decimal] = None
    builder_id: Optional[int] = None
    rfq: Optional[CreateOrderRfqModel] = None


class PlacedOrderModel(X10BaseModel):
    id: int
    external_id: str


class OpenOrderTpslTriggerModel(X10BaseModel):
    trigger_price: Decimal
    trigger_price_type: OrderTriggerPriceType
    price: Decimal
    price_type: OrderPriceType
    status: Optional[OrderStatus] = None


class OpenOrderModel(X10BaseModel):
    """
    Attributes:
        price: Price of the order. If it's a TP/SL order, it will be null.
    """

    id: int
    account_id: int
    external_id: str
    market: str
    type: OrderType
    side: OrderSide
    status: OrderStatus
    status_reason: Optional[OrderStatusReason] = None
    price: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    qty: Decimal
    filled_qty: Optional[Decimal] = None
    cancelled_qty: Optional[Decimal] = None
    reduce_only: bool
    post_only: bool
    payed_fee: Optional[Decimal] = None
    created_time: int
    updated_time: int
    expiry_time: Optional[int] = None
    time_in_force: TimeInForce
    tp_sl_type: Optional[OrderTpslType] = None
    take_profit: Optional[OpenOrderTpslTriggerModel] = None
    stop_loss: Optional[OpenOrderTpslTriggerModel] = None


class MassCancelRequestModel(X10BaseModel):
    order_ids: Optional[List[int]] = None
    external_order_ids: Optional[List[str]] = None
    markets: Optional[List[str]] = None
    cancel_all: Optional[bool] = None
