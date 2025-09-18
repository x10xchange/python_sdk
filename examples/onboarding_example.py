import asyncio

from eth_account import Account
from eth_account.signers.local import LocalAccount

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient
from x10.perpetual.user_client.user_client import UserClient


async def on_board_example():
    environment_config = TESTNET_CONFIG
    eth_account_1: LocalAccount = Account.from_key("YOUR_ETH_PRIVATE_KEY")
    onboarding_client = UserClient(endpoint_config=environment_config, l1_private_key=eth_account_1.key.hex)
    root_account = await onboarding_client.onboard()

    trading_key = await onboarding_client.create_account_api_key(root_account.account, "trading_key")

    root_trading_client = PerpetualTradingClient(
        environment_config,
        StarkPerpetualAccount(
            vault=root_account.account.l2_vault,
            private_key=root_account.l2_key_pair.private_hex,
            public_key=root_account.l2_key_pair.public_hex,
            api_key=trading_key,
        ),
    )

    print(f"User 1 v: {root_account.account.l2_vault}")
    print(f"User 1 pub: {root_account.l2_key_pair.public_hex}")
    print(f"User 1 priv: {root_account.l2_key_pair.private_hex}")
    claim_response = await root_trading_client.testnet.claim_testing_funds()
    claim_id = claim_response.data.id if claim_response.data else None
    print(f"Claim ID: {claim_id}")

    resp = await root_trading_client.account.asset_operations(id=claim_id)
    print(f"Asset Operations: {resp.data}")


asyncio.run(on_board_example())
