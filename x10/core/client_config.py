from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, TypeAlias

ClientConfigName: TypeAlias = Literal["TESTNET", "MAINNET"]


@dataclass(kw_only=True, frozen=True)
class StarknetDomain:
    name: str
    version: str
    chain_id: str
    revision: str


@dataclass(kw_only=True, frozen=True)
class DefaultsConfig:
    market_price_slippage: Decimal
    request_timeout_seconds: int


@dataclass(kw_only=True, frozen=True)
class SigningConfig:
    signing_domain: str
    starknet_domain: StarknetDomain


@dataclass(kw_only=True, frozen=True)
class EndpointsConfig:
    api_base_url: str
    api_base_order_management_url: str
    stream_url: str
    stream_rpc_url: str
    onboarding_url: str

    vault_asset_name: str


@dataclass(kw_only=True, frozen=True)
class ClientConfig:
    defaults: DefaultsConfig
    signing: SigningConfig
    endpoints: EndpointsConfig
