from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import send_get_request
from x10.utils.model import X10BaseModel


class _SettingsModel(X10BaseModel):
    stark_ex_contract_address: str


class InfoModule(BaseModule):
    async def get_settings(self):
        url = self._get_url("/info/settings")
        return await send_get_request(await self.get_session(), url, _SettingsModel)
