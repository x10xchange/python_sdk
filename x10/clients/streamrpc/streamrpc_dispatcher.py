import asyncio
import json
from typing import Any, Callable, Coroutine, TypeAlias

from x10.clients.streamrpc.subscription_params import TopicId, TopicSubscription
from x10.errors import StreamRpcServerError
from x10.models.stream_rpc import StreamRpcResponseModel
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)

RequestId: TypeAlias = str
PendingRequestsMap: TypeAlias = dict[RequestId, asyncio.Future[dict[str, Any]]]
OnSequenceBreakCallback = Callable[[str, int, int], Coroutine[Any, Any, None]]


class StreamRpcDispatcher:
    def __init__(
        self,
        *,
        pending_requests: PendingRequestsMap,
        subscriptions: dict[TopicId, TopicSubscription],
        on_sequence_break: OnSequenceBreakCallback | None = None,
    ) -> None:
        # Last observed connection-level sequence (reset to `None` on each re-connect).
        self._last_seq: int | None = None
        self._pending_requests = pending_requests
        self._subscriptions = subscriptions
        self._on_sequence_break = on_sequence_break

    def reset_last_seq(self) -> None:
        self._last_seq = None

    def dispatch_raw(self, raw: str) -> None:
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

        enveloped_data = StreamRpcResponseModel(
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
