from decimal import Decimal
from typing import Literal

from x10.utils.model import HexValue, SettlementSignatureModel, X10BaseModel


class StarkWithdrawalSettlement(X10BaseModel):
    amount: int
    collateral_asset_id: HexValue
    eth_address: HexValue
    expiration_timestamp: int
    nonce: int
    position_id: int
    public_key: HexValue
    signature: SettlementSignatureModel


class PerpetualWithdrawalModel(X10BaseModel):
    type: Literal["SLOW_SELF"]
    account_id: int
    amount: Decimal
    asset: str
    settlement: StarkWithdrawalSettlement


class PerpetualSlowWithdrawal(X10BaseModel):
    amount: Decimal
    settlement: StarkWithdrawalSettlement
    description: str | None
