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
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
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
    
    jar_path = "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"
    
    if os.path.exists(jar_path):
        print(f"✅ JDBC driver found: {jar_path}")
        
        # Check file size
        size = os.path.getsize(jar_path)
        print(f"   File size: {size:,} bytes ({size/1024/1024:.1f} MB)")
        
        if size > 1024 * 1024:  # At least 1MB
            print("✅ Driver file size looks reasonable")
            return True
        else:
            print("⚠ Driver file seems too small")
            return False
    else:
        print(f"❌ JDBC driver not found: {jar_path}")
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
        
        print("🔄 Starting JVM...")

        # Use Java 11 which is more compatible with JPype
        java11_path = "/Library/Java/JavaVirtualMachines/temurin-11.jdk/Contents/Home/lib/server/libjvm.dylib"

        if os.path.exists(java11_path):
            print("   Using Java 11 for better JPype compatibility")
            jvm_path = java11_path
        else:
            print("   Using default Java (may cause issues with Java 21)")
            jvm_path = jpype.getDefaultJVMPath()

        # Start JVM with conservative settings
        jpype.startJVM(
            jvm_path,
            "-Xmx256m",  # Limited memory
            "-Xms64m",   # Small initial heap
            "-XX:+UseSerialGC",  # Use simple serial GC
            "-Djava.awt.headless=true",  # Headless mode
            convertStrings=False  # Don't auto-convert strings
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
        return False

def test_jdbc_connection():
    """Test JDBC connection to Dremio."""
    print("\n🔗 Testing JDBC Connection")
    print("=" * 50)
    
    # Get configuration
    dremio_url = os.environ.get('DREMIO_CLOUD_URL')
    pat = os.environ.get('DREMIO_PAT')
    
    if not dremio_url or not pat:
        print("❌ Missing DREMIO_CLOUD_URL or DREMIO_PAT environment variables")
        return False
    
    try:
        import jaydebeapi
        import jpype
        
        # Prepare JDBC URL
        if 'api.dremio.cloud' in dremio_url:
            jdbc_url = dremio_url.replace('https://api.dremio.cloud', 'jdbc:dremio:direct=data.dremio.cloud:443;ssl=true')
        else:
            jdbc_url = dremio_url.replace('https://', 'jdbc:dremio:direct=').replace('http://', 'jdbc:dremio:direct=') + ':31010'
        
        jar_path = "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"
        
        print(f"📡 Connecting to: {jdbc_url}")
        print("🔐 Using Personal Access Token authentication")
        
        # Create connection
        connection = jaydebeapi.connect(
            "com.dremio.jdbc.Driver",
            jdbc_url,
            {"user": "dremio_cloud_pat", "password": pat},
            jar_path
        )
        
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

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
