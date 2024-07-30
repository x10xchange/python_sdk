from typing import Dict, Optional

import aiohttp

from x10.utils.http import CLIENT_TIMEOUT, get_url


class UserClient:
    __api_url: str
    __session: Optional[aiohttp.ClientSession] = None

    def __init__(self, api_url: str):
        super().__init__()
        self.__api_url = api_url

    def _get_url(self, path: str, *, query: Optional[Dict] = None, **path_params) -> str:
        return get_url(f"{self.__api_url}{path}", query=query, **path_params)

    async def get_session(self) -> aiohttp.ClientSession:
        if self.__session is None:
            created_session = aiohttp.ClientSession(timeout=CLIENT_TIMEOUT)
            self.__session = created_session

        return self.__session

    async def close_session(self):
        if self.__session:
            await self.__session.close()
            self.__session = None
