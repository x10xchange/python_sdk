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
        # Last observed connection-level sequence (reset to `None` on each reconnect).
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

            if request_result is None:
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

        try:
            msg_model: StreamRpcResponseModel[Any] = StreamRpcResponseModel.model_validate(msg)
        except Exception as exc:
            LOGGER.exception("Failed to validate message for subscription %s: %s", subscription_id, exc)
            return

        if self._last_seq is not None and msg_model.seq != self._last_seq + 1:
            LOGGER.warning(
                "Sequence break detected for subscription %s: last_seq=%s, msg_seq=%s",
                subscription_id,
                self._last_seq,
                msg_model.seq,
            )

            if self._on_sequence_break:
                try:
                    sequence_break_result = self._on_sequence_break(subscription_id, self._last_seq, msg_model.seq)

                    if asyncio.iscoroutine(sequence_break_result):
                        await sequence_break_result
                except Exception:
                    LOGGER.exception("Unhandled exception in `on_sequence_break` callback")

        self._last_seq = msg_model.seq

        try:
            deserialized_data = subscription.params.deserialize_data(msg_model.data, msg_model.type)
        except Exception as exc:
            LOGGER.exception(
                "Failed to deserialize message for subscription %s (type=%s, seq=%s): %s",
                subscription_id,
                msg_model.type,
                msg_model.seq,
                exc,
            )
            return

        msg_model_with_deserialized_data = msg_model.model_copy(update={"data": deserialized_data})

        try:
            subscription_handler_result = subscription.handler(msg_model_with_deserialized_data)

            if asyncio.iscoroutine(subscription_handler_result):
                await subscription_handler_result
        except Exception:
            LOGGER.exception("Unhandled exception in handler for subscription %s", subscription_id)
