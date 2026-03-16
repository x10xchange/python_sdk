"""
Base sync API class for Extended Exchange SDK.

Provides common functionality for sync API classes by wrapping async operations.
"""

from typing import Any, TypeVar

from x10.perpetual.configuration import EndpointConfig

from extended.auth import ExtendedAuth
from extended.utils.helpers import run_sync

T = TypeVar("T")


class BaseSyncAPI:
    """
    Base class for sync API implementations.

    Wraps async API operations to provide a synchronous interface.
    """

    def __init__(self, auth: ExtendedAuth, config: EndpointConfig):
        """
        Initialize the base API.

        Args:
            auth: ExtendedAuth instance with credentials
            config: Endpoint configuration
        """
        self._auth = auth
        self._config = config

    def close(self):
        """Close the API and release resources."""
        run_sync(self._auth.close())
