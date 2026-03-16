"""
Unit tests for Extended SDK Client and setup functions.

Tests Client, AsyncClient, setup(), and async_setup().
"""

import pytest
from hamcrest import assert_that, equal_to, is_not, none, instance_of

from extended.client import Client
from extended.async_client import AsyncClient
from extended.setup import setup as extended_setup, async_setup
from extended.api.info import InfoAPI
from extended.api.info_async import AsyncInfoAPI
from extended.api.exchange import ExchangeAPI
from extended.api.exchange_async import AsyncExchangeAPI


# Test credentials
TEST_API_KEY = "test-api-key-12345"
TEST_VAULT = 10001
TEST_PRIVATE_KEY = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
TEST_PUBLIC_KEY = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"


class TestClientInit:
    """Tests for Client initialization."""

    def test_client_init_with_required_params(self):
        """Test client initialization with required parameters."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.address, equal_to(TEST_PUBLIC_KEY))
        assert_that(client.public_key, equal_to(TEST_PUBLIC_KEY))

    def test_client_init_with_testnet(self):
        """Test client initialization with testnet=True."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=True,
        )

        assert_that(client, is_not(none()))

    def test_client_init_with_timeout(self):
        """Test client initialization with custom timeout."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            timeout=60,
        )

        assert_that(client._timeout, equal_to(60))


class TestClientProperties:
    """Tests for Client properties."""

    def test_info_property(self):
        """Test info property returns InfoAPI."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.info, is_not(none()))
        assert_that(client.info, instance_of(InfoAPI))

    def test_exchange_property(self):
        """Test exchange property returns ExchangeAPI."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.exchange, is_not(none()))
        assert_that(client.exchange, instance_of(ExchangeAPI))

    def test_address_property(self):
        """Test address property returns stark public key."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.address, equal_to(TEST_PUBLIC_KEY))

    def test_public_key_property(self):
        """Test public_key property returns stark public key."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.public_key, equal_to(TEST_PUBLIC_KEY))


class TestClientClose:
    """Tests for Client close method."""

    def test_client_close(self):
        """Test that close() runs without error."""
        client = Client(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        # Should not raise
        client.close()


class TestAsyncClientInit:
    """Tests for AsyncClient initialization."""

    def test_async_client_init(self):
        """Test async client initialization."""
        client = AsyncClient(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.address, equal_to(TEST_PUBLIC_KEY))
        assert_that(client.public_key, equal_to(TEST_PUBLIC_KEY))

    def test_async_client_info_property(self):
        """Test async client info property returns AsyncInfoAPI."""
        client = AsyncClient(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.info, is_not(none()))
        assert_that(client.info, instance_of(AsyncInfoAPI))

    def test_async_client_exchange_property(self):
        """Test async client exchange property returns AsyncExchangeAPI."""
        client = AsyncClient(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(client.exchange, is_not(none()))
        assert_that(client.exchange, instance_of(AsyncExchangeAPI))


class TestSetupFunction:
    """Tests for extended_setup() function."""

    def test_setup_returns_tuple(self):
        """Test extended_setup() returns (address, info, exchange) tuple."""
        address, info, exchange = extended_setup(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(address, equal_to(TEST_PUBLIC_KEY))
        assert_that(info, instance_of(InfoAPI))
        assert_that(exchange, instance_of(ExchangeAPI))

    def test_setup_with_testnet(self):
        """Test extended_setup() with testnet=True."""
        address, info, exchange = extended_setup(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=True,
        )

        assert_that(address, equal_to(TEST_PUBLIC_KEY))


class TestAsyncSetupFunction:
    """Tests for async_setup() function."""

    def test_async_setup_returns_tuple(self):
        """Test async_setup() returns (address, info, exchange) tuple."""
        address, info, exchange = async_setup(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
        )

        assert_that(address, equal_to(TEST_PUBLIC_KEY))
        assert_that(info, instance_of(AsyncInfoAPI))
        assert_that(exchange, instance_of(AsyncExchangeAPI))

    def test_async_setup_with_testnet(self):
        """Test async_setup() with testnet=True."""
        address, info, exchange = async_setup(
            api_key=TEST_API_KEY,
            vault=TEST_VAULT,
            stark_private_key=TEST_PRIVATE_KEY,
            stark_public_key=TEST_PUBLIC_KEY,
            testnet=True,
        )

        assert_that(address, equal_to(TEST_PUBLIC_KEY))
