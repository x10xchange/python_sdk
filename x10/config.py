from dataclasses import dataclass
from decimal import Decimal


@dataclass(kw_only=True, frozen=True)
class StarknetDomain:
    name: str
    version: str
    chain_id: str
    revision: str


@dataclass(kw_only=True, frozen=True)
class EndpointsConfig:
    """
    Attributes:
        chain_rpc_url (str): Field is deprecated and will be removed.
        asset_operations_contract (str): Field is deprecated and will be removed.
        collateral_asset_contract (str): Field is deprecated and will be removed.
        collateral_asset_on_chain_id (str): Field is deprecated and will be removed.
        collateral_decimals (int): Field is deprecated and will be removed.
        collateral_asset_id (str): Field is deprecated and will be removed.
    """

    chain_rpc_url: str
    api_base_url: str
    stream_url: str
    onboarding_url: str

    asset_operations_contract: str
    collateral_asset_contract: str
    collateral_asset_on_chain_id: str
    collateral_decimals: int
    collateral_asset_id: str

    vault_asset_name: str


@dataclass(kw_only=True, frozen=True)
class Config:
    default_market_price_slippage: Decimal
    default_request_timeout_seconds: int
    default_maker_fee_rate: Decimal
    default_taker_fee_rate: Decimal
    default_builder_fee_rate: Decimal

    signing_domain: str
    starknet_domain: StarknetDomain

    endpoints: EndpointsConfig


TESTNET_CONFIG = Config(
    default_market_price_slippage=Decimal("0.0075"),
    # FIXME: Reduce
    default_request_timeout_seconds=500,
    default_maker_fee_rate=Decimal("0.0002"),
    default_taker_fee_rate=Decimal("0.0005"),
    default_builder_fee_rate=Decimal("0"),
    signing_domain="starknet.sepolia.extended.exchange",
    starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_SEPOLIA", revision="1"),
    endpoints=EndpointsConfig(
        chain_rpc_url="https://rpc.sepolia.org",
        api_base_url="https://api.starknet.sepolia.extended.exchange/api/v1",
        stream_url="wss://api.starknet.sepolia.extended.exchange/stream.extended.exchange/v1",
        onboarding_url="https://api.starknet.sepolia.extended.exchange",
        asset_operations_contract="",
        collateral_asset_contract="0x05ba91db44b3e6a4485b5dbfcb17d791faa9cb6890a42731b66b3536b28b8ed5",
        collateral_asset_on_chain_id="0x1",
        collateral_decimals=6,
        collateral_asset_id="0x1",
        vault_asset_name="XVS",
    ),
)


MAINNET_CONFIG = Config(
    default_market_price_slippage=Decimal("0.0075"),
    # FIXME: Reduce
    default_request_timeout_seconds=500,
    default_maker_fee_rate=Decimal("0.0002"),
    default_taker_fee_rate=Decimal("0.0005"),
    default_builder_fee_rate=Decimal("0"),
    signing_domain="extended.exchange",
    starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_MAIN", revision="1"),
    endpoints=EndpointsConfig(
        chain_rpc_url="",
        api_base_url="https://api.starknet.extended.exchange/api/v1",
        stream_url="wss://api.starknet.extended.exchange/stream.extended.exchange/v1",
        onboarding_url="https://api.starknet.extended.exchange",
        asset_operations_contract="",
        collateral_asset_contract="",
        collateral_asset_on_chain_id="0x1",
        collateral_decimals=6,
        collateral_asset_id="0x1",
        vault_asset_name="XVS",
    ),
)
