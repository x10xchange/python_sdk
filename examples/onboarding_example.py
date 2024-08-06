import asyncio
from decimal import Decimal

from eth_account import Account

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.contract import call_erc20_approve, call_stark_perpetual_deposit
from x10.perpetual.trading_client.trading_client import PerpetualTradingClient
from x10.perpetual.user_client.user_client import UserClient


async def do_something():
    environment_config = TESTNET_CONFIG
    eth_account = Account.create()
    user_client = UserClient(endpoint_config=environment_config, l1_private_key=eth_account.key.hex)
    onboarded_user = await user_client.onboard()
    default_api_key = await user_client.create_account_api_key(onboarded_user.account, "trading api key")

    sub_account_1 = await user_client.onboard_subaccount(1, "sub account 1")
    # account_1_api_key = await user_client.create_account_api_key(sub_account_1.account, "sub account 1 api key")

    call_erc20_approve(Decimal("1000"), eth_account.key.hex, environment_config)
    call_stark_perpetual_deposit(
        l2_vault=int(onboarded_user.account.l2_vault),
        l2_key=onboarded_user.l2_key_pair.public_hex,
        config=environment_config,
        human_readable_amount=Decimal("1000"),
        get_eth_private_key=eth_account.key.hex,
    )

    default_account_trading_client = PerpetualTradingClient(
        environment_config,
        StarkPerpetualAccount(
            vault=onboarded_user.account.l2_vault,
            private_key=onboarded_user.l2_key_pair.private_hex,
            public_key=onboarded_user.l2_key_pair.public_hex,
            api_key=default_api_key,
        ),
    )

    default_account_trading_client.account.transfer(
        to_vault=int(sub_account_1.account.l2_vault),
        to_l2_key=sub_account_1.l2_key_pair.public_hex,
        amount=Decimal("10"),
    )

    print("User onboarded, default account:")
    print(f"\taccount_id: {onboarded_user.account.id}")
    print(f"\tdefault_vault: {onboarded_user.account.l2_vault}")
    print(f"\tdefault_L2PublicKey: {onboarded_user.l2_key_pair.public_hex}")
    print(f"\tdefault_L2PrivateKey: {onboarded_user.l2_key_pair.private_hex}")

    print("Sub account 1:")
    print(f"\taccount_id: {sub_account_1.account.id}")
    print(f"\tsub_account_1_vault: {sub_account_1.account.l2_vault}")
    print(f"\tsub_account_1_L2PublicKey: {sub_account_1.l2_key_pair.public_hex}")
    print(f"\tsub_account_1_L2PrivateKey: {sub_account_1.l2_key_pair.private_hex}")


asyncio.run(do_something())
