from decimal import Decimal

from x10.utils.model import HexValue, SettlementSignatureModel, X10BaseModel


class Timestamp(X10BaseModel):
    seconds: int


class StarkWithdrawalSettlement(X10BaseModel):
    recipient: HexValue
    position_id: int
    collateral_id: HexValue
    amount: int
    expiration: Timestamp
    salt: int
    signature: SettlementSignatureModel


class WithdrawalRequest(X10BaseModel):
    account_id: int
    amount: Decimal
    description: str | None
    settlement: StarkWithdrawalSettlement
    chain_id: str
    quote_id: str | None = None
    asset: str
