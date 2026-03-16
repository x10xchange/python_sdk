"""
Authentication module for Extended Exchange SDK.

Manages pre-configured Extended credentials for use with the SDK.

Note: Onboarding (L1->L2 key derivation, account creation, API key generation)
is handled by a separate infrastructure component. This SDK assumes credentials
are already available.
"""

from typing import Optional

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import EndpointConfig, TESTNET_CONFIG, MAINNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient


class ExtendedAuth:
    """
    Manages Extended Exchange authentication credentials.

    Accepts pre-configured credentials from your onboarding infrastructure:
    - api_key: Extended Exchange API key
    - vault: Account/vault ID
    - stark_private_key: L2 Stark private key (hex string)
    - stark_public_key: L2 Stark public key (hex string)

    Example:
        auth = ExtendedAuth(
            api_key="your-api-key",
            vault=12345,
            stark_private_key="0x...",
            stark_public_key="0x...",
            testnet=True,
        )

        # Get the configured trading client
        client = auth.get_trading_client()
    """

    def __init__(
        self,
        api_key: str,
        vault: int,
        stark_private_key: str,
        stark_public_key: str,
        testnet: bool = False,
    ):
        """
        Initialize authentication with pre-configured credentials.

        Args:
            api_key: Extended Exchange API key
            vault: Account/vault ID
            stark_private_key: L2 Stark private key (hex string, e.g., "0x...")
            stark_public_key: L2 Stark public key (hex string, e.g., "0x...")
            testnet: Use testnet configuration (default False)
        """
        self.api_key = api_key
        self.vault = vault
        self.stark_private_key = stark_private_key
        self.stark_public_key = stark_public_key
        self.testnet = testnet
        self._stark_account: Optional[StarkPerpetualAccount] = None
        self._config: EndpointConfig = TESTNET_CONFIG if testnet else MAINNET_CONFIG
        self._trading_client: Optional[PerpetualTradingClient] = None

    @property
    def address(self) -> str:
        """
        Return the stark public key as the user's address/identifier.

        This is used for Hyperliquid interface compatibility.
        """
        return self.stark_public_key

    def get_stark_account(self) -> StarkPerpetualAccount:
        """
        Get or create StarkPerpetualAccount from credentials.

        Returns:
            Configured StarkPerpetualAccount instance
        """
        if self._stark_account is None:
            self._stark_account = StarkPerpetualAccount(
                vault=self.vault,
                private_key=self.stark_private_key,
                public_key=self.stark_public_key,
                api_key=self.api_key,
            )
        return self._stark_account

    def get_config(self) -> EndpointConfig:
        """
        Return endpoint configuration.

        Returns:
            TESTNET_CONFIG or MAINNET_CONFIG based on testnet flag
        """
        return self._config

    def get_trading_client(self) -> PerpetualTradingClient:
        """
        Create or return a configured PerpetualTradingClient.

        Returns:
            Configured PerpetualTradingClient instance
        """
        if self._trading_client is None:
            self._trading_client = PerpetualTradingClient(
                endpoint_config=self._config,
                stark_account=self.get_stark_account(),
            )
        return self._trading_client

    async def close(self):
        """
        Close the trading client and release resources.
        """
        if self._trading_client is not None:
            await self._trading_client.close()
            self._trading_client = None
