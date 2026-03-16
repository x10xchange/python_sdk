"""
Base sync API class for Extended Exchange SDK.

Provides common functionality for sync API classes using native sync implementation.
Uses native sync implementation instead of wrapper approach.
"""

from typing import Any, TypeVar

from extended.api.base_native_sync import BaseNativeSyncClient
from extended.auth_sync import SimpleSyncAuth
from extended.config_sync import SimpleSyncConfig

T = TypeVar("T")


class BaseSyncAPI(BaseNativeSyncClient):
    """
    Base class for sync API implementations.

    Uses native sync HTTP operations instead of wrapping async operations.
    MIRRORS Pacifica's BaseAPIClient approach exactly.
    """

    def __init__(self, auth: SimpleSyncAuth, config: SimpleSyncConfig):
        """
        Initialize the base API.

        Args:
            auth: SimpleSyncAuth instance with credentials
            config: SimpleSyncConfig configuration
        """
        # Use native sync client directly
        super().__init__(auth, config)

    def close(self):
        """Close the API and release resources."""
        # No async cleanup needed for native sync implementation
        pass