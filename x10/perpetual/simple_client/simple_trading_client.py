import asyncio
import dataclasses
from decimal import Decimal
from typing import Dict, Union

from x10.perpetual.accounts import AccountStreamDataModel, StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OpenOrderModel, OrderSide, PerpetualOrderModel
from x10.perpetual.stream_client.perpetual_stream_connection import (
    PerpetualStreamConnection,
)
from x10.perpetual.stream_client.stream_client import PerpetualStreamClient
from x10.perpetual.trading_client.markets_information_module import (
    MarketsInformationModule,
)
from x10.perpetual.trading_client.order_management_module import OrderManagementModule
from x10.utils.http import WrappedStreamResponse


@dataclasses.dataclass
class OrderWaiter:
    condition: asyncio.Condition
    open_order: None | OpenOrderModel


class BlockingTradingClient:
    def __init__(self, endpoint_config: EndpointConfig, account: StarkPerpetualAccount):
        self.__endpoint_config = endpoint_config
        self.__account = account
        self.__market_module = MarketsInformationModule(endpoint_config.api_base_url, account.api_key)
        self.__orders_module = OrderManagementModule(endpoint_config.api_base_url, account.api_key)
        self.__markets: Union[None, Dict[str, MarketModel]] = None
        self.__stream_client: PerpetualStreamClient = PerpetualStreamClient(api_url=endpoint_config.stream_url)
        self.__account_stream: Union[
            None,
            PerpetualStreamConnection[WrappedStreamResponse[AccountStreamDataModel]],
        ] = None
        self.__order_waiters: Dict[str, OrderWaiter] = {}
        self.__orders_task: Union[None, asyncio.Task] = None
        self.__stream_lock = asyncio.Lock()

    async def ___order_stream(self):
        async for event in self.__account_stream:
            if not (event.data and event.data.orders):
                continue
            for order in event.data.orders:
                if order.external_id not in self.__order_waiters:
                    continue
                order_waiter = self.__order_waiters.get(order.external_id)
                if not order_waiter:
                    continue
                if order_waiter.condition:
                    async with order_waiter.condition:
                        order_waiter.open_order = order
                        order_waiter.condition.notify_all()

    async def cancel_order(self, order_id: int):
        await self.__orders_module.cancel_order(order_id)

    async def create_and_place_order(
        self,
        market_name: str,
        amount_of_synthetic: Decimal,
        price: Decimal,
        side: OrderSide,
        post_only: bool = False,
        previous_order_id: str | None = None,
    ) -> OpenOrderModel:
        if not self.__markets:
            markets = await self.__market_module.get_markets()
            self.__markets = {m.name: m for m in markets.data}
        market = self.__markets.get(market_name)
        if not market:
            raise ValueError(f"Market '{market_name}' not found.")

        if not self.__account_stream:
            await self.__stream_lock.acquire()
            if not self.__account_stream:
                self.__account_stream = await self.__stream_client.subscribe_to_account_updates(self.__account.api_key)
                self.__orders_task = asyncio.create_task(self.___order_stream())
            self.__stream_lock.release()

        order: PerpetualOrderModel = create_order_object(
            account=self.__account,
            market=market,
            amount_of_synthetic=amount_of_synthetic,
            price=price,
            side=side,
            post_only=post_only,
            previous_order_id=previous_order_id,
        )

        if order.id in self.__order_waiters:
            raise ValueError(f"order with {order.id} hash already placed")

        self.__order_waiters[order.id] = OrderWaiter(asyncio.Condition(), None)
        placed_order_task = asyncio.create_task(self.__orders_module.place_order(order))
        order_waiter = self.__order_waiters[order.id]
        if order_waiter.open_order:
            return order_waiter.open_order
        async with order_waiter.condition:
            await asyncio.gather(
                placed_order_task,
                asyncio.wait_for(order_waiter.condition.wait(), 5),
                return_exceptions=False,
            )
            open_model = self.__order_waiters[order.id].open_order
            del self.__order_waiters[order.id]
            if not open_model:
                raise ValueError("No Fill or Placement received for order")
            return open_model
