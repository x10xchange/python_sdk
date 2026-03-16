"""
Native Sync Client for Extended Exchange SDK.

Main entry point matching Hyperliquid/Pacifica Client class.
REPLACES problematic run_sync() approach with native sync implementation.
"""

from typing import Optional

from extended.api.exchange_new_sync import ExchangeAPI
from extended.api.info_new_sync import InfoAPI
from extended.auth import ExtendedAuth
from extended.config import MAINNET_CONFIG, TESTNET_CONFIG


class Client:
    """
    Extended Exchange client with Hyperliquid-compatible interface.

    Provides synchronous access to Info and Exchange APIs using NATIVE SYNC implementation.
    NO async/await or run_sync() anywhere - pure synchronous operation.

    Usage:
        client = Client(
            api_key="your-api-key",
            vault=12345,
            stark_private_key="0x...",
            stark_public_key="0x...",
            testnet=True,
        )

        # Info operations - NATIVE SYNC
        state = client.info.user_state()
        orders = client.info.open_orders()

        # Exchange operations - NATIVE SYNC
        client.exchange.order("BTC", is_buy=True, sz=0.01, limit_px=50000)
        client.exchange.cancel("BTC", oid=12345)

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
        Initialize Extended client with NATIVE SYNC implementation.

        Args:
            api_key: Extended Exchange API key
            vault: Account/vault ID
            stark_private_key: L2 Stark private key (hex string)
            stark_public_key: L2 Stark public key (hex string)
            testnet: Use testnet (default False)
            base_url: Custom API base URL (optional)
            timeout: Request timeout in seconds

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

        # Use appropriate config
        self._config = TESTNET_CONFIG if testnet else MAINNET_CONFIG
        if base_url:
            # Create custom config with provided base_url
            from x10.perpetual.configuration import EndpointConfig
            self._config = EndpointConfig(api_base_url=base_url)

        self._timeout = timeout

        # Create NATIVE SYNC APIs - NO run_sync() wrapper
        self._info = InfoAPI(self._auth, self._config)
        self._exchange = ExchangeAPI(self._auth, self._config)

    @property
    def info(self) -> InfoAPI:
        """Access Info API for read operations - NATIVE SYNC."""
        return self._info

    @property
    def exchange(self) -> ExchangeAPI:
        """Access Exchange API for trading operations - NATIVE SYNC."""
        return self._exchange

    @property
    def address(self) -> Optional[str]:
        """Get the authenticated user's address (stark public key)."""
        return self._auth.address

    @property
    def public_key(self) -> Optional[str]:
        """Get the L2 public key."""
        return self._auth.stark_public_key

    def close(self):
        """Close the client and release resources - NATIVE SYNC."""
        self._info.close()
        self._exchange.close()
        # No async cleanup needed for native sync implementation