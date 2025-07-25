#!/usr/bin/env python3
"""
Test script to verify JDBC setup and prevent JVM crashes.
This script tests the JDBC environment step by step.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_java_environment():
    """Test Java environment."""
    print("🔧 Testing Java Environment")
    print("=" * 50)

    import subprocess

    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java is available")
            print(f"   Version info: {result.stderr.split()[2]}")
            return True
        else:
            print("❌ Java not found")
            return False
    except FileNotFoundError:
        print("❌ Java not found in PATH")
        return False


def test_python_dependencies():
    """Test Python JDBC dependencies."""
    print("\n🐍 Testing Python Dependencies")
    print("=" * 50)

    try:
        import jaydebeapi

        print(f"✅ JayDeBeApi available: v{jaydebeapi.__version__}")
    except ImportError as e:
        print(f"❌ JayDeBeApi not available: {e}")
        return False

    try:
        import jpype

        print(f"✅ JPype1 available: v{jpype.__version__}")
    except ImportError as e:
        print(f"❌ JPype1 not available: {e}")
        return False

    return True


def test_jdbc_driver():
    """Test JDBC driver availability."""
    print("\n📦 Testing JDBC Driver")
    print("=" * 50)

    # Prioritize Flight SQL JDBC driver
    flight_sql_jar = "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
    legacy_jar = "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"

    if os.path.exists(flight_sql_jar):
        jar_path = flight_sql_jar
        driver_type = "Apache Arrow Flight SQL JDBC"
        print(f"✅ {driver_type} driver found: {jar_path}")
    elif os.path.exists(legacy_jar):
        jar_path = legacy_jar
        driver_type = "Legacy Dremio JDBC"
        print(f"✅ {driver_type} driver found: {jar_path}")
        print("⚠️ Consider upgrading to Flight SQL JDBC driver for better performance")
    else:
        print(f"❌ No JDBC driver found")
        print(f"   Expected: {flight_sql_jar}")
        print(f"   Or: {legacy_jar}")
        print("   Run setup script to download: ./setup.sh")
        return False

    # Check file size
    size = os.path.getsize(jar_path)
    print(f"   File size: {size:,} bytes ({size/1024/1024:.1f} MB)")

    if size > 1024 * 1024:  # At least 1MB
        print("✅ Driver file size looks reasonable")
        return True
    else:
        print("⚠ Driver file seems too small")
        return False


def test_jpype_startup():
    """Test JPype JVM startup safely."""
    print("\n🚀 Testing JPype JVM Startup")
    print("=" * 50)

    try:
        import jpype

        if jpype.isJVMStarted():
            print("ℹ JVM already started")
            return True

        print("🔄 Testing JVM startup capability...")

        # Check if we're on macOS with Java 21+ which has known compatibility issues
        import platform

        java_version = os.popen("java -version 2>&1 | head -n 1").read()
        is_macos = platform.system() == "Darwin"
        is_java21_plus = (
            "21." in java_version or "22." in java_version or "23." in java_version
        )

        if is_macos and is_java21_plus:
            print("⚠️  Detected macOS with Java 21+ - known JPype compatibility issues")
            print("   JDBC functionality may be limited on this platform")
            print("   Consider using ADBC driver for better compatibility")
            print("✅ JPype available but JVM startup skipped for safety")
            return True

        print("🔄 Starting JVM...")

        # Use the current Java installation
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            print(f"   Using JAVA_HOME: {java_home}")
            # Try to find the JVM library
            possible_jvm_paths = [
                os.path.join(java_home, "lib", "server", "libjvm.dylib"),  # macOS
                os.path.join(java_home, "lib", "server", "libjvm.so"),  # Linux
                os.path.join(
                    java_home, "jre", "lib", "server", "libjvm.dylib"
                ),  # macOS older
                os.path.join(
                    java_home, "jre", "lib", "server", "libjvm.so"
                ),  # Linux older
            ]

            jvm_path = None
            for path in possible_jvm_paths:
                if os.path.exists(path):
                    jvm_path = path
                    break

            if not jvm_path:
                print("   Could not find JVM library, using default")
                jvm_path = jpype.getDefaultJVMPath()
        else:
            print("   Using default Java")
            jvm_path = jpype.getDefaultJVMPath()

        print(f"   JVM path: {jvm_path}")

        # Start JVM with Apache Arrow Flight SQL JDBC driver requirements
        # Apache Arrow requires specific module access for memory management
        jpype.startJVM(
            jvm_path,
            "-Xmx512m",  # Reasonable memory limit
            "-Xms128m",  # Small initial heap
            "-Djava.awt.headless=true",  # Headless mode
            # Apache Arrow Flight SQL JDBC driver requirements
            "--add-opens=java.base/java.nio=org.apache.arrow.memory.core,ALL-UNNAMED",
            "--add-opens=java.base/sun.nio.ch=org.apache.arrow.memory.core,ALL-UNNAMED",
            "--add-opens=java.base/java.lang=org.apache.arrow.memory.core,ALL-UNNAMED",
            "--add-opens=java.base/java.lang.reflect=org.apache.arrow.memory.core,ALL-UNNAMED",
            "--add-opens=java.base/java.io=org.apache.arrow.memory.core,ALL-UNNAMED",
            "--add-opens=java.base/java.util=org.apache.arrow.memory.core,ALL-UNNAMED",
            convertStrings=False,  # Don't auto-convert strings
        )

        print("✅ JVM started successfully")

        # Test basic Java functionality
        java_lang = jpype.JPackage("java").lang
        system = java_lang.System
        java_version = system.getProperty("java.version")
        print(f"   Java version from JVM: {java_version}")

        return True

    except Exception as e:
        print(f"❌ JVM startup failed: {e}")
        print("   This is expected on some macOS + Java 21+ combinations")
        print("   JDBC functionality will be limited but ADBC driver should work")
        return False


def test_jdbc_connection():
    """Test JDBC connection to Dremio."""
    print("\n🔗 Testing JDBC Connection")
    print("=" * 50)

    # Check if JVM is available
    try:
        import jpype

        if not jpype.isJVMStarted():
            print("❌ JVM not started - JDBC connection test skipped")
            print("   This is expected on macOS with Java 21+ compatibility issues")
            return False
    except Exception as e:
        print(f"❌ JPype not available: {e}")
        return False

    # Get configuration
    dremio_url = os.environ.get("DREMIO_CLOUD_URL")
    pat = os.environ.get("DREMIO_PAT")

    if not dremio_url or not pat:
        print("❌ Missing DREMIO_CLOUD_URL or DREMIO_PAT environment variables")
        print("   Set these in your .env file to test JDBC connectivity")
        return False

    try:
        import jaydebeapi

        # Determine which JDBC driver to use first
        flight_sql_jar = "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
        legacy_jar = "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"

        if os.path.exists(flight_sql_jar):
            jar_path = flight_sql_jar
            driver_class = "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver"
            driver_type = "Flight SQL"
            print(f"🔧 Using Apache Arrow Flight SQL JDBC driver: {jar_path}")
        elif os.path.exists(legacy_jar):
            jar_path = legacy_jar
            driver_class = "com.dremio.jdbc.Driver"
            driver_type = "Legacy Dremio"
            print(f"🔧 Using Legacy Dremio JDBC driver: {jar_path}")
        else:
            print("❌ No JDBC driver found")
            return False

        # Generate JDBC URLs based on driver type
        if driver_type == "Flight SQL":
            if "api.dremio.cloud" in dremio_url:
                # Flight SQL JDBC URLs for Dremio Cloud
                import urllib.parse
                encoded_pat = urllib.parse.quote(pat, safe="")
                jdbc_urls = [
                    f"jdbc:arrow-flight-sql://data.dremio.cloud:443?useEncryption=true&token={encoded_pat}",
                ]
            else:
                # On-premise Flight SQL
                jdbc_urls = [
                    f"jdbc:arrow-flight-sql://{dremio_url.replace('https://', '').replace('http://', '')}:32010"
                ]
        else:
            # Legacy Dremio JDBC URLs with SSL troubleshooting options
            if "api.dremio.cloud" in dremio_url:
                jdbc_urls = [
                    "jdbc:dremio:direct=data.dremio.cloud:443;ssl=true",
                    "jdbc:dremio:direct=data.dremio.cloud:443;ssl=true;useSSL=true",
                    "jdbc:dremio:direct=data.dremio.cloud:443;ssl=true;disableCertificateVerification=true",
                    "jdbc:dremio:direct=sql.dremio.cloud:443;ssl=true",
                ]
            else:
                jdbc_urls = [
                    dremio_url.replace("https://", "jdbc:dremio:direct=").replace(
                        "http://", "jdbc:dremio:direct="
                    )
                    + ":31010"
                ]

        print("🔐 Using Personal Access Token authentication")
        print(f"🔧 Driver: {driver_type}")

        # Configure authentication based on driver type
        if driver_type == "Flight SQL":
            # Flight SQL JDBC uses token in URL
            auth_configs = [{}]  # No separate auth needed, token in URL
        else:
            # Legacy Dremio JDBC uses separate auth
            auth_configs = [
                {"user": "$token", "password": pat},
                {"user": "dremio_cloud_pat", "password": pat},
                {"user": "token", "password": pat},
            ]

        # Add JDBC JAR to classpath before attempting connection
        print(f"🔄 Adding JDBC JAR to classpath: {jar_path}")
        try:
            import jpype
            if jpype.isJVMStarted():
                jpype.addClassPath(jar_path)
                print("✅ JAR added to classpath successfully")
            else:
                print("⚠️ JVM not started, JAR will be loaded by jaydebeapi.connect()")
        except Exception as e:
            print(f"⚠️ Could not add JAR to classpath: {e}")

        connection = None
        last_error = None
        successful_config = None

        # Try each JDBC URL with each auth config
        for url_idx, jdbc_url in enumerate(jdbc_urls, 1):
            print(f"\n📡 Trying JDBC URL {url_idx}: {jdbc_url}")

            for auth_idx, auth_config in enumerate(auth_configs, 1):
                try:
                    if driver_type == "Flight SQL":
                        print(f"🔄 Flight SQL connection (token in URL)")
                        connection = jaydebeapi.connect(
                            driver_class, jdbc_url, auth_config, jar_path
                        )
                    else:
                        print(f"🔄 Auth method {auth_idx}: user='{auth_config.get('user', 'N/A')}'")
                        connection = jaydebeapi.connect(
                            driver_class, jdbc_url, auth_config, jar_path
                        )
                    print(f"✅ Connection successful!")
                    print(f"   URL: {jdbc_url}")
                    if driver_type == "Flight SQL":
                        print(f"   Auth: Token in URL")
                    else:
                        print(f"   Auth: {auth_config.get('user', 'N/A')}")
                    successful_config = (jdbc_url, auth_config)
                    break
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    print(f"❌ Failed: {error_msg}")

                    # Provide specific guidance based on error type
                    if "SSL negotiation failed" in error_msg:
                        print(
                            "   🔍 SSL negotiation failed - certificate or TLS version issue"
                        )
                    elif "ConnectionFailedException" in error_msg:
                        print(
                            "   🔍 Connection failed - network, auth, or endpoint issue"
                        )
                    elif "Class com.dremio.jdbc.Driver is not found" in error_msg:
                        print("   🔍 JDBC driver class not found - JAR loading issue")
                    elif "Authentication failed" in error_msg:
                        print("   🔍 Authentication failed - check PAT validity")
                    continue

            if connection is not None:
                break

        if connection is None:
            print(f"\n❌ All connection attempts failed. Last error: {last_error}")
            raise last_error

        print("✅ JDBC connection established")

        # Test simple query
        cursor = connection.cursor()
        cursor.execute("SELECT 'JDBC Test' as test_column")
        result = cursor.fetchone()

        print(f"✅ Test query successful: {result}")

        # Clean up
        cursor.close()
        connection.close()

        print("✅ Connection closed cleanly")
        return True

    except Exception as e:
        print(f"❌ JDBC connection failed: {e}")
        print("   This may be due to:")
        print("   - Missing or incorrect credentials in .env file")
        print("   - Network connectivity issues")
        print("   - JVM compatibility issues on this platform")
        return False


def cleanup_jvm():
    """Safely shutdown JVM."""
    print("\n🧹 Cleaning Up")
    print("=" * 50)

    try:
        import jpype

        if jpype.isJVMStarted():
            print("🔄 Shutting down JVM...")
            jpype.shutdownJVM()
            print("✅ JVM shutdown complete")
    except Exception as e:
        print(f"⚠ JVM shutdown warning: {e}")


def main():
    """Run all JDBC tests."""
    print("🧪 JDBC Environment Testing Suite")
    print("Testing JDBC setup to prevent JVM crashes")
    print("=" * 70)

    success = True

    # Test 1: Java environment
    if not test_java_environment():
        success = False

    # Test 2: Python dependencies
    if not test_python_dependencies():
        success = False

    # Test 3: JDBC driver
    if not test_jdbc_driver():
        success = False

    # Test 4: JPype JVM startup
    if not test_jpype_startup():
        success = False

    # Test 5: JDBC connection (only if previous tests passed)
    if success:
        if not test_jdbc_connection():
            success = False
    else:
        print("\n⚠ Skipping JDBC connection test due to previous failures")

    # Cleanup
    cleanup_jvm()

    print("\n" + "=" * 70)
    if success:
        print("🎉 All JDBC tests passed! Environment is ready.")
        print("✅ JDBC driver can be safely enabled in the server.")
    else:
        print("❌ Some JDBC tests failed. Check the output above.")
        print("⚠ Recommend keeping JDBC disabled until issues are resolved.")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
