"""
Sync Info API for Extended Exchange SDK.

Provides read-only operations matching Hyperliquid's Info class interface.
Uses native sync implementation instead of async wrapper.
"""

from typing import Any, Dict, List, Optional

from extended.api.base_native_sync import BaseNativeSyncClient
from extended.api.info_native_sync import NativeSyncInfoAPI
from extended.auth_sync import SimpleSyncAuth
from extended.config_sync import SimpleSyncConfig


class InfoAPI(NativeSyncInfoAPI):
    """
    Extended Exchange Info API with Hyperliquid-compatible interface.

    Native synchronous implementation - pure sync.

    Note: Unlike Hyperliquid, Extended requires authentication for
    user-specific data. The `address` parameter is accepted for
    interface compatibility but ignored (uses authenticated user).

    Example:
        info = InfoAPI(auth, config)
        state = info.user_state()
        orders = info.open_orders()
    """

    def __init__(self, auth: SimpleSyncAuth, config: SimpleSyncConfig):
        """
        Initialize the sync Info API.

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