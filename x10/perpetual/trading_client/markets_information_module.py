from datetime import datetime
from typing import List, Optional

from x10.perpetual.candles import CandleInterval, CandleModel, CandleType
from x10.perpetual.funding_rates import FundingRateModel
from x10.perpetual.markets import MarketModel, MarketStatsModel
from x10.perpetual.orderbooks import OrderbookUpdateModel
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.date import to_epoch_millis
from x10.utils.http import send_get_request


class MarketsInformationModule(BaseModule):
    async def get_markets(self, *, market_names: Optional[List[str]] = None):
        """
        https://api.docs.extended.exchange/#get-markets
        """

        url = self._get_url("/info/markets", query={"market": market_names})
        return await send_get_request(await self.get_session(), url, List[MarketModel])

    async def get_market_statistics(self, *, market_name: str):
        """
        https://api.docs.extended.exchange/#get-market-statistics
        """

        url = self._get_url("/info/markets/<market>/stats", market=market_name)
        return await send_get_request(await self.get_session(), url, MarketStatsModel)

    async def get_candles_history(
        self,
        *,
        market_name: str,
        candle_type: CandleType,
        interval: CandleInterval,
        limit: Optional[int] = None,
        end_time: Optional[datetime] = None,
    ):
        """
        https://api.docs.extended.exchange/#get-candles-history
        """

        url = self._get_url(
            "/info/candles/<market>/<candle_type>",
            market=market_name,
            candle_type=candle_type,
            query={
                "interval": interval,
                "limit": limit,
                "endTime": to_epoch_millis(end_time) if end_time else None,
            },
        )
        return await send_get_request(await self.get_session(), url, List[CandleModel])

    async def get_funding_rates_history(self, *, market_name: str, start_time: datetime, end_time: datetime):
        """
        https://api.docs.extended.exchange/#get-funding-rates-history
        """

        url = self._get_url(
            "/info/<market>/funding",
            market=market_name,
            query={
                "startTime": to_epoch_millis(start_time),
                "endTime": to_epoch_millis(end_time),
            },
        )
        return await send_get_request(await self.get_session(), url, List[FundingRateModel])

    async def get_orderbook_snapshot(self, *, market_name: str):
        """
        https://api.docs.extended.exchange/#get-market-order-book
        """

        url = self._get_url("/info/markets/<market>/orderbook", market=market_name)
        return await send_get_request(await self.get_session(), url, OrderbookUpdateModel)
