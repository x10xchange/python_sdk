import json
import os

from web3 import Web3

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.markets import MarketModel

DEFAULT_API_TIMEOUT = 30

PROVIDER_ENDPOINT_URI = "https://rpc.sepolia.org/"
STARK_PERPETUAL_ABI = "stark-perpetual.json"


def test(contract_address: str, market: MarketModel, eth_address: str):
    web3_provider = Web3.HTTPProvider(PROVIDER_ENDPOINT_URI, request_kwargs={"timeout": DEFAULT_API_TIMEOUT})
    web3 = Web3(web3_provider)
    abi_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "abi",
    )

    contract = web3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=json.load(open(os.path.join(abi_folder, STARK_PERPETUAL_ABI), "r")),
    )

    method = contract.functions.withdraw(
        int(eth_address, base=16),
        int(market.l2_config.collateral_id, base=16),
    )

    # https://sepolia.etherscan.io/address/0x7f0C670079147C5c5C45eef548E55D2cAc53B391
    tx_hash = method.call()

    # return self.send_eth_transaction(
    #     method=contract.functions.withdraw(
    #         int(stark_public_key, 16),
    #         COLLATERAL_ASSET_ID_BY_NETWORK_ID[self.network_id],
    #     ),
    #     options=send_options,
    # )
