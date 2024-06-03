from typing import Dict, Optional

import aiohttp

from x10.errors import X10Error
from x10.utils.http import CLIENT_TIMEOUT, get_url


class BaseModule:
    __api_url: str
    __api_key: Optional[str]
    __session: aiohttp.ClientSession | None = None

    def __init__(self, api_url: str, api_key: Optional[str]):
        super().__init__()

        self.__api_url = api_url
        self.__api_key = api_key

    def _get_url(self, path: str, *, query: Optional[Dict] = None, **path_params) -> str:
        return get_url(f"{self.__api_url}{path}", query=query, **path_params)

    def _get_api_key(self):
        if not self.__api_key:
            raise X10Error("API key is not set")

        return self.__api_key

    async def get_session(self) -> aiohttp.ClientSession:
        if self.__session is None:
            created_session = aiohttp.ClientSession(timeout=CLIENT_TIMEOUT)
            self.__session = created_session
        return self.__session
