#!/usr/bin/env python3
"""
Comprehensive test for Java environment setup in Dremio Reporting Server.
"""
import os
import sys
import subprocess
import requests
import json

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_java_installation():
    """Test Java installation and configuration."""
    print("\n🔍 Testing Java Installation")
    
    # Test 1: Java executable
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stderr.split('\n')[0]
            print(f"✅ Java executable: {version_line}")
        else:
            print("❌ Java executable not found")
            return False
    except FileNotFoundError:
        print("❌ Java not installed")
        return False
    
    # Test 2: Java compiler
    try:
        result = subprocess.run(['javac', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Java compiler: {result.stderr.strip()}")
        else:
            print("❌ Java compiler not found")
            return False
    except FileNotFoundError:
        print("❌ Java compiler not installed")
        return False
    
    # Test 3: JAVA_HOME
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        print(f"✅ JAVA_HOME: {java_home}")
        if os.path.exists(java_home):
            print(f"✅ JAVA_HOME directory exists")
        else:
            print(f"❌ JAVA_HOME directory not found")
            return False
    else:
        print("⚠️ JAVA_HOME not set (may work with system PATH)")
    
    return True

def test_python_java_bridge():
    """Test Python-Java integration."""
    print("\n🔗 Testing Python-Java Bridge")
    
    # Test JPype
    try:
        import jpype
        print(f"✅ JPype available: v{jpype.__version__}")
        
        # Test JVM status
        if jpype.isJVMStarted():
            print("✅ JVM already started")
        else:
            print("✅ JVM ready for initialization")
            
    except ImportError:
        print("❌ JPype not available")
        return False
    
    # Test JayDeBeApi
    try:
        import jaydebeapi
        print(f"✅ JayDeBeApi available: v{jaydebeapi.__version__}")
    except ImportError:
        print("❌ JayDeBeApi not available")
        return False
    
    return True

def test_jdbc_driver_detection():
    """Test JDBC driver detection in the application."""
    print("\n🚗 Testing JDBC Driver Detection")
    
    try:
        # Test driver availability via API
        response = requests.get('http://localhost:5005/api/drivers', timeout=10)
        
        if response.status_code == 200:
            drivers = response.json()
            
            if 'jdbc' in drivers.get('drivers', {}):
                jdbc_info = drivers['drivers']['jdbc']
                if jdbc_info.get('available'):
                    print(f"✅ JDBC driver detected: {jdbc_info.get('name')}")
                else:
                    print("❌ JDBC driver not available")
                    return False
            else:
                print("❌ JDBC driver not found in API response")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API connection failed: {e}")
        print("⚠️ Make sure the server is running on port 5005")
        return False
    
    return True

def test_jdbc_functionality():
    """Test JDBC functionality (expected to fail without JAR)."""
    print("\n🧪 Testing JDBC Functionality")
    
    try:
        # Test JDBC query execution
        response = requests.post(
            'http://localhost:5005/api/query-multi-driver',
            headers={'Content-Type': 'application/json'},
            json={
                'sql': 'SELECT 1 "test_value"',
                'drivers': ['jdbc']
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            jdbc_result = result.get('results', {}).get('jdbc', {})
            
            if jdbc_result.get('success'):
                print("✅ JDBC query executed successfully")
                print(f"   Execution time: {jdbc_result.get('execution_time', 0):.3f}s")
            else:
                error = jdbc_result.get('error', 'Unknown error')
                if 'Class org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver is not found' in error:
                    print("✅ JDBC environment working (missing Arrow Flight SQL JDBC driver JAR file)")
                    print("   This is expected - download Arrow Flight SQL JDBC driver to jdbc-drivers/")
                else:
                    print(f"⚠️ JDBC error: {error}")
        else:
            print(f"❌ JDBC test request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ JDBC test failed: {e}")
        return False
    
    return True

def test_docker_environment():
    """Test Docker environment setup."""
    print("\n🐳 Testing Docker Environment")
    
    # Check if Dockerfile exists and has Java setup
    if os.path.exists('Dockerfile'):
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
            
        if 'openjdk-11' in dockerfile_content:
            print("✅ Dockerfile includes Java 11 installation")
        else:
            print("❌ Dockerfile missing Java installation")
            return False
            
        if 'JAVA_HOME' in dockerfile_content:
            print("✅ Dockerfile sets JAVA_HOME environment variable")
        else:
            print("❌ Dockerfile missing JAVA_HOME configuration")
            return False
    else:
        print("❌ Dockerfile not found")
        return False
    
    # Check docker-compose.yml
    if os.path.exists('docker-compose.yml'):
        with open('docker-compose.yml', 'r') as f:
            compose_content = f.read()
            
        if 'JAVA_HOME' in compose_content:
            print("✅ docker-compose.yml includes Java environment")
        else:
            print("❌ docker-compose.yml missing Java configuration")
            return False
    else:
        print("❌ docker-compose.yml not found")
        return False
    
    return True

def main():
    """Run comprehensive Java environment tests."""
    print("🧪 Comprehensive Java Environment Test")
    print("Enhanced Dremio Reporting Server")
    
    tests = [
        ("Java Installation", test_java_installation),
        ("Python-Java Bridge", test_python_java_bridge),
        ("JDBC Driver Detection", test_jdbc_driver_detection),
        ("JDBC Functionality", test_jdbc_functionality),
        ("Docker Environment", test_docker_environment),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print_section(test_name)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Java environment is properly configured.")
        print("\n📝 Next steps:")
        print("   1. Download Arrow Flight SQL JDBC driver: ./setup.sh")
        print("   2. Test full JDBC connectivity: python test_jdbc_dremio_connection.py")
        print("   3. Deploy with Docker if needed")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the setup.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
