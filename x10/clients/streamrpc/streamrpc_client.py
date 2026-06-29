import asyncio
import json
import random
from typing import Any, Callable, Coroutine, TypeAlias, TypeVar

import websockets
from websockets import ConnectionClosed

from x10.clients.streamrpc.subscription import (
    StreamMessageHandler,
    SubscribeParams,
    TopicId,
    TopicSubscription,
)
from x10.errors import (
    StreamRpcConnectionError,
    StreamRpcError,
    StreamRpcServerError,
    StreamRpcTimeoutError,
)
from x10.models.stream_rpc import StreamMessageEnvelope
from x10.utils.http import USER_AGENT, RequestHeader
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)
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
        """
        Stops the client and close the WebSocket connection.
        """

        self._is_stopped = True
        self._ready.clear()
        self._fail_pending(StreamRpcConnectionError("Client disconnected"))

        if self._ws is not None:
            await self._ws.close()
            self._ws = None

        if self._connection_loop_task is not None:
            self._connection_loop_task.cancel()

            try:
                await self._connection_loop_task
            except (asyncio.CancelledError, Exception):
                pass

            self._connection_loop_task = None

    async def ping(self):
        """
        Sends a ping and wait for the server's acknowledgement.
        """

        await self._rpc("ping")

    async def list_subscriptions(self):
        """
        Return the list of active subscription IDs as reported by the server.
        """

        result = await self._rpc("list-subscriptions")
        # FIXME: Simplify?
        return result.get("subscriptions") or []

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
        self._request_timeout = 10
        self._reconnect_initial_delay = 1
        self._reconnect_max_delay = 10
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

    def _fail_pending(self, exc: Exception) -> None:
        """
        Resolve all pending RPC futures with an exception.
        """

        for request_result in list(self._pending_requests.values()):
            if not request_result.done():
                request_result.set_exception(exc)

        self._pending_requests.clear()

    # FIXME: Create a class for connection loop?
    async def _run_connection_loop(self):
        """
        Background task that maintains the connection (including reconnections)
        and dispatches incoming messages.
        """

        reconnect_delay = self._reconnect_initial_delay
        is_first_connection_attempt = True

        extra_headers: dict[str, str] = {
            RequestHeader.USER_AGENT: USER_AGENT,
        }

        if self._api_key is not None:
            extra_headers[RequestHeader.API_KEY] = self._api_key

        async def handle_lost_connection(exc: Exception) -> bool:
            nonlocal reconnect_delay

            self._ws = None
            self._ready.clear()
            self._fail_pending(StreamRpcConnectionError(f"Connection lost: {exc}"))

            LOGGER.warning("Connection lost: %s", exc)

            if self._is_stopped:
                return False

            jitter = random.uniform(0.0, 1.0)
            reconnect_after = min(reconnect_delay + jitter, self._reconnect_max_delay)

            LOGGER.debug("Reconnecting in %.1fs…", reconnect_after)

            await asyncio.sleep(reconnect_after)
            reconnect_delay = min(reconnect_delay * 1.5, self._reconnect_max_delay)

            return True

        while not self._is_stopped:
            try:
                async with websockets.connect(self._api_url, extra_headers=extra_headers) as ws:
                    self._ws = ws

                    LOGGER.debug("Connected to %s", self._api_url)

                    # `seq` restarts at 0 on each new connection
                    self._last_seq = None
                    reconnect_delay = self._reconnect_initial_delay

                    await self._resubscribe()
                    self._ready.set()

                    if not is_first_connection_attempt and self._on_reconnect:
                        await self._on_reconnect(list(self._subscriptions))

                    is_first_connection_attempt = False

                    async for raw in ws:
                        if isinstance(raw, str):
                            self._dispatch_raw(raw)
            except asyncio.CancelledError:
                break
            except (ConnectionClosed, OSError, asyncio.TimeoutError) as exc:
                should_break = not await handle_lost_connection(exc)

                if should_break:
                    break
            except Exception as exc:
                LOGGER.exception("Unexpected error in connection loop: %s", exc)

                self._ws = None
                self._ready.clear()
                self._fail_pending(StreamRpcConnectionError(str(exc)))

                if self._is_stopped:
                    break

                await asyncio.sleep(self._reconnect_initial_delay)

        self._ws = None
        self._ready.clear()
        self._fail_pending(StreamRpcConnectionError("Client stopped"))

        LOGGER.debug("Connection loop exited")

    async def _resubscribe(self) -> None:
        """
        Replay all active subscriptions after a reconnection.
        """

        if self._ws is None or not self._subscriptions:
            return

        LOGGER.debug("Resubscribing to %d topic(s)…", len(self._subscriptions))

        for topic_id, subscription in list(self._subscriptions.items()):
            request_id = self._get_next_request_id()
            request = {
                "method": "subscribe",
                "id": request_id,
                "jsonrpc": "2.0",
                "params": subscription.params.to_dict(),
            }
            try:
                await self._ws.send(json.dumps(request))
            except Exception:
                LOGGER.exception("Failed to resubscribe to %s", topic_id)

    # FIXME: Create a dispatcher class?
    def _dispatch_raw(self, raw: str) -> None:
        """
        Parse a raw WebSocket text frame and route it to the right handler.
        """

        try:
            msg: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            LOGGER.warning("Received invalid JSON (%.120s…)", raw)
            return

        # (1) JSON-RPC response
        request_id: RequestId | None = msg.get("id")

        if request_id is not None:
            # FIXME: Create a class instance?
            request_result = self._pending_requests.get(str(request_id))

            if not request_result:
                LOGGER.warning("Received response for unknown request id=%s", request_id)
                return

            err = msg.get("error")

            if err:
                request_result.set_exception(
                    StreamRpcServerError(code=err["code"], message=err["message"], data=err.get("data"))
                )
            else:
                request_result.set_result(msg["result"])

            return

        # (2) Stream data
        # FIXME: Create a class instance?
        subscription_id: str | None = msg.get("subscription")

        if subscription_id is not None:
            asyncio.ensure_future(self._dispatch_message(msg, subscription_id))
            return

        # (3) Unknown message
        LOGGER.error("Unrecognised message shape: %s", raw)

    async def _dispatch_message(self, msg: dict[str, Any], subscription_id: str) -> None:
        """
        Deserialize a stream message and invoke the registered handler.
        """

        subscription = self._subscriptions.get(subscription_id)

        if subscription is None:
            LOGGER.warning("Received message for unknown subscription id=%s", subscription_id)
            return

        msg_seq = msg["seq"]

        if self._last_seq is not None and msg_seq != self._last_seq + 1:
            LOGGER.warning(
                "Sequence break detected for subscription %s: last_seq=%s, msg_seq=%s",
                subscription_id,
                self._last_seq,
                msg_seq,
            )

            if self._on_sequence_break:
                try:
                    result = await self._on_sequence_break(subscription_id, self._last_seq, msg_seq)

                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    LOGGER.exception("Unhandled exception in `on_sequence_break` callback")

        self._last_seq = msg_seq

        msg_data = msg["data"]
        msg_type = msg["type"]

        try:
            deserialized_data = subscription.params.deserialize_data(msg_data, msg_type)
        except Exception as exc:
            LOGGER.exception(
                "Failed to deserialize message for subscription %s (type=%s, seq=%s): %s",
                subscription_id,
                msg_type,
                msg_seq,
                exc,
            )
            return

        enveloped_data = StreamMessageEnvelope(
            type=msg_type,
            data=deserialized_data,
            ts=msg["ts"],
            seq=msg_seq,
            subscription=subscription_id,
        )

        try:
            result = subscription.handler(enveloped_data)

            if asyncio.iscoroutine(result):
                await result
        except Exception:
            LOGGER.exception("Unhandled exception in handler for subscription %s", subscription_id)
