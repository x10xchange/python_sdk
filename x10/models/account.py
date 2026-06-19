from decimal import Decimal
from typing import List, Optional

from pydantic import AliasChoices, Field

from x10.models.balance import BalanceModel, SpotBalanceModel
from x10.models.base import X10BaseModel
from x10.models.order import OpenOrderModel
from x10.models.position import PositionModel
from x10.models.trade import AccountTradeModel


class AccountStreamDataModel(X10BaseModel):
    orders: Optional[List[OpenOrderModel]] = None
    positions: Optional[List[PositionModel]] = None
    trades: Optional[List[AccountTradeModel]] = None
    balance: Optional[BalanceModel] = None
    spot_balances: Optional[List[SpotBalanceModel]] = None


class AccountLeverageModel(X10BaseModel):
    market: str
    leverage: Decimal


class AccountModel(X10BaseModel):
    id: int = Field(validation_alias=AliasChoices("accountId", "id"), serialization_alias="id")
    description: str
    account_index: int
    status: str
    l2_key: str
    l2_vault: int
    bridge_starknet_address: Optional[str] = None


class ApiKeyRequestModel(X10BaseModel):
    description: str


class ApiKeyResponseModel(X10BaseModel):
    key: str
