import asyncio
import dataclasses
import decimal
from typing import Callable

from sortedcontainers import SortedDict  # type: ignore[import-untyped]

from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.orderbooks import OrderbookUpdateModel
from x10.perpetual.stream_client.stream_client import PerpetualStreamClient
from x10.utils.http import StreamDataType


@dataclasses.dataclass
class OrderBookEntry:
    price: decimal.Decimal
    amount: decimal.Decimal

    def __repr__(self) -> str:
        return f"OrderBookEntry(price={self.price}, amount={self.amount})"


class OrderBook:
    @staticmethod
    async def create(
        endpoint_config: EndpointConfig,
        market_name: str,
        best_ask_change_callback: Callable[[OrderBookEntry], None] | None = None,
        best_bid_change_callback: Callable[[OrderBookEntry], None] | None = None,
        start=False,
    ) -> "OrderBook":
        ob = OrderBook(
            endpoint_config,
            market_name,
            best_ask_change_callback,
            best_bid_change_callback,
        )
        if start:
            await ob.start_orderbook()
        return ob

    def __init__(
        self,
        endpoint_config: EndpointConfig,
        market_name: str,
        best_ask_change_callback: Callable[[OrderBookEntry], None] | None = None,
        best_bid_change_callback: Callable[[OrderBookEntry], None] | None = None,
    ) -> None:
        self.__stream_client = PerpetualStreamClient(api_url=endpoint_config.stream_url)
        self.__market_name = market_name
        self.__task: asyncio.Task | None = None
        self._bid_prices: SortedDict[decimal.Decimal, OrderBookEntry] = SortedDict()
        self._ask_prices: SortedDict[decimal.Decimal, OrderBookEntry] = SortedDict()
        self.best_ask_change_callback = best_ask_change_callback
        self.best_bid_change_callback = best_bid_change_callback

    def update_orderbook(self, data: OrderbookUpdateModel):
        best_bid_before_update = self.best_bid()
        for bid in data.bid:
            if bid.price in self._bid_prices:
                existing_bid_entry: OrderBookEntry = self._bid_prices.get(bid.price)
                existing_bid_entry.amount = existing_bid_entry.amount + bid.qty
                if existing_bid_entry.amount == 0:
                    del self._bid_prices[bid.price]
            else:
                self._bid_prices[bid.price] = OrderBookEntry(
                    price=bid.price,
                    amount=bid.qty,
                )
        now_best_bid = self.best_bid()
        if now_best_bid and best_bid_before_update != now_best_bid:
            if self.best_bid_change_callback:
                self.best_bid_change_callback(now_best_bid)

        best_ask_before_update = self.best_ask()
        for ask in data.ask:
            if ask.price in self._ask_prices:
                existing_ask_entry: OrderBookEntry = self._ask_prices.get(ask.price)
                existing_ask_entry.amount = existing_ask_entry.amount + ask.qty
                if existing_ask_entry.amount == 0:
                    del self._ask_prices[ask.price]
            else:
                self._ask_prices[ask.price] = OrderBookEntry(
                    price=ask.price,
                    amount=ask.qty,
                )
        now_best_ask = self.best_ask()
        if now_best_ask and best_ask_before_update != now_best_ask:
            if self.best_ask_change_callback:
                self.best_ask_change_callback(now_best_ask)

    def init_orderbook(self, data: OrderbookUpdateModel):
        for bid in data.bid:
            self._bid_prices[bid.price] = OrderBookEntry(
                price=bid.price,
                amount=bid.qty,
            )
        for ask in data.ask:
            self._ask_prices[ask.price] = OrderBookEntry(
                price=ask.price,
                amount=ask.qty,
            )

    async def start_orderbook(self) -> asyncio.Task:
        loop = asyncio.get_running_loop()

        async def inner():
            async with self.__stream_client.subscribe_to_orderbooks(self.__market_name) as stream:
                async for event in stream:
                    if event.type == StreamDataType.SNAPSHOT.value:
                        self.init_orderbook(event.data)
                    elif event.type == StreamDataType.DELTA.value:
                        self.update_orderbook(event.data)

        self.__task = loop.create_task(inner())
        return self.__task

    def stop_orderbook(self):
        if self.__task:
            self.__task.cancel()
            self.__task = None

    def best_bid(self) -> OrderBookEntry | None:
        try:
            entry = self._bid_prices.peekitem(-1)
            return entry[1]
        except IndexError:
            return None

    def best_ask(self) -> OrderBookEntry | None:
        try:
            entry = self._ask_prices.peekitem(0)
            return entry[1]
        except IndexError:
            return None
