from dataclasses import dataclass

from errors import ValidationError
from eth_account import Account
from eth_account.signers.local import LocalAccount
from models.account import AccountModel
from models.client import OnboardedClientModel
from utils.http import send_post_request

from x10.clients.onboarding.modules.base_module import BaseModule
from x10.signing.onboarding import (
    StarkKeyPair,
    get_l2_keys_from_l1_account,
    get_onboarding_payload,
)


# FIXME: Move?
@dataclass(frozen=True)
class OnBoardedAccount:
    account: AccountModel
    l2_key_pair: StarkKeyPair


class AuthModule(BaseModule):
    async def onboard_client(self, *, referral_code: str | None = None) -> OnBoardedAccount:
        signing_account: LocalAccount = Account.from_key(self._get_l1_private_key())
        l2_key_pair = get_l2_keys_from_l1_account(
            l1_account=signing_account, account_index=0, signing_domain=self.__config.signing.signing_domain
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
        pass
