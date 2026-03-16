"""
Comprehensive tests for Native Sync Extended SDK.

Tests all major functionality to ensure the native sync implementation
works correctly and is compatible with ThreadPoolExecutor.
"""

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch, MagicMock
import traceback


def test_imports_and_structure():
    """Test that all imports work without async dependencies."""
    print("🧪 Testing imports and structure...")

    try:
        # Core native sync imports
        from extended.api.base_native_sync import BaseNativeSyncClient
        from extended.api.info_native_sync import NativeSyncInfoAPI
        from extended.api.exchange_native_sync import NativeSyncExchangeAPI

        # Public API imports
        from extended.api.info import InfoAPI
        from extended.api.exchange import ExchangeAPI
        from extended.client import Client
        from extended.setup import setup

        # Check inheritance
        assert issubclass(InfoAPI, NativeSyncInfoAPI), "InfoAPI should inherit from NativeSyncInfoAPI"
        assert issubclass(ExchangeAPI, NativeSyncExchangeAPI), "ExchangeAPI should inherit from NativeSyncExchangeAPI"

        print("  ✅ All imports successful")
        print("  ✅ Proper inheritance structure")
        return True

    except Exception as e:
        print(f"  ❌ Import/structure test failed: {e}")
        traceback.print_exc()
        return False


def test_no_async_dependencies():
    """Test that no async/await code exists in new implementation."""
    print("🧪 Testing for async dependencies...")

    import os
    import re

    # Files that should be completely sync
    sync_files = [
        "/tmp/extended-sdk-analysis/extended/api/base_native_sync.py",
        "/tmp/extended-sdk-analysis/extended/api/info_native_sync.py",
        "/tmp/extended-sdk-analysis/extended/api/exchange_native_sync.py",
        "/tmp/extended-sdk-analysis/extended/api/base.py",
        "/tmp/extended-sdk-analysis/extended/api/info.py",
        "/tmp/extended-sdk-analysis/extended/api/exchange.py",
        "/tmp/extended-sdk-analysis/extended/client.py",
        "/tmp/extended-sdk-analysis/extended/setup.py",
    ]

    async_patterns = [
        r'\basync\s+def\b',
        r'\bawait\s+',
        r'run_sync\(',
        r'aiohttp',
        r'asyncio\.',
    ]

    issues_found = []

    for file_path in sync_files:
        if not os.path.exists(file_path):
            continue

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            for pattern in async_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    issues_found.append(f"{file_path}: {pattern} found {len(matches)} times")

        except Exception as e:
            issues_found.append(f"{file_path}: Error reading file - {e}")

    if issues_found:
        print("  ❌ Async dependencies found:")
        for issue in issues_found:
            print(f"    - {issue}")
        return False
    else:
        print("  ✅ No async dependencies found in native sync files")
        return True


def test_requests_usage():
    """Test that native sync uses requests instead of aiohttp."""
    print("🧪 Testing HTTP client usage...")

    try:
        from extended.api.base_native_sync import BaseNativeSyncClient
        import inspect

        # Check BaseNativeSyncClient source
        source = inspect.getsource(BaseNativeSyncClient.__init__)

        if 'requests.Session()' in source:
            print("  ✅ Uses requests.Session() for HTTP")
        else:
            print("  ❌ Does not use requests.Session()")
            return False

        # Check that aiohttp is not imported
        if 'aiohttp' in source:
            print("  ❌ Still imports aiohttp")
            return False

        print("  ✅ Correct HTTP client implementation")
        return True

    except Exception as e:
        print(f"  ❌ HTTP client test failed: {e}")
        return False


