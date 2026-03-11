from dataclasses import dataclass
from decimal import Decimal

from x10.perpetual.orders import SettlementSignatureModel
from x10.utils.model import HexValue, X10BaseModel
from datetime import datetime, timezone
from eth_account.messages import SignableMessage, encode_typed_data



class StarkTransferSettlement(X10BaseModel):
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
    settlement: StarkTransferSettlement


class OnChainPerpetualTransferModel(X10BaseModel):
    from_vault: int
    to_vault: int
    amount: Decimal
    settlement: StarkTransferSettlement
    transferred_asset: str
    signature: str


class TransferResponseModel(X10BaseModel):
    valid_signature: bool
    id: int | None = None
    hash_calculated: str | None = None
    stark_ex_representation: dict | None = None

@dataclass
class Transfer:
    source_account: int
    target_account: int
    asset_id: str
    amount: Decimal
    expiration: datetime

    def __post_init__(self):
        self.expiration_string = self.expiration.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_signable_message(self, signing_domain) -> SignableMessage:
        asset = int(self.asset_id, 16)
        domain = {"name": signing_domain}

        message = {
            "sourceAccount": self.source_account,
            "targetAccount": self.target_account,
            "assetId": asset,
            "amount": str(self.amount),
            "expiration": self.expiration_string,
        }
        types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"}
            ],
            "Transfer": [
                {"name": "sourceAccount", "type": "int64"},
                {"name": "targetAccount", "type": "int64"},
                {"name": "assetId", "type": "int64"},
                {"name": "amount", "type": "string"},
                {"name": "expiration", "type": "string"}
            ]
        }
        primary_type = "Transfer"
        structured_data = {
            "types": types,
            "domain": domain,
            "primaryType": primary_type,
            "message": message,
        }
        return encode_typed_data(full_message=structured_data)