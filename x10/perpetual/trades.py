from decimal import Decimal
from enum import Enum

from pydantic import AliasChoices, Field

from x10.perpetual.orders import OrderSide
from x10.utils.model import X10BaseModel


class TradeType(Enum):
    TRADE = "TRADE"
    LIQUIDATION = "LIQUIDATION"


class PublicTradeModel(X10BaseModel):
    id: int = Field(validation_alias=AliasChoices("id", "i"), serialization_alias="i")
    market: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    side: OrderSide = Field(validation_alias=AliasChoices("side", "S"), serialization_alias="S")
    trade_type: TradeType = Field(validation_alias=AliasChoices("trade_type", "tT"), serialization_alias="tT")
    timestamp: int = Field(validation_alias=AliasChoices("timestamp", "T"), serialization_alias="T")
    price: Decimal = Field(validation_alias=AliasChoices("price", "p"), serialization_alias="p")
    qty: Decimal = Field(validation_alias=AliasChoices("qty", "q"), serialization_alias="q")


class AccountTradeModel(X10BaseModel):
    id: int
    account_id: int
    market: str
    order_id: int
    side: OrderSide
    price: Decimal
    qty: Decimal
    value: Decimal
    fee: Decimal
    is_taker: bool
    trade_type: TradeType
    created_time: int
