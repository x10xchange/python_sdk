from decimal import Decimal

from x10.utils.model import X10BaseModel


class TradingFeeModel(X10BaseModel):
    market: str
    maker_fee: Decimal
    taker_fee: Decimal


DEFAULT_FEES = TradingFeeModel(
    market="BTC-USD",
    maker_fee=(Decimal("2") / Decimal("10000")),
    taker_fee=(Decimal("5") / Decimal("10000")),
)
