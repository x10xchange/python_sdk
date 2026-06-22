import logging.handlers
from asyncio import run
from decimal import Decimal

from examples.utils import create_rest_client, init_env

LOGGER = logging.getLogger()
USDC_TRANSFER_AMOUNT = 5


async def run_example():
    env_config = init_env()
    rest_client = create_rest_client()

    assets_response = await rest_client.info.get_assets()
    accounts_response = await rest_client.account.get_accounts()
    balance_response = await rest_client.account.get_balance()

    assets = assets_response.data or []
    accounts = accounts_response.data or []
    balance = balance_response.data

    if len(accounts) < 2:
        LOGGER.error("At least 2 sub-accounts are required to transfer")
        return

    if not balance or balance.balance < USDC_TRANSFER_AMOUNT:
        LOGGER.error(f"No balance or too low (at least {USDC_TRANSFER_AMOUNT}USDC required) to transfer")
        return

    usd_asset = next((asset for asset in assets if asset.symbol == "USD"), None)
    from_subaccount = accounts[0]
    to_subaccount = accounts[1]

    if usd_asset is None:
        LOGGER.error("USD asset not found")
        return

    if from_subaccount.l2_vault != env_config.vault_id:
        LOGGER.error("`from` subaccount must be the one specified in env config")
        return

    LOGGER.info(
        "Transferring %sUSDC from `%s` to `%s`",
        USDC_TRANSFER_AMOUNT,
        from_subaccount.description,
        to_subaccount.description,
    )

    transfer_response = await rest_client.account.transfer(
        to_vault=to_subaccount.l2_vault,
        to_l2_public_key=to_subaccount.l2_key,
        amount=Decimal(USDC_TRANSFER_AMOUNT),
        asset=usd_asset.to_settlement_asset(),
    )
    transfer = transfer_response.data

    LOGGER.info("Transfer: %s", transfer.to_pretty_json())


if __name__ == "__main__":
    run(main=run_example())
