import asyncio
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Awaitable, Dict, Optional, cast

from x10.clients.rest.modules.info_module import InfoModule
from x10.clients.rest.modules.order_management_module import OrderManagementModule
from x10.clients.stream import StreamClient, StreamConnection
from x10.core.client_config import ClientConfig
from x10.core.stark_account import StarkPerpetualAccount
from x10.errors import SdkError, ValidationError
from x10.models.account import AccountStreamDataModel
from x10.models.http import WrappedStreamResponseModel
from x10.models.market import MarketModel
from x10.models.order import (
    NewOrderModel,
    OpenOrderModel,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from x10.signing.order_object import create_order_object


def condition_to_awaitable(condition: asyncio.Condition) -> Awaitable:
    async def __inner():
        async with condition:
            await condition.wait()

    return __inner()


class TimedOpenOrderModel(OpenOrderModel):
    start_nanos: int
    end_nanos: int
    operation_ms: float

    def __init__(self, start_nanos: int, end_nanos: int, open_order: OpenOrderModel):
        super().__init__(
            **dict(
                open_order.model_dump(),
                **{
                    "start_nanos": start_nanos,
                    "end_nanos": end_nanos,
                    "operation_ms": (end_nanos - start_nanos) / 1_000_000,
                },
            )
        )


@dataclass
class TimedCancel:
    start_nanos: int
    end_nanos: int
    operation_ms: float


@dataclass
class OrderWaiter:
    condition: asyncio.Condition
    open_order: None | TimedOpenOrderModel
    start_nanos: int


@dataclass
class CancelWaiter:
    condition: asyncio.Condition
    start_nanos: int
    end_nanos: int | None


class BlockingTradingClient:
    """
    A client for placing orders and receiving updates in a blocking manner.
    Waits for the confirmation from the WS stream after placing or canceling an order.
    """

    def __init__(self, config: ClientConfig, account: StarkPerpetualAccount):
        if not asyncio.get_event_loop().is_running():
            raise SdkError(
                "BlockingTradingClient must be initialized from an async function, use BlockingTradingClient.create()"
            )

        self.__config = config
        self.__account = account
        self.__info_module = InfoModule(config, api_key=account.api_key)
        self.__orders_module = OrderManagementModule(config, api_key=account.api_key)
        self.__markets: Optional[Dict[str, MarketModel]] = None
        self.__stream_client: StreamClient = StreamClient(api_url=config.endpoints.stream_url)
        self.__account_stream: Optional[StreamConnection[WrappedStreamResponseModel[AccountStreamDataModel]]] = None
        self.__order_waiters: Dict[str, OrderWaiter] = {}
        self.__cancel_waiters: Dict[str, CancelWaiter] = {}
        self.__stream_task = asyncio.create_task(self.__order_stream())

    @staticmethod
    async def create(config: ClientConfig, account: StarkPerpetualAccount) -> "BlockingTradingClient":
        client = BlockingTradingClient(config, account)
        await client.__stream_client.subscribe_to_account_updates(account.api_key)
        return client

    async def __handle_cancel(self, order_external_id: str):
        if order_external_id not in self.__cancel_waiters:
            return
        cancel_waiter = self.__cancel_waiters.get(order_external_id)
        if not cancel_waiter:
            return
        if cancel_waiter.condition:
            async with cancel_waiter.condition:
                cancel_waiter.end_nanos = time.time_ns()
                cancel_waiter.condition.notify_all()

    async def __handle_update(self, order: OpenOrderModel):
        order_waiter: OrderWaiter | None = self.__order_waiters.get(order.external_id)
        if not order_waiter:
            return
        async with order_waiter.condition:
            order_waiter.open_order = TimedOpenOrderModel(
                start_nanos=order_waiter.start_nanos,
                end_nanos=time.time_ns(),
                open_order=order,
            )
            order_waiter.condition.notify_all()

    async def __handle_order(self, order: OpenOrderModel):
        if order.status == OrderStatus.CANCELLED:
            await self.__handle_cancel(order.external_id)
        else:
            await self.__handle_update(order)

    async def __order_stream(self):
        self.__account_stream = await self.__stream_client.subscribe_to_account_updates(self.__account.api_key)
        async for event in self.__account_stream:
            if not (event.data and event.data.orders):
                continue
            for order in event.data.orders:
                await self.__handle_order(order)
        print("Order stream closed, reconnecting...")
        await self.__order_stream()

    async def cancel_order(self, order_external_id: str) -> TimedCancel:
        awaitable: Awaitable
        if order_external_id in self.__cancel_waiters:
            awaitable = condition_to_awaitable(self.__cancel_waiters[order_external_id].condition)
        else:
            self.__cancel_waiters[order_external_id] = CancelWaiter(
                asyncio.Condition(), start_nanos=time.time_ns(), end_nanos=None
            )
            cancel_task = asyncio.create_task(self.__orders_module.cancel_order_by_external_id(order_external_id))
            awaitable = asyncio.gather(
                cancel_task,
                asyncio.wait_for(condition_to_awaitable(self.__cancel_waiters[order_external_id].condition), 5),
                return_exceptions=False,
            )

        cancel_waiter = self.__cancel_waiters[order_external_id]
        end_nanos = None
        if cancel_waiter.end_nanos:
            end_nanos = cancel_waiter.end_nanos
        else:
            await awaitable
            end_nanos = self.__cancel_waiters[order_external_id].end_nanos
        del self.__cancel_waiters[order_external_id]
        end_nanos = cast(int, end_nanos)
        return TimedCancel(
            start_nanos=cancel_waiter.start_nanos,
            end_nanos=end_nanos,
            operation_ms=(end_nanos - cancel_waiter.start_nanos) / 1_000_000,
        )

    async def get_markets(self) -> Dict[str, MarketModel]:
        if not self.__markets:
            markets = await self.__info_module.get_markets()
            market_data = markets.data
            if not market_data:
                raise ValidationError("Core market data is empty, check your connection or API key.")
            self.__markets = {m.name: m for m in market_data}
        return self.__markets

    async def mass_cancel(
        self,
        order_ids: list[int] | None = None,
        external_order_ids: list[str] | None = None,
        markets: list[str] | None = None,
        cancel_all: bool = False,
    ) -> None:
        await self.__orders_module.mass_cancel(
            order_ids=order_ids,
            external_order_ids=external_order_ids,
            markets=markets,
            cancel_all=cancel_all,
        )

    async def create_and_place_order(
        self,
        market_name: str,
        amount_of_synthetic: Decimal,
        price: Decimal,
        side: OrderSide,
        taker_fee: Decimal,
        post_only: bool = False,
        previous_order_external_id: str | None = None,
        external_id: str | None = None,
        builder_fee: Decimal | None = None,
        builder_id: int | None = None,
        time_in_force: TimeInForce = TimeInForce.GTT,
        reduce_only: bool = False,
        order_type: OrderType = OrderType.LIMIT,
    ) -> TimedOpenOrderModel:
        market = (await self.get_markets()).get(market_name)
        if not market:
            raise ValidationError(f"Market '{market_name}' not found.")

        order: NewOrderModel = create_order_object(
            account=self.__account,
            market=market,
            order_type=order_type,
            amount_of_synthetic=amount_of_synthetic,
            price=price,
            side=side,
            post_only=post_only,
            reduce_only=reduce_only,
            previous_order_external_id=previous_order_external_id,
            starknet_domain=self.__config.signing.starknet_domain,
            order_external_id=external_id,
            builder_fee=builder_fee,
            builder_id=builder_id,
            time_in_force=time_in_force,
            taker_fee=taker_fee,
        )

        if order.id in self.__order_waiters:
            raise ValidationError(f"order with {order.id} hash already placed")

        self.__order_waiters[order.id] = OrderWaiter(asyncio.Condition(), None, start_nanos=time.time_ns())
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
                raise ValidationError("No Fill or Placement received for order")
            return open_model

    async def close(self):
        if self.__stream_task:
            self.__stream_task.cancel()
        if self.__account_stream:
            await self.__account_stream.close()

    @property
    def config(self):
        return self.__config
