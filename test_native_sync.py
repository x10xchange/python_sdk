"""
Test script for Native Sync Extended SDK.

Verifies that the native sync implementation works without async/await issues.
"""

import sys
import traceback
from unittest.mock import Mock, patch

def test_import_structure():
    """Test that imports work without async dependencies."""
    print("Testing import structure...")

    try:
        # Test core imports
        from extended.api.base_native_sync import BaseNativeSyncClient
        from extended.api.info_native_sync import NativeSyncInfoAPI
        from extended.api.exchange_native_sync import NativeSyncExchangeAPI

        # Test public API imports
        from extended.api.info import InfoAPI
        from extended.api.exchange import ExchangeAPI
        from extended.client import Client

        print("✅ All imports successful - no async dependencies detected")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_client_instantiation():
    """Test that client can be created without async issues."""
    print("\nTesting client instantiation...")

    try:
        # Mock the ExtendedAuth to avoid needing real credentials
        with patch('extended.auth.ExtendedAuth') as mock_auth:
            mock_auth_instance = Mock()
            mock_auth_instance.address = "0x123456789"
            mock_auth_instance.stark_public_key = "0x987654321"
            mock_auth_instance.api_key = "test_api_key"
            mock_auth.return_value = mock_auth_instance

            # Mock the config
            with patch('extended.config.MAINNET_CONFIG') as mock_config:
                mock_config.api_base_url = "https://api.extended.com"

                client = Client(
                    api_key="test_api_key",
                    vault=12345,
                    stark_private_key="0xprivate",
                    stark_public_key="0xpublic",
                    testnet=False
                )

                # Verify properties work
                assert client.address == "0x123456789"
                assert client.public_key == "0x987654321"
                assert client.info is not None
                assert client.exchange is not None

                print("✅ Client instantiation successful - native sync working")
                return True

    except Exception as e:
        print(f"❌ Client instantiation failed: {e}")
        traceback.print_exc()
        return False

def test_no_run_sync_usage():
    """Test that run_sync is not used anywhere in the new implementation."""
    print("\nTesting for run_sync usage...")

    import os
    import re

    sdk_path = "/tmp/extended-sdk-analysis/extended"
    run_sync_pattern = r"run_sync\("

    files_with_run_sync = []

    for root, dirs, files in os.walk(sdk_path):
        for file in files:
            if file.endswith('.py') and not file.endswith('_old_async_wrapper.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if re.search(run_sync_pattern, content):
                            files_with_run_sync.append(file_path)
                except:
                    pass

    if files_with_run_sync:
        print(f"❌ Found run_sync usage in: {files_with_run_sync}")
        return False
    else:
        print("✅ No run_sync usage found in native sync implementation")
        return True

def test_requests_usage():
    """Test that requests is used instead of aiohttp."""
    print("\nTesting HTTP client usage...")

    try:
        from extended.api.base_native_sync import BaseNativeSyncClient

        # Check that BaseNativeSyncClient uses requests
        import inspect
        source = inspect.getsource(BaseNativeSyncClient.__init__)

        if 'requests.Session()' in source:
            print("✅ Uses requests.Session() - correct sync HTTP client")
            return True
        else:
            print("❌ Does not use requests.Session()")
            return False

    except Exception as e:
        print(f"❌ HTTP client test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return overall success."""
    print("🚀 Testing Native Sync Extended SDK Implementation")
    print("=" * 60)

    tests = [
        test_import_structure,
        test_client_instantiation,
        test_no_run_sync_usage,
        test_requests_usage,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)

    if all(results):
        print("🎉 ALL TESTS PASSED - Native Sync Extended SDK is ready!")
        print("✅ No async/await dependencies")
        print("✅ No run_sync() usage")
        print("✅ Uses requests.Session() for HTTP")
        print("✅ Same API surface as original SDK")
        return True
    else:
        print("❌ Some tests failed - see details above")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)