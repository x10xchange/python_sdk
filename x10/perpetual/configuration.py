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
    api_base_url="https://api.testnet.x10.exchange/api/v1",
    stream_url="wss://api.testnet.x10.exchange/stream.x10.exchange/v1",
    onboarding_url="https://api.testnet.x10.exchange",
    signing_domain="testnet.x10.exchange",
    collateral_asset_contract="0x0c9165046063b7bcd05c6924bbe05ed535c140a1",
    asset_operations_contract="0x7f0C670079147C5c5C45eef548E55D2cAc53B391",
    collateral_asset_on_chain_id="0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
    collateral_decimals=6,
)

TESTNET_CONFIG_LEGACY_SIGNING_DOMAIN = EndpointConfig(
    chain_rpc_url="https://rpc.sepolia.org",
    api_base_url="https://api.testnet.x10.exchange/api/v1",
    stream_url="wss://api.testnet.x10.exchange/stream.x10.exchange/v1",
    onboarding_url="https://api.testnet.x10.exchange",
    signing_domain="x10.exchange",
    collateral_asset_contract="0x0c9165046063b7bcd05c6924bbe05ed535c140a1",
    asset_operations_contract="0x7f0C670079147C5c5C45eef548E55D2cAc53B391",
    collateral_asset_on_chain_id="0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
    collateral_decimals=6,
)

MAINNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://cloudflare-eth.com",
    api_base_url="https://api.prod.x10.exchange/api/v1",
    stream_url="wss://api.prod.x10.exchange/stream.x10.exchange/v1",
    onboarding_url="https://api.prod.x10.exchange",
    signing_domain="x10.exchange",
    collateral_asset_contract="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    asset_operations_contract="0x1cE5D7f52A8aBd23551e91248151CA5A13353C65",
    collateral_asset_on_chain_id="0x2893294412a4c8f915f75892b395ebbf6859ec246ec365c3b1f56f47c3a0a5d",
    collateral_decimals=6,
)
