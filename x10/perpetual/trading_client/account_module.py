from decimal import Decimal
from typing import List, Optional

from x10.perpetual.accounts import AccountLeverage, AccountModel
from x10.perpetual.assets import (
    AssetOperationModel,
    AssetOperationStatus,
    AssetOperationType,
)
from x10.perpetual.balances import BalanceModel
from x10.perpetual.bridges import BridgesConfig, Quote
from x10.perpetual.clients import ClientModel
from x10.perpetual.fees import TradingFeeModel
from x10.perpetual.orders import OpenOrderModel, OrderSide, OrderType
from x10.perpetual.positions import PositionHistoryModel, PositionModel, PositionSide
from x10.perpetual.trades import AccountTradeModel, TradeType
from x10.perpetual.trading_client.base_module import BaseModule
from x10.perpetual.transfer_object import create_transfer_object
from x10.perpetual.transfers import TransferResponseModel
from x10.perpetual.withdrawal_object import create_withdrawal_object
from x10.utils.http import (
    WrappedApiResponse,
    send_get_request,
    send_patch_request,
    send_post_request,
)
from x10.utils.model import EmptyModel


class AccountModule(BaseModule):
    async def get_account(self) -> WrappedApiResponse[AccountModel]:
        url = self._get_url("/user/account/info")
        return await send_get_request(await self.get_session(), url, AccountModel, api_key=self._get_api_key())

    async def get_client(self) -> WrappedApiResponse[ClientModel]:
        url = self._get_url("/user/client/info")
        return await send_get_request(await self.get_session(), url, ClientModel, api_key=self._get_api_key())

    async def get_balance(self) -> WrappedApiResponse[BalanceModel]:
        """
        https://api.docs.extended.exchange/#get-balance
        """

        url = self._get_url("/user/balance")
        return await send_get_request(await self.get_session(), url, BalanceModel, api_key=self._get_api_key())

    async def get_positions(
        self, *, market_names: Optional[List[str]] = None, position_side: Optional[PositionSide] = None
    ) -> WrappedApiResponse[List[PositionModel]]:
        """
        https://api.docs.extended.exchange/#get-positions
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
        https://api.docs.extended.exchange/#get-positions-history
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
        https://api.docs.extended.exchange/#get-open-orders
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
        https://api.docs.extended.exchange/#get-orders-history
        """

        url = self._get_url(
            "/user/orders/history",
            query={"market": market_names, "type": order_type, "side": order_side, "cursor": cursor, "limit": limit},
        )
        return await send_get_request(await self.get_session(), url, List[OpenOrderModel], api_key=self._get_api_key())

    async def get_order_by_id(self, order_id: int) -> WrappedApiResponse[OpenOrderModel]:
        """
        https://api.docs.extended.exchange/#get-order-by-id
        """

        url = self._get_url("/user/orders/<order_id>", order_id=order_id)

        return await send_get_request(await self.get_session(), url, OpenOrderModel, api_key=self._get_api_key())

    async def get_order_by_external_id(self, external_id: str) -> WrappedApiResponse[list[OpenOrderModel]]:
        """
        https://api.docs.extended.exchange/#get-order-by-external-id
        """

        url = self._get_url("/user/orders/external/<external_id>", external_id=external_id)

        return await send_get_request(await self.get_session(), url, list[OpenOrderModel], api_key=self._get_api_key())

    async def get_trades(
        self,
        market_names: List[str],
        trade_side: Optional[OrderSide] = None,
        trade_type: Optional[TradeType] = None,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> WrappedApiResponse[List[AccountTradeModel]]:
        """
        https://api.docs.extended.exchange/#get-trades
        """

        url = self._get_url(
            "/user/trades",
            query={"market": market_names, "side": trade_side, "type": trade_type, "cursor": cursor, "limit": limit},
        )

        return await send_get_request(
            await self.get_session(), url, List[AccountTradeModel], api_key=self._get_api_key()
        )

    async def get_fees(
        self, *, market_names: List[str], builder_id: Optional[int] = None
    ) -> WrappedApiResponse[List[TradingFeeModel]]:
        """
        https://api.docs.extended.exchange/#get-fees
        """

        url = self._get_url(
            "/user/fees",
            query={
                "market": market_names,
                "builderId": builder_id,
            },
        )
        return await send_get_request(await self.get_session(), url, List[TradingFeeModel], api_key=self._get_api_key())

    async def get_leverage(self, market_names: List[str]) -> WrappedApiResponse[List[AccountLeverage]]:
        """
        https://api.docs.extended.exchange/#get-current-leverage
        """

        url = self._get_url("/user/leverage", query={"market": market_names})
        return await send_get_request(await self.get_session(), url, List[AccountLeverage], api_key=self._get_api_key())

    async def update_leverage(self, market_name: str, leverage: Decimal) -> WrappedApiResponse[EmptyModel]:
        """
        https://api.docs.extended.exchange/#update-leverage
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

    async def get_bridge_config(self) -> WrappedApiResponse[BridgesConfig]:
        url = self._get_url("/user/bridge/config")
        return await send_get_request(await self.get_session(), url, BridgesConfig, api_key=self._get_api_key())

    async def get_bridge_quote(self, chain_in: str, chain_out: str, amount: Decimal) -> WrappedApiResponse[Quote]:
        url = self._get_url(
            "/user/bridge/quote",
            query={
                "chainIn": chain_in,
                "chainOut": chain_out,
                "amount": amount,
            },
        )
        return await send_get_request(await self.get_session(), url, Quote, api_key=self._get_api_key())

    async def commit_bridge_quote(self, id: str):
        url = self._get_url(
            "/user/bridge/quote",
            query={
                "id": id,
            },
        )
        await send_post_request(await self.get_session(), url, EmptyModel, api_key=self._get_api_key())

    async def transfer(
        self,
        to_vault: int,
        to_l2_key: int | str,
        amount: Decimal,
        nonce: int | None = None,
    ) -> WrappedApiResponse[TransferResponseModel]:
        from_vault = self._get_stark_account().vault
        url = self._get_url("/user/transfer/onchain")

        if isinstance(to_l2_key, str):
            to_l2_key = int(to_l2_key, base=16)

        request_model = create_transfer_object(
            from_vault=from_vault,
            to_vault=to_vault,
            to_l2_key=to_l2_key,
            amount=amount,
            config=self._get_endpoint_config(),
            stark_account=self._get_stark_account(),
            nonce=nonce,
        )

        return await send_post_request(
            await self.get_session(),
            url,
            TransferResponseModel,
            json=request_model.to_api_request_json(),
            api_key=self._get_api_key(),
        )

    async def withdraw(
        self,
        amount: Decimal,
        chain_id: str = "STRK",
        stark_address: str | None = None,
        nonce: int | None = None,
        quote_id: str | None = None,
    ) -> WrappedApiResponse[int]:
        url = self._get_url("/user/withdrawal")
        account = (await self.get_account()).data
        if account is None:
            raise ValueError("Account not found")
        if quote_id is None and chain_id != "STRK":
            raise ValueError("quote_id is required for EVM withdrawals")

        recipient_stark_address = None
        if stark_address is None:
            if chain_id == "STRK":
                client = (await self.get_client()).data
                if client is None:
                    raise ValueError("Client not found")
                if client.starknet_wallet_address is None:
                    raise ValueError(
                        "Client does not have attached starknet_wallet_address. Can't determine withdrawal address."
                    )
                else:
                    recipient_stark_address = client.starknet_wallet_address
            else:
                if account.bridge_starknet_address is None:
                    raise ValueError("Account bridge_starknet_address not found")
                recipient_stark_address = account.bridge_starknet_address
        else:
            recipient_stark_address = stark_address

        request_model = create_withdrawal_object(
            amount=amount,
            recipient_stark_address=recipient_stark_address,
            stark_account=self._get_stark_account(),
            config=self._get_endpoint_config(),
            account_id=account.id,
            chain_id=chain_id,
            quote_id=quote_id,
            nonce=nonce,
        )
        return await send_post_request(
            await self.get_session(),
            url,
            int,
            json=request_model.to_api_request_json(),
            api_key=self._get_api_key(),
        )

    async def asset_operations(
        self,
        id: Optional[int] = None,
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
                "type": [operation_type.name for operation_type in operations_type] if operations_type else None,
                "status": [operation_status.name for operation_status in operations_status]
                if operations_status
                else None,
                "startTime": start_time,
                "endTime": end_time,
                "cursor": cursor,
                "limit": limit,
                "id": id if id is not None else None,
            },
        )
        return await send_get_request(
            await self.get_session(), url, List[AssetOperationModel], api_key=self._get_api_key()
        )
