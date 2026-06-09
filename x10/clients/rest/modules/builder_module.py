from typing import List, Optional

from x10.clients.rest.modules.base_module import BaseModule
from x10.models.trade import BuilderTradeModel
from x10.utils.http import WrappedApiResponseModel, send_get_request


class BuilderModule(BaseModule):
    async def get_trades(
        self,
        cursor: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> WrappedApiResponseModel[List[BuilderTradeModel]]:
        """
        Returns the trades attributed to the authenticated builder, newest first.
        The response is paginated by trade id via the `cursor`.
        """

        url = self._get_url("/builder/trades", query={"cursor": cursor, "limit": limit})
        return await send_get_request(
            await self._get_session(), url, List[BuilderTradeModel], api_key=self._get_api_key()
        )
