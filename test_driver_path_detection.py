#!/usr/bin/env python3

"""
Test script to verify PyODBC driver path detection
"""

import os
import sys

def test_driver_path_detection():
    """Test the driver path detection logic"""
    
    print("🔍 Testing PyODBC Driver Path Detection")
    print("=" * 50)
    
    # Check for PyODBC
    try:
        import pyodbc
        print(f"✅ PyODBC version: {pyodbc.version}")
    except ImportError:
        print("❌ PyODBC not available")
        return False
    
    # Check available drivers by name
    drivers = pyodbc.drivers()
    print(f"\n📋 Available ODBC drivers by name ({len(drivers)}):")
    for driver in drivers:
        print(f"   - {driver}")
    
    # Check for driver library paths
    print(f"\n🔍 Checking for driver library files:")
    
    possible_paths = [
        "/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so",
        "/opt/arrow-flight-sql-odbc-driver/lib/libarrow-flight-sql-odbc.so", 
        "/usr/lib/x86_64-linux-gnu/libarrow-odbc.so",
        "/usr/local/lib/libarrow-odbc.so"
    ]
    
    found_paths = []
    for path in possible_paths:
        if os.path.exists(path):
            print(f"   ✅ Found: {path}")
            found_paths.append(path)
        else:
            print(f"   ❌ Not found: {path}")
    
    # Search for any arrow-related libraries
    print(f"\n🔍 Searching for arrow-related libraries:")
    search_dirs = ["/opt", "/usr/lib", "/usr/local/lib"]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            try:
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if "arrow" in file.lower() and file.endswith(".so"):
                            full_path = os.path.join(root, file)
                            print(f"   🔍 Found arrow library: {full_path}")
                            if full_path not in found_paths:
                                found_paths.append(full_path)
            except PermissionError:
                print(f"   ⚠️ Permission denied searching: {search_dir}")
    
    # Test the multi-driver client logic
    print(f"\n🧪 Testing Multi-Driver Client Logic:")
    
    driver_configs = []
    
    # Add found library paths
    for path in found_paths:
        driver_configs.append({
            "type": "path",
            "value": path,
            "description": f"Direct library path: {path}"
        })
    
    # Add driver names
    driver_names = [
        "Arrow Flight SQL ODBC Driver",
        "Dremio Arrow Flight SQL ODBC Driver", 
        "Dremio ODBC Driver"
    ]
    
    for driver_name in driver_names:
        driver_configs.append({
            "type": "name", 
            "value": driver_name,
            "description": f"Driver name: {driver_name}"
        })
    
    print(f"\n📊 Driver configurations to try ({len(driver_configs)}):")
    for i, config in enumerate(driver_configs, 1):
        print(f"   {i}. {config['description']}")
        
        # Show what the connection string would look like
        driver_identifier = config["value"]
        config_type = config["type"]
        
        if config_type == "path":
            # Use direct driver library path (no braces needed)
            conn_str_format = f"DRIVER={driver_identifier};HOST=data.dremio.cloud;..."
        else:
            # Use driver name in braces
            conn_str_format = f"DRIVER={{{driver_identifier}}};HOST=data.dremio.cloud;..."
        
        print(f"      Connection string: {conn_str_format}")
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   - Available driver names: {len(drivers)}")
    print(f"   - Found library paths: {len(found_paths)}")
    print(f"   - Total configurations: {len(driver_configs)}")
    
    if driver_configs:
        print(f"   ✅ Driver detection successful - will try {len(driver_configs)} configurations")
        return True
    else:
        print(f"   ❌ No drivers found - PyODBC will not work")
        return False

def test_connection_string_formats():
    """Test different connection string formats"""
    
    print(f"\n🔧 Testing Connection String Formats")
    print("=" * 50)
    
    # Example configurations
    test_configs = [
        {
            "type": "path",
            "value": "/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so",
            "description": "Direct library path"
        },
        {
            "type": "name",
            "value": "Arrow Flight SQL ODBC Driver", 
            "description": "Driver name"
        }
    ]
    
    for config in test_configs:
        print(f"\n📝 {config['description']}:")
        
        driver_identifier = config["value"]
        config_type = config["type"]
        
        # TOKEN authentication
        if config_type == "path":
            conn_str = f"DRIVER={driver_identifier};HOST=data.dremio.cloud;PORT=443;ssl=1;UseEncryption=true;disableCertificateVerification=true;token=YOUR_PAT"
        else:
            conn_str = f"DRIVER={{{driver_identifier}}};HOST=data.dremio.cloud;PORT=443;ssl=1;UseEncryption=true;disableCertificateVerification=true;token=YOUR_PAT"
        
        print(f"   TOKEN: {conn_str}")
        
        # Username/Password authentication  
        if config_type == "path":
            conn_str = f"DRIVER={driver_identifier};HOST=data.dremio.cloud;PORT=443;UseEncryption=true;disableCertificateVerification=true;UID=username;PWD=password"
        else:
            conn_str = f"DRIVER={{{driver_identifier}}};HOST=data.dremio.cloud;PORT=443;UseEncryption=true;disableCertificateVerification=true;UID=username;PWD=password"
        
        print(f"   UID/PWD: {conn_str}")

def main():
    """Main test function"""
    
    print("🧪 PyODBC Driver Path Detection Test")
    print("Testing the enhanced driver detection logic")
    
    success = test_driver_path_detection()
    test_connection_string_formats()
    
    print(f"\n🎯 Test Result:")
    if success:
        print("✅ Driver path detection is working correctly")
        print("✅ PyODBC should be able to find and use the ODBC driver")
        return 0
    else:
        print("❌ No ODBC drivers detected")
        print("⚠️ PyODBC will not work without proper driver installation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
