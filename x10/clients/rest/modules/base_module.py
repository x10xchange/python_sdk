from typing import Dict, Optional

import aiohttp
from aiohttp import ClientTimeout

from x10.core.client_config import ClientConfig
from x10.core.stark_account import StarkPerpetualAccount
from x10.errors import ValidationError
from x10.utils.http import get_url


class BaseModule:
    __config: ClientConfig
    __api_key: Optional[str]
    __stark_account: Optional[StarkPerpetualAccount]
    __session: Optional[aiohttp.ClientSession]

    def __init__(
        self,
        config: ClientConfig,
        *,
        api_key: Optional[str] = None,
        stark_account: Optional[StarkPerpetualAccount] = None,
    ):
        super().__init__()

        self.__config = config
        self.__api_key = api_key
        self.__stark_account = stark_account
        self.__session = None

    def _get_url(self, path: str, *, query: Optional[Dict] = None, **path_params) -> str:
        return get_url(f"{self.__config.endpoints.api_base_url}{path}", query=query, **path_params)

    def _get_config(self) -> ClientConfig:
        return self.__config

    def _get_api_key(self):
        if not self.__api_key:
            raise ValidationError("API key is not set")

        return self.__api_key

    def _get_stark_account(self):
        if not self.__stark_account:
            raise ValidationError("Stark account is not set")

        return self.__stark_account

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
