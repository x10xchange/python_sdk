import json
import os

from web3 import Web3

from x10.perpetual.configuration import EndpointConfig
from x10.perpetual.markets import MarketModel

DEFAULT_API_TIMEOUT = 30

ABI_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "abi",
)
STARK_PERPETUAL_ABI = "stark-perpetual.json"


def call_stark_perpetual_withdraw(contract_address: str, eth_address: str, market: MarketModel, config: EndpointConfig):
    web3_provider = Web3.HTTPProvider(config.chain_rpc_url, request_kwargs={"timeout": DEFAULT_API_TIMEOUT})
    web3 = Web3(web3_provider)

    contract = web3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=json.load(open(os.path.join(ABI_FOLDER, STARK_PERPETUAL_ABI), "r")),
    )

    method = contract.functions.withdraw(
        int(eth_address, base=16),
        int(market.l2_config.collateral_id, base=16),
    )

    return method.transact()
