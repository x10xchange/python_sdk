"""
Base sync API class for Extended Exchange SDK.

Provides common functionality for sync API classes using native sync implementation.
REPLACES the problematic run_sync() wrapper approach.
"""

from typing import Any, TypeVar

from x10.perpetual.configuration import EndpointConfig

from extended.api.base_native_sync import BaseNativeSyncClient
from extended.auth import ExtendedAuth

T = TypeVar("T")


class BaseSyncAPI(BaseNativeSyncClient):
    """
    Base class for sync API implementations.

    Uses native sync HTTP operations instead of wrapping async operations.
    MIRRORS Pacifica's BaseAPIClient approach exactly.
    """

    def __init__(self, auth: ExtendedAuth, config: EndpointConfig):
        """
        Initialize the base API.

        Args:
            auth: ExtendedAuth instance with credentials
            config: Endpoint configuration
        """
        # Use native sync client directly
        super().__init__(auth, config)

    def close(self):
        """Close the API and release resources."""
        # No async cleanup needed for native sync implementation
        pass