from decimal import Decimal
from typing import List

from pydantic import AliasChoices, Field

from x10.utils.model import X10BaseModel


class OrderbookQuantityModel(X10BaseModel):
    qty: Decimal = Field(validation_alias=AliasChoices("qty", "q"), serialization_alias="q")
    price: Decimal = Field(validation_alias=AliasChoices("price", "p"), serialization_alias="p")


class OrderbookUpdateModel(X10BaseModel):
    market: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    bid: List[OrderbookQuantityModel] = Field(validation_alias=AliasChoices("bid", "b"), serialization_alias="b")
    ask: List[OrderbookQuantityModel] = Field(validation_alias=AliasChoices("ask", "a"), serialization_alias="a")
