from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from x10.clients.rest.modules.base_module import BaseModule
from x10.models.asset import AssetModel
from x10.models.candle import CandleInterval, CandleModel, CandleType
from x10.models.funding_rate import FundingRateModel
from x10.models.market import MarketModel, MarketStatsModel
from x10.models.orderbook import OrderbookUpdateModel
from x10.models.settings import SettingsModel
from x10.utils.date import to_epoch_millis
from x10.utils.http import send_get_request


class InfoModule(BaseModule):
    async def get_settings(self):
        url = self._get_url("/info/settings")
        return await send_get_request(await self._get_session(), url, SettingsModel)

    async def get_assets(self):
        url = self._get_url("/info/assets")
        return await send_get_request(await self._get_session(), url, List[AssetModel])

    async def get_assets_dict(self):
        assets = await self.get_assets()
        return {asset.name: asset for asset in assets.data}

    async def get_asset_price(self, *, asset_name: str):
        url = self._get_url("/info/assets/<asset_name>/price", asset_name=asset_name)
        return await send_get_request(await self._get_session(), url, Decimal)

    async def get_markets(self, *, market_names: Optional[List[str]] = None):
        """
        https://api.docs.extended.exchange/#get-markets
        """

        url = self._get_url("/info/markets", query={"market": market_names})
        return await send_get_request(await self._get_session(), url, List[MarketModel])

    async def get_markets_dict(self):
        markets = await self.get_markets()
        return {m.name: m for m in markets.data}

    async def get_market_statistics(self, *, market_name: str):
        """
        https://api.docs.extended.exchange/#get-market-statistics
        """

        url = self._get_url("/info/markets/<market>/stats", market=market_name)
        return await send_get_request(await self._get_session(), url, MarketStatsModel)

    async def get_candles_history(
        self,
        *,
        market_name: str,
        candle_type: CandleType,
        interval: CandleInterval,
        limit: int,
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
        return await send_get_request(await self._get_session(), url, List[CandleModel])

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
        return await send_get_request(await self._get_session(), url, List[FundingRateModel])

    async def get_orderbook_snapshot(self, *, market_name: str):
        """
        https://api.docs.extended.exchange/#get-market-order-book
        """

        url = self._get_url("/info/markets/<market>/orderbook", market=market_name)
        return await send_get_request(await self._get_session(), url, OrderbookUpdateModel)
