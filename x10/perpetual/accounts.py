from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from pydantic import AliasChoices, Field

from x10.perpetual.balances import BalanceModel
from x10.perpetual.fees import TradingFeeModel
from x10.perpetual.orders import OpenOrderModel
from x10.perpetual.positions import PositionModel
from x10.perpetual.trades import AccountTradeModel
from x10.utils.model import X10BaseModel
from x10.utils.starkex import sign
from x10.utils.string import is_hex_string


class StarkPerpetualAccount:
    __vault: int
    __private_key: int
    __public_key: int
    __trading_fee: Dict[str, TradingFeeModel]

    def __init__(self, vault: int | str, private_key: str, public_key: str, api_key: str):
        assert is_hex_string(private_key)
        assert is_hex_string(public_key)

        if isinstance(vault, str):
            vault = int(vault)
        elif isinstance(vault, int):
            self.__vault = vault
        else:
            raise ValueError("Invalid vault type")

        self.__vault = vault
        self.__private_key = int(private_key, base=16)
        self.__public_key = int(public_key, base=16)
        self.__api_key = api_key
        self.__trading_fee = {}

    @property
    def vault(self):
        return self.__vault

    @property
    def public_key(self):
        return self.__public_key

    @property
    def api_key(self):
        return self.__api_key

    @property
    def trading_fee(self):
        return self.__trading_fee

    def sign(self, msg_hash: int) -> Tuple[int, int]:
        return sign(private_key=self.__private_key, msg_hash=msg_hash)


class AccountStreamDataModel(X10BaseModel):
    orders: Optional[List[OpenOrderModel]] = None
    positions: Optional[List[PositionModel]] = None
    trades: Optional[List[AccountTradeModel]] = None
    balance: Optional[BalanceModel] = None


class AccountLeverage(X10BaseModel):
    market: str
    leverage: Decimal


class AccountModel(X10BaseModel):
    id: int = Field(validation_alias=AliasChoices("accountId", "id"), serialization_alias="id")
    description: str
    account_index: int
    status: str
    l2_key: str
    l2_vault: int
    api_keys: Optional[List[str]] = None


class ApiKeyResponseModel(X10BaseModel):
    key: str


class ApiKeyRequestModel(X10BaseModel):
    description: str
