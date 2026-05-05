from typing import Callable

from models.account import AccountModel
from models.base import EmptyModel
from signing.sign_api_request import sign_api_request

from x10.clients.onboarding.modules.base_module import BaseModule
from x10.errors import ValidationError
from x10.models.account import ApiKeyRequestModel, ApiKeyResponseModel
from x10.utils.http import RequestHeader, send_get_request, send_post_request


class AccountModule(BaseModule):
    async def create_api_key(self, *, account_id: int, description: str) -> str:
        request_path = "/api/v1/user/account/api-key"
        signature = sign_api_request(request_path, self._sign_message)
        headers = {
            RequestHeader.AUTH_L1_SIGNATURE: signature.value,
            RequestHeader.AUTH_L1_MESSAGE_TIME: signature.time,
            RequestHeader.AUTH_ACTIVE_ACCOUNT: str(account_id),
        }

        payload = ApiKeyRequestModel(description=description)
        url = self._get_url(self._get_endpoint_config().onboarding_url, path=request_path)
        response = await send_post_request(
            await self.get_session(),
            url,
            ApiKeyResponseModel,
            json=payload.to_api_request_json(),
            request_headers=headers,
        )
        response_data = response.data

        if response_data is None:
            raise ValidationError("No API key data returned from onboarding")

        return response_data.key

    # FIXME: Remove?
    async def get_accounts(self, *, sign: Callable[[str], dict]) -> list[AccountModel]:
        request_path = "/api/v1/user/accounts"
        signature = sign(request_path)
        headers = {
            RequestHeader.AUTH_L1_SIGNATURE: signature["signature"],
            RequestHeader.AUTH_L1_MESSAGE_TIME: signature["time"],
        }

        url = self._get_url(self._get_endpoint_config().onboarding_url, path=request_path)
        response = await send_get_request(await self.get_session(), url, list[AccountModel], request_headers=headers)

        return response.data or []
