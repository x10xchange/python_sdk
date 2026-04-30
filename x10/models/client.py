from x10.models.account import AccountModel
from x10.models.base import X10BaseModel


class ClientModel(X10BaseModel):
    id: int
    evm_wallet_address: str | None = None
    starknet_wallet_address: str | None = None
    referral_link_code: str | None = None


class OnboardedClientModel(X10BaseModel):
    l1_address: str
    default_account: AccountModel
