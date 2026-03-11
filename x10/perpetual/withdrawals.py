from dataclasses import dataclass
from datetime import datetime, timezone
from eth_account.messages import SignableMessage, encode_typed_data

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
    target_wallet: str | None = None
    signature: str | None = None


@dataclass
class Withdrawal:
    account_id: int
    target_wallet: str
    asset_id: str
    amount: Decimal
    expiration: datetime

    def __post_init__(self):
        self.expiration_string = self.expiration.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_signable_message(self, signing_domain) -> SignableMessage:
        domain = {"name": signing_domain}
        asset = int(self.asset_id, 16)
        message = {
            "account": self.account_id,
            "targetWallet": self.target_wallet,
            "assetId": asset,
            "amount": str(self.amount),
            "expiration": self.expiration_string,
        }
        types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"}
            ],
            "Withdrawal": [
                {"name": "account", "type": "int64"},
                {"name": "targetWallet", "type": "string"},
                {"name": "assetId", "type": "int64"},
                {"name": "amount", "type": "string"},
                {"name": "expiration", "type": "string"}
            ]
        }
        primary_type = "Withdrawal"
        structured_data = {
            "types": types,
            "domain": domain,
            "primaryType": primary_type,
            "message": message,
        }
        return encode_typed_data(full_message=structured_data)

