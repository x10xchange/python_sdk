import logging
from asyncio import run

from eth_account import Account
from eth_account.signers.local import LocalAccount

from examples.utils import init_env
from x10.clients.rest import RestApiClient
from x10.config import TESTNET_CONFIG
from x10.core.stark_account import StarkPerpetualAccount
from x10.perpetual.user_client.user_client import UserClient
from x10.utils.string import is_hex_string

LOGGER = logging.getLogger()
CONFIG = TESTNET_CONFIG


async def run_example():
    init_env(require_private_api=False)

    eth_account_private_key = "<PRIVATE_KEY>"

    assert is_hex_string(eth_account_private_key), "`eth_account_private_key` must be a hex string"

    eth_local_account: LocalAccount = Account.from_key(eth_account_private_key)
    user_client = UserClient(config=CONFIG, l1_private_key=eth_local_account.key.hex)

    LOGGER.info("Onboarding with ETH account %s...", eth_local_account.address)

    main_account = await user_client.onboard()
    main_account_api_key = await user_client.create_account_api_key(main_account.account, "Onboarding example API key")

    starknet_account = StarkPerpetualAccount(
        api_key=main_account_api_key,
        public_key=main_account.l2_key_pair.public_hex,
        private_key=main_account.l2_key_pair.private_hex,
        vault=main_account.account.l2_vault,
    )
    rest_client = RestApiClient(CONFIG, starknet_account)
    rest_client.account.create_api_key("Onboarding example API key")

    LOGGER.info("StarkNet public key: %s", starknet_account.public_key)

    claim = await rest_client.testnet.claim_testing_funds()
    claim_id = claim.data.id if claim.data else None

    if claim_id:
        asset_operations = await rest_client.account.asset_operations(id=claim_id)
        LOGGER.info("Test funds asset operation: %s", asset_operations.data[0].to_pretty_json())


if __name__ == "__main__":
    run(main=run_example())
