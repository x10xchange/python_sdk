"""
Async Client for Extended Exchange SDK.

Async version of the main entry point matching Hyperliquid/Pacifica Client class.
"""

from typing import Optional

from extended.api.exchange_async import AsyncExchangeAPI
from extended.api.info_async import AsyncInfoAPI
from extended.auth import ExtendedAuth
from extended.config import MAINNET_CONFIG, TESTNET_CONFIG


class AsyncClient:
    """
    Async Extended Exchange client with Hyperliquid-compatible interface.

    Provides asynchronous access to Info and Exchange APIs.

    Usage:
        client = AsyncClient(
            api_key="your-api-key",
            vault=12345,
            stark_private_key="0x...",
            stark_public_key="0x...",
            testnet=True,
        )

        # Info operations
        state = await client.info.user_state()
        orders = await client.info.open_orders()

        # Exchange operations
        result = await client.exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)
        await client.exchange.cancel("BTC", oid=12345)

        # Clean up
        await client.close()

    Note:
        Credentials (api_key, vault, stark keys) must be obtained from your
        onboarding infrastructure. This SDK does not perform onboarding.
    """

    def __init__(
        self,
        api_key: str,
        vault: int,
        stark_private_key: str,
        stark_public_key: str,
        testnet: bool = False,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize async Extended client.

        Args:
            api_key: Extended Exchange API key
            vault: Account/vault ID
            stark_private_key: L2 Stark private key (hex string)
            stark_public_key: L2 Stark public key (hex string)
            testnet: Use testnet (default False)
            base_url: Custom API base URL (optional, not currently used)
            timeout: Request timeout in seconds (default 30, not currently used)

        Note:
            Credentials must be obtained from your onboarding infrastructure.
            This SDK does not perform onboarding.
        """
        self._auth = ExtendedAuth(
            api_key=api_key,
            vault=vault,
            stark_private_key=stark_private_key,
            stark_public_key=stark_public_key,
            testnet=testnet,
        )
        self._config = self._auth.get_config()
        self._timeout = timeout

        self._info = AsyncInfoAPI(self._auth, self._config)
        self._exchange = AsyncExchangeAPI(self._auth, self._config)

    @property
    def info(self) -> AsyncInfoAPI:
        """Access async Info API for read operations."""
        return self._info

    @property
    def exchange(self) -> AsyncExchangeAPI:
        """Access async Exchange API for trading operations."""
        return self._exchange

    @property
    def address(self) -> Optional[str]:
        """Get the authenticated user's address (stark public key)."""
        return self._auth.address

    @property
    def public_key(self) -> Optional[str]:
        """Get the L2 public key."""
        return self._auth.stark_public_key

    async def close(self):
        """Close the client and release resources."""
        await self._auth.close()
