import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Iterable, Tuple

from sortedcontainers import SortedDict

from x10.clients.stream import StreamClient
from x10.core.client_config import ClientConfig
from x10.models.http import StreamDataType
from x10.models.orderbook import OrderbookUpdateModel


@dataclass
class OrderBookEntry:
    price: Decimal
    amount: Decimal

    def __repr__(self) -> str:
        return f"OrderBookEntry(price={self.price}, amount={self.amount})"


@dataclass(frozen=True)
class ImpactDetails:
    price: Decimal
    amount: Decimal


class OrderBook:
    @staticmethod
    async def create(
        config: ClientConfig,
        *,
        market_name: str,
        best_ask_change_callback: Callable[[OrderBookEntry | None], Awaitable[None]] | None = None,
        best_bid_change_callback: Callable[[OrderBookEntry | None], Awaitable[None]] | None = None,
        start=False,
        depth: int | None = None,
    ) -> "OrderBook":
        ob = OrderBook(config, market_name, best_ask_change_callback, best_bid_change_callback, depth)
        if start:
            await ob.start_orderbook()
        return ob

    def __init__(
        self,
        config: ClientConfig,
        market_name: str,
        best_ask_change_callback: Callable[[OrderBookEntry | None], Awaitable[None]] | None = None,
        best_bid_change_callback: Callable[[OrderBookEntry | None], Awaitable[None]] | None = None,
        depth: int | None = None,
    ) -> None:
        self.__stream_client = StreamClient(api_url=config.endpoints.stream_url)
        self.__market_name = market_name
        self.__task: asyncio.Task | None = None
        self._bid_prices: SortedDict = SortedDict()
        self._ask_prices: SortedDict = SortedDict()
        self.best_ask_change_callback = best_ask_change_callback
        self.best_bid_change_callback = best_bid_change_callback
        self.depth = depth

    async def update_orderbook(self, data: OrderbookUpdateModel):
        best_bid_before_update = self.best_bid()
        for bid in data.bid:
            if bid.price in self._bid_prices:
                existing_bid_entry: OrderBookEntry = self._bid_prices[bid.price]
                existing_bid_entry.amount = existing_bid_entry.amount + bid.qty
                if existing_bid_entry.amount == 0:
                    del self._bid_prices[bid.price]
            else:
                self._bid_prices[bid.price] = OrderBookEntry(
                    price=bid.price,
                    amount=bid.qty,
                )
        now_best_bid = self.best_bid()
        if best_bid_before_update != now_best_bid:
            if self.best_bid_change_callback:
                await self.best_bid_change_callback(now_best_bid)

        best_ask_before_update = self.best_ask()
        for ask in data.ask:
            if ask.price in self._ask_prices:
                existing_ask_entry: OrderBookEntry = self._ask_prices[ask.price]
                existing_ask_entry.amount = existing_ask_entry.amount + ask.qty
                if existing_ask_entry.amount == 0:
                    del self._ask_prices[ask.price]
            else:
                self._ask_prices[ask.price] = OrderBookEntry(
                    price=ask.price,
                    amount=ask.qty,
                )
        now_best_ask = self.best_ask()
        if best_ask_before_update != now_best_ask:
            if self.best_ask_change_callback:
                await self.best_ask_change_callback(now_best_ask)

    async def init_orderbook(self, data: OrderbookUpdateModel):
        self._bid_prices.clear()
        self._ask_prices.clear()

        best_bid_before_update = self.best_bid()
        for bid in data.bid:
            self._bid_prices[bid.price] = OrderBookEntry(
                price=bid.price,
                amount=bid.qty,
            )
        now_best_bid = self.best_bid()
        if best_bid_before_update != now_best_bid:
            if self.best_bid_change_callback:
                await self.best_bid_change_callback(now_best_bid)

        best_ask_before_update = self.best_ask()
        for ask in data.ask:
            self._ask_prices[ask.price] = OrderBookEntry(
                price=ask.price,
                amount=ask.qty,
            )
        now_best_ask = self.best_ask()
        if best_ask_before_update != now_best_ask:
            if self.best_ask_change_callback:
                await self.best_ask_change_callback(now_best_ask)

    async def start_orderbook(self) -> asyncio.Task:
        loop = asyncio.get_running_loop()

        async def inner():
            while True:
                async with self.__stream_client.subscribe_to_orderbooks(self.__market_name, depth=self.depth) as stream:
                    async for event in stream:
                        if event.type == StreamDataType.SNAPSHOT:
                            if not event.data:
                                continue
                            await self.init_orderbook(event.data)
                        elif event.type == StreamDataType.DELTA:
                            if not event.data:
                                continue
                            await self.update_orderbook(event.data)
                await asyncio.sleep(1)

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

    def __price_impact_notional(self, notional: Decimal, levels: Iterable[Tuple[Decimal, OrderBookEntry]]):
        remaining_to_spend = notional
        total_amount = Decimal(0)
        weighted_sum = Decimal(0)
        for price, entry in levels:
            available_at_price = entry.amount
            amount_to_purchase = min(remaining_to_spend / price, available_at_price)
            if remaining_to_spend <= 0:
                break
            if available_at_price <= 0:
                continue
            take = amount_to_purchase
            spent = take * price
            weighted_sum += take * price
            total_amount += take
            remaining_to_spend -= spent

        if remaining_to_spend > 0:
            return None
        average_price = weighted_sum / total_amount
        return ImpactDetails(price=average_price, amount=total_amount)

    def __price_impact_qty(self, qty: Decimal, levels: Iterable[Tuple[Decimal, OrderBookEntry]]):
        remaining_qty = qty
        total_amount = Decimal(0)
        total_spent = Decimal(0)
        for price, entry in levels:
            available_at_price = entry.amount
            take = min(remaining_qty, available_at_price)
            if remaining_qty <= 0:
                break
            if available_at_price <= 0:
                continue
            total_spent += take * price
            total_amount += take
            remaining_qty -= take

        if remaining_qty > 0:
            return None
        average_price = total_spent / total_amount
        return ImpactDetails(price=average_price, amount=total_amount)

    def calculate_price_impact_notional(self, notional: Decimal, side: str) -> ImpactDetails | None:
        if notional <= 0:
            return None
        if side == "SELL":
            if not self._bid_prices:
                return None
            return self.__price_impact_notional(notional, reversed(self._bid_prices.items()))
        elif side == "BUY":
            if not self._ask_prices:
                return None
            return self.__price_impact_notional(notional, self._ask_prices.items())
        return None

    def calculate_price_impact_qty(self, qty: Decimal, side: str) -> ImpactDetails | None:
        if qty <= 0:
            return None
        if side == "SELL":
            if not self._bid_prices:
                return None
            return self.__price_impact_qty(qty, reversed(self._bid_prices.items()))
        elif side == "BUY":
            if not self._ask_prices:
                return None
            return self.__price_impact_qty(qty, self._ask_prices.items())
        return None

    async def close(self):
        self.stop_orderbook()
