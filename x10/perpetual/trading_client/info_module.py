from datetime import datetime
from typing import List, Optional

from x10.perpetual.candles import CandleInterval, CandleModel, CandleType
from x10.perpetual.funding_rates import FundingRateModel
from x10.perpetual.markets import MarketModel, MarketStatsModel
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.date import to_epoch_millis
from x10.utils.http import send_get_request
from x10.utils.model import X10BaseModel


class _SettingsModel(X10BaseModel):
    stark_ex_contract_address: str


class InfoModule(BaseModule):
    async def get_settings(self):
        url = self._get_url("/info/settings")
        return await send_get_request(await self.get_session(), url, _SettingsModel)
