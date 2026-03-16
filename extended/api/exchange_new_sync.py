"""
Sync Exchange API for Extended Exchange SDK.

Provides trading operations matching Hyperliquid's Exchange class interface.
Uses native sync implementation instead of async wrapper.
"""

from typing import Any, Dict, List, Optional

from x10.perpetual.configuration import EndpointConfig

from extended.api.base_native_sync import BaseNativeSyncClient
from extended.api.exchange_native_sync import NativeSyncExchangeAPI
from extended.auth import ExtendedAuth


class ExchangeAPI(NativeSyncExchangeAPI):
    """
    Extended Exchange trading API with Hyperliquid-compatible interface.

    Native synchronous implementation - NO async/await anywhere.

    Handles order placement, cancellation, and account management.

    Example:
        exchange = ExchangeAPI(auth, config)
        result = exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)
        exchange.cancel("BTC", oid=12345)
    """

    def __init__(self, auth: ExtendedAuth, config: EndpointConfig):
        """
        Initialize the sync Exchange API.

        Args:
            auth: ExtendedAuth instance with credentials
            config: Endpoint configuration
        """
        # Use native sync implementation directly
        super().__init__(auth, config)

    def close(self):
        """Close the API and release resources."""
        # No async cleanup needed for native sync implementation
        pass