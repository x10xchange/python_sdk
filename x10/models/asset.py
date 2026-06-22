from decimal import Decimal
from typing import Optional

from strenum import StrEnum

from x10.core.amount import SettlementAsset
from x10.models.base import HexValue, X10BaseModel


class AssetType(StrEnum):
    SPOT = "SPOT"
    PERPETUAL = "PERPETUAL"


class RiskFactorSegmentModel(X10BaseModel):
    upper_bound: Decimal
    risk_factor: Decimal


class AssetModel(X10BaseModel):
    id: int
    name: str
    symbol: str
    precision: int
    is_active: bool
    is_collateral: bool
    starkex_id: HexValue
    starkex_resolution: int
    l1_id: str
    l1_resolution: int
    version: int
    type: AssetType
    can_be_used_as_collateral: bool

    def to_settlement_asset(self) -> SettlementAsset:
        return SettlementAsset(
            name=self.name,
            precision=self.precision,
            is_collateral=self.is_collateral,
            starkex_id=hex(self.starkex_id),
            starkex_resolution=self.starkex_resolution,
            l1_id=self.l1_id,
            l1_resolution=self.l1_resolution,
        )


class AssetOperationType(StrEnum):
    CLAIM = "CLAIM"
    DEPOSIT = "DEPOSIT"
    FAST_WITHDRAWAL = "FAST_WITHDRAWAL"
    SLOW_WITHDRAWAL = "SLOW_WITHDRAWAL"
    TRANSFER = "TRANSFER"


class AssetOperationStatus(StrEnum):
    # Technical status
    UNKNOWN = "UNKNOWN"

    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    REJECTED = "REJECTED"
    READY_FOR_CLAIM = "READY_FOR_CLAIM"
    COMPLETED = "COMPLETED"


class AssetOperationModel(X10BaseModel):
    id: str
    type: AssetOperationType
    status: AssetOperationStatus
    amount: Decimal
    fee: Decimal
    asset: int
    time: int
    account_id: int

    # When operation type is `TRANSFER`
    counterparty_account_id: Optional[int] = None
    transaction_hash: Optional[HexValue] = None
