from typing import Callable, Dict, Optional

import aiohttp
from aiohttp import ClientTimeout

from x10.config import Config
from x10.utils.http import get_url


class BaseModule:
    __config: Config
    __session: Optional[aiohttp.ClientSession]
    __get_l1_private_key: Callable[[], str]

    def __init__(
        self,
        config: Config,
        *,
        get_l1_private_key: Callable[[], str],
    ):
        super().__init__()

        self.__config = config
        self.__get_l1_private_key = get_l1_private_key
        self.__session = None

    def _get_url(self, path: str, *, query: Optional[Dict] = None, **path_params) -> str:
        return get_url(f"{self.__config.endpoints.api_base_url}{path}", query=query, **path_params)

    def _get_l1_private_key(self):
        return self.__get_l1_private_key()

    async def get_session(self) -> aiohttp.ClientSession:
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
