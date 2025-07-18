#!/usr/bin/env python3
"""
Test JDBC connection directly to Dremio using Arrow Flight SQL JDBC Driver.
This script tests the JDBC setup by making direct connections to Dremio.
"""

import os
import sys
import glob
from pathlib import Path
from config import Config

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_jdbc_environment():
    """Test JDBC environment prerequisites."""
    print("🔍 Testing JDBC Environment Prerequisites")
    
    # Test Java environment
    java_home = os.environ.get('JAVA_HOME')
    if not java_home:
        print("❌ JAVA_HOME not set")
        return False
    
    if not os.path.exists(java_home):
        print(f"❌ JAVA_HOME directory not found: {java_home}")
        return False
    
    print(f"✅ JAVA_HOME: {java_home}")
    
    # Test JPype
    try:
        import jpype
        print(f"✅ JPype available: v{jpype.__version__}")
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
    
    # Test JDBC driver JAR
    jar_pattern = os.path.join(os.path.dirname(__file__), 'jdbc-drivers', '*.jar')
    jar_files = glob.glob(jar_pattern)
    
    if not jar_files:
        print("❌ No JDBC driver JAR files found in jdbc-drivers/ directory")
        print("   Run: ./setup.sh to download the Arrow Flight SQL JDBC driver")
        return False
    
    jar_path = jar_files[0]
    jar_size = os.path.getsize(jar_path) / (1024 * 1024)  # MB
    print(f"✅ JDBC driver found: {os.path.basename(jar_path)} ({jar_size:.1f} MB)")
    
    return True

def test_dremio_jdbc_connection():
    """Test direct JDBC connection to Dremio."""
    print("🔌 Testing Direct JDBC Connection to Dremio")
    
    try:
        import jpype
        import jaydebeapi
        
        # Load configuration
        Config.validate_dremio_config()
        
        # Find JDBC driver JAR
        jar_pattern = os.path.join(os.path.dirname(__file__), 'jdbc-drivers', '*.jar')
        jar_files = glob.glob(jar_pattern)
        jar_path = jar_files[0]
        
        print(f"Using JAR: {os.path.basename(jar_path)}")
        
        # Build connection URL for Dremio Cloud
        if Config.DREMIO_CLOUD_URL and 'api.dremio.cloud' in Config.DREMIO_CLOUD_URL:
            # Dremio Cloud connection
            jdbc_url = "jdbc:arrow-flight-sql://data.dremio.cloud:443?useEncryption=true"
            auth_user = "$token"
            auth_pass = Config.DREMIO_PAT
            print(f"🌐 Connecting to Dremio Cloud: data.dremio.cloud:443")
        else:
            print("❌ Only Dremio Cloud connections are currently supported in this test")
            return False
        
        if not auth_pass:
            print("❌ No Personal Access Token (PAT) found")
            print("   Set DREMIO_PAT in your .env file")
            return False
        
        print(f"🔑 Using PAT authentication")
        
        # Start JVM if not already started
        if not jpype.isJVMStarted():
            print("🚀 Starting JVM...")
            jpype.startJVM(classpath=[jar_path])
        else:
            jpype.addClassPath(jar_path)
        
        print("🔗 Establishing JDBC connection...")
        
        # Connect using Arrow Flight SQL JDBC driver
        connection = jaydebeapi.connect(
            "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver",
            jdbc_url,
            {"user": auth_user, "password": auth_pass},
            jar_path
        )
        
        print("✅ JDBC connection established successfully!")
        
        # Test simple query
        print("🧪 Testing simple query...")
        cursor = connection.cursor()
        cursor.execute("SELECT 1 as test_value")
        result = cursor.fetchone()
        
        print(f"✅ Query executed successfully: {result}")
        
        # Test system query
        print("🧪 Testing system information query...")
        cursor.execute("SELECT current_timestamp as server_time")
        result = cursor.fetchone()
        
        print(f"✅ Server time query: {result}")
        
        # Clean up
        cursor.close()
        connection.close()
        
        print("✅ JDBC connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ JDBC connection failed: {e}")
        
        # Provide specific error guidance
        error_msg = str(e)
        if "Class org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver is not found" in error_msg:
            print("💡 Solution: Download the Arrow Flight SQL JDBC driver")
            print("   Run: ./setup.sh")
        elif "UNAUTHENTICATED" in error_msg or "authentication" in error_msg.lower():
            print("💡 Solution: Check your Personal Access Token (PAT)")
            print("   1. Verify DREMIO_PAT in your .env file")
            print("   2. Ensure the PAT is valid and not expired")
        elif "UNAVAILABLE" in error_msg or "Connection refused" in error_msg:
            print("💡 Solution: Check network connectivity")
            print("   1. Verify internet connection")
            print("   2. Check if data.dremio.cloud is accessible")
        elif "SSL" in error_msg or "certificate" in error_msg:
            print("💡 Solution: SSL/TLS issue")
            print("   1. Check network firewall settings")
            print("   2. Verify SSL certificates")
        
        return False

def test_jdbc_queries():
    """Test various JDBC queries against Dremio."""
    print("📊 Testing JDBC Queries")
    
    try:
        import jpype
        import jaydebeapi
        
        # Find JDBC driver JAR
        jar_pattern = os.path.join(os.path.dirname(__file__), 'jdbc-drivers', '*.jar')
        jar_files = glob.glob(jar_pattern)
        jar_path = jar_files[0]
        
        # Build connection
        jdbc_url = "jdbc:arrow-flight-sql://data.dremio.cloud:443?useEncryption=true"
        auth_user = "$token"
        auth_pass = Config.DREMIO_PAT
        
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[jar_path])
        
        connection = jaydebeapi.connect(
            "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver",
            jdbc_url,
            {"user": auth_user, "password": auth_pass},
            jar_path
        )
        
        cursor = connection.cursor()
        
        # Test queries
        test_queries = [
            ("Basic SELECT", "SELECT 1 as number, 'test' as text"),
            ("Current timestamp", "SELECT current_timestamp as now"),
            ("Math operations", "SELECT 2 + 2 as sum, 10 * 5 as product"),
        ]
        
        for description, sql in test_queries:
            print(f"\n🔍 {description}")
            print(f"   SQL: {sql}")
            
            try:
                cursor.execute(sql)
                result = cursor.fetchone()
                print(f"   ✅ Result: {result}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        # Clean up
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Query testing failed: {e}")
        return False

def main():
    """Run comprehensive JDBC tests."""
    print("🧪 Dremio JDBC Connection Test")
    print("Arrow Flight SQL JDBC Driver")
    
    tests = [
        ("JDBC Environment", test_jdbc_environment),
        ("Dremio JDBC Connection", test_dremio_jdbc_connection),
        ("JDBC Queries", test_jdbc_queries),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print_section(test_name)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
        
        # Stop if a critical test fails
        if not results[test_name] and test_name in ["JDBC Environment", "Dremio JDBC Connection"]:
            print(f"\n❌ Critical test '{test_name}' failed. Stopping further tests.")
            break
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    if all(results.values()):
        print("\n🎉 All JDBC tests passed!")
        print("Your JDBC setup is working correctly with Dremio.")
    else:
        print("\n⚠️ Some tests failed.")
        print("Check the error messages above for troubleshooting guidance.")
    
    # Cleanup
    try:
        import jpype
        if jpype.isJVMStarted():
            jpype.shutdownJVM()
            print("\n🧹 JVM shutdown complete")
    except:
        pass
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
