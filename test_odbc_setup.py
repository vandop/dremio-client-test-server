#!/usr/bin/env python3
"""
Test script to verify ODBC setup is working correctly.
This script tests that the Dremio Arrow Flight SQL ODBC driver is properly installed and configured.
"""

import sys
import subprocess
import os

def test_odbc_system():
    """Test ODBC system components."""
    print("🔧 Testing ODBC System Components")
    print("=" * 50)
    
    # Test odbcinst command
    try:
        result = subprocess.run(['odbcinst', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ odbcinst available: {result.stdout.strip()}")
        else:
            print(f"❌ odbcinst failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("❌ odbcinst command not found")
        return False
    
    # Check ODBC configuration files
    config_files = [
        ('/etc/odbcinst.ini', 'Driver definitions'),
        ('/etc/odbc.ini', 'Data source definitions')
    ]
    
    for file_path, description in config_files:
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ {description}: {file_path} - NOT FOUND")
    
    return True

def test_odbc_drivers():
    """Test installed ODBC drivers."""
    print("\n🚗 Testing ODBC Drivers")
    print("=" * 50)
    
    # List installed drivers
    try:
        result = subprocess.run(['odbcinst', '-q', '-d'], capture_output=True, text=True)
        if result.returncode == 0:
            drivers = result.stdout.strip().split('\n')
            drivers = [d.strip('[]') for d in drivers if d.strip()]
            
            if drivers:
                print(f"✅ Found {len(drivers)} ODBC driver(s):")
                for driver in drivers:
                    print(f"   • {driver}")
                
                # Check for Dremio driver specifically
                dremio_drivers = [d for d in drivers if 'arrow' in d.lower() or 'flight' in d.lower() or 'dremio' in d.lower()]
                if dremio_drivers:
                    print(f"✅ Dremio-compatible drivers found: {', '.join(dremio_drivers)}")
                    return True
                else:
                    print("⚠️  No Dremio-compatible drivers found")
                    return False
            else:
                print("❌ No ODBC drivers found")
                return False
        else:
            print(f"❌ Failed to list drivers: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error listing drivers: {e}")
        return False

def test_odbc_dsns():
    """Test configured Data Source Names (DSNs)."""
    print("\n📊 Testing ODBC Data Sources")
    print("=" * 50)
    
    # List configured DSNs
    try:
        result = subprocess.run(['odbcinst', '-q', '-s'], capture_output=True, text=True)
        if result.returncode == 0:
            dsns = result.stdout.strip().split('\n')
            dsns = [d.strip('[]') for d in dsns if d.strip()]
            
            if dsns:
                print(f"✅ Found {len(dsns)} configured DSN(s):")
                for dsn in dsns:
                    print(f"   • {dsn}")
                return True
            else:
                print("⚠️  No DSNs configured (this is optional)")
                return True
        else:
            print(f"❌ Failed to list DSNs: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Error listing DSNs: {e}")
        return False

def test_pyodbc_integration():
    """Test PyODBC integration with installed drivers."""
    print("\n🐍 Testing PyODBC Integration")
    print("=" * 50)
    
    try:
        import pyodbc
        print("✅ PyODBC module available")
        
        # Get available drivers from PyODBC
        drivers = pyodbc.drivers()
        if drivers:
            print(f"✅ PyODBC can see {len(drivers)} driver(s):")
            for driver in drivers:
                print(f"   • {driver}")
            
            # Check for Dremio driver
            dremio_drivers = [d for d in drivers if 'arrow' in d.lower() or 'flight' in d.lower() or 'dremio' in d.lower()]
            if dremio_drivers:
                print(f"✅ Dremio-compatible drivers available to PyODBC: {', '.join(dremio_drivers)}")
                return True
            else:
                print("⚠️  No Dremio-compatible drivers available to PyODBC")
                return False
        else:
            print("❌ PyODBC cannot see any drivers")
            return False
            
    except ImportError:
        print("❌ PyODBC module not available")
        return False
    except Exception as e:
        print(f"❌ Error testing PyODBC: {e}")
        return False

def test_driver_library():
    """Test if the ODBC driver library file exists."""
    print("\n📚 Testing Driver Library")
    print("=" * 50)
    
    # Common locations for Dremio ODBC driver
    possible_locations = [
        '/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so*',
        '/usr/lib/x86_64-linux-gnu/libarrow-odbc.so*',
        '/usr/local/lib/libarrow-odbc.so*'
    ]
    
    import glob
    
    for pattern in possible_locations:
        matches = glob.glob(pattern)
        if matches:
            for match in matches:
                if os.path.exists(match):
                    print(f"✅ Driver library found: {match}")
                    
                    # Check if file is readable
                    if os.access(match, os.R_OK):
                        print(f"   ✅ Library is readable")
                    else:
                        print(f"   ⚠️  Library exists but is not readable")
                    
                    return True
    
    print("❌ No Dremio ODBC driver library found")
    print("   Expected locations:")
    for pattern in possible_locations:
        print(f"   • {pattern}")
    
    return False

def main():
    """Run all ODBC tests."""
    print("🧪 ODBC Setup Verification")
    print("=" * 60)
    print("This script verifies that the Dremio Arrow Flight SQL ODBC driver")
    print("is properly installed and configured.")
    print()
    
    # Run tests
    tests = [
        ("ODBC System", test_odbc_system),
        ("ODBC Drivers", test_odbc_drivers),
        ("ODBC DSNs", test_odbc_dsns),
        ("Driver Library", test_driver_library),
        ("PyODBC Integration", test_pyodbc_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! ODBC setup is working correctly.")
        print("The PyODBC driver should now be available in the multi-driver client.")
        return 0
    elif passed >= 3:  # At least basic functionality works
        print(f"\n⚠️  {total - passed} test(s) failed, but basic ODBC functionality appears to work.")
        print("The PyODBC driver may still be usable.")
        return 0
    else:
        print(f"\n💥 {total - passed} test(s) failed. ODBC setup needs attention.")
        print("Run './setup.sh' to install and configure the ODBC driver.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
