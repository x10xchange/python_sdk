from decimal import Decimal
from typing import List, Optional

from x10.perpetual.accounts import AccountLeverage
from x10.perpetual.balances import BalanceModel
from x10.perpetual.fees import TradingFeeModel
from x10.perpetual.orders import OpenOrderModel, OrderSide, OrderType
from x10.perpetual.positions import PositionHistoryModel, PositionModel, PositionSide
from x10.perpetual.trades import AccountTradeModel, TradeType
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import send_get_request, send_patch_request
from x10.utils.model import EmptyModel


class AccountModule(BaseModule):
    def get_balance(self):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-balance
        """

        url = self._get_url("/user/balance")
        return send_get_request(url, BalanceModel, api_key=self._get_api_key())

    def get_positions(self, *, market_names: Optional[List[str]] = None, position_side: Optional[PositionSide] = None):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-positions
        """

        url = self._get_url("/user/positions", query={"market": market_names, "side": position_side})
        return send_get_request(url, List[PositionModel], api_key=self._get_api_key())

    def get_positions_history(
        self, *, market_names: Optional[List[str]] = None, position_side: Optional[PositionSide] = None
    ):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-positions-history
        """

        url = self._get_url("/user/positions/history", query={"market": market_names, "side": position_side})
        return send_get_request(url, List[PositionHistoryModel], api_key=self._get_api_key())

    def get_open_orders(
        self,
        *,
        market_names: Optional[List[str]] = None,
        order_type: Optional[OrderType] = None,
        order_side: Optional[OrderSide] = None,
    ):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-open-orders
        """

        url = self._get_url("/user/orders", query={"market": market_names, "type": order_type, "side": order_side})
        return send_get_request(url, List[OpenOrderModel], api_key=self._get_api_key())

    def get_orders_history(
        self,
        *,
        market_names: Optional[List[str]] = None,
        order_type: Optional[OrderType] = None,
        order_side: Optional[OrderSide] = None,
    ):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-orders-history
        """

        url = self._get_url(
            "/user/orders/history", query={"market": market_names, "type": order_type, "side": order_side}
        )
        return send_get_request(url, List[OpenOrderModel], api_key=self._get_api_key())

    def get_trades(
        self, *, market_names: List[str], trade_side: Optional[OrderSide] = None, trade_type: Optional[TradeType] = None
    ):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-trades
        """

        url = self._get_url("/user/trades", query={"market": market_names, "side": trade_side, "type": trade_type})

        return send_get_request(url, List[AccountTradeModel], api_key=self._get_api_key())

    def get_fees(self, *, market_names: List[str]):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-fees
        """

        url = self._get_url("/user/fees", query={"market": market_names})
        return send_get_request(url, List[TradingFeeModel], api_key=self._get_api_key())

    def get_leverage(self, *, market_names: List[str]):
        """
        https://x101.docs.apiary.io/#reference/0/account/get-current-leverage
        """

        url = self._get_url("/user/leverage", query={"market": market_names})
        return send_get_request(url, List[AccountLeverage], api_key=self._get_api_key())

    def update_leverage(self, *, market_name: str, leverage: Decimal):
        """
        https://x101.docs.apiary.io/#reference/0/account/update-leverage
        """

        url = self._get_url("/user/leverage")
        request_model = AccountLeverage(market=market_name, leverage=leverage)
        return send_patch_request(
            url, EmptyModel, json=request_model.to_api_request_json(), api_key=self._get_api_key()
        )
