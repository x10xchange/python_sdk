from decimal import Decimal

from strenum import StrEnum

from x10.models.base import X10BaseModel


class DepositStatus(StrEnum):
    CREATED = "CREATED"
    PROCESSED = "PROCESSED"
    REJECTED = "REJECTED"


class DepositStatusUpdateModel(X10BaseModel):
    asset_id: int
    amount: Decimal
    timestamp: int
    status: DepositStatus
