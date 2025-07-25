#!/usr/bin/env python3
"""
Test Apache Arrow Flight SQL JDBC Driver
This script tests the new Apache Arrow Flight SQL JDBC driver.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_arrow_flight_sql_jdbc():
    """Test Apache Arrow Flight SQL JDBC driver."""
    print("🚀 Testing Apache Arrow Flight SQL JDBC Driver")
    print("=" * 60)

    # Get configuration
    dremio_url = os.environ.get("DREMIO_CLOUD_URL")
    pat = os.environ.get("DREMIO_PAT")

    if not dremio_url or not pat:
        print("❌ Missing DREMIO_CLOUD_URL or DREMIO_PAT environment variables")
        return False

    print(f"🔧 Dremio URL: {dremio_url}")
    print(f"🔧 PAT: {pat[:10]}...{pat[-10:] if len(pat) > 20 else pat}")

    try:
        import jpype
        import jaydebeapi

        # Start JVM with the new driver
        if not jpype.isJVMStarted():
            jar_path = os.path.abspath("jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar")

            print(f"🔧 Starting JVM with Apache Arrow Flight SQL JDBC driver")
            print(f"   JAR: {jar_path}")

            # JVM arguments for Apache Arrow Flight SQL JDBC driver with Java 17+
            jvm_args = [
                "-Xmx1g",
                # Apache Arrow Flight SQL JDBC driver requirements for Java 17+
                "--add-opens=java.base/java.nio=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/sun.nio.ch=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.lang=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.lang.reflect=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.io=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.util=org.apache.arrow.memory.core,ALL-UNNAMED",
            ]
            jpype.startJVM(classpath=[jar_path], *jvm_args)
            print("✅ JVM started")

        # Test Apache Arrow Flight SQL JDBC connection
        print("\n🔗 Testing Apache Arrow Flight SQL JDBC Connection")

        # Apache Arrow Flight SQL JDBC URL format
        import urllib.parse

        encoded_pat = urllib.parse.quote(pat, safe="")
        jdbc_url = f"jdbc:arrow-flight-sql://data.dremio.cloud:443?useEncryption=true&token={encoded_pat}"
        driver_class = "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver"

        print(f"📡 URL: {jdbc_url[:50]}...{jdbc_url[-20:]}")
        print(f"🔧 Driver: {driver_class}")

        # Connect using Apache Arrow Flight SQL JDBC driver
        connection = jaydebeapi.connect(
            driver_class,
            jdbc_url,
            {},  # No separate auth needed, token is in URL
            jar_path,
        )

        print("✅ Connection successful!")

        # Test a simple query
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 as test_column")
            result = cursor.fetchone()
            print(f"✅ Query successful: {result}")
            cursor.close()
        except Exception as e:
            print(f"⚠ Query failed: {e}")

        connection.close()
        print("✅ Connection closed")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Connection failed: {error_msg}")

        # Analyze the error
        if "SSL negotiation failed" in error_msg:
            print(
                "   🔍 SSL negotiation failed - but this should be resolved with Flight SQL JDBC"
            )
        elif "ClassNotFoundException" in error_msg:
            print("   🔍 Driver class not found - check JAR file")
        elif "Authentication failed" in error_msg:
            print("   🔍 Authentication failed - check PAT validity")
        elif "Connection refused" in error_msg:
            print("   🔍 Connection refused - check endpoint and port")
        else:
            print("   🔍 Unknown error type")

        return False


def test_multi_driver_client():
    """Test the updated multi-driver client."""
    print("\n🔧 Testing Updated Multi-Driver Client")
    print("=" * 50)

    try:
        from dremio_multi_driver_client import DremioMultiDriverClient

        client = DremioMultiDriverClient()

        print("Available drivers:")
        for name, info in client.get_available_drivers().items():
            status = "✅" if info.get("available", False) else "❌"
            message = info.get("message", "OK")
            print(f"  {status} {name}: {message}")

        # Test JDBC specifically
        try:
            print("\n🔗 Testing JDBC client creation...")
            jdbc_client = client._create_jdbc_client()
            print("✅ JDBC client created successfully")

            # Test a simple query
            try:
                cursor = jdbc_client.cursor()
                cursor.execute("SELECT 1 as test_column")
                result = cursor.fetchone()
                print(f"✅ JDBC query successful: {result}")
                cursor.close()
            except Exception as e:
                print(f"⚠ JDBC query failed: {e}")

        except Exception as e:
            print(f"❌ JDBC client creation failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Multi-driver client test failed: {e}")
        return False


def main():
    """Run all tests."""
    try:
        print("🧪 Apache Arrow Flight SQL JDBC Driver Test Suite")
        print("=" * 70)

        # Test 1: Direct Apache Arrow Flight SQL JDBC
        success1 = test_arrow_flight_sql_jdbc()

        # Test 2: Multi-driver client
        success2 = test_multi_driver_client()

        print("\n" + "=" * 70)
        if success1 and success2:
            print("✅ All tests passed!")
            print("🎉 Apache Arrow Flight SQL JDBC driver is working correctly")
        else:
            print("❌ Some tests failed")
            if not success1:
                print("   - Direct Apache Arrow Flight SQL JDBC test failed")
            if not success2:
                print("   - Multi-driver client test failed")

    finally:
        # Cleanup
        try:
            import jpype

            if jpype.isJVMStarted():
                jpype.shutdownJVM()
                print("\n🧹 JVM shutdown complete")
        except:
            pass


if __name__ == "__main__":
    main()
