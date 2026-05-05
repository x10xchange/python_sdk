from eth_typing import ChecksumAddress

from x10.clients.onboarding.modules.account_module import AccountModule
from x10.clients.onboarding.modules.auth_module import AuthModule
from x10.config import Config
from x10.core.types import SignMessageCallback


class OnboardingClient:
    __account_module: AccountModule
    __auth_module: AuthModule

    async def close(self):
        await self.__account_module.close_session()
        await self.__auth_module.close_session()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    def __init__(self, config: Config, *, account_address: ChecksumAddress, sign_message: SignMessageCallback):
        self.__account_module = AccountModule(config, account_address=account_address, sign_message=sign_message)
        self.__auth_module = AuthModule(config, account_address=account_address, sign_message=sign_message)

    @property
    def account(self):
        return self.__account_module

    @property
    def auth(self):
        return self.__auth_module
