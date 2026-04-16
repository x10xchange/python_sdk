from decimal import Decimal

from x10.models.base import X10BaseModel


class TradingFeeModel(X10BaseModel):
    market: str
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    builder_fee_rate: Decimal
