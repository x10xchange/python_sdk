import asyncio
from typing import Any, Callable, Coroutine, TypeAlias, TypeVar

import websockets
from errors import StreamRpcError

from x10.clients.streamrpc.subscription import (
    StreamMessageHandler,
    SubscribeParams,
    TopicId,
    TopicSubscription,
)
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


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
        LOGGER.debug("Connecting to %s", self._api_url)

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
        self._run_task: asyncio.Task[None] | None = None

        # FIXME: Update description
        # Pending RPC request futures keyed by request id.
        self._pending: dict[RequestId, asyncio.Future[dict[str, Any]]] = {}

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

        raise NotImplementedError
