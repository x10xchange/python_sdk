"""
Hyperliquid-style setup functions for Extended Exchange SDK.

Provides setup() and async_setup() functions that return
(address, info, exchange) tuples, matching Hyperliquid/Pacifica's interface.
"""

from typing import Optional, Tuple

from extended.api.exchange import ExchangeAPI
from extended.api.exchange_async import AsyncExchangeAPI
from extended.api.info import InfoAPI
from extended.api.info_async import AsyncInfoAPI
from extended.client import Client
from extended.async_client import AsyncClient


def setup(
    api_key: str,
    vault: int,
    stark_private_key: str,
    stark_public_key: str,
    testnet: bool = False,
    base_url: Optional[str] = None,
) -> Tuple[str, InfoAPI, ExchangeAPI]:
    """
    Initialize Extended SDK with Hyperliquid-compatible return format.

    This is a convenience function that mirrors the Hyperliquid/Pacifica setup()
    pattern, returning a tuple of (address, info, exchange) for easy integration
    with existing trading engines.

    Args:
        api_key: Extended Exchange API key
        vault: Account/vault ID
        stark_private_key: L2 Stark private key (hex string)
        stark_public_key: L2 Stark public key (hex string)
        testnet: Use testnet environment (default False)
        base_url: Optional custom API base URL (not currently used)

    Returns:
        Tuple[str, InfoAPI, ExchangeAPI]: A tuple containing:
            - address: The stark public key (used as identifier)
            - info: InfoAPI instance for read operations
            - exchange: ExchangeAPI instance for trading operations

    Example:
        from extended import setup

        address, info, exchange = setup(
            api_key="your-api-key",
            vault=12345,
            stark_private_key="0x...",
            stark_public_key="0x...",
            testnet=True
        )

        # Now use exactly like Hyperliquid
        state = info.user_state()
        exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)

    Note:
        Credentials (api_key, vault, stark keys) must be obtained from your
        onboarding infrastructure. This SDK does not perform onboarding.
    """
    client = Client(
        api_key=api_key,
        vault=vault,
        stark_private_key=stark_private_key,
        stark_public_key=stark_public_key,
        testnet=testnet,
        base_url=base_url,
    )

    # Return (address, info, exchange) tuple like Hyperliquid
    return (client.public_key, client.info, client.exchange)


def async_setup(
    api_key: str,
    vault: int,
    stark_private_key: str,
    stark_public_key: str,
    testnet: bool = False,
    base_url: Optional[str] = None,
) -> Tuple[str, AsyncInfoAPI, AsyncExchangeAPI]:
    """
    Async version of setup() for use with AsyncClient.

    Returns a tuple of (address, info, exchange) where info and exchange
    are async API instances.

    Args:
        api_key: Extended Exchange API key
        vault: Account/vault ID
        stark_private_key: L2 Stark private key (hex string)
        stark_public_key: L2 Stark public key (hex string)
        testnet: Use testnet environment (default False)
        base_url: Optional custom API base URL (not currently used)

    Returns:
        Tuple[str, AsyncInfoAPI, AsyncExchangeAPI]: A tuple containing:
            - address: The stark public key (used as identifier)
            - info: AsyncInfoAPI instance for async read operations
            - exchange: AsyncExchangeAPI instance for async trading operations

    Example:
        from extended import async_setup

        address, info, exchange = async_setup(
            api_key="your-api-key",
            vault=12345,
            stark_private_key="0x...",
            stark_public_key="0x...",
            testnet=True
        )

        # Now use exactly like Hyperliquid (async)
        state = await info.user_state()
        await exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)

    Note:
        Credentials (api_key, vault, stark keys) must be obtained from your
        onboarding infrastructure. This SDK does not perform onboarding.
    """
    client = AsyncClient(
        api_key=api_key,
        vault=vault,
        stark_private_key=stark_private_key,
        stark_public_key=stark_public_key,
        testnet=testnet,
        base_url=base_url,
    )

    # Return (address, info, exchange) tuple like Hyperliquid
    return (client.public_key, client.info, client.exchange)
