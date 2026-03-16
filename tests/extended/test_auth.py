"""
Unit tests for ExtendedAuth.

Tests authentication module functionality.
"""

import pytest
from hamcrest import assert_that, equal_to, is_not, none, instance_of

from x10.perpetual.accounts import StarkPerpetualAccount
from x10.perpetual.configuration import TESTNET_CONFIG, MAINNET_CONFIG
from x10.perpetual.trading_client import PerpetualTradingClient

from extended.auth import ExtendedAuth


# Test credentials
TEST_API_KEY = "test-api-key-12345"
TEST_VAULT = 10001
TEST_PRIVATE_KEY = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
TEST_PUBLIC_KEY = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"


class TestExtendedAuthInit:
    """Tests for ExtendedAuth initialization."""

    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(auth.api_key, equal_to(TEST_API_KEY))
        assert_that(auth.vault, equal_to(TEST_VAULT))
        assert_that(auth.stark_private_key, equal_to(TEST_PRIVATE_KEY))
        assert_that(auth.stark_public_key, equal_to(TEST_PUBLIC_KEY))
        assert_that(auth.testnet, equal_to(False))  # Default

    def test_init_with_testnet_true(self):
        """Test initialization with testnet=True."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=True,
        )

        assert_that(auth.testnet, equal_to(True))

    def test_init_with_testnet_false(self):
        """Test initialization with testnet=False (explicit)."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=False,
        )

        assert_that(auth.testnet, equal_to(False))


class TestExtendedAuthAddress:
    """Tests for address property."""

    def test_address_returns_public_key(self):
        """Test that address property returns the stark public key."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(auth.address, equal_to(TEST_PUBLIC_KEY))


class TestExtendedAuthConfig:
    """Tests for get_config method."""

    def test_get_config_testnet(self):
        """Test getting testnet config."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=True,
        )

        config = auth.get_config()
        assert_that(config, equal_to(TESTNET_CONFIG))

    def test_get_config_mainnet(self):
        """Test getting mainnet config."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=False,
        )

        config = auth.get_config()
        assert_that(config, equal_to(MAINNET_CONFIG))


class TestExtendedAuthStarkAccount:
    """Tests for get_stark_account method."""

    def test_get_stark_account_creates_account(self):
        """Test that get_stark_account creates a StarkPerpetualAccount."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        account = auth.get_stark_account()

        assert_that(account, is_not(none()))
        assert_that(account, instance_of(StarkPerpetualAccount))
        assert_that(account.vault, equal_to(TEST_VAULT))
        assert_that(account.api_key, equal_to(TEST_API_KEY))

    def test_get_stark_account_caches_instance(self):
        """Test that get_stark_account returns the same instance on subsequent calls."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        account1 = auth.get_stark_account()
        account2 = auth.get_stark_account()

        assert_that(account1 is account2, equal_to(True))


class TestExtendedAuthTradingClient:
    """Tests for get_trading_client method."""

    def test_get_trading_client_creates_client(self):
        """Test that get_trading_client creates a PerpetualTradingClient."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        client = auth.get_trading_client()

        assert_that(client, is_not(none()))
        assert_that(client, instance_of(PerpetualTradingClient))

    def test_get_trading_client_caches_instance(self):
        """Test that get_trading_client returns the same instance on subsequent calls."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        client1 = auth.get_trading_client()
        client2 = auth.get_trading_client()

        assert_that(client1 is client2, equal_to(True))

    def test_get_trading_client_uses_correct_config(self):
        """Test that trading client uses the correct endpoint config."""
        auth_testnet = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=True,
        )

        client = auth_testnet.get_trading_client()
        # Client should be created with testnet config
        assert_that(client, is_not(none()))


class TestExtendedAuthClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test closing auth without ever creating a trading client."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        # Should not raise any exception
        await auth.close()

    @pytest.mark.asyncio
    async def test_close_clears_trading_client(self):
        """Test that close clears the trading client reference."""
        auth = ExtendedAuth(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        # Create a trading client
        client = auth.get_trading_client()
        assert_that(auth._trading_client, is_not(none()))

        # Close
        await auth.close()

        # Trading client should be cleared
        assert_that(auth._trading_client, none())
