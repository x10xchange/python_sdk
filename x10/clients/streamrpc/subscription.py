from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Generic, TypeVar

from x10.models.stream_rpc import StreamMessageEnvelope
from x10.models.trade import PublicTradeModel

T = TypeVar("T")
StreamMessageHandler = Callable[[StreamMessageEnvelope[Any]], Coroutine[Any, Any, None] | None]


class SubscribeParams(ABC, Generic[T]):
    """
    Base class for all subscription parameter types.
    """

    @property
    @abstractmethod
    def topic_id(self) -> str:
        """
        The unique topic identifier (e.g. ``trades.BTC-USD``).
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to the JSON structure expected by the RPC ``subscribe`` call.
        """

    @abstractmethod
    def deserialize_data(self, data: Any, msg_type: str) -> T:
        """
        Convert a raw JSON payload into the typed domain model ``T``.

        :param data: The raw dict from the ``data`` field of the envelope.
        :param msg_type: The ``type`` field of the envelope, used by multi-type subscriptions
                         (e.g. ``account``) to select the correct model.
        """


class TradesParams(SubscribeParams[list[PublicTradeModel]]):
    """
    Subscribe to public trade events for a market (or all markets).
    """

    def __init__(self, market: str | None = None) -> None:
        self.market = market

    @property
    def topic_id(self) -> str:
        return f"trades.{self.market or 'all'}"

    def to_dict(self) -> dict[str, Any]:
        return {"scope": "trades", "selector": {"market": self.market}}

    def deserialize_data(self, data: list[dict[str, Any]], msg_type: str) -> list[PublicTradeModel]:
        return [PublicTradeModel.model_validate(item) for item in data]


@dataclass
class TopicSubscription:
    params: SubscribeParams[Any]
    handler: StreamMessageHandler
