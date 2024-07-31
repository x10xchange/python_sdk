from typing import List

from x10.perpetual.accounts import AccountModel
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import WrappedApiResponse, send_get_request


class UserModule(BaseModule):
    async def get_accounts(self) -> WrappedApiResponse[List[AccountModel]]:
        url = self._get_url("/user/accounts")
        return await send_get_request(
            await self.get_session(),
            url,
            List[AccountModel],
            api_key=self._get_api_key(),
        )
