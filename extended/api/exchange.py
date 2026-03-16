"""
Sync Exchange API for Extended Exchange SDK.

Provides trading operations matching Hyperliquid's Exchange class interface.
Uses native sync implementation instead of async wrapper.
"""

from typing import Any, Dict, List, Optional

from extended.api.base_native_sync import BaseNativeSyncClient
from extended.api.exchange_native_sync import NativeSyncExchangeAPI
from extended.auth_sync import SimpleSyncAuth
from extended.config_sync import SimpleSyncConfig


class ExchangeAPI(NativeSyncExchangeAPI):
    """
    Extended Exchange trading API with Hyperliquid-compatible interface.

    Native synchronous implementation - pure sync.

    Handles order placement, cancellation, and account management.

    Example:
        exchange = ExchangeAPI(auth, config)
        result = exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)
        exchange.cancel("BTC", oid=12345)
    """

    def __init__(self, auth: SimpleSyncAuth, config: SimpleSyncConfig):
        """
        Initialize the sync Exchange API.

        Args:
            auth: SimpleSyncAuth instance with credentials
            config: SimpleSyncConfig configuration
        """
        # Use native sync implementation directly
        super().__init__(auth, config)

    def close(self):
        """Close the API and release resources."""
        # No async cleanup needed for native sync implementation
        pass