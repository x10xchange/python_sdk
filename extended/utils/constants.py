"""
Constants for Extended Exchange SDK.

Provides mappings between Hyperliquid and Extended formats.
"""

from x10.perpetual.orders import TimeInForce as X10TimeInForce

# Time in force mapping (Hyperliquid -> Extended)
TIF_MAPPING = {
    "Gtc": X10TimeInForce.GTT,
    "Ioc": X10TimeInForce.IOC,
    "Alo": X10TimeInForce.GTT,  # ALO uses GTT with post_only=True
}

# Side mapping (is_buy -> Extended OrderSide)
SIDE_MAPPING = {
    True: "BUY",
    False: "SELL",
}

# Side to Hyperliquid format
SIDE_TO_HL = {
    "BUY": "B",
    "SELL": "A",
    "LONG": "B",
    "SHORT": "A",
}

# Candle interval mapping (Hyperliquid -> Extended)
INTERVAL_MAPPING = {
    "1m": "PT1M",
    "5m": "PT5M",
    "15m": "PT15M",
    "30m": "PT30M",
    "1h": "PT1H",
    "2h": "PT2H",
    "4h": "PT4H",
    "1d": "P1D",
}

# Reverse interval mapping (Extended -> Hyperliquid)
INTERVAL_MAPPING_REVERSE = {v: k for k, v in INTERVAL_MAPPING.items()}

# Interval in milliseconds for close timestamp calculation
INTERVAL_MS = {
    "1m": 60000,
    "5m": 300000,
    "15m": 900000,
    "30m": 1800000,
    "1h": 3600000,
    "2h": 7200000,
    "4h": 14400000,
    "1d": 86400000,
}

# Candle type options (Extended API path parameter)
CANDLE_TYPES = ["trades", "mark-prices", "index-prices"]
DEFAULT_CANDLE_TYPE = "trades"

# Default order expiry (1 hour in milliseconds)
DEFAULT_ORDER_EXPIRY_MS = 3600000

# Default slippage for market orders
DEFAULT_SLIPPAGE = 0.05  # 5%

# Price cap/floor for market orders (Extended constraint)
MARKET_ORDER_PRICE_CAP = 1.05  # Buy: mark * 1.05
MARKET_ORDER_PRICE_FLOOR = 0.95  # Sell: mark * 0.95
