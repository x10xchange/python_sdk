from typing import Optional

from x10.perpetual.trading_client.account_module import AccountModule
from x10.perpetual.trading_client.markets_information_module import (
    MarketsInformationModule,
)
from x10.perpetual.trading_client.order_management_module import OrderManagementModule
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


class PerpetualTradingClient:
    """
    X10 Perpetual Trading Client for the X10 REST API v1.
    """

    __markets_info_module: MarketsInformationModule
    __account_module: AccountModule
    __order_management_module: OrderManagementModule

    def __init__(self, *, api_url: str, api_key: Optional[str]):
        self.__markets_info_module = MarketsInformationModule(api_url, api_key)
        self.__account_module = AccountModule(api_url, api_key)
        self.__order_management_module = OrderManagementModule(api_url, api_key)

    @property
    def markets_info(self):
        return self.__markets_info_module

    @property
    def account(self):
        return self.__account_module

    @property
    def orders(self):
        return self.__order_management_module
