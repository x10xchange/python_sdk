from decimal import Decimal

from pydantic import AliasChoices, Field

from x10.utils.model import X10BaseModel


class FundingRateModel(X10BaseModel):
    market: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    funding_rate: Decimal = Field(validation_alias=AliasChoices("funding_rate", "f"), serialization_alias="f")
    timestamp: int = Field(validation_alias=AliasChoices("timestamp", "T"), serialization_alias="T")
