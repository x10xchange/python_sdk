"""
Simplified sync auth interface for Extended Exchange SDK.

Provides the minimal auth interface needed by the native sync implementation
without async dependencies.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class SimpleSyncAuth:
    """
    Simplified synchronous auth interface.

    Contains only the essential fields needed by the native sync HTTP client.
    No async dependencies or complex crypto operations.
    """

    api_key: str
    vault: int
    stark_private_key: str
    stark_public_key: str
    testnet: bool = False

    @property
    def address(self) -> str:
        """Get the account address (stark public key)."""
        return self.stark_public_key

    def get_auth_headers(self) -> dict:
        """Get authentication headers for HTTP requests."""
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }


# For compatibility with existing code that expects ExtendedAuth
ExtendedAuth = SimpleSyncAuth