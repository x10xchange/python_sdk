from typing import List, Optional

import tenacity
from x10.perpetual.assets import AssetOperationModel, AssetOperationStatus
from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.trading_client.account_module import AccountModule
from x10.perpetual.trading_client.base_module import BaseModule
from x10.utils.http import WrappedApiResponse, send_post_request
from x10.utils.model import X10BaseModel


class ClaimResponseModel(X10BaseModel):
    id: int


class TestnetModule(BaseModule):
    def __init__(
        self,
        endpoint_config: EndpointConfig,
        api_key: Optional[str] = None,
        account_module: Optional[AccountModule] = None,
    ):
        super().__init__(endpoint_config, api_key=api_key)
        self._account_module = account_module

    async def claim_testing_funds(
        self,
    ) -> WrappedApiResponse[ClaimResponseModel]:
        url = self._get_url("/user/claim")
        resp = await send_post_request(
            await self.get_session(),
            url,
            ClaimResponseModel,
            json={},
            api_key=self._get_api_key(),
        )

        if resp.error:
            return resp
        if self._account_module and resp.data:
            account_module = self._account_module
            claim_to_check = resp.data.id

            @tenacity.retry(
                stop=tenacity.stop_after_delay(10),
                wait=tenacity.wait_fixed(1),
                retry=tenacity.retry_if_result(
                    lambda asset_ops: not (
                        asset_ops
                        and len(asset_ops) > 0
                        and (
                            asset_ops[0].status
                            == AssetOperationStatus.COMPLETED.value
                            # or asset_ops[0].status == AssetOperationStatus.REJECTED.value
                        )
                    )
                ),
                reraise=False,
            )
            async def wait_for_claim_to_complete() -> List[AssetOperationModel]:
                asset_ops = (await account_module.asset_operations(id=claim_to_check)).data
                return asset_ops or []

            try:
                await wait_for_claim_to_complete()
            except tenacity.RetryError:
                pass
        return resp
