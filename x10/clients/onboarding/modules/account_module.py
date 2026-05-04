from typing import Callable

from models.account import AccountModel
from models.base import EmptyModel

from x10.clients.onboarding.modules.base_module import BaseModule
from x10.errors import ValidationError
from x10.models.account import ApiKeyRequestModel, ApiKeyResponseModel
from x10.utils.http import RequestHeader, send_get_request, send_post_request


class AccountModule(BaseModule):
    async def create_api_key(self, *, account_id: int, description: str, sign: Callable[[str], dict]) -> str:
        request_path = "/api/v1/user/account/api-key"
        signature = sign(request_path)
        headers = {
            RequestHeader.AUTH_L1_SIGNATURE: signature["signature"],
            RequestHeader.AUTH_L1_MESSAGE_TIME: signature["time"],
            RequestHeader.AUTH_ACTIVE_ACCOUNT: str(account_id),
        }

        url = self._get_url(self._get_endpoint_config().onboarding_url, path=request_path)
        payload = ApiKeyRequestModel(description=description)
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

        # return [
        #     OnBoardedAccount(
        #         account=account,
        #         l2_key_pair=get_l2_keys_from_l1_account(
        #             l1_account=signing_account,
        #             account_index=account.account_index,
        #             signing_domain=self.__config.signing.signing_domain,
        #         ),
        #     )
        #     for account in accounts
        # ]
