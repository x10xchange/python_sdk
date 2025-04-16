from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import WrappedApiResponse, send_post_request
from x10.utils.model import X10BaseModel


class ClaimResponseModel(X10BaseModel):
    id: int


class TestnetModule(BaseModule):
    async def claim_testing_funds(
        self,
    ) -> WrappedApiResponse[ClaimResponseModel]:
        url = self._get_url("/user/claim")
        return await send_post_request(
            await self.get_session(),
            url,
            ClaimResponseModel,
            json={},
            api_key=self._get_api_key(),
        )