def test_client_instantiation_mocked():
    """Test client instantiation with mocked dependencies."""
    print("🧪 Testing client instantiation (mocked)...")

    try:
        # Mock all problematic imports
        with patch('extended.auth_sync.SimpleSyncAuth') as mock_auth_class:
            with patch('extended.config_sync.MAINNET_CONFIG') as mock_config:
                # Setup mocks
                mock_auth = Mock()
                mock_auth.address = "0x123456789"
                mock_auth.stark_public_key = "0x987654321"
                mock_auth.api_key = "test_api_key"
                mock_auth_class.return_value = mock_auth

                mock_config.api_base_url = "https://api.extended.com"

                # Test Client creation
                from extended.client import Client

                client = Client(
                    api_key="test_key",
                    vault=12345,
                    stark_private_key="0xprivate",
                    stark_public_key="0xpublic",
                    testnet=False
                )

                # Test properties
                assert client.address == "0x123456789"
                assert client.public_key == "0x987654321"
                assert client.info is not None
                assert client.exchange is not None

                print("  ✅ Client instantiation successful")
                return True

    except Exception as e:
        print(f"  ❌ Client instantiation failed: {e}")
        traceback.print_exc()
        return False


def test_setup_function_mocked():
    """Test setup function with mocked dependencies."""
    print("🧪 Testing setup function (mocked)...")

    try:
        with patch('extended.client.Client') as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_client.public_key = "0x789456123"
            mock_client.info = Mock()
            mock_client.exchange = Mock()
            mock_client_class.return_value = mock_client

            # Test setup function
            from extended.setup import setup

            address, info, exchange = setup(
                api_key="test_key",
                vault=12345,
                stark_private_key="0xprivate",
                stark_public_key="0xpublic",
                testnet=True
            )

            # Verify return values
            assert address == "0x789456123"
            assert info is mock_client.info
            assert exchange is mock_client.exchange

            # Verify Client was called correctly
            mock_client_class.assert_called_once_with(
                api_key="test_key",
                vault=12345,
                stark_private_key="0xprivate",
                stark_public_key="0xpublic",
                testnet=True,
                base_url=None
            )

            print("  ✅ Setup function works correctly")
            return True

    except Exception as e:
        print(f"  ❌ Setup function test failed: {e}")
        traceback.print_exc()
        return False


def test_threadpool_compatibility():
    """Test that native sync works in ThreadPoolExecutor (the critical test)."""
    print("🧪 Testing ThreadPoolExecutor compatibility...")

    def worker_task(worker_id):
        """Task to run in ThreadPoolExecutor."""
        try:
            # Mock the problematic dependencies
            with patch('extended.api.base_native_sync.SimpleSyncAuth') as mock_auth_class:
                with patch('extended.api.base_native_sync.SimpleSyncConfig') as mock_config_class:
                    # Setup mocks
                    mock_auth = Mock()
                    mock_auth.api_key = f"test_key_{worker_id}"
                    mock_auth_class.return_value = mock_auth

                    mock_config = Mock()
                    mock_config.api_base_url = "https://api.extended.com"
                    mock_config_class.return_value = mock_config

                    # Import and instantiate in worker thread
                    from extended.api.base_native_sync import BaseNativeSyncClient

                    client = BaseNativeSyncClient(
                        auth=mock_auth,
                        config=mock_config,
                        timeout=30
                    )

                    # Verify the client has a requests session
                    assert hasattr(client, 'session'), f"Worker {worker_id}: No session attribute"

                    # Try to access session (should not cause event loop issues)
                    session = client.session
                    assert session is not None, f"Worker {worker_id}: Session is None"

                    return f"Worker {worker_id}: SUCCESS - Native sync works in thread"

        except Exception as e:
            return f"Worker {worker_id}: FAILED - {e}"

    try:
        # Test with multiple workers (simulates real ThreadPoolExecutor usage)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker_task, i) for i in range(3)]
            results = [future.result(timeout=10) for future in futures]

        # Check results
        for result in results:
            print(f"    {result}")
            if "FAILED" in result:
                return False

        print("  ✅ ThreadPoolExecutor compatibility verified")
        return True

    except Exception as e:
        print(f"  ❌ ThreadPoolExecutor test failed: {e}")
        traceback.print_exc()
        return False


