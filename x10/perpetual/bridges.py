from x10.utils.model import X10BaseModel
from decimal import Decimal

class ChainConfig(X10BaseModel):
    chain: str
    contractAddress: str

class BridgesConfig(X10BaseModel):
    chains: list[ChainConfig]

class Quote(X10BaseModel):
    id: str
    fee: Decimal