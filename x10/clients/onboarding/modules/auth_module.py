from dataclasses import dataclass

from errors import ValidationError
from eth_account import Account
from eth_account.signers.local import LocalAccount
from models.account import AccountModel
from models.client import OnboardedClientModel
from utils.http import send_post_request

from x10.clients.onboarding.modules.base_module import BaseModule
from x10.signing.onboarding import (
    OnBoardedAccount,
    StarkKeyPair,
    get_l2_keys_from_l1_account,
    get_onboarding_payload,
)


class AuthModule(BaseModule):
    async def onboard_client(self, *, referral_code: str | None = None) -> OnBoardedAccount:
        signing_account: LocalAccount = Account.from_key(self._get_l1_private_key())
        l2_key_pair = get_l2_keys_from_l1_account(
            account_index=0,
            account_address=signing_account.address,
            signing_domain=self.__config.signing.signing_domain,
            sign_message=self._sign_message,
        )
        payload = get_onboarding_payload(
            signing_account,
            signing_domain=self.__config.signing.signing_domain,
            key_pair=l2_key_pair,
            referral_code=referral_code,
            host=self._get_endpoint_config().onboarding_url,
        )

        url = self._get_url(self._get_endpoint_config().onboarding_url, path="/auth/onboard")
        onboarding_response = await send_post_request(
            await self.get_session(), url, OnboardedClientModel, json=payload.to_json()
        )

        onboarded_client = onboarding_response.data
        if onboarded_client is None:
            raise ValidationError("No account data returned from onboarding")

        return OnBoardedAccount(account=onboarded_client.default_account, l2_key_pair=l2_key_pair)

    async def onboard_subaccount(self):
        request_path = "/auth/onboard/subaccount"
        if description is None:
            description = f"Subaccount {account_index}"

        # signing_account: LocalAccount = Account.from_key(self.__l1_private_key())
        time = datetime.now(timezone.utc)
        auth_time_string = time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        l1_message = f"{request_path}@{auth_time_string}".encode(encoding="utf-8")
        signable_message = encode_defunct(l1_message)
        l1_signature = signing_account.sign_message(signable_message)
        key_pair = get_l2_keys_from_l1_account(
            l1_account=signing_account,
            account_index=account_index,
            signing_domain=self.__config.signing.signing_domain,
        )
        payload = get_sub_account_creation_payload(
            account_index=account_index,
            l1_address=signing_account.address,
            key_pair=key_pair,
            description=description,
            host=self._get_endpoint_config().onboarding_url,
        )
        headers = {
            L1_AUTH_SIGNATURE_HEADER: l1_signature.signature.hex(),
            L1_MESSAGE_TIME_HEADER: auth_time_string,
        }
        url = self._get_url(self._get_endpoint_config().onboarding_url, path=request_path)

        try:
            onboarding_response = await send_post_request(
                await self.get_session(),
                url,
                AccountModel,
                json=payload.to_json(),
                request_headers=headers,
                response_code_to_exception={HTTPConflict.status_code: SubAccountExists},
            )
            onboarded_account = onboarding_response.data
        except SubAccountExists:
            # FIXME: Remove???
            client_accounts = await self.get_accounts()
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
            account_with_index = [
                account for account in client_accounts if account.account.account_index == account_index
            ]
            if not account_with_index:
                raise ValidationError("Subaccount already exists but not found in client accounts")
            onboarded_account = account_with_index[0].account
        if onboarded_account is None:
            raise ValidationError("No account data returned from onboarding")
        return OnBoardedAccount(account=onboarded_account, l2_key_pair=key_pair)
