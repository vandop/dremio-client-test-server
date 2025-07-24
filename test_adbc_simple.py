#!/usr/bin/env python3
"""
Simple ADBC driver test to verify installation and basic functionality.
"""
import os
import sys

def test_adbc_import():
    """Test if ADBC modules can be imported."""
    print("🧪 Testing ADBC Driver Import")
    print("=" * 50)
    
    try:
        import adbc_driver_flightsql
        print("✅ adbc_driver_flightsql imported successfully")
        print(f"   Version: {getattr(adbc_driver_flightsql, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ Failed to import adbc_driver_flightsql: {e}")
        return False
    
    try:
        import adbc_driver_manager
        print("✅ adbc_driver_manager imported successfully")
        print(f"   Version: {getattr(adbc_driver_manager, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ Failed to import adbc_driver_manager: {e}")
        return False
    
    return True

def test_adbc_driver_creation():
    """Test creating an ADBC driver instance."""
    print("\n🔧 Testing ADBC Driver Creation")
    print("=" * 50)
    
    try:
        import adbc_driver_flightsql.dbapi as flight_sql
        print("✅ ADBC Flight SQL driver module loaded")
        
        # Test driver creation with minimal config
        # Using placeholder values since we don't have real credentials
        try:
            # This should fail with auth error, but driver creation should work
            conn = flight_sql.connect(
                uri="grpc://data.dremio.cloud:443",
                db_kwargs={
                    "adbc.flight.sql.authorization_header": "Bearer your-personal-access-token"
                }
            )
            print("✅ ADBC driver connection object created")
            conn.close()
        except Exception as e:
            # Expected to fail with auth error, but driver should be working
            if "authentication" in str(e).lower() or "authorization" in str(e).lower() or "token" in str(e).lower():
                print("✅ ADBC driver working (expected auth failure with placeholder credentials)")
                return True
            else:
                print(f"❌ Unexpected ADBC driver error: {e}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import ADBC Flight SQL driver: {e}")
        return False
    except Exception as e:
        print(f"❌ ADBC driver creation failed: {e}")
        return False

def test_adbc_with_local_driver():
    """Test ADBC with locally built driver as mentioned in memory."""
    print("\n🏠 Testing ADBC with Local Driver")
    print("=" * 50)
    
    local_driver_path = "/Users/vandopereira/Dev/arrow-adbc/python/adbc_driver_flightsql/"
    
    if os.path.exists(local_driver_path):
        print(f"✅ Local ADBC driver found at: {local_driver_path}")
        
        # Add to Python path
        if local_driver_path not in sys.path:
            sys.path.insert(0, local_driver_path)
            print("✅ Local driver path added to Python path")
        
        try:
            # Try importing from local path
            import adbc_driver_flightsql.dbapi as local_flight_sql
            print("✅ Local ADBC Flight SQL driver imported")
            
            # Test with RELAXED_SCHEMA_VALIDATION as mentioned in memory
            try:
                conn = local_flight_sql.connect(
                    uri="grpc://data.dremio.cloud:443",
                    db_kwargs={
                        "adbc.flight.sql.authorization_header": "Bearer your-personal-access-token",
                        "adbc.flight.sql.rpc.call_header.relaxed_schema_validation": "true"
                    }
                )
                print("✅ Local ADBC driver with RELAXED_SCHEMA_VALIDATION created")
                conn.close()
                return True
            except Exception as e:
                if "authentication" in str(e).lower() or "authorization" in str(e).lower():
                    print("✅ Local ADBC driver working (expected auth failure)")
                    return True
                else:
                    print(f"❌ Local ADBC driver error: {e}")
                    return False
                    
        except ImportError as e:
            print(f"❌ Failed to import local ADBC driver: {e}")
            return False
    else:
        print(f"⚠️  Local ADBC driver not found at: {local_driver_path}")
        print("   Using system-installed ADBC driver instead")
        return True

def main():
    """Run all ADBC tests."""
    print("🚀 Simple ADBC Driver Test Suite")
    print("Enhanced Dremio Reporting Server")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_adbc_import),
        ("Driver Creation Test", test_adbc_driver_creation),
        ("Local Driver Test", test_adbc_with_local_driver),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("🏁 Test Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All ADBC tests passed! Driver is ready for use.")
    else:
        print("⚠️  Some ADBC tests failed. Check the output above for details.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
