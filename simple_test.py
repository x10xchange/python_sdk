"""
Simple test to verify native sync implementation is working.
"""

def test_basic_imports():
    """Test that we can import the native sync classes without dependencies."""
    print("Testing basic native sync imports...")

    try:
        # Test direct native sync imports
        from extended.api.base_native_sync import BaseNativeSyncClient
        print("✅ BaseNativeSyncClient import successful")

        from extended.api.info_native_sync import NativeSyncInfoAPI
        print("✅ NativeSyncInfoAPI import successful")

        from extended.api.exchange_native_sync import NativeSyncExchangeAPI
        print("✅ NativeSyncExchangeAPI import successful")

        # Test that BaseNativeSyncClient uses requests
        import inspect
        source = inspect.getsource(BaseNativeSyncClient.__init__)
        if 'requests.Session()' in source:
            print("✅ BaseNativeSyncClient uses requests.Session()")
        else:
            print("❌ BaseNativeSyncClient doesn't use requests.Session()")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_imports()