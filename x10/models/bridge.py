from decimal import Decimal

from x10.models.base import X10BaseModel


class ChainConfigModel(X10BaseModel):
    chain: str
    contractAddress: str


class BridgesConfigModel(X10BaseModel):
    chains: list[ChainConfigModel]


class QuoteModel(X10BaseModel):
    id: str
    fee: Decimal
