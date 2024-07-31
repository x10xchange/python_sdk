from decimal import Decimal

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
    account_id: int
    amount: Decimal
    asset: str
    settlement: StarkWithdrawalSettlement
