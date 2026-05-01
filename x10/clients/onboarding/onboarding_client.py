from typing import Callable

from x10.clients.onboarding.modules.account_module import AccountModule
from x10.clients.onboarding.modules.auth_module import AuthModule
from x10.config import Config

class OnboardingClient:
    __config: Config
    __get_l1_private_key: Callable[[], str]

    __account_module: AccountModule
    __auth_module: AuthModule

    async def close(self):
        await self.__account_module.close_session()
        await self.__auth_module.close_session()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    def __init__(self, config: Config, get_l1_private_key: Callable[[], str]):
        self.__config = config
        self.__get_l1_private_key = get_l1_private_key

    @property
    def account(self):
        return self.__account_module

    @property
    def auth(self):
        return self.__auth_module
