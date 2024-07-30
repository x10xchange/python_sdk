from datetime import timedelta
from decimal import Decimal
from typing import Dict

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.markets import MarketModel
from x10.perpetual.order_object import create_order_object
from x10.perpetual.orders import OrderSide, PlacedOrderModel
from x10.perpetual.trading_client.account_module import AccountModule
from x10.perpetual.trading_client.markets_information_module import (
    MarketsInformationModule,
)
from x10.perpetual.trading_client.order_management_module import OrderManagementModule
from x10.utils.date import utc_now
from x10.utils.http import WrappedApiResponse
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


class PerpetualTradingClient:
    """
    X10 Perpetual Trading Client for the X10 REST API v1.
    """

    __markets: Dict[str, MarketModel] | None
    __stark_account: StarkPerpetualAccount

    __markets_info_module: MarketsInformationModule
    __account_module: AccountModule
    __order_management_module: OrderManagementModule

    @classmethod
    def create(cls, endpoint_config: EndpointConfig, trading_account: StarkPerpetualAccount):
        return cls(endpoint_config.api_base_url, trading_account)

    async def place_order(
        self,
        market_name: str,
        amount_of_synthetic: Decimal,
        price: Decimal,
        side: OrderSide,
        post_only: bool = False,
        previous_order_id=None,
        expire_time=utc_now() + timedelta(hours=8),
    ) -> WrappedApiResponse[PlacedOrderModel]:
        if not self.__stark_account:
            raise ValueError("Stark account is not set")

        if not self.__markets:
            markets = await self.__markets_info_module.get_markets()
            self.__markets = {m.name: m for m in markets.data}

        market = self.__markets.get(market_name)
        if not market:
            raise ValueError(f"Market {market_name} not found")

        order = create_order_object(
            self.__stark_account,
            market,
            amount_of_synthetic,
            price,
            side,
            post_only,
            previous_order_id,
            expire_time,
        )

        return await self.__order_management_module.place_order(order)

    async def close(self):
        await self.__markets_info_module.close_session()
        await self.__account_module.close_session()
        await self.__order_management_module.close_session()

    def __init__(self, api_url: str, stark_account: StarkPerpetualAccount | None = None):
        api_key = stark_account.api_key if stark_account else None

        self.__markets = None

        if stark_account:
            self.__stark_account = stark_account

        self.__markets_info_module = MarketsInformationModule(api_url, api_key=api_key)
        self.__account_module = AccountModule(api_url, api_key=api_key, stark_account=stark_account)
        self.__order_management_module = OrderManagementModule(api_url, api_key=api_key)

    @property
    def markets_info(self):
        return self.__markets_info_module

    @property
    def account(self):
        return self.__account_module

    @property
    def orders(self):
        return self.__order_management_module
