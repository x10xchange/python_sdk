from decimal import Decimal

from x10.core.client_config import (
    ClientConfig,
    ClientConfigName,
    DefaultsConfig,
    EndpointsConfig,
    SigningConfig,
    StarknetDomain,
)
from x10.errors import ValidationError

DEFAULTS = DefaultsConfig(market_price_slippage=Decimal("0.0075"), request_timeout_seconds=500)

TESTNET_CONFIG = ClientConfig(
    defaults=DEFAULTS,
    signing=SigningConfig(
        signing_domain="starknet.sepolia.extended.exchange",
        starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_SEPOLIA", revision="1"),
    ),
    endpoints=EndpointsConfig(
        chain_rpc_url="https://rpc.sepolia.org",
        api_base_url="https://api.starknet.sepolia.extended.exchange/api/v1",
        api_base_order_management_url="https://api.starknet.sepolia.extended.exchange/api/v1",
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


MAINNET_CONFIG = ClientConfig(
    defaults=DEFAULTS,
    signing=SigningConfig(
        signing_domain="extended.exchange",
        starknet_domain=StarknetDomain(name="Perpetuals", version="v0", chain_id="SN_MAIN", revision="1"),
    ),
    endpoints=EndpointsConfig(
        chain_rpc_url="",
        api_base_url="https://api.starknet.extended.exchange/api/v1",
        api_base_order_management_url="https://api.starknet.extended.exchange/api/v1",
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


def get_config_by_name(name: ClientConfigName) -> ClientConfig:
    if name == "TESTNET":
        return TESTNET_CONFIG

    if name == "MAINNET":
        return MAINNET_CONFIG

    raise ValidationError(f"Unknown config name: {name}")
