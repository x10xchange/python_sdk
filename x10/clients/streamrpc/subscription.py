from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Coroutine, Generic, Optional, TypeAlias, TypeVar

from pydantic import AliasChoices, Field

from x10.errors import ValidationError
from x10.models.balance import BalanceModel, SpotBalanceModel
from x10.models.base import X10BaseModel
from x10.models.candle import CandleModel
from x10.models.deposit import DepositStatusUpdateModel
from x10.models.funding_rate import FundingRateModel
from x10.models.order import OpenOrderModel
from x10.models.orderbook import OrderbookUpdateModel
from x10.models.position import PositionModel
from x10.models.stream_rpc import StreamMessageEnvelope
from x10.models.trade import AccountTradeModel, PublicTradeModel
from x10.models.withdrawal import WithdrawalStatusUpdateModel

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


# FIXME: Rename
class OrderbookUpdateModel2(OrderbookUpdateModel):
    type: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    depth: str = Field(validation_alias=AliasChoices("depth", "d"), serialization_alias="d")


class OrderbooksParams(SubscribeParams[OrderbookUpdateModel]):
    """
    Subscribe to order book snapshots and delta updates.

    :param market: Market symbol or ``None`` for all markets.
    :param depth:  ``"full"`` (default) for the full order book, or ``"1"`` for best bid/ask only.
    :param rfq_only: If ``True``, only include RFQ (request-for-quote) levels. Only valid when ``depth="full"``.
    """

    def __init__(self, market: str | None = None, depth: str = "full", rfq_only: bool = False) -> None:
        if depth not in ("full", "1"):
            raise ValidationError(f"`depth` must be `full` or `1`, got {depth!r}")

        if rfq_only and depth != "full":
            raise ValidationError("`rfq_only` is only valid when depth is `full`")

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


class FundingRatesParams(SubscribeParams[FundingRateModel]):
    """
    Subscribe to funding rate updates for a market (or all markets).

    :param market: Market symbol or ``None`` for all markets.
    """

    def __init__(self, market: str | None = None) -> None:
        self.market = market

    @property
    def topic_id(self) -> str:
        return f"funding-rates.{self.market or 'all'}"

    def to_dict(self) -> dict[str, Any]:
        return {"scope": "funding-rates", "selector": {"market": self.market}}

    # FIXME: Remove `None` from `msg_type`
    def deserialize_data(self, data: dict[str, Any], msg_type: str | None) -> FundingRateModel:
        return FundingRateModel.model_validate(data)


class PriceModel(X10BaseModel):
    market: str = Field(validation_alias=AliasChoices("market", "m"), serialization_alias="m")
    price: Decimal = Field(validation_alias=AliasChoices("price", "p"), serialization_alias="p")
    ts: int


class PricesParams(SubscribeParams[PriceModel]):
    """
    Subscribe to mark / index price updates for a market (or all markets)

    :param price_type: ``"mark"`` or ``"index"``.
    :param market: Market symbol or ``None`` for all markets.
    """

    def __init__(self, price_type: str, market: str | None = None) -> None:
        if price_type not in ("mark", "index"):
            raise ValidationError(f"`price_type` must be `mark` or `index`, got {price_type!r}")

        self.price_type = price_type
        self.market = market

    @property
    def topic_id(self) -> str:
        return f"prices.{self.price_type}.{self.market or 'all'}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": "prices",
            "selector": {"type": self.price_type, "market": self.market},
        }

    def deserialize_data(self, data: dict[str, Any], msg_type: str | None) -> PriceModel:
        return PriceModel.model_validate(data)


class CandlesParams(SubscribeParams[list[CandleModel]]):
    """
    Subscribe to candles OHLC (`mark` or `index`) / OHLCV (`last`) for a market and interval.

    :param candle_type: ``"mark"``, ``"index"``, or ``"last"``.
    :param market: Market symbol.
    :param interval: ISO-8601 duration.
    """

    def __init__(self, candle_type: str, market: str, interval: str) -> None:
        if candle_type not in ("mark", "index", "last"):
            raise ValidationError(f"`candle_type` must be `mark`, `index`, or `last`, got {candle_type!r}")

        self.candle_type = candle_type
        self.market = market
        self.interval = interval

    @property
    def topic_id(self) -> str:
        return f"candles.{self.candle_type}.{self.market}.{self.interval}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": "candles",
            "selector": {"type": self.candle_type, "market": self.market, "interval": self.interval},
        }

    def deserialize_data(self, data: dict[str, Any], msg_type: str | None) -> list[CandleModel]:
        return [CandleModel.model_validate(item) for item in data]


class StreamResponseModel(X10BaseModel, Generic[T]):
    type: str = None
    data: T
    error: Optional[str] = None
    ts: int
    seq: int
    subscription: str


class AccountStreamDataModelPosition(X10BaseModel):
    isSnapshot: bool
    positions: list[PositionModel]


class AccountStreamDataModelOrder(X10BaseModel):
    isSnapshot: bool
    orders: list[OpenOrderModel]


class AccountStreamDataModelTrade(X10BaseModel):
    isSnapshot: bool
    trades: list[AccountTradeModel]


class AccountStreamDataModelBalance(X10BaseModel):
    isSnapshot: bool
    balance: BalanceModel


class AccountStreamDataModelSpotBalance(X10BaseModel):
    isSnapshot: bool
    spotBalances: list[SpotBalanceModel]


class AccountStreamDataModelDeposit(X10BaseModel):
    isSnapshot: bool
    deposit: DepositStatusUpdateModel


class AccountStreamDataModelWithdrawal(X10BaseModel):
    isSnapshot: bool
    withdrawal: WithdrawalStatusUpdateModel


X: TypeAlias = (
    AccountStreamDataModelPosition
    | AccountStreamDataModelOrder
    | AccountStreamDataModelTrade
    | AccountStreamDataModelBalance
    | AccountStreamDataModelSpotBalance
    | AccountStreamDataModelDeposit
    | AccountStreamDataModelWithdrawal
)


# FIXME: Mark as not supported yet due to auth issues
class _AccountParams(SubscribeParams[X]):
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

    def deserialize_data(self, data: dict[str, Any], msg_type: str | None) -> X:
        match msg_type:
            case "ACCOUNT.POSITION":
                return AccountStreamDataModelOrder.model_validate(data)
            case "ACCOUNT.ORDER":
                return AccountStreamDataModelOrder.model_validate(data)
            case "ACCOUNT.TRADE":
                return AccountStreamDataModelTrade.model_validate(data)
            case "ACCOUNT.BALANCE":
                return AccountStreamDataModelBalance.model_validate(data)
            case "ACCOUNT.SPOT_BALANCE":
                return AccountStreamDataModelSpotBalance.model_validate(data)
            case "ACCOUNT.DEPOSIT":
                return AccountStreamDataModelDeposit.model_validate(data)
            case "ACCOUNT.WITHDRAWAL":
                return AccountStreamDataModelWithdrawal.model_validate(data)
            case _:
                raise ValidationError(f"Unknown account stream message type: {msg_type!r}")
