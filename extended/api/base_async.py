"""
Base async API class for Extended Exchange SDK.

Provides common functionality for async API classes.
"""

from typing import Any, Awaitable, Callable, List, TypeVar

from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.trading_client import PerpetualTradingClient

from extended.auth import ExtendedAuth
from extended.utils.async_helpers import thread_safe_gather

T = TypeVar("T")


class BaseAsyncAPI:
    """
    Base class for async API implementations.

    Provides access to the Extended trading client and common utilities.
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
        self._client: PerpetualTradingClient = auth.get_trading_client()

    @property
    def trading_client(self) -> PerpetualTradingClient:
        """Get the underlying trading client."""
        return self._client

    async def execute_parallel(
        self,
        tasks: List[Callable[[], Awaitable[T]]],
    ) -> List[T]:
        """
        Execute multiple async tasks in parallel.

        Uses thread-safe gather to prevent "Future attached to
        different loop" errors in ThreadPoolExecutor contexts.

        Args:
            tasks: List of async callables

        Returns:
            List of results from all tasks
        """
        coroutines = [task() for task in tasks]
        return await thread_safe_gather(*coroutines)

    async def close(self):
        """Close the API and release resources."""
        await self._auth.close()
