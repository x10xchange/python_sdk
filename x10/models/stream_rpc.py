from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import AliasChoices, Field

from x10.models.balance import BalanceModel, SpotBalanceModel
from x10.models.base import X10BaseModel
from x10.models.deposit import DepositStatusUpdateModel
from x10.models.order import OpenOrderModel
from x10.models.orderbook import OrderbookUpdateModel
from x10.models.position import PositionModel
from x10.models.trade import AccountTradeModel
from x10.models.withdrawal import WithdrawalStatusUpdateModel

T = TypeVar("T")


class StreamRpcResponseModel(X10BaseModel, Generic[T]):
    type: str
    data: T
    error: str | None = None
    ts: int
    seq: int
    subscription: str


class StreamRpcOrderbookUpdateModel(OrderbookUpdateModel):
    depth: str = Field(validation_alias=AliasChoices("depth", "d"), serialization_alias="d")


class StreamRpcPriceModel(X10BaseModel):
    market: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    price: Decimal = Field(validation_alias=AliasChoices("price", "p"), serialization_alias="p")
    ts: int


class StreamRpcAccountPositionsModel(X10BaseModel):
    is_snapshot: bool
    positions: list[PositionModel]


class StreamRpcAccountOrdersModel(X10BaseModel):
    is_snapshot: bool
    orders: list[OpenOrderModel]


class StreamRpcAccountTradesModel(X10BaseModel):
    is_snapshot: bool
    trades: list[AccountTradeModel]


class StreamRpcAccountBalanceModel(X10BaseModel):
    is_snapshot: bool
    balance: BalanceModel


class StreamRpcAccountSpotBalancesModel(X10BaseModel):
    is_snapshot: bool
    spotBalances: list[SpotBalanceModel]


class StreamRpcAccountDepositUpdateModel(X10BaseModel):
    is_snapshot: bool
    deposit: DepositStatusUpdateModel


class StreamRpcAccountWithdrawalUpdateModel(X10BaseModel):
    is_snapshot: bool
    withdrawal: WithdrawalStatusUpdateModel
