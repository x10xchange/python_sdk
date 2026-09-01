from decimal import Decimal
from typing import List, Optional

from pydantic import AliasChoices, Field

from x10.models.base import X10BaseModel
from x10.models.http import StreamDataType


class OrderbookQuantityModel(X10BaseModel):
    qty: Decimal = Field(validation_alias=AliasChoices("qty", "q"), serialization_alias="q")
    price: Decimal = Field(validation_alias=AliasChoices("price", "p"), serialization_alias="p")


class OrderbookUpdateModel(X10BaseModel):
    market: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    type: Optional[StreamDataType] = Field(
        default=None, validation_alias=AliasChoices("type", "t"), serialization_alias="t"
    )
    bid: List[OrderbookQuantityModel] = Field(validation_alias=AliasChoices("bid", "b"), serialization_alias="b")
    ask: List[OrderbookQuantityModel] = Field(validation_alias=AliasChoices("ask", "a"), serialization_alias="a")
