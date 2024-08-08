import json
import os
from decimal import Decimal
from typing import Callable

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

from x10.errors import X10Error
from x10.perpetual.configuration import EndpointConfig
from x10.utils.log import get_logger

LOGGER = get_logger(__name__)


class InsufficientAllowance(X10Error):
    pass


DEFAULT_API_TIMEOUT = 30

ABI_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "abi",
)
STARK_PERPETUAL_ABI = "stark-perpetual.json"
ERC20_ABI = "erc20.json"


def call_stark_perpetual_withdraw_balance(
    get_eth_private_key: Callable[[], str],
    config: EndpointConfig,
) -> Decimal:
    signing_account: LocalAccount = Account.from_key(get_eth_private_key())
    web3_provider = Web3.HTTPProvider(config.chain_rpc_url, request_kwargs={"timeout": DEFAULT_API_TIMEOUT})
    web3 = Web3(web3_provider)
    checksum_asset_operations_address = Web3.to_checksum_address(config.asset_operations_contract)
    asset_operations_contract = web3.eth.contract(
        address=checksum_asset_operations_address,
        abi=json.load(open(os.path.join(ABI_FOLDER, STARK_PERPETUAL_ABI), "r")),
    )
    withdrawable_amount = asset_operations_contract.functions.getWithdrawalBalance(
        int(signing_account.address, 16), int(config.collateral_asset_on_chain_id, 16)
    ).call()

    asset_erc20_checksum_address = Web3.to_checksum_address(config.collateral_asset_contract)
    asset_erc20_contract = web3.eth.contract(
        address=asset_erc20_checksum_address,
        abi=json.load(open(os.path.join(ABI_FOLDER, ERC20_ABI), "r")),
    )
    decimals = asset_erc20_contract.functions.decimals().call()
    return Decimal(withdrawable_amount).scaleb(-decimals)


def call_erc20_approve(
    human_readable_amount: Decimal,
    get_eth_private_key: Callable[[], str],
    config: EndpointConfig,
) -> str:
    web3_provider = Web3.HTTPProvider(config.chain_rpc_url, request_kwargs={"timeout": DEFAULT_API_TIMEOUT})
    web3 = Web3(web3_provider)
    asset_erc20_checksum_address = Web3.to_checksum_address(config.collateral_asset_contract)
    asset_erc20_contract = web3.eth.contract(
        address=asset_erc20_checksum_address,
        abi=json.load(open(os.path.join(ABI_FOLDER, ERC20_ABI), "r")),
    )
    spender = Web3.to_checksum_address(config.asset_operations_contract)
    amount_to_approve = int(human_readable_amount * 10 ** asset_erc20_contract.functions.decimals().call())
    method = asset_erc20_contract.functions.approve(spender, amount_to_approve)
    signing_account: LocalAccount = Account.from_key(get_eth_private_key())
    LOGGER.info(
        f"approving spender: {spender} for {amount_to_approve} on behalf of l1 account: {signing_account.address}"
    )
    signed_transaction = signing_account.sign_transaction(
        method.build_transaction(
            {
                "from": signing_account.address,
                "nonce": web3.eth.get_transaction_count(signing_account.address),
            }
        ),
    )
    web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    return signed_transaction.hash.hex()


def call_stark_perpetual_deposit(
    l2_vault: int,
    l2_key: str,
    config: EndpointConfig,
    human_readable_amount: Decimal,
    get_eth_private_key: Callable[[], str],
) -> str:
    signing_account: LocalAccount = Account.from_key(get_eth_private_key())
    LOGGER.info(
        f"Depositing into vault: {l2_vault}, l2_key: {l2_key}, amount: {human_readable_amount}, as l1 account: {signing_account.address}"  # noqa
    )
    web3_provider = Web3.HTTPProvider(config.chain_rpc_url, request_kwargs={"timeout": DEFAULT_API_TIMEOUT})
    web3 = Web3(web3_provider)
    checksum_asset_operations_address = Web3.to_checksum_address(config.asset_operations_contract)
    asset_operations_contract = web3.eth.contract(
        address=checksum_asset_operations_address,
        abi=json.load(open(os.path.join(ABI_FOLDER, STARK_PERPETUAL_ABI), "r")),
    )

    asset_erc20_checksum_address = Web3.to_checksum_address(config.collateral_asset_contract)
    asset_erc20_contract = web3.eth.contract(
        address=asset_erc20_checksum_address,
        abi=json.load(open(os.path.join(ABI_FOLDER, ERC20_ABI), "r")),
    )

    decimals = asset_erc20_contract.functions.decimals().call()
    amount_to_deposit = int(human_readable_amount * 10**decimals)
    allowance_amount = asset_erc20_contract.functions.allowance(
        signing_account.address,
        checksum_asset_operations_address,
    ).call()

    if allowance_amount < amount_to_deposit:
        raise InsufficientAllowance(
            f"Insufficient allowance. Required: {amount_to_deposit}, current: {allowance_amount}"
        )

    method = asset_operations_contract.functions.deposit(
        int(l2_key, base=16),
        int(config.collateral_asset_on_chain_id, base=16),
        l2_vault,
        amount_to_deposit,
    )
    signed_transaction = signing_account.sign_transaction(
        method.build_transaction(
            {
                "from": signing_account.address,
                "nonce": web3.eth.get_transaction_count(signing_account.address),
            }
        ),
    )
    web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    return signed_transaction.hash.hex()


def call_stark_perpetual_withdraw(
    config: EndpointConfig,
    get_eth_private_key: Callable[[], str],
) -> str:
    signing_account: LocalAccount = Account.from_key(get_eth_private_key())

    web3_provider = Web3.HTTPProvider(config.chain_rpc_url, request_kwargs={"timeout": DEFAULT_API_TIMEOUT})
    web3 = Web3(web3_provider)

    checksum_contract_address = Web3.to_checksum_address(config.asset_operations_contract)
    checksum_eth_address = Web3.to_checksum_address(signing_account.address)

    asset_operations_contract = web3.eth.contract(
        address=checksum_contract_address,
        abi=json.load(open(os.path.join(ABI_FOLDER, STARK_PERPETUAL_ABI), "r")),
    )

    method = asset_operations_contract.functions.withdraw(
        int(checksum_eth_address, base=16),
        int(config.collateral_asset_on_chain_id, base=16),
    )

    signed_transaction = signing_account.sign_transaction(
        method.build_transaction(
            {
                "from": signing_account.address,
                "nonce": web3.eth.get_transaction_count(signing_account.address),
            }
        ),
    )
    web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    return signed_transaction.hash.hex()
