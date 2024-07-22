from decimal import Decimal

from x10.utils.model import X10BaseModel


class TradingFeeModel(X10BaseModel):
    market: str
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal


DEFAULT_FEES = TradingFeeModel(
    market="BTC-USD",
    maker_fee_rate=(Decimal("2") / Decimal("10000")),
    taker_fee_rate=(Decimal("5") / Decimal("10000")),
)
