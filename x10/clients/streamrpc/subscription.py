from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Generic, TypeAlias, TypeVar

from pydantic import AliasChoices, Field

from x10.errors import ValidationError
from x10.models.account import AccountStreamDataModel
from x10.models.base import X10BaseModel
from x10.models.orderbook import OrderbookUpdateModel
from x10.models.stream_rpc import StreamMessageEnvelope
from x10.models.trade import PublicTradeModel

T = TypeVar("T")
TopicId: TypeAlias = str
StreamMessageHandler = Callable[[StreamMessageEnvelope[Any]], Coroutine[Any, Any, None] | None]


class SubscribeParams(ABC, Generic[T]):
    """
    Base class for all subscription parameter types.
    """

    @property
    @abstractmethod
    def topic_id(self) -> TopicId:
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
    def topic_id(self) -> TopicId:
        return f"trades.{self.market or 'all'}"

    def to_dict(self) -> dict[str, Any]:
        return {"scope": "trades", "selector": {"market": self.market}}

    def deserialize_data(self, data: list[dict[str, Any]], msg_type: str) -> list[PublicTradeModel]:
        return [PublicTradeModel.model_validate(item) for item in data]


@dataclass
class TopicSubscription:
    params: SubscribeParams[Any]
    handler: StreamMessageHandler


# FIXME
class OrderbookUpdateModel2(OrderbookUpdateModel):
    type: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    depth: str = Field(validation_alias=AliasChoices("depth", "d"), serialization_alias="d")


class OrderBookParams(SubscribeParams[OrderbookUpdateModel]):
    """
    Subscribe to order book snapshots and delta updates.

    :param market: Market symbol or ``None`` for all markets.
    :param depth:  ``"full"`` (default) for the full order book, or ``"1"`` for best bid/ask only.
    :param rfq_only: If ``True``, only include RFQ (request-for-quote) levels. Only valid when ``depth="full"``.
    """

    def __init__(self, market: str | None = None, depth: str = "full", rfq_only: bool = False) -> None:
        if depth not in ("full", "1"):
            raise ValidationError(f"depth must be 'full' or '1', got {depth!r}")

        if rfq_only and depth != "full":
            raise ValueError("rfq_only is only valid when depth='full'")

        self.market = market
        self.depth = depth
        self.rfq_only = rfq_only

    @property
    def topic_id(self) -> str:
        if self.depth == "1":
            return f"orderbooks.1.{self.market or 'all'}"

        return f"orderbooks.{self.market or 'all'}{'.rfq' if self.rfq_only else ''}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": "orderbooks",
            "selector": {
                "market": self.market,
                "depth": self.depth,
                "rfqOnly": self.rfq_only,
            },
        }

    def deserialize_data(self, data: dict[str, Any], msg_type: str | None) -> OrderbookUpdateModel2:
        return OrderbookUpdateModel2.model_validate(data)


# FIXME
class AccountStreamDataModel2(X10BaseModel):
    pass


class AccountParams(SubscribeParams[AccountStreamDataModel2]):
    """
    Subscribe to the private account stream.
    """

    def __init__(
        self,
        *,
        account: str,
        # FIXME: BE auth is broken
        api_key: str,
    ) -> None:
        self.account = account
        self.api_key = api_key

    @property
    def topic_id(self) -> str:
        return f"account.{self.account}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": "account",
            "selector": {"account": self.account},
            "apiKey": self.api_key,
        }

    def deserialize_data(self, data: dict[str, Any], msg_type: str | None) -> AccountStreamDataModel2:
        # return [PublicTradeModel.model_validate(item) for item in data]
        match msg_type:
            # case "ACCOUNT.ORDER":
            #     return Order.from_dict(data)
            # case "ACCOUNT.POSITION":
            #     return Position.from_dict(data)
            # case "ACCOUNT.BALANCE":
            #     return Balance.from_dict(data)
            # case "ACCOUNT.WITHDRAWAL":
            #     return Withdrawal.from_dict(data)
            # case "ACCOUNT.DEPOSIT":
            #     return DepositUpdate.from_dict(data)
            # case "ACCOUNT.TRADE":
            #     return Trade.from_dict(data)
            # case "ACCOUNT.SPOT_BALANCE":
            #     return SpotBalance.from_dict(data)
            case _:
                raise ValueError(f"Unknown account stream message type: {msg_type!r}")
