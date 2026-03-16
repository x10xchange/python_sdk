"""
API modules for Extended Exchange SDK.
"""

# Only import sync APIs - async imports removed to eliminate dependencies
from extended.api.info import InfoAPI
from extended.api.exchange import ExchangeAPI

__all__ = [
    "InfoAPI",
    "ExchangeAPI",
]
