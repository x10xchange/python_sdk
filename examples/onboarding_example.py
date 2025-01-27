import asyncio
from decimal import Decimal

from eth_account import Account
from eth_account.signers.local import LocalAccount

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.assets import AssetOperationType
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.contract import call_erc20_approve, call_stark_perpetual_deposit
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient
from x10.perpetual.user_client.user_client import UserClient


# flake8: noqa
async def on_board_example():
    environment_config = TESTNET_CONFIG
    eth_account: LocalAccount = Account.from_key("<your private key>")
    user_client = UserClient(endpoint_config=environment_config, l1_private_key=eth_account.key.hex)
    onboarded_user = await user_client.onboard()
    sub_account_1 = await user_client.onboard_subaccount(1, "sub account 1")

    default_api_key = await user_client.create_account_api_key(onboarded_user.account, "trading api key")
    account_1_api_key = await user_client.create_account_api_key(sub_account_1.account, "sub account 1 api key")

    default_account_trading_client = PerpetualTradingClient(
        environment_config,
        StarkPerpetualAccount(
            vault=onboarded_user.account.l2_vault,
            private_key=onboarded_user.l2_key_pair.private_hex,
            public_key=onboarded_user.l2_key_pair.public_hex,
            api_key=default_api_key,
        ),
    )

    sub_account_1_trading_client = PerpetualTradingClient(
        environment_config,
        StarkPerpetualAccount(
            vault=sub_account_1.account.l2_vault,
            private_key=sub_account_1.l2_key_pair.private_hex,
            public_key=sub_account_1.l2_key_pair.public_hex,
            api_key=account_1_api_key,
        ),
    )

    call_erc20_approve(
        human_readable_amount=Decimal("1000"), get_eth_private_key=eth_account.key.hex, config=environment_config
    )

    await default_account_trading_client.account.deposit(
        human_readable_amount=Decimal("1000"),
        get_eth_private_key=eth_account.key.hex,
    )

    default_account_trading_client.account.transfer(
        to_vault=int(sub_account_1.account.l2_vault),
        to_l2_key=sub_account_1.l2_key_pair.public_hex,
        amount=Decimal("10"),
    )

    created_withdrawal_id = await default_account_trading_client.account.slow_withdrawal(
        amount=Decimal("10"),
        eth_address=eth_account.address,
    )

    withdrawals = await default_account_trading_client.account.asset_operations(
        operations_type=[AssetOperationType.SLOW_WITHDRAWAL],
    )

    #### wait until withdrawal is in status READY_FOR_CLAIM

    available_withdrawal_balance = await user_client.available_l1_withdrawal_balance()

    withdrawal_tx_hash = await user_client.perform_l1_withdrawal()

    print()


asyncio.run(on_board_example())
