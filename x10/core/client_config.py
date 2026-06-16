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
class ClientConfig:
    defaults: DefaultsConfig
    signing: SigningConfig
    endpoints: EndpointsConfig
