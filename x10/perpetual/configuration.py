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


TESTNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://rpc.sepolia.org",
    api_base_url="https://api.testnet.x10.exchange/api/v1",
    stream_url="wss://api.testnet.x10.exchange/stream.x10.exchange/v1",
    onboarding_url="https://api.testnet.x10.exchange",
    signing_domain="testnet.x10.exchange",
    collateral_asset_contract="0x0c9165046063b7bcd05c6924bbe05ed535c140a1",
    asset_operations_contract="0x7f0C670079147C5c5C45eef548E55D2cAc53B391",
)

TESTNET_CONFIG_LEGACY_SIGNING_DOMAIN = EndpointConfig(
    chain_rpc_url="https://rpc.sepolia.org",
    api_base_url="https://api.testnet.x10.exchange/api/v1",
    stream_url="wss://api.testnet.x10.exchange/stream.x10.exchange/v1",
    onboarding_url="https://api.testnet.x10.exchange",
    signing_domain="x10.exchange",
    collateral_asset_contract="0x0c9165046063b7bcd05c6924bbe05ed535c140a1",
    asset_operations_contract="0x7f0C670079147C5c5C45eef548E55D2cAc53B391",
)

MAINNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://cloudflare-eth.com",
    api_base_url="https://api.prod.x10.exchange/api/v1",
    stream_url="wss://api.prod.x10.exchange/stream.x10.exchange/v1",
    onboarding_url="https://api.prod.x10.exchange",
    signing_domain="x10.exchange",
    collateral_asset_contract="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    asset_operations_contract="0x1cE5D7f52A8aBd23551e91248151CA5A13353C65",
)
