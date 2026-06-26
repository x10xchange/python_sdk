import asyncio
import json
from typing import Any, Callable, Coroutine, TypeAlias, TypeVar

import websockets
from errors import StreamRpcConnectionError, StreamRpcError, StreamRpcTimeoutError

from x10.clients.streamrpc.subscription import (
    StreamMessageHandler,
    SubscribeParams,
    TopicId,
    TopicSubscription,
)
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10
CONNECTION_LOOP_TASK_NAME = "x10-rpc-connection-loop"

T = TypeVar("T")
RequestId: TypeAlias = str
OnReconnectCallback = Callable[[list[str]], Coroutine[Any, Any, None]]
OnSequenceBreakCallback = Callable[[str, int, int], Coroutine[Any, Any, None]]


class StreamRpcClient:
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
        """
        Starts the client's connection management loop and waits for the first connection to be established.
        :raises StreamRpcConnectionError: If the initial connection fails (reconnect is not attempted).
        """

        if self._connection_loop_task is not None:
            LOGGER.debug("Connection loop already running")
            return

        LOGGER.debug("Connecting to %s", self._api_url)

        loop = asyncio.get_running_loop()

        self._is_stopped = False
        self._connection_loop_task = loop.create_task(self._run_connection_loop(), name=CONNECTION_LOOP_TASK_NAME)

        try:
            await asyncio.wait_for(self._ready.wait(), timeout=self._request_timeout)
        except asyncio.TimeoutError as exc:
            self._is_stopped = True

            if self._connection_loop_task:
                self._connection_loop_task.cancel()

            raise StreamRpcConnectionError(
                f"Connection to {self._api_url} timed out after {self._request_timeout}s"
            ) from exc

    async def close(self):
        raise NotImplementedError

    async def ping(self):
        raise NotImplementedError

    async def list_subscriptions(self):
        raise NotImplementedError

    async def subscribe(self, *, params: SubscribeParams[T], handler: StreamMessageHandler):
        """
        Subscribe to a topic and register a handler for incoming messages.

        If a subscription with the same topic_id already exists it is replaced
        (the server cancels the previous one automatically).

        :param params: Subscription parameters.
        :param handler: Callable invoked for each message. May be sync or async.
        :returns: The ``topic_id`` string.
        """

        await self._ready.wait()

        result = await self._rpc("subscribe", params=params.to_dict())
        topic_id: TopicId = result["subscription"]
        self._subscriptions[topic_id] = TopicSubscription(params=params, handler=handler)

        LOGGER.debug("Subscribed to %s", topic_id)

        return topic_id

    async def unsubscribe(self, topic_id: TopicId):
        """
        Cancel an active subscription.

        :param topic_id: The string returned by :meth:`subscribe`.
        :raises StreamRpcError: If no subscription with this ``topic_id`` exists.
        """

        subscription = self._subscriptions.get(topic_id)

        if subscription is None:
            raise StreamRpcError(f"No active subscription: {topic_id}")

        await self._ready.wait()
        await self._rpc("unsubscribe", params=subscription.params.to_dict())
        self._subscriptions.pop(topic_id, None)

        LOGGER.debug("Unsubscribed from %s", topic_id)

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
        self._request_timeout = DEFAULT_REQUEST_TIMEOUT_SECONDS
        # FIXME: Replace with state?
        self._is_stopped = False
        self._next_request_id = 0
        # FIXME: Update description
        # Last observed connection-level sequence number; None until the first
        # message arrives on a connection (also reset to None on each reconnect).
        self._last_seq: int | None = None

        # FIXME: Update description
        # Fires when a connection is fully established (and resubscription done).
        self._ready = asyncio.Event()

        # FIXME: Rename?
        self._connection_loop_task: asyncio.Task[None] | None = None

        # FIXME: Update description
        # Pending RPC request futures keyed by request id.
        self._pending_requests: dict[RequestId, asyncio.Future[dict[str, Any]]] = {}

        # FIXME: Update description
        # Active subscriptions keyed by topic_id.
        self._subscriptions: dict[TopicId, TopicSubscription] = {}

    async def __aenter__(self) -> "StreamRpcClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    def _get_next_request_id(self) -> RequestId:
        self._next_request_id += 1
        return RequestId(self._next_request_id)

    async def _rpc(self, method: str, **kwargs: Any) -> dict[str, Any]:
        """
        Send an RPC request and wait for its response.
        """

        if self._ws is None:
            raise StreamRpcConnectionError("WebSocket connection is not open")

        request_id = self._get_next_request_id()
        request: dict[str, Any] = {"method": method, "id": request_id, "jsonrpc": "2.0"}

        if kwargs:
            request.update(kwargs)

        loop = asyncio.get_running_loop()
        request_result: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_requests[request_id] = request_result

        try:
            await self._ws.send(json.dumps(request))
            # Shield the future so that cancelling the outer `wait_for` does not
            # cancel the future itself (it is cleaned up in the `finally` block).
            return await asyncio.wait_for(asyncio.shield(request_result), timeout=self._request_timeout)
        except asyncio.TimeoutError as exc:
            raise StreamRpcTimeoutError(
                f"RPC request timed out: {method} (id={request_id}) after {self._request_timeout}s"
            ) from exc
        finally:
            self._pending_requests.pop(request_id, None)

    async def _run_connection_loop(self):
        pass
