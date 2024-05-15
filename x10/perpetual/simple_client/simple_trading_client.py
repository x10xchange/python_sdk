import asyncio
from decimal import Decimal
from typing import Dict, Tuple, Union

from x10.perpetual.accounts import AccountStreamDataModel, StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OpenOrderModel, OrderSide
from x10.perpetual.stream_client.perpetual_stream_connection import (
    PerpetualStreamConnection,
)
from x10.perpetual.stream_client.stream_client import PerpetualStreamClient
from x10.perpetual.trading_client.markets_information_module import (
    MarketsInformationModule,
)
from x10.perpetual.trading_client.order_management_module import OrderManagementModule
from x10.utils.http import WrappedStreamResponse


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
        self.__order_waiters: Dict[str, Tuple[asyncio.Condition, Union[None, OpenOrderModel]]] = {}
        self.__orders_task: Union[None, asyncio.Task] = None

    async def ___order_stream(self):
        async for event in self.__account_stream:
            if not (event.data and event.data.orders):
                continue
            else:
                pass
            for order in event.data.orders:
                (condition, open_order) = self.__order_waiters.get(order.external_id)
                if not condition:
                    continue
                if condition:
                    async with condition:
                        self.__order_waiters[order.external_id] = (condition, order)
                        condition.notify_all()

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
            self.__account_stream = await self.__stream_client.subscribe_to_account_updates(self.__account.api_key)
            self.__orders_task = asyncio.create_task(self.___order_stream())

        order = create_order_object(
            account=self.__account,
            market=market,
            amount_of_synthetic=amount_of_synthetic,
            price=price,
            side=side,
            post_only=post_only,
            previous_order_id=previous_order_id,
        )

        self.__order_waiters[order.id] = (asyncio.Condition(), None)
        placed_order_task = asyncio.create_task(self.__orders_module.place_order(order))
        (waiting_condition, open_order) = self.__order_waiters[order.id]
        if open_order:
            return open_order
        async with waiting_condition:
            await asyncio.gather(
                placed_order_task, asyncio.wait_for(waiting_condition.wait(), 5), return_exceptions=False
            )
            open_model = self.__order_waiters[order.id][1]
            del self.__order_waiters[order.id]
            if not open_model:
                raise ValueError("No Fill or Placement received for order")
            return open_model

    async def cancel_order(self, order_id: int):
        await self.__orders_module.cancel_order(order_id)
