from x10.utils.model import X10BaseModel


class ClientModel(X10BaseModel):
    id: int
    evm_wallet_address: str | None = None
    starknet_wallet_address: str | None = None
    referral_link_code: str | None = None
