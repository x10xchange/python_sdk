import json
import os
from typing import Callable

from web3 import Web3

from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.markets import MarketModel
from x10.utils.string import is_hex_string

DEFAULT_API_TIMEOUT = 30

ABI_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "abi",
)
STARK_PERPETUAL_ABI = "stark-perpetual.json"


def call_stark_perpetual_withdraw(
    contract_address: str,
    eth_address: str,
    market: MarketModel,
    config: EndpointConfig,
    get_eth_private_key: Callable[[], str],
):
    web3_provider = Web3.HTTPProvider(config.chain_rpc_url, request_kwargs={"timeout": DEFAULT_API_TIMEOUT})
    web3 = Web3(web3_provider)

    checksum_contract_address = Web3.to_checksum_address(contract_address)
    checksum_eth_address = Web3.to_checksum_address(eth_address)

    contract = web3.eth.contract(
        address=checksum_contract_address,
        abi=json.load(open(os.path.join(ABI_FOLDER, STARK_PERPETUAL_ABI), "r")),
    )

    method = contract.functions.withdraw(
        int(checksum_eth_address, base=16),
        int(market.l2_config.collateral_id, base=16),
    )

    eth_private_key = get_eth_private_key()

    assert is_hex_string(eth_private_key)

    signed_tx = web3.eth.account.sign_transaction(
        method.build_transaction(
            {
                "from": checksum_eth_address,
                "nonce": web3.eth.get_transaction_count(checksum_eth_address),
            }
        ),
        eth_private_key,
    )

    return web3.eth.send_raw_transaction(signed_tx.rawTransaction)
