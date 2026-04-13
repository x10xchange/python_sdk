import importlib.metadata
from decimal import Decimal

BTC_USD_MARKET = "BTC-USD"
SOL_USD_MARKET = "SOL-USD"
ADA_USD_MARKET = "ADA-USD"
ETH_USD_MARKET = "ETH-USD"

DEFAULT_MARKET_PRICE_SLIPPAGE = Decimal("0.0075")
DEFAULT_REQUEST_TIMEOUT_SECONDS = 500
SDK_VERSION = importlib.metadata.version("x10-python-trading-starknet")
USER_AGENT = f"X10PythonTradingClient/{SDK_VERSION}"
