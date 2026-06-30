from decimal import Decimal

from strenum import StrEnum

from x10.models.base import HexValue, SettlementSignatureModel, X10BaseModel


class WithdrawalStatus(StrEnum):
    CREATED = "CREATED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_CLAIM = "READY_FOR_CLAIM"
    COMPLETED = "COMPLETED"


class TimestampModel(X10BaseModel):
    seconds: int


class StarkWithdrawalSettlementModel(X10BaseModel):
    recipient: HexValue
    position_id: int
    collateral_id: HexValue
    amount: int
    expiration: TimestampModel
    salt: int
    signature: SettlementSignatureModel


class WithdrawalRequestModel(X10BaseModel):
    account_id: int
    amount: Decimal
    description: str | None
    settlement: StarkWithdrawalSettlementModel
    chain_id: str
    quote_id: str | None = None
    asset: str


class WithdrawalStatusUpdateModel(X10BaseModel):
    id: int
    asset_id: int
    amount: Decimal
    status: WithdrawalStatus
    reason: str | None = None
