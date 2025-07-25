#!/usr/bin/env python3
"""
Test script to verify Python setup is working correctly.
This script tests that all required Python dependencies are available.
"""

import sys
import subprocess

def test_python_command():
    """Test that 'python' command is available and working."""
    print("🐍 Testing Python Command Availability")
    print("=" * 50)
    
    # Test python command
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 'python' command available: {result.stdout.strip()}")
        else:
            print(f"❌ 'python' command failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("❌ 'python' command not found")
        return False
    
    # Test python3 command
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 'python3' command available: {result.stdout.strip()}")
        else:
            print(f"❌ 'python3' command failed: {result.stderr.strip()}")
    except FileNotFoundError:
        print("❌ 'python3' command not found")
    
    return True

def test_core_dependencies():
    """Test that core Python dependencies are available."""
    print("\n📦 Testing Core Dependencies")
    print("=" * 50)
    
    dependencies = [
        ('flask', 'Flask web framework'),
        ('requests', 'HTTP requests library'),
        ('pandas', 'Data analysis library'),
        ('pyarrow', 'Apache Arrow Python library'),
        ('dotenv', 'Environment variable loader'),
    ]
    
    all_available = True
    
    for module, description in dependencies:
        try:
            if module == 'dotenv':
                from dotenv import load_dotenv
                print(f"✅ {module}: {description}")
            else:
                __import__(module)
                print(f"✅ {module}: {description}")
        except ImportError:
            print(f"❌ {module}: {description} - NOT AVAILABLE")
            all_available = False
    
    return all_available

def test_jdbc_dependencies():
    """Test JDBC-related dependencies."""
    print("\n☕ Testing JDBC Dependencies")
    print("=" * 50)
    
    jdbc_deps = [
        ('jpype', 'Java-Python bridge'),
        ('jaydebeapi', 'JDBC driver for Python'),
    ]
    
    all_available = True
    
    for module, description in jdbc_deps:
        try:
            imported_module = __import__(module)
            if hasattr(imported_module, '__version__'):
                version = imported_module.__version__
                print(f"✅ {module}: {description} (v{version})")
            else:
                print(f"✅ {module}: {description}")
        except ImportError:
            print(f"❌ {module}: {description} - NOT AVAILABLE")
            all_available = False
    
    return all_available

def test_adbc_dependencies():
    """Test ADBC-related dependencies."""
    print("\n🚀 Testing ADBC Dependencies")
    print("=" * 50)
    
    try:
        import adbc_driver_flightsql.dbapi
        print("✅ adbc_driver_flightsql: ADBC Flight SQL driver")
        return True
    except ImportError:
        print("❌ adbc_driver_flightsql: ADBC Flight SQL driver - NOT AVAILABLE")
        return False

def main():
    """Run all tests."""
    print("🧪 Python Setup Verification")
    print("=" * 60)
    print("This script verifies that Python and all required dependencies")
    print("are properly installed and accessible.")
    print()
    
    # Run tests
    tests = [
        ("Python Command", test_python_command),
        ("Core Dependencies", test_core_dependencies),
        ("JDBC Dependencies", test_jdbc_dependencies),
        ("ADBC Dependencies", test_adbc_dependencies),
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
        print("\n🎉 All tests passed! Python setup is working correctly.")
        print("You can now run './run.sh' to start the server.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Run './setup.sh' to fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
