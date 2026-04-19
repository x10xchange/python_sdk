from decimal import Decimal
from typing import List

from x10.models.asset import AssetModel
from x10.models.base import X10BaseModel
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import send_get_request


class _SettingsModel(X10BaseModel):
    stark_ex_contract_address: str


class InfoModule(BaseModule):
    async def get_settings(self):
        url = self._get_url("/info/settings")
        return await send_get_request(await self.get_session(), url, _SettingsModel)

    async def get_assets(self):
        url = self._get_url("/info/assets")
        return await send_get_request(await self.get_session(), url, List[AssetModel])

    async def get_assets_dict(self):
        assets = await self.get_assets()
        return {asset.name: asset for asset in assets.data}

    async def get_asset_price(self, *, asset_name: str):
        url = self._get_url("/info/assets/<asset_name>/price", asset_name=asset_name)
        return await send_get_request(await self.get_session(), url, Decimal)
