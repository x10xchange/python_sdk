from decimal import Decimal
from typing import Callable, List, Optional

from x10.perpetual.accounts import AccountLeverage
from x10.perpetual.assets import (
    AssetOperationModel,
    AssetOperationStatus,
    AssetOperationType,
)
from x10.perpetual.balances import BalanceModel
from x10.perpetual.contract import call_stark_perpetual_withdraw
from x10.perpetual.fees import TradingFeeModel
from x10.perpetual.markets import MarketModel
from x10.perpetual.orders import OpenOrderModel, OrderSide, OrderType
from x10.perpetual.positions import PositionHistoryModel, PositionModel, PositionSide
from x10.perpetual.trades import AccountTradeModel, TradeType
from x10.perpetual.trading_client.base_module import BaseModule
from x10.perpetual.transfer_object import create_transfer_object
from x10.perpetual.withdrawal_object import create_withdrawal_object
from x10.utils.http import (
    WrappedApiResponse,
    send_get_request,
    send_patch_request,
    send_post_request,
)
from x10.utils.model import EmptyModel


class AccountModule(BaseModule):
    async def get_balance(self) -> WrappedApiResponse[BalanceModel]:
        """
        https://x10xchange.github.io/x10-documentation/#get-balance
        """

        url = self._get_url("/user/balance")
        return await send_get_request(await self.get_session(), url, BalanceModel, api_key=self._get_api_key())

    async def get_positions(
        self, *, market_names: Optional[List[str]] = None, position_side: Optional[PositionSide] = None
    ) -> WrappedApiResponse[List[PositionModel]]:
        """
        https://x10xchange.github.io/x10-documentation/#get-positions
        """

        url = self._get_url("/user/positions", query={"market": market_names, "side": position_side})
        return await send_get_request(await self.get_session(), url, List[PositionModel], api_key=self._get_api_key())

    async def get_positions_history(
        self,
        market_names: Optional[List[str]] = None,
        position_side: Optional[PositionSide] = None,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> WrappedApiResponse[List[PositionHistoryModel]]:
        """
        https://x10xchange.github.io/x10-documentation/#get-positions-history
        """

        url = self._get_url(
            "/user/positions/history",
            query={"market": market_names, "side": position_side, "cursor": cursor, "limit": limit},
        )
        return await send_get_request(
            await self.get_session(), url, List[PositionHistoryModel], api_key=self._get_api_key()
        )

    async def get_open_orders(
        self,
        market_names: Optional[List[str]] = None,
        order_type: Optional[OrderType] = None,
        order_side: Optional[OrderSide] = None,
    ) -> WrappedApiResponse[List[OpenOrderModel]]:
        """
        https://x10xchange.github.io/x10-documentation/#get-open-orders
        """

        url = self._get_url(
            "/user/orders",
            query={"market": market_names, "type": order_type, "side": order_side},
        )
        return await send_get_request(await self.get_session(), url, List[OpenOrderModel], api_key=self._get_api_key())

    async def get_orders_history(
        self,
        market_names: Optional[List[str]] = None,
        order_type: Optional[OrderType] = None,
        order_side: Optional[OrderSide] = None,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> WrappedApiResponse[List[OpenOrderModel]]:
        """
        https://x10xchange.github.io/x10-documentation/#get-orders-history
        """

        url = self._get_url(
            "/user/orders/history",
            query={"market": market_names, "type": order_type, "side": order_side, "cursor": cursor, "limit": limit},
        )
        return await send_get_request(await self.get_session(), url, List[OpenOrderModel], api_key=self._get_api_key())

    async def get_trades(
        self,
        market_names: List[str],
        trade_side: Optional[OrderSide] = None,
        trade_type: Optional[TradeType] = None,
    ) -> WrappedApiResponse[List[AccountTradeModel]]:
        """
        https://x10xchange.github.io/x10-documentation/#get-trades
        """

        url = self._get_url(
            "/user/trades",
            query={"market": market_names, "side": trade_side, "type": trade_type},
        )

        return await send_get_request(
            await self.get_session(), url, List[AccountTradeModel], api_key=self._get_api_key()
        )

    async def get_fees(self, *, market_names: List[str]) -> WrappedApiResponse[List[TradingFeeModel]]:
        """
        https://x10xchange.github.io/x10-documentation/#get-fees
        """

        url = self._get_url("/user/fees", query={"market": market_names})
        return await send_get_request(await self.get_session(), url, List[TradingFeeModel], api_key=self._get_api_key())

    async def get_leverage(self, market_names: List[str]) -> WrappedApiResponse[List[AccountLeverage]]:
        """
        https://x10xchange.github.io/x10-documentation/#get-current-leverage
        """

        url = self._get_url("/user/leverage", query={"market": market_names})
        return await send_get_request(await self.get_session(), url, List[AccountLeverage], api_key=self._get_api_key())

    async def update_leverage(self, market_name: str, leverage: Decimal) -> WrappedApiResponse[EmptyModel]:
        """
        https://x10xchange.github.io/x10-documentation/#update-leverage
        """

        url = self._get_url("/user/leverage")
        request_model = AccountLeverage(market=market_name, leverage=leverage)
        return await send_patch_request(
            await self.get_session(),
            url,
            EmptyModel,
            json=request_model.to_api_request_json(),
            api_key=self._get_api_key(),
        )

    async def transfer(
        self,
        to_vault: int,
        to_l2_key: str,
        amount: Decimal,
    ) -> WrappedApiResponse[EmptyModel]:
        from_vault = self._get_stark_account().vault
        from_l2_key = self._get_stark_account().public_key
        url = self._get_url("/user/transfer/onchain")
        request_model = create_transfer_object(
            from_vault=from_vault,
            from_l2_key=from_l2_key,
            to_vault=to_vault,
            to_l2_key=to_l2_key,
            amount=amount,
            config=self._get_endpoint_config(),
            stark_account=self._get_stark_account(),
        )

        return await send_post_request(
            await self.get_session(),
            url,
            EmptyModel,
            json=request_model.to_api_request_json(),
            api_key=self._get_api_key(),
        )

    async def withdrawal_slow_request(
        self,
        amount: Decimal,
        eth_address: str,
    ) -> WrappedApiResponse[int]:
        url = self._get_url("/user/withdrawal/onchain")
        request_model = create_withdrawal_object(
            amount=amount,
            eth_address=eth_address,
            stark_account=self._get_stark_account(),
            config=self._get_endpoint_config(),
        )

        return await send_post_request(
            await self.get_session(),
            url,
            int,
            json=request_model.to_api_request_json(),
            api_key=self._get_api_key(),
        )

    def withdrawal_slow_reclaim(
        self,
        contract_address: str,
        eth_address: str,
        market: MarketModel,
        get_eth_private_key: Callable[[], str],
    ):
        return call_stark_perpetual_withdraw(
            contract_address,
            eth_address,
            market,
            self._get_endpoint_config(),
            get_eth_private_key,
        )

    async def get_asset_operations(
        self,
        operations_type: Optional[List[AssetOperationType]] = None,
        operations_status: Optional[List[AssetOperationStatus]] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> WrappedApiResponse[List[AssetOperationModel]]:
        url = self._get_url(
            "/user/assetOperations",
            query={
                "type": operations_type,
                "status": operations_status,
                "startTime": start_time,
                "endTime": end_time,
                "cursor": cursor,
                "limit": limit,
            },
        )
        return await send_get_request(
            await self.get_session(), url, List[AssetOperationModel], api_key=self._get_api_key()
        )
