from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional

from x10.clients.rest.modules.account_module import AccountModule
from x10.clients.rest.modules.builder_module import BuilderModule
from x10.clients.rest.modules.info_module import InfoModule
from x10.clients.rest.modules.order_management_module import OrderManagementModule
from x10.clients.rest.modules.testnet_module import TestnetModule
from x10.clients.rest.modules.vault_module import VaultModule
from x10.config import Config
from x10.core.stark_account import StarkPerpetualAccount
from x10.errors import ValidationError
from x10.models.market import MarketModel
from x10.models.order import (
    OrderSide,
    OrderTpslType,
    PlacedOrderModel,
    SelfTradeProtectionLevel,
    TimeInForce,
)
from x10.signing.order_object import OrderTpslTriggerParam, create_order_object
from x10.utils.date import utc_now
from x10.utils.http import WrappedApiResponseModel
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


class RestApiClient:
    """
    Extended REST API Client.
    """

    __markets: Dict[str, MarketModel] | None

    __config: Config
    __stark_account: StarkPerpetualAccount | None

    __info_module: InfoModule
    __account_module: AccountModule
    __order_management_module: OrderManagementModule
    __vault_module: VaultModule
    __testnet_module: TestnetModule
    __builder_module: BuilderModule

    async def place_order(
        self,
        market_name: str,
        amount_of_synthetic: Decimal,
        price: Decimal,
        side: OrderSide,
        taker_fee: Decimal,
        post_only: bool = False,
        previous_order_id=None,
        expire_time: Optional[datetime] = None,
        time_in_force: TimeInForce = TimeInForce.GTT,
        self_trade_protection_level: SelfTradeProtectionLevel = SelfTradeProtectionLevel.ACCOUNT,
        external_id: Optional[str] = None,
        builder_fee: Optional[Decimal] = None,
        builder_id: Optional[int] = None,
        reduce_only: bool = False,
        tp_sl_type: Optional[OrderTpslType] = None,
        take_profit: Optional[OrderTpslTriggerParam] = None,
        stop_loss: Optional[OrderTpslTriggerParam] = None,
    ) -> WrappedApiResponseModel[PlacedOrderModel]:
        # FIXME: Remove all the checks, should proxy the request?
        if not self.__stark_account:
            raise ValidationError("Stark account is not set")

        if not self.__markets:
            self.__markets = await self.__info_module.get_markets_dict()

        market = self.__markets.get(market_name)

        if not market:
            raise ValidationError(f"Market {market_name} not found")

        if expire_time is None:
            expire_time = utc_now() + timedelta(hours=1)

        order = create_order_object(
            account=self.__stark_account,
            market=market,
            amount_of_synthetic=amount_of_synthetic,
            price=price,
            side=side,
            post_only=post_only,
            previous_order_external_id=previous_order_id,
            expire_time=expire_time,
            time_in_force=time_in_force,
            self_trade_protection_level=self_trade_protection_level,
            starknet_domain=self.__config.signing.starknet_domain,
            order_external_id=external_id,
            taker_fee=taker_fee,
            builder_fee=builder_fee,
            builder_id=builder_id,
            reduce_only=reduce_only,
            tp_sl_type=tp_sl_type,
            take_profit=take_profit,
            stop_loss=stop_loss,
        )
        if market.is_rfq:
            return await self.__order_management_module.place_rfq_order(order)
        return await self.__order_management_module.place_order(order)

    async def close(self):
        await self.__info_module.close_session()
        await self.__account_module.close_session()
        await self.__order_management_module.close_session()
        await self.__vault_module.close_session()
        await self.__testnet_module.close_session()
        await self.__builder_module.close_session()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    def __init__(self, config: Config, stark_account: StarkPerpetualAccount | None = None):
        api_key = stark_account.api_key if stark_account else None

        self.__config = config
        self.__markets = None
        self.__stark_account = stark_account

        self.__info_module = InfoModule(config)
        self.__account_module = AccountModule(config, api_key=api_key, stark_account=stark_account)
        self.__order_management_module = OrderManagementModule(config, api_key=api_key)
        self.__vault_module = VaultModule(
            config,
            info_module=self.__info_module,
            account_module=self.__account_module,
            account=stark_account,
            api_key=api_key,
        )
        self.__testnet_module = TestnetModule(config, api_key=api_key, account_module=self.__account_module)
        self.__builder_module = BuilderModule(config, api_key=api_key)

    @property
    def config(self):
        return self.__config

    @property
    def stark_account(self):
        return self.__stark_account

    @property
    def info(self):
        return self.__info_module

    @property
    def account(self):
        return self.__account_module

    @property
    def orders(self):
        return self.__order_management_module

    @property
    def testnet(self):
        return self.__testnet_module

    @property
    def vault(self):
        return self.__vault_module

    @property
    def builder(self):
        return self.__builder_module
