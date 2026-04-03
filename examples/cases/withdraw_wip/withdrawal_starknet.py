from asyncio import run
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient


async def setup_and_run():
    stark_account = StarkPerpetualAccount(
        vault=200027,
        private_key="<>",
        public_key="<>",
        api_key="<>",
    )
    trading_client = PerpetualTradingClient(
        endpoint_config=MAINNET_CONFIG,
        stark_account=stark_account,
    )

    resp = await trading_client.account.withdraw(
        amount=Decimal("10"),
        stark_address="0x037D9c8bBf6DE8b08F0C4072eBfAE9D1E890d094b9d117bABFCb3D41379B63ce".lower(),
        nonce=123,
    )

    print("Withdrawal response:")
    print(resp)

    print("Withdrawal complete")
    print("press enter to continue")
    input()


if __name__ == "__main__":
    run(main=setup_and_run())
