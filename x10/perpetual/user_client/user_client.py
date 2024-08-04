import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount

from x10.perpetual.accounts import AccountModel, ApiKeyRequestModel, ApiKeyResponseModel
from x10.perpetual.configuration import TESTNET_CONFIG, EndpointConfig
from x10.perpetual.user_client.onboarding import (
    OnboardedClientModel,
    StarkKeyPair,
    get_l2_keys_from_l1_account,
    get_onboarding_payload,
    get_sub_account_creation_payload,
)
from x10.utils.http import (  # WrappedApiResponse,; send_get_request,; send_patch_request,
    CLIENT_TIMEOUT,
    get_url,
    send_get_request,
    send_post_request,
)

L1_AUTH_SIGNATURE_HEADER = "L1_SIGNATURE"
L1_MESSAGE_TIME_HEADER = "L1_MESSAGE_TIME"
ACTIVE_ACCOUNT_HEADER = "X-X10-ACTIVE-ACCOUNT"


class SubAccountExists(Exception):
    pass


@dataclass
class OnBoardedAccount:
    account: AccountModel
    l2_key_pair: StarkKeyPair


class UserClient:
    __endpoint_config: EndpointConfig
    __l1_private_key: str
    __session: Optional[aiohttp.ClientSession] = None

    def __init__(
        self,
        endpoint_config: EndpointConfig,
        l1_private_key: str,
    ):
        super().__init__()
        self.__endpoint_config = endpoint_config
        self.__l1_private_key = l1_private_key

    def _get_url(self, base_url: str, path: str, *, query: Optional[Dict] = None, **path_params) -> str:
        return get_url(f"{base_url}{path}", query=query, **path_params)

    async def get_session(self) -> aiohttp.ClientSession:
        if self.__session is None:
            created_session = aiohttp.ClientSession(timeout=CLIENT_TIMEOUT)
            self.__session = created_session

        return self.__session

    async def close_session(self):
        if self.__session:
            await self.__session.close()
            self.__session = None

    async def onboard(self, referral_code: Optional[str] = None):
        signing_account: LocalAccount = Account.from_key(self.__l1_private_key)
        key_pair = get_l2_keys_from_l1_account(
            l1_account=signing_account, account_index=0, signing_domain=self.__endpoint_config.signing_domain
        )
        payload = get_onboarding_payload(
            signing_account,
            signing_domain=self.__endpoint_config.signing_domain,
            key_pair=key_pair,
            referral_code=referral_code,
        )
        url = self._get_url(self.__endpoint_config.onboarding_url, path="/auth/onboard")
        onboarding_response = await send_post_request(
            await self.get_session(), url, OnboardedClientModel, json=payload.to_json()
        )

        onboarded_client = onboarding_response.data
        if onboarded_client is None:
            raise ValueError("No account data returned from onboarding")

        return OnBoardedAccount(account=onboarded_client.default_account, l2_key_pair=key_pair)

    async def onboard_subaccount(self, account_index: int, description: str | None = None):
        request_path = "/auth/onboard/subaccount"
        if description is None:
            description = f"Subaccount {account_index}"

        signing_account: LocalAccount = Account.from_key(self.__l1_private_key)
        time = datetime.now(timezone.utc)
        auth_time_string = time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        l1_message = f"{request_path}@{auth_time_string}".encode(encoding="utf-8")
        signable_message = encode_defunct(l1_message)
        l1_signature = signing_account.sign_message(signable_message)
        key_pair = get_l2_keys_from_l1_account(
            l1_account=signing_account,
            account_index=account_index,
            signing_domain=self.__endpoint_config.signing_domain,
        )
        payload = get_sub_account_creation_payload(
            account_index=account_index,
            l1_address=signing_account.address,
            key_pair=key_pair,
            description=description,
        )
        headers = {
            L1_AUTH_SIGNATURE_HEADER: l1_signature.signature.hex(),
            L1_MESSAGE_TIME_HEADER: auth_time_string,
        }
        url = self._get_url(self.__endpoint_config.onboarding_url, path=request_path)
        onboarding_response = await send_post_request(
            await self.get_session(),
            url,
            AccountModel,
            json=payload.to_json(),
            request_headers=headers,
            response_code_to_exception={409: SubAccountExists},
        )

        onboarded_account = onboarding_response.data
        if onboarded_account is None:
            raise ValueError("No account data returned from onboarding")

        return OnBoardedAccount(account=onboarded_account, l2_key_pair=key_pair)

    async def get_accounts(self) -> List[OnBoardedAccount]:
        request_path = "/api/v1/user/accounts"
        signing_account: LocalAccount = Account.from_key(self.__l1_private_key)
        time = datetime.now(timezone.utc)
        auth_time_string = time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        l1_message = f"{request_path}@{auth_time_string}".encode(encoding="utf-8")
        signable_message = encode_defunct(l1_message)
        l1_signature = signing_account.sign_message(signable_message)
        headers = {
            L1_AUTH_SIGNATURE_HEADER: l1_signature.signature.hex(),
            L1_MESSAGE_TIME_HEADER: auth_time_string,
        }
        url = self._get_url(self.__endpoint_config.onboarding_url, path=request_path)
        response = await send_get_request(await self.get_session(), url, List[AccountModel], request_headers=headers)
        accounts = response.data or []

        return [
            OnBoardedAccount(
                account=account,
                l2_key_pair=get_l2_keys_from_l1_account(
                    l1_account=signing_account,
                    account_index=account.account_index,
                    signing_domain=self.__endpoint_config.signing_domain,
                ),
            )
            for account in accounts
        ]

    async def create_account_api_key(self, account: AccountModel, description: str | None) -> str:
        request_path = "/api/v1/user/account/api-key"
        if description is None:
            description = "trading api key for account {}".format(account.id)

        signing_account: LocalAccount = Account.from_key(self.__l1_private_key)
        time = datetime.now(timezone.utc)
        auth_time_string = time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        l1_message = f"{request_path}@{auth_time_string}".encode(encoding="utf-8")
        signable_message = encode_defunct(l1_message)
        l1_signature = signing_account.sign_message(signable_message)
        headers = {
            L1_AUTH_SIGNATURE_HEADER: l1_signature.signature.hex(),
            L1_MESSAGE_TIME_HEADER: auth_time_string,
            ACTIVE_ACCOUNT_HEADER: str(account.id),
        }
        url = self._get_url(self.__endpoint_config.onboarding_url, path=request_path)
        request = ApiKeyRequestModel(description=description)
        response = await send_post_request(
            await self.get_session(),
            url,
            ApiKeyResponseModel,
            json=request.to_api_request_json(),
            request_headers=headers,
        )
        response_data = response.data
        if response_data is None:
            raise ValueError("No API key data returned from onboarding")
        return response_data.key


async def do_something():
    eth_account = Account.from_key("0x179edf14fb885920e1dbb4311a102aa972fcb2e8c3e6128a7718867d19ea3338")
    user_client = UserClient(endpoint_config=TESTNET_CONFIG, l1_private_key=eth_account.key.hex())
    onboarded_user = await user_client.onboard()
    print("User onboarded, default account:")
    print(f"\tvault: {onboarded_user.account.l2_vault}")
    print(f"\tL2PublicKey: {onboarded_user.l2_key_pair.public_hex}")
    print(f"\tL2PrivateKey: {onboarded_user.l2_key_pair.private_hex}")
    print("All accounts: {}".format(await user_client.get_accounts()))
    api_key = await user_client.create_account_api_key(onboarded_user.account, "trading key test")
    print(api_key)


asyncio.run(do_something())
