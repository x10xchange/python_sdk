from decimal import Decimal
from typing import Literal

from pydantic import AliasChoices, Field

from x10.utils.model import X10BaseModel

CandleType = Literal["trades", "mark-prices", "index-prices"]
CandleInterval = Literal["PT1M", "PT5M", "PT15M", "PT30M", "PT1H", "PT2H", "PT4H", "P1D"]


class CandleModel(X10BaseModel):
    open: Decimal = Field(validation_alias=AliasChoices("open", "o"), serialization_alias="o")
    low: Decimal = Field(validation_alias=AliasChoices("low", "l"), serialization_alias="o")
    high: Decimal = Field(validation_alias=AliasChoices("high", "h"), serialization_alias="o")
    close: Decimal = Field(validation_alias=AliasChoices("close", "c"), serialization_alias="o")
    volume: Decimal = Field(validation_alias=AliasChoices("volume", "v"), serialization_alias="o")
    timestamp: int = Field(validation_alias=AliasChoices("timestamp", "T"), serialization_alias="o")
