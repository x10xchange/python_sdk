from typing import Dict, List, Optional, Type

from x10.perpetual.accounts import AccountStreamDataModel
from x10.perpetual.funding_rates import FundingRateModel
from x10.perpetual.orderbooks import OrderbookUpdateModel
from x10.perpetual.stream_client.perpetual_stream_connection import (
    PerpetualStreamConnection,
    StreamMsgResponseType,
)
from x10.perpetual.trades import PublicTradeModel
from x10.utils.http import WrappedStreamResponse, get_url


class PerpetualStreamClient:
    """
    X10 Perpetual Stream Client for the X10 WebSocket v1.
    """

    __api_url: str

    def __init__(self, *, api_url: str):
        super().__init__()

        self.__api_url = api_url

    def subscribe_to_orderbooks(self, market_name: Optional[str] = None):
        """
        https://x101.docs.apiary.io/#reference/0/websocket-streams/orderbooks-stream
        """

        url = self.__get_url("/orderbooks/<market?>", market=market_name)
        return self.__connect(url, WrappedStreamResponse[OrderbookUpdateModel])

    def subscribe_to_public_trades(self, market_name: Optional[str] = None):
        """
        https://x101.docs.apiary.io/#reference/0/websocket-streams/trades-stream
        """

        url = self.__get_url("/publicTrades/<market?>", market=market_name)
        return self.__connect(url, WrappedStreamResponse[List[PublicTradeModel]])

    def subscribe_to_funding_rates(self, market_name: Optional[str] = None):
        """
        https://x101.docs.apiary.io/#reference/0/websocket-streams/funding-rates-stream
        """

        url = self.__get_url("/funding/<market?>", market=market_name)
        return self.__connect(url, WrappedStreamResponse[FundingRateModel])

    def subscribe_to_account_updates(self, api_key: str):
        """
        https://x101.docs.apiary.io/#reference/0/websocket-streams/account-updates-stream
        """

        url = self.__get_url("/account")
        return self.__connect(url, WrappedStreamResponse[AccountStreamDataModel], api_key)

    def __get_url(self, path: str, *, query: Optional[Dict[str, str | List[str]]] = None, **path_params) -> str:
        return get_url(f"{self.__api_url}{path}", query=query, **path_params)

    @staticmethod
    def __connect(
        stream_url: str,
        msg_model_class: Type[StreamMsgResponseType],
        api_key: Optional[str] = None,
    ) -> PerpetualStreamConnection[StreamMsgResponseType]:
        return PerpetualStreamConnection(stream_url, msg_model_class, api_key)
