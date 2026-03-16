"""
Simplified sync configuration for Extended Exchange SDK.

Provides the minimal config interface needed by the native sync implementation
without X10 dependencies.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class SimpleSyncConfig:
    """
    Simplified synchronous config interface.

    Contains only the essential fields needed by the native sync HTTP client.
    No X10 or async dependencies.
    """

    api_base_url: str
    signing_domain: str = ""
    timeout: int = 30

    def __init__(self, api_base_url: str = None, signing_domain: str = "", testnet: bool = False, timeout: int = 30):
        if api_base_url:
            self.api_base_url = api_base_url
        elif testnet:
            self.api_base_url = "https://api.starknet.sepolia.extended.exchange/api/v1"
        else:
            self.api_base_url = "https://api.starknet.extended.exchange/api/v1"

        if signing_domain:
            self.signing_domain = signing_domain
        elif testnet:
            self.signing_domain = "starknet.sepolia.extended.exchange"
        else:
            self.signing_domain = "extended.exchange"

        self.timeout = timeout


# Default configurations
MAINNET_CONFIG = SimpleSyncConfig(testnet=False)
TESTNET_CONFIG = SimpleSyncConfig(testnet=True)

# For compatibility with existing code
EndpointConfig = SimpleSyncConfig