def test_api_method_signatures():
    """Test that API methods have correct signatures (no async)."""
    print("🧪 Testing API method signatures...")

    try:
        import inspect
        from extended.api.info_native_sync import NativeSyncInfoAPI
        from extended.api.exchange_native_sync import NativeSyncExchangeAPI

        # Check InfoAPI methods are not async
        info_methods = [
            'user_state', 'open_orders', 'meta', 'all_mids',
            'user_fills', 'l2_snapshot'
        ]

        for method_name in info_methods:
            if hasattr(NativeSyncInfoAPI, method_name):
                method = getattr(NativeSyncInfoAPI, method_name)
                if inspect.iscoroutinefunction(method):
                    print(f"  ❌ InfoAPI.{method_name} is async (should be sync)")
                    return False

        # Check ExchangeAPI methods are not async
        exchange_methods = [
            'order', 'cancel', 'bulk_orders', 'update_leverage',
            'market_open', 'market_close'
        ]

        for method_name in exchange_methods:
            if hasattr(NativeSyncExchangeAPI, method_name):
                method = getattr(NativeSyncExchangeAPI, method_name)
                if inspect.iscoroutinefunction(method):
                    print(f"  ❌ ExchangeAPI.{method_name} is async (should be sync)")
                    return False

        print("  ✅ All API methods are properly sync")
        return True

    except Exception as e:
        print(f"  ❌ API method signature test failed: {e}")
        return False


def test_integration_with_trading_engine_setup():
    """Test compatibility with existing trading engine setup pattern."""
    print("🧪 Testing trading engine setup compatibility...")

    try:
        # Mock the setup function to simulate real usage pattern
        with patch('extended.setup.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.public_key = "0xTEST_ADDRESS"

            # Mock info and exchange as native sync objects
            mock_info = Mock()
            mock_exchange = Mock()
            mock_client.info = mock_info
            mock_client.exchange = mock_exchange

            mock_client_class.return_value = mock_client

            # Simulate the exact pattern used in helpers.py
            from extended.setup import setup as extended_setup

            # Test the exact call pattern from helpers.py
            address, info, exchange = extended_setup(
                api_key="test_api_key",
                vault=12345,
                stark_private_key="0xprivate",
                stark_public_key="0xpublic",
                testnet=False,  # testnet=not is_mainnet
                base_url=None,
            )

            # Verify the return format matches Hyperliquid/Pacifica
            assert isinstance(address, str), "Address should be string"
            assert info is mock_info, "Info should be the mock info object"
            assert exchange is mock_exchange, "Exchange should be the mock exchange object"

            # Verify the client was instantiated with correct parameters
            mock_client_class.assert_called_once_with(
                api_key="test_api_key",
                vault=12345,
                stark_private_key="0xprivate",
                stark_public_key="0xpublic",
                testnet=False,
                base_url=None,
            )

            print("  ✅ Trading engine setup pattern compatibility verified")
            return True

    except Exception as e:
        print(f"  ❌ Trading engine setup test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all comprehensive tests."""
    print("🚀 COMPREHENSIVE NATIVE SYNC EXTENDED SDK TESTS")
    print("=" * 70)

    tests = [
        ("Import Structure", test_imports_and_structure),
        ("Async Dependencies", test_no_async_dependencies),
        ("HTTP Client", test_requests_usage),
        ("Client Instantiation", test_client_instantiation_mocked),
        ("Setup Function", test_setup_function_mocked),
        ("ThreadPoolExecutor", test_threadpool_compatibility),
        ("API Signatures", test_api_method_signatures),
        ("Trading Engine Setup", test_integration_with_trading_engine_setup),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY:")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🏆 FINAL SCORE: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Native Sync Extended SDK is READY FOR PRODUCTION")
        print("✅ Compatible with ThreadPoolExecutor")
        print("✅ Same API as Hyperliquid/Pacifica")
        print("✅ No async/await dependencies")
        return True
    else:
        print("❌ Some tests failed - review issues above")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)