from decimal import Decimal
from typing import Optional

from pydantic import AliasChoices, Field
from strenum import StrEnum

from x10.models.base import X10BaseModel
from x10.models.order import OrderSide


class TradeType(StrEnum):
    TRADE = "TRADE"
    LIQUIDATION = "LIQUIDATION"
    DELEVERAGE = "DELEVERAGE"


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


class BuilderTradeModel(X10BaseModel):
    """
    A trade as seen by a builder. Only the side (maker/taker) that belongs to the
    requesting builder is populated; the counterparty side is masked with `None`.
    """

    id: int
    time: int
    volume: Decimal
    maker_id: Optional[int] = None
    taker_id: Optional[int] = None
    maker_builder_id: Optional[int] = None
    taker_builder_id: Optional[int] = None
    maker_fee: Optional[Decimal] = None
    taker_fee: Optional[Decimal] = None
    maker_builder_fee: Optional[Decimal] = None
    taker_builder_fee: Optional[Decimal] = None
