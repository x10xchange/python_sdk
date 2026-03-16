"""
Hyperliquid-style setup functions for Native Sync Extended Exchange SDK.

Provides setup() function that returns (address, info, exchange) tuples,
matching Hyperliquid/Pacifica's interface exactly.
NATIVE SYNC ONLY - no async dependencies.
"""

from typing import Optional, Tuple

from extended.api.exchange import ExchangeAPI
from extended.api.info import InfoAPI
from extended.client import Client


def setup(
    api_key: str,
    vault: int,
    stark_private_key: str,
    stark_public_key: str,
    testnet: bool = False,
    base_url: Optional[str] = None,
) -> Tuple[str, InfoAPI, ExchangeAPI]:
    """
    Initialize Extended SDK with Hyperliquid-compatible return format - NATIVE SYNC.

    This is a convenience function that mirrors the Hyperliquid/Pacifica setup()
    pattern, returning a tuple of (address, info, exchange) for easy integration
    with existing trading engines.

    NATIVE SYNC IMPLEMENTATION - pure synchronous.

    Args:
        api_key: Extended Exchange API key
        vault: Account/vault ID
        stark_private_key: L2 Stark private key (hex string)
        stark_public_key: L2 Stark public key (hex string)
        testnet: Use testnet environment (default False)
        base_url: Optional custom API base URL

    Returns:
        Tuple[str, InfoAPI, ExchangeAPI]: A tuple containing:
            - address: The stark public key (used as identifier)
            - info: InfoAPI instance for read operations (NATIVE SYNC)
            - exchange: ExchangeAPI instance for trading operations (NATIVE SYNC)

    Example:
        from extended import setup

        address, info, exchange = setup(
            api_key="your-api-key",
            vault=12345,
            stark_private_key="0x...",
            stark_public_key="0x...",
            testnet=True
        )

        # Now use exactly like Hyperliquid/Pacifica - NATIVE SYNC
        state = info.user_state()  # Pure sync - no waiting needed
        exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)  # Pure sync

    Note:
        Credentials (api_key, vault, stark keys) must be obtained from your
        onboarding infrastructure. This SDK does not perform onboarding.
    """
    # Create native sync client - NO async dependencies
    client = Client(
        api_key=api_key,
        vault=vault,
        stark_private_key=stark_private_key,
        stark_public_key=stark_public_key,
        testnet=testnet,
        base_url=base_url,
    )

    # Return (address, info, exchange) tuple like Hyperliquid/Pacifica
    # All components are NATIVE SYNC
    return (client.public_key, client.info, client.exchange)