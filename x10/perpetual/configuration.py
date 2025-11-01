from dataclasses import dataclass


@dataclass
class StarknetDomain:
    name: str
    version: str
    chain_id: str
    revision: str


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
    collateral_asset_id: str
    starknet_domain: StarknetDomain


TESTNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://rpc.sepolia.org",
    api_base_url="https://api.starknet.sepolia.extended.exchange/api/v1",
    stream_url="wss://api.starknet.sepolia.extended.exchange/stream.extended.exchange/v1",
    onboarding_url="https://api.starknet.sepolia.extended.exchange",
    signing_domain="starknet.sepolia.extended.exchange",
    collateral_asset_contract="0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
    asset_operations_contract="",
    collateral_asset_on_chain_id="0x1",
    collateral_decimals=6,
    collateral_asset_id="0x1",
    starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_SEPOLIA", revision="1"),
)

MAINNET_CONFIG = EndpointConfig(
    chain_rpc_url="",
    api_base_url="https://api.starknet.extended.exchange/api/v1",
    stream_url="wss://api.starknet.extended.exchange/stream.extended.exchange/v1",
    onboarding_url="https://api.starknet.extended.exchange",
    signing_domain="extended.exchange",
    collateral_asset_contract="",
    asset_operations_contract="",
    collateral_asset_on_chain_id="0x1",
    collateral_decimals=6,
    collateral_asset_id="0x1",
    starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_MAIN", revision="1"),
)
