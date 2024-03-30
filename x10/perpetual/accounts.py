from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from x10.perpetual.balances import BalanceModel
from x10.perpetual.fees import TradingFeeModel
from x10.perpetual.orders import OpenOrderModel
from x10.perpetual.positions import PositionModel
from x10.utils.model import X10BaseModel
from x10.utils.starkex import sign
from x10.utils.string import is_hex_string


class StarkPerpetualAccount:
    __vault: int
    __private_key: int
    __public_key: int
    __trading_fee: Dict[str, TradingFeeModel]

    def __init__(self, *, vault: int, private_key: str, public_key: str):
        assert vault > 10000
        assert is_hex_string(private_key)
        assert is_hex_string(public_key)

        self.__vault = vault
        self.__private_key = int(private_key, base=16)
        self.__public_key = int(public_key, base=16)
        self.__trading_fee = {}

    @property
    def vault(self):
        return self.__vault

    @property
    def public_key(self):
        return self.__public_key

    @property
    def trading_fee(self):
        return self.__trading_fee

    def sign(self, msg_hash: int) -> Tuple[int, int]:
        return sign(private_key=self.__private_key, msg_hash=msg_hash)


class AccountStreamDataModel(X10BaseModel):
    orders: Optional[List[OpenOrderModel]] = None
    positions: Optional[List[PositionModel]] = None
    balance: Optional[BalanceModel] = None


class AccountLeverage(X10BaseModel):
    market: str
    leverage: Decimal
