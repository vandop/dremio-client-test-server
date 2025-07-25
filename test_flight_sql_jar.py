#!/usr/bin/env python3

"""
Test script to verify Flight SQL JDBC JAR loading
"""

import os
import sys

def test_jar_loading():
    """Test if the Flight SQL JDBC JAR can be loaded"""
    
    print("🧪 Testing Flight SQL JDBC JAR Loading")
    print("=" * 50)
    
    jar_path = "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
    
    if not os.path.exists(jar_path):
        print(f"❌ JAR file not found: {jar_path}")
        return False
    
    print(f"✅ JAR file found: {jar_path}")
    
    try:
        import jpype
        import jaydebeapi
        
        print(f"✅ JPype version: {jpype.__version__}")
        print(f"✅ JayDeBeApi version: {jaydebeapi.__version__}")
        
        # Start JVM if not already started
        if not jpype.isJVMStarted():
            print("🔄 Starting JVM with Apache Arrow Flight SQL requirements...")
            # Apache Arrow Flight SQL JDBC driver requirements for Java 17+
            jvm_args = [
                "--add-opens=java.base/java.nio=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/sun.nio.ch=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.lang=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.lang.reflect=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.io=org.apache.arrow.memory.core,ALL-UNNAMED",
                "--add-opens=java.base/java.util=org.apache.arrow.memory.core,ALL-UNNAMED",
            ]
            jpype.startJVM(classpath=[jar_path], *jvm_args)
            print("✅ JVM started successfully")
        else:
            print("✅ JVM already running")
            jpype.addClassPath(jar_path)
            print("✅ JAR added to classpath")
        
        # Try to load the driver class
        print("🔄 Testing driver class loading...")
        
        try:
            # Method 1: Direct class loading
            driver_class = jpype.JClass("org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver")
            print("✅ Driver class loaded successfully via JClass")
            
            # Try to instantiate the driver
            driver_instance = driver_class()
            print("✅ Driver instance created successfully")
            
            # Get driver info
            major_version = driver_instance.getMajorVersion()
            minor_version = driver_instance.getMinorVersion()
            print(f"✅ Driver version: {major_version}.{minor_version}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load driver class: {e}")
            
            # Method 2: Try using DriverManager
            try:
                print("🔄 Trying DriverManager approach...")
                DriverManager = jpype.JClass("java.sql.DriverManager")
                driver_class = jpype.JClass("org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver")
                DriverManager.registerDriver(driver_class())
                print("✅ Driver registered with DriverManager")
                return True
            except Exception as e2:
                print(f"❌ DriverManager approach failed: {e2}")
                return False
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Clean up
        if jpype.isJVMStarted():
            print("🔄 Shutting down JVM...")
            jpype.shutdownJVM()
            print("✅ JVM shutdown complete")

def test_jar_contents():
    """Test JAR file contents"""
    
    print("\n🔍 Testing JAR Contents")
    print("=" * 50)
    
    jar_path = "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
    
    try:
        import zipfile
        
        with zipfile.ZipFile(jar_path, 'r') as jar:
            # Check for driver class
            driver_class_path = "org/apache/arrow/driver/jdbc/ArrowFlightJdbcDriver.class"
            if driver_class_path in jar.namelist():
                print(f"✅ Driver class found: {driver_class_path}")
            else:
                print(f"❌ Driver class not found: {driver_class_path}")
                return False
            
            # Check for service registration
            service_path = "META-INF/services/java.sql.Driver"
            if service_path in jar.namelist():
                print(f"✅ Service registration found: {service_path}")
                
                # Read service file
                with jar.open(service_path) as service_file:
                    content = service_file.read().decode('utf-8')
                    if "org.apache.arrow.driver.jdbc.ArrowFlightJdbcDriver" in content:
                        print("✅ Driver class properly registered in service file")
                    else:
                        print("❌ Driver class not found in service file")
                        print(f"   Content: {content}")
                        return False
            else:
                print(f"❌ Service registration not found: {service_path}")
                return False
            
            # Check JAR size and structure
            file_count = len(jar.namelist())
            print(f"✅ JAR contains {file_count} files")
            
            # Look for key dependencies
            key_classes = [
                "org/apache/arrow/",
                "io/grpc/",
                "com/google/protobuf/"
            ]
            
            for key_class in key_classes:
                matching_files = [f for f in jar.namelist() if f.startswith(key_class)]
                if matching_files:
                    print(f"✅ Found {len(matching_files)} files for {key_class}")
                else:
                    print(f"⚠️ No files found for {key_class}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error reading JAR file: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 Flight SQL JDBC JAR Testing Suite")
    print("Diagnosing JAR loading issues")
    
    # Test JAR contents first
    contents_ok = test_jar_contents()
    
    if not contents_ok:
        print("\n❌ JAR contents test failed")
        return 1
    
    # Test JAR loading
    loading_ok = test_jar_loading()
    
    print(f"\n📋 Test Results:")
    print(f"   JAR Contents: {'✅ PASS' if contents_ok else '❌ FAIL'}")
    print(f"   JAR Loading: {'✅ PASS' if loading_ok else '❌ FAIL'}")
    
    if contents_ok and loading_ok:
        print("\n🎉 Flight SQL JDBC JAR is working correctly!")
        return 0
    else:
        print("\n❌ Flight SQL JDBC JAR has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
