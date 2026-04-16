import importlib.metadata
from decimal import Decimal

from x10.models.fee import TradingFeeModel

BTC_USD_MARKET = "BTC-USD"
SOL_USD_MARKET = "SOL-USD"
ADA_USD_MARKET = "ADA-USD"
ETH_USD_MARKET = "ETH-USD"

DEFAULT_MARKET_PRICE_SLIPPAGE = Decimal("0.0075")
DEFAULT_REQUEST_TIMEOUT_SECONDS = 500
SDK_VERSION = importlib.metadata.version("x10-python-trading-starknet")
USER_AGENT = f"X10PythonTradingClient/{SDK_VERSION}"

DEFAULT_FEES = TradingFeeModel(
    market="BTC-USD",
    maker_fee_rate=(Decimal("2") / Decimal("10000")),
    taker_fee_rate=(Decimal("5") / Decimal("10000")),
    builder_fee_rate=Decimal("0"),
)
