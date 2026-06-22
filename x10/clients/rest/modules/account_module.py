from decimal import Decimal
from typing import List, Optional

from x10.clients.rest.modules.base_module import BaseModule
from x10.errors import ValidationError
from x10.models.account import AccountLeverageModel, AccountModel
from x10.models.asset import (
    AssetOperationModel,
    AssetOperationStatus,
    AssetOperationType,
)
from x10.models.balance import BalanceModel, SpotBalanceModel
from x10.models.base import EmptyModel
from x10.models.bridge import BridgesConfigModel, QuoteModel
from x10.models.client import ClientModel
from x10.models.fee import TradingFeeModel
from x10.models.order import OpenOrderModel, OrderSide, OrderSortBy, OrderType
from x10.models.position import PositionHistoryModel, PositionModel, PositionSide
from x10.models.trade import AccountTradeModel, TradeType
from x10.models.transfer import TransferResponseModel
from x10.signing.transfer_object import create_transfer_object
from x10.signing.withdrawal_object import create_withdrawal_object
from x10.utils.http import (
    WrappedApiResponseModel,
    send_get_request,
    send_patch_request,
    send_post_request,
)


class AccountModule(BaseModule):
    async def get_client(self) -> WrappedApiResponseModel[ClientModel]:
        url = self._get_url("/user/client/info")
        return await send_get_request(await self._get_session(), url, ClientModel, api_key=self._get_api_key())

    async def get_accounts(self) -> WrappedApiResponseModel[list[AccountModel]]:
        url = self._get_url("/user/accounts")
        return await send_get_request(await self._get_session(), url, list[AccountModel], api_key=self._get_api_key())

    async def get_account(self) -> WrappedApiResponseModel[AccountModel]:
        url = self._get_url("/user/account/info")
        return await send_get_request(await self._get_session(), url, AccountModel, api_key=self._get_api_key())

    async def get_balance(self) -> WrappedApiResponseModel[BalanceModel]:
        """
        Fetches the balance of the user's account.
        https://api.docs.extended.exchange/#get-balance
        """

        url = self._get_url("/user/balance")
        return await send_get_request(await self._get_session(), url, BalanceModel, api_key=self._get_api_key())

    async def get_positions(
        self, *, market_names: Optional[List[str]] = None, position_side: Optional[PositionSide] = None
    ) -> WrappedApiResponseModel[List[PositionModel]]:
        """
        Fetches the current positions of the user's account.
        Can filter the positions based on market names and position side.
        https://api.docs.extended.exchange/#get-positions
        """

        url = self._get_url("/user/positions", query={"market": market_names, "side": position_side})
        return await send_get_request(await self._get_session(), url, List[PositionModel], api_key=self._get_api_key())

    async def get_positions_history(
        self,
        market_names: Optional[List[str]] = None,
        position_side: Optional[PositionSide] = None,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> WrappedApiResponseModel[List[PositionHistoryModel]]:
        """
        Fetches the historical positions of the user's account.
        Can filter the positions based on market names and position side.
        https://api.docs.extended.exchange/#get-positions-history
        """

        url = self._get_url(
            "/user/positions/history",
            query={"market": market_names, "side": position_side, "cursor": cursor, "limit": limit},
        )
        return await send_get_request(
            await self._get_session(), url, List[PositionHistoryModel], api_key=self._get_api_key()
        )

    async def get_open_orders(
        self,
        market_names: Optional[List[str]] = None,
        order_type: Optional[OrderType] = None,
        order_side: Optional[OrderSide] = None,
    ) -> WrappedApiResponseModel[List[OpenOrderModel]]:
        """
        Fetches the open orders of the user's account.
        Can filter the orders based on market names, order type, and order side.
        https://api.docs.extended.exchange/#get-open-orders
        """

        url = self._get_url(
            "/user/orders",
            query={"market": market_names, "type": order_type, "side": order_side},
        )
        return await send_get_request(await self._get_session(), url, List[OpenOrderModel], api_key=self._get_api_key())

    async def get_orders_history(
        self,
        market_names: Optional[List[str]] = None,
        order_type: Optional[OrderType] = None,
        order_side: Optional[OrderSide] = None,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[OrderSortBy] = None,
    ) -> WrappedApiResponseModel[List[OpenOrderModel]]:
        """
        Fetches the historical orders of the user's account.
        Can filter the orders based on market names, order type, and order side.
        https://api.docs.extended.exchange/#get-orders-history
        """

        url = self._get_url(
            "/user/orders/history",
            query={
                "market": market_names,
                "type": order_type,
                "side": order_side,
                "cursor": cursor,
                "limit": limit,
                "sort": sort,
            },
        )
        return await send_get_request(await self._get_session(), url, List[OpenOrderModel], api_key=self._get_api_key())

    async def get_order_by_id(self, order_id: int) -> WrappedApiResponseModel[OpenOrderModel]:
        """
        https://api.docs.extended.exchange/#get-order-by-id
        """

        url = self._get_url("/user/orders/<order_id>", order_id=order_id)

        return await send_get_request(await self._get_session(), url, OpenOrderModel, api_key=self._get_api_key())

    async def get_order_by_external_id(self, external_id: str) -> WrappedApiResponseModel[list[OpenOrderModel]]:
        """
        https://api.docs.extended.exchange/#get-order-by-external-id
        """

        url = self._get_url("/user/orders/external/<external_id>", external_id=external_id)

        return await send_get_request(await self._get_session(), url, list[OpenOrderModel], api_key=self._get_api_key())

    async def get_spot_balances(self) -> WrappedApiResponseModel[List[SpotBalanceModel]]:
        """
        https://api.docs.extended.exchange/#get-spot-balance
        """

        url = self._get_url("/user/spot/balances")
        return await send_get_request(
            await self._get_session(), url, List[SpotBalanceModel], api_key=self._get_api_key()
        )

    async def get_trades(
        self,
        market_names: Optional[List[str]] = None,
        trade_side: Optional[OrderSide] = None,
        trade_type: Optional[TradeType] = None,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> WrappedApiResponseModel[List[AccountTradeModel]]:
        """
        Fetches the trades of the user's account.
        Can filter the trades based on market names, trade side, and trade type.
        https://api.docs.extended.exchange/#get-trades
        """

        url = self._get_url(
            "/user/trades",
            query={"market": market_names, "side": trade_side, "type": trade_type, "cursor": cursor, "limit": limit},
        )

        return await send_get_request(
            await self._get_session(), url, List[AccountTradeModel], api_key=self._get_api_key()
        )

    async def get_fees(
        self, *, market_names: Optional[List[str]] = None, builder_id: Optional[int] = None
    ) -> WrappedApiResponseModel[List[TradingFeeModel]]:
        """
        Fetches the trading fees for the specified markets.
        https://api.docs.extended.exchange/#get-fees
        """

        url = self._get_url(
            "/user/fees",
            query={
                "market": market_names,
                "builderId": builder_id,
            },
        )
        return await send_get_request(
            await self._get_session(), url, List[TradingFeeModel], api_key=self._get_api_key()
        )

    async def get_leverage(
        self, market_names: Optional[List[str]] = None
    ) -> WrappedApiResponseModel[List[AccountLeverageModel]]:
        """
        Fetches the leverage for the specified markets.
        https://api.docs.extended.exchange/#get-current-leverage
        """

        url = self._get_url("/user/leverage", query={"market": market_names})
        return await send_get_request(
            await self._get_session(), url, List[AccountLeverageModel], api_key=self._get_api_key()
        )

    async def update_leverage(self, market_name: str, leverage: Decimal) -> WrappedApiResponseModel[EmptyModel]:
        """
        Updates the leverage for a specific market.
        https://api.docs.extended.exchange/#update-leverage
        """

        url = self._get_url("/user/leverage")
        request_model = AccountLeverageModel(market=market_name, leverage=leverage)
        return await send_patch_request(
            await self._get_session(),
            url,
            EmptyModel,
            json=request_model.to_api_request_json(),
            api_key=self._get_api_key(),
        )

    async def get_bridge_config(self) -> WrappedApiResponseModel[BridgesConfigModel]:
        url = self._get_url("/user/bridge/config")
        return await send_get_request(await self._get_session(), url, BridgesConfigModel, api_key=self._get_api_key())

    async def get_bridge_quote(
        self, chain_in: str, chain_out: str, amount: Decimal
    ) -> WrappedApiResponseModel[QuoteModel]:
        url = self._get_url(
            "/user/bridge/quote",
            query={
                "chainIn": chain_in,
                "chainOut": chain_out,
                "amount": amount,
            },
        )
        return await send_get_request(await self._get_session(), url, QuoteModel, api_key=self._get_api_key())

    async def commit_bridge_quote(self, id: str):
        url = self._get_url(
            "/user/bridge/quote",
            query={
                "id": id,
            },
        )
        await send_post_request(await self._get_session(), url, EmptyModel, api_key=self._get_api_key())

    async def transfer(
        self,
        *,
        to_vault: int,
        to_l2_public_key: int | str,
        amount: Decimal,
        asset_id: str,
        nonce: int | None = None,
    ) -> WrappedApiResponseModel[TransferResponseModel]:
        from_vault = self._get_stark_account().vault
        url = self._get_url("/user/transfer/onchain")

        if isinstance(to_l2_public_key, str):
            to_l2_public_key = int(to_l2_public_key, base=16)

        request_model = create_transfer_object(
            from_vault=from_vault,
            to_vault=to_vault,
            to_l2_public_key=to_l2_public_key,
            amount=amount,
            asset_id=asset_id,
            config=self._get_config(),
            stark_account=self._get_stark_account(),
            nonce=nonce,
        )

        return await send_post_request(
            await self._get_session(),
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
    ) -> WrappedApiResponseModel[int]:
        url = self._get_url("/user/withdrawal")
        account = (await self.get_account()).data

        if account is None:
            raise ValidationError("Account not found")

        if quote_id is None and chain_id != "STRK":
            raise ValidationError("quote_id is required for EVM withdrawals")

        async def get_recipient_stark_address() -> str:
            if stark_address:
                return stark_address

            if chain_id == "STRK":
                client = (await self.get_client()).data

                if client is None:
                    raise ValidationError("Client not found")

                if client.starknet_wallet_address is None:
                    raise ValidationError(
                        "Client does not have attached `starknet_wallet_address`. Can't determine withdrawal address."
                    )

                return client.starknet_wallet_address

            if account.bridge_starknet_address is None:
                raise ValidationError("Account `bridge_starknet_address` not found")

            return account.bridge_starknet_address

        recipient_stark_address = await get_recipient_stark_address()
        request_model = create_withdrawal_object(
            amount=amount,
            recipient_stark_address=recipient_stark_address,
            stark_account=self._get_stark_account(),
            config=self._get_config(),
            account_id=account.id,
            chain_id=chain_id,
            quote_id=quote_id,
            nonce=nonce,
        )
        return await send_post_request(
            await self._get_session(),
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
    ) -> WrappedApiResponseModel[List[AssetOperationModel]]:
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
            await self._get_session(), url, List[AssetOperationModel], api_key=self._get_api_key()
        )
