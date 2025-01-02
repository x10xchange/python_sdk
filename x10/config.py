import importlib.metadata

TRADING_API_URL_DEV = "http://api.testnet.extended.exchange/api/v1"
STREAM_API_URL_DEV = "wss://api.testnet.extended.exchange/stream.extended.exchange/v1"

BTC_USD_MARKET = "BTC-USD"
SOL_USD_MARKET = "SOL-USD"
ADA_USD_MARKET = "ADA-USD"
ETH_USD_MARKET = "ETH-USD"

DEFAULT_REQUEST_TIMEOUT_SECONDS = 500
SDK_VERSION = importlib.metadata.version("x10-python-trading")
USER_AGENT = f"X10PythonTradingClient/{SDK_VERSION}"
