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
        """
        Handles the onboarding process of a user. It generates an L2 key pair from
        the user's L1 Ethereum account, creates an onboarding payload, and sends it
        to the onboarding endpoint. Upon successful onboarding, it returns an `OnBoardedAccount`
        object containing the default account and the L2 key pair.
        """

        l2_key_pair = get_l2_keys_from_l1_account(
            account_index=0,
            account_address=self._get_account_address(),
            signing_domain=self._get_config().signing.signing_domain,
            sign_message=self._sign_message,
        )
        payload = get_onboarding_payload(
            account_address=self._get_account_address(),
            signing_domain=self._get_config().signing.signing_domain,
            key_pair=l2_key_pair,
            referral_code=referral_code,
            host=self._get_config().endpoints.onboarding_url,
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
        """
        This method onboards a subaccount associated with the user's main account.
        It allows you to specify an `account_index` and an optional description.
        If a subaccount with the given index already exists, it raises a `ValidationError` exception.
        Otherwise, it creates a new subaccount and returns an `OnBoardedAccount` object with
        the subaccount details and the associated L2 key pair.
        """

        request_path = "/auth/onboard/subaccount"
        signature = sign_api_request(request_path, self._sign_message)
        headers: dict[str, str] = {
            RequestHeader.AUTH_L1_SIGNATURE: signature.value,
            RequestHeader.AUTH_L1_MESSAGE_TIME: signature.time,
        }

        key_pair = get_l2_keys_from_l1_account(
            account_index=account_index,
            account_address=self._get_account_address(),
            signing_domain=self._get_config().signing.signing_domain,
            sign_message=self._sign_message,
        )
        payload = get_sub_account_creation_payload(
            account_index=account_index,
            l1_address=self._get_account_address(),
            key_pair=key_pair,
            description=description,
            host=self._get_config().endpoints.onboarding_url,
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
            raise ValidationError("Subaccount already exists")

        if onboarded_account is None:
            raise ValidationError("No account data returned from onboarding")

        return OnBoardedAccount(account=onboarded_account, l2_key_pair=key_pair)
