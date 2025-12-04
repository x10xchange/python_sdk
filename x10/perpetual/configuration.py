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
    starknet_domain: StarknetDomain
    vault_position: int = 0
    vault_asset_on_chain_id: str = "0x0"
    vault_asset_id: int = 0
    vault_asset_name: str = "UNKNOWN"


TESTNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://rpc.sepolia.org",
    api_base_url="https://api.starknet.sepolia.extended.exchange/api/v1",
    stream_url="wss://api.starknet.sepolia.extended.exchange/stream.extended.exchange/v1",
    onboarding_url="https://api.starknet.sepolia.extended.exchange",
    signing_domain="starknet.sepolia.extended.exchange",
    collateral_asset_contract="0x05ba91db44b3e6a4485b5dbfcb17d791faa9cb6890a42731b66b3536b28b8ed5",
    asset_operations_contract="",
    collateral_asset_on_chain_id="0x31857064564ed0ff978e687456963cba09c2c6985d8f9300a1de4962fafa054",
    collateral_decimals=6,
    starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_SEPOLIA", revision="1"),
    vault_position=7,
    vault_asset_on_chain_id="0x04471D52BA219221ba25A254f771bDA2BC89998895D3640A307D3C49aE262990",
    vault_asset_id=33,
    vault_asset_name="XVS",
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
    starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_MAIN", revision="1"),
)
