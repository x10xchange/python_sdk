import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

import websockets

from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


OnReconnectCallback = Callable[[list[str]], Coroutine[Any, Any, None]]
OnSequenceBreakCallback = Callable[[str, int, int], Coroutine[Any, Any, None]]


class StreamRPCClient:
    """
    X10 WebSocket RPC client.

    Implements the JSON-RPC 2.0 like protocol over a WebSocket connection.
    Supports automatic reconnection and transparent re-subscription after connection loss.

    :param api_url: Full WebSocket URL.
    :param api_key: API key for private topics.
    :param on_reconnect: Optional async callback invoked after a successful reconnection.
    :param on_sequence_break: Optional callback invoked when a gap is detected in the
                              connection-level ``seq`` counter, indicating that one or more stream
                              messages were dropped.
    """

    async def connect(self):
        LOGGER.debug("Connecting to %s", self._api_url)
        pass

    async def close(self):
        pass

    async def ping(self):
        pass

    async def list_subscriptions(self):
        pass

    async def subscribe(self):
        pass

    async def unsubscribe(self):
        pass

    def __init__(
        self,
        *,
        api_url: str,
        api_key: str | None = None,
        on_reconnect: OnReconnectCallback | None = None,
        on_sequence_break: OnSequenceBreakCallback | None = None,
    ):
        self._api_url = api_url
        self._api_key = api_key
        self._on_reconnect = on_reconnect
        self._on_sequence_break = on_sequence_break

        self._ws: websockets.WebSocketClientProtocol | None = None
        # FIXME: Rename?
        self._run_task: asyncio.Task[None] | None = None
        # FIXME: Replace with state?
        self._is_stopped = False

        # Fires when a connection is fully established (and resubscription done).
        self._ready = asyncio.Event()

        # Pending RPC request futures keyed by request id.
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}

        # Active subscriptions keyed by topic_id.
        self._subscriptions: dict[str, _Subscription] = {}

    async def __aenter__(self) -> "StreamRPCClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()
