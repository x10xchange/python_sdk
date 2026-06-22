from typing import Dict, Optional

import aiohttp
from aiohttp import ClientTimeout
from eth_account.messages import SignableMessage
from eth_typing import ChecksumAddress

from x10.core.client_config import ClientConfig
from x10.signing.onboarding import SignMessageCallback
from x10.utils.http import get_url


class BaseModule:
    __config: ClientConfig
    __account_address: ChecksumAddress
    __sign_message: SignMessageCallback
    __session: Optional[aiohttp.ClientSession]

    def __init__(self, config: ClientConfig, *, account_address: ChecksumAddress, sign_message: SignMessageCallback):
        super().__init__()

        self.__config = config
        self.__account_address = account_address
        self.__sign_message = sign_message
        self.__session = None

    def _get_url(self, path: str, *, query: Optional[Dict] = None, **path_params) -> str:
        return get_url(f"{self.__config.endpoints.onboarding_url}{path}", query=query, **path_params)

    def _get_config(self) -> ClientConfig:
        return self.__config

    def _get_account_address(self) -> ChecksumAddress:
        return self.__account_address

    def _sign_message(self, msg: SignableMessage) -> str:
        return self.__sign_message(msg)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.__session is None:
            created_session = aiohttp.ClientSession(
                timeout=ClientTimeout(total=self.__config.defaults.request_timeout_seconds)
            )
            self.__session = created_session

        return self.__session

    async def close_session(self):
        if self.__session:
            await self.__session.close()
            self.__session = None
