from datetime import datetime
from typing import List, Optional

from x10.perpetual.funding_rates import FundingRateModel
from x10.perpetual.markets import MarketModel, MarketStatsModel
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.date import to_epoch_millis
from x10.utils.http import send_get_request


class MarketsInformationModule(BaseModule):
    def get_markets(self, *, market_names: Optional[List[str]] = None):
        """
        https://x101.docs.apiary.io/#reference/0/markets-information/get-markets
        """

        url = self._get_url("/info/markets", query={"market": market_names})
        return send_get_request(url, List[MarketModel])

    def get_market_statistics(self, *, market_name: str):
        """
        https://x101.docs.apiary.io/#reference/0/markets-information/get-market-statistics
        """

        url = self._get_url("/info/markets/<market>/stats", market=market_name)
        return send_get_request(url, MarketStatsModel)

    def get_funding_rates_history(self, *, market_name: str, start_time: datetime, end_time: datetime):
        """
        https://x101.docs.apiary.io/#reference/0/markets-information/get-funding-rates-history
        """

        url = self._get_url(
            "/info/<market>/funding",
            query={"startTime": to_epoch_millis(start_time), "endTime": to_epoch_millis(end_time)},
            market=market_name,
        )
        return send_get_request(url, List[FundingRateModel])
