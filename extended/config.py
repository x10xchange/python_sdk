"""
Configuration for Extended Exchange SDK.

Re-exports the endpoint configurations from x10 for convenience.
"""

from x10.perpetual.configuration import (
    EndpointConfig,
    MAINNET_CONFIG,
    TESTNET_CONFIG,
    StarknetDomain,
)

__all__ = [
    "EndpointConfig",
    "MAINNET_CONFIG",
    "TESTNET_CONFIG",
    "StarknetDomain",
]
