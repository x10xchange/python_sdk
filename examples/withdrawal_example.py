from asyncio import run
from decimal import Decimal

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import MAINNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient


async def setup_and_run():
    stark_account = StarkPerpetualAccount(
        vault=1337,
        private_key="<>",
        public_key="<>",
        api_key="<>",
    )
    trading_client = PerpetualTradingClient(
        endpoint_config=MAINNET_CONFIG,
        stark_account=stark_account,
    )

    await trading_client.account.slow_withdrawal(
        amount=Decimal("20"), eth_address="0x9361F2761cc1349ceA6606D4Bc6f048c1E4881d1"
    )

    print("Withdrawal complete")
    print("press enter to continue")
    input()


if __name__ == "__main__":
    run(main=setup_and_run())
