from aiohttp.web_exceptions import HTTPConflict

from x10.clients.onboarding.modules.base_module import BaseModule
from x10.errors import SdkError, ValidationError
from x10.models.account import AccountModel
from x10.models.client import OnboardedClientModel
from x10.signing.onboarding import (
    OnBoardedAccount,
    get_l2_keys_from_l1_account,
    get_onboarding_payload,
    get_sub_account_creation_payload,
    sign_api_request,
)
from x10.utils.http import RequestHeader, send_post_request


class SubAccountExists(SdkError):
    pass


class AuthModule(BaseModule):
    async def onboard_client(self, *, referral_code: str | None = None) -> OnBoardedAccount:
        l2_key_pair = get_l2_keys_from_l1_account(
            account_index=0,
            account_address=self._get_account_address(),
            signing_domain=self._get_signing_domain(),
            sign_message=self._sign_message,
        )
        payload = get_onboarding_payload(
            account_address=self._get_account_address(),
            signing_domain=self._get_signing_domain(),
            key_pair=l2_key_pair,
            referral_code=referral_code,
            host=self._get_endpoint_config().onboarding_url,
            sign_message=self._sign_message,
        )

        url = self._get_url("/auth/onboard")
        onboarding_response = await send_post_request(
            await self._get_session(), url, OnboardedClientModel, json=payload.to_json()
        )

        onboarded_client = onboarding_response.data

        if onboarded_client is None:
            raise ValidationError("No account data returned from onboarding")

        return OnBoardedAccount(account=onboarded_client.default_account, l2_key_pair=l2_key_pair)

    async def onboard_subaccount(self, *, account_index: int, description: str):
        request_path = "/auth/onboard/subaccount"
        signature = sign_api_request(request_path, self._sign_message)
        headers: dict[str, str] = {
            RequestHeader.AUTH_L1_SIGNATURE: signature.value,
            RequestHeader.AUTH_L1_MESSAGE_TIME: signature.time,
        }

        key_pair = get_l2_keys_from_l1_account(
            account_index=account_index,
            account_address=self._get_account_address(),
            signing_domain=self._get_signing_domain(),
            sign_message=self._sign_message,
        )
        payload = get_sub_account_creation_payload(
            account_index=account_index,
            l1_address=self._get_account_address(),
            key_pair=key_pair,
            description=description,
            host=self._get_endpoint_config().onboarding_url,
        )
        url = self._get_url(request_path)

        try:
            onboarding_response = await send_post_request(
                await self._get_session(),
                url,
                AccountModel,
                json=payload.to_json(),
                request_headers=headers,
                response_code_to_exception={HTTPConflict.status_code: SubAccountExists},
            )
            onboarded_account = onboarding_response.data
        except SubAccountExists:
            raise ValidationError("Subaccount already exists but no account data returned from onboarding")

        if onboarded_account is None:
            raise ValidationError("No account data returned from onboarding")

        return OnBoardedAccount(account=onboarded_account, l2_key_pair=key_pair)
