from dataclasses import dataclass


@dataclass
class EndpointConfig:
    chain_rpc_url: str
    api_base_url: str
    stream_url: str
    onboarding_url: str
    signing_domain: str
    collateral_asset_contract: str
    asset_operations_contract: str
    collateral_asset_on_chain_id: str
    collateral_decimals: int


TESTNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://rpc.sepolia.org",
    api_base_url="https://api.testnet.extended.exchange/api/v1",
    stream_url="wss://api.testnet.extended.exchange/stream.extended.exchange/v1",
    onboarding_url="https://api.testnet.extended.exchange",
    signing_domain="testnet.extended.exchange",
    collateral_asset_contract="0x0C9165046063B7bCD05C6924Bbe05ed535c140a1",
    asset_operations_contract="0xe42bb60Fab4EA4905832AEbDf0f001c784dA271b",
    collateral_asset_on_chain_id="0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
    collateral_decimals=6,
)

MAINNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://cloudflare-eth.com",
    api_base_url="https://api.extended.exchange/api/v1",
    stream_url="wss://api.extended.exchange/stream.extended.exchange/v1",
    onboarding_url="https://api.extended.exchange",
    signing_domain="extended.exchange",
    collateral_asset_contract="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    asset_operations_contract="0x1cE5D7f52A8aBd23551e91248151CA5A13353C65",
    collateral_asset_on_chain_id="0x2893294412a4c8f915f75892b395ebbf6859ec246ec365c3b1f56f47c3a0a5d",
    collateral_decimals=6,
)

"""
Identical to the MAINNET_CONFIG, but with a different signing domain.
Use it for accounts that were created before the signing domain was changed.
"""
MAINNET_CONFIG_LEGACY_SIGNING_DOMAIN = EndpointConfig(
    chain_rpc_url="https://cloudflare-eth.com",
    api_base_url="https://api.extended.exchange/api/v1",
    stream_url="wss://api.extended.exchange/stream.extended.exchange/v1",
    onboarding_url="https://api.extended.exchange",
    signing_domain="x10.exchange",
    collateral_asset_contract="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    asset_operations_contract="0x1cE5D7f52A8aBd23551e91248151CA5A13353C65",
    collateral_asset_on_chain_id="0x2893294412a4c8f915f75892b395ebbf6859ec246ec365c3b1f56f47c3a0a5d",
    collateral_decimals=6,
)
