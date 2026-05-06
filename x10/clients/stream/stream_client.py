from typing import Dict, List, Optional, Type

from x10.clients.stream.stream_connection import StreamConnection, StreamMsgResponseType
from x10.models.account import AccountStreamDataModel
from x10.models.candle import CandleInterval, CandleModel, CandleType
from x10.models.funding_rate import FundingRateModel
from x10.models.http import WrappedStreamResponseModel
from x10.models.orderbook import OrderbookUpdateModel
from x10.models.trade import PublicTradeModel
from x10.utils.http import UrlQueryParam, get_url


class StreamClient:
    """
    Extended Stream (WebSocket) Client.
    """

    __api_url: str

    def __init__(self, *, api_url: str):
        super().__init__()

        self.__api_url = api_url

    def subscribe_to_orderbooks(self, market_name: Optional[str] = None, depth: int | None = None):
        """
        https://api.docs.extended.exchange/#orderbooks-stream
        """

        url = self.__get_url("/orderbooks/<market?>" + (f"?depth={depth}" if depth else ""), market=market_name)
        return self.__connect(url, WrappedStreamResponseModel[OrderbookUpdateModel])

    def subscribe_to_public_trades(self, market_name: Optional[str] = None):
        """
        https://api.docs.extended.exchange/#trades-stream
        """

        url = self.__get_url("/publicTrades/<market?>", market=market_name)
        return self.__connect(url, WrappedStreamResponseModel[List[PublicTradeModel]])

    def subscribe_to_funding_rates(self, market_name: Optional[str] = None):
        """
        https://api.docs.extended.exchange/#funding-rates-stream
        """

        url = self.__get_url("/funding/<market?>", market=market_name)
        return self.__connect(url, WrappedStreamResponseModel[FundingRateModel])

    def subscribe_to_candles(self, market_name: str, candle_type: CandleType, interval: CandleInterval):
        """
        https://api.docs.extended.exchange/#candles-stream
        """

        url = self.__get_url(
            "/candles/<market>/<candle_type>",
            market=market_name,
            candle_type=candle_type,
            query={
                "interval": interval,
            },
        )
        return self.__connect(url, WrappedStreamResponseModel[List[CandleModel]])

    def subscribe_to_account_updates(self, api_key: str):
        """
        https://api.docs.extended.exchange/#account-updates-stream
        """

        url = self.__get_url("/account")
        return self.__connect(url, WrappedStreamResponseModel[AccountStreamDataModel], api_key)

    def __get_url(self, path: str, *, query: Optional[Dict[str, UrlQueryParam]] = None, **path_params) -> str:
        return get_url(f"{self.__api_url}{path}", query=query, **path_params)

    @staticmethod
    def __connect(
        stream_url: str,
        msg_model_class: Type[StreamMsgResponseType],
        api_key: Optional[str] = None,
    ) -> StreamConnection[StreamMsgResponseType]:
        return StreamConnection(stream_url, msg_model_class, api_key)
