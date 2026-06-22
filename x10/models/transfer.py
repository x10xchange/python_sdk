from decimal import Decimal

from x10.models.base import HexValue, SettlementSignatureModel, X10BaseModel


class StarkTransferSettlementModel(X10BaseModel):
    amount: int
    asset_id: HexValue
    expiration_timestamp: int
    nonce: int
    receiver_position_id: int
    receiver_public_key: HexValue
    sender_position_id: int
    sender_public_key: HexValue
    signature: SettlementSignatureModel


class PerpetualTransferModel(X10BaseModel):
    from_account: int
    to_account: int
    amount: Decimal
    transferred_asset: str
    settlement: StarkTransferSettlementModel


class OnChainPerpetualTransferModel(X10BaseModel):
    from_vault: int
    to_vault: int
    amount: Decimal
    transferred_asset: str
    settlement: StarkTransferSettlementModel


class TransferResponseModel(X10BaseModel):
    valid_signature: bool
    id: int | None = None
    hash_calculated: str | None = None
    stark_ex_representation: dict | None = None
