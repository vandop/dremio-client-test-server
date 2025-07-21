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
import jpype
import jaydebeapi
from typing import Tuple, Dict, Any, Optional

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def setup_jdbc_client() -> Tuple[str, str, Dict[str, str], Optional[str]]:
    """
    Set up JDBC client configuration and return connection parameters.

    Returns:
        Tuple of (jdbc_url, jar_path, auth_args, project_id)
    """
    # Load configuration
    Config.validate_dremio_config()

    # Find JDBC driver JAR
    jar_pattern = os.path.join(os.path.dirname(__file__), 'jdbc-drivers', '*.jar')
    jar_files = glob.glob(jar_pattern)

    if not jar_files:
        raise FileNotFoundError("No JDBC driver JAR files found in jdbc-drivers/ directory")

    jar_path = jar_files[0]
    print(f"Using JAR: {os.path.basename(jar_path)}")

    # Build connection URL for Dremio Cloud
    if Config.DREMIO_CLOUD_URL and 'api.dremio.cloud' in Config.DREMIO_CLOUD_URL:
        if not Config.DREMIO_PAT:
            raise ValueError("No Personal Access Token (PAT) found. Set DREMIO_PAT in your .env file")

        # Use Arrow Flight SQL JDBC driver with token authentication
        jdbc_url = "jdbc:arrow-flight-sql://data.dremio.cloud:443?useEncryption=true"
        jdbc_arrow_flight_args = { "user": "", "token": Config.DREMIO_PAT }

        # Add project_id if available
        project_id = getattr(Config, 'DREMIO_PROJECT_ID', None)

        print(f"🌐 Connecting to Dremio Cloud: data.dremio.cloud:443")
        print(f"🔑 Using PAT authentication")

        return jdbc_url, jar_path, jdbc_arrow_flight_args, project_id
    else:
        raise ValueError("Only Dremio Cloud connections are currently supported")

def create_jdbc_connection(jdbc_url: str, jar_path: str, auth_args: Dict[str, str]) -> Any:
    """
    Create a JDBC connection using the Arrow Flight SQL JDBC driver.

    Args:
        jdbc_url: The JDBC connection URL
        jar_path: Path to the JDBC driver JAR file
        auth_args: Authentication arguments (user/token)

    Returns:
        JDBC connection object
    """
    # Start JVM if not already started
    if not jpype.isJVMStarted():
        print("🚀 Starting JVM with Arrow memory access...")
        jpype.startJVM(
            "--add-opens=java.base/java.nio=org.apache.arrow.memory.core,ALL-UNNAMED",
            classpath=[jar_path]
        )
    else:
        jpype.addClassPath(jar_path)

    print("🔗 Establishing JDBC connection...")

    # Use authentication arguments
    connection = jaydebeapi.connect(
        "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver",
        jdbc_url,
        auth_args,
        jar_path
    )

    return connection

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
        # Set up JDBC client configuration
        jdbc_url, jar_path, auth_args, project_id = setup_jdbc_client()

        # Create JDBC connection
        connection = create_jdbc_connection(jdbc_url, jar_path, auth_args)
        
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
        # Set up JDBC client configuration
        jdbc_url, jar_path, auth_args, project_id = setup_jdbc_client()

        # Create JDBC connection
        connection = create_jdbc_connection(jdbc_url, jar_path, auth_args)
        
        cursor = connection.cursor()
        
        # Test queries
        test_queries = [
            ("Basic SELECT", "SELECT 1 as number, 'test' as text"),
            ("Current timestamp", "SELECT current_timestamp as now"),
            ("Math operations", "SELECT 2 + 2 sum_, 10 * 5 product"),
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
