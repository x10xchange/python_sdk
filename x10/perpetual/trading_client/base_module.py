from typing import Dict, Optional

from x10.errors import X10Error
from x10.utils.http import get_url


class BaseModule:
    __api_url: str
    __api_key: Optional[str]

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
