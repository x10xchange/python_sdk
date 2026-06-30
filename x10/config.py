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
        api_base_url="https://api.starknet.sepolia.extended.exchange/api/v1",
        api_base_order_management_url="https://api.starknet.sepolia.extended.exchange/api/v1",
        stream_url="wss://api.starknet.sepolia.extended.exchange/stream.extended.exchange/v1",
        stream_rpc_url="wss://api.starknet.sepolia.extended.exchange/stream.extended.exchange/v2/rpc",
        onboarding_url="https://api.starknet.sepolia.extended.exchange",
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
        api_base_url="https://api.starknet.extended.exchange/api/v1",
        api_base_order_management_url="https://api.starknet.extended.exchange/api/v1",
        stream_url="wss://api.starknet.extended.exchange/stream.extended.exchange/v1",
        stream_rpc_url="wss://api.starknet.extended.exchange/stream.extended.exchange/v2/rpc",
        onboarding_url="https://api.starknet.extended.exchange",
        vault_asset_name="XVS",
    ),
)


def get_config_by_name(name: ClientConfigName) -> ClientConfig:
    if name == "TESTNET":
        return TESTNET_CONFIG

    if name == "MAINNET":
        return MAINNET_CONFIG

    raise ValidationError(f"Unknown config name: {name}")
