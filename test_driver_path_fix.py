#!/usr/bin/env python3

"""
Test script to verify the driver path detection fix
"""

import os
import sys
import glob
from dotenv import load_dotenv

def test_driver_path_detection():
    """Test the enhanced driver path detection"""
    
    print("🔍 Testing Enhanced Driver Path Detection")
    print("=" * 50)
    
    # Test the same logic as in the multi-driver client
    driver_configs = []
    
    try:
        # Look for Arrow Flight SQL ODBC driver library with version numbers
        search_patterns = [
            "/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so*",  # Primary location with version
            "/opt/arrow-flight-sql-odbc-driver/lib/libarrow-odbc.so*",   # Alternative lib directory
            "/usr/lib/x86_64-linux-gnu/libarrow-odbc.so*",               # System lib directory
            "/usr/local/lib/libarrow-odbc.so*"                           # Local lib directory
        ]
        
        print(f"Searching for ODBC driver libraries in {len(search_patterns)} locations...")
        
        for pattern in search_patterns:
            print(f"  Checking pattern: {pattern}")
            matching_files = glob.glob(pattern)
            if matching_files:
                # Use the first matching file (usually the one with version number)
                driver_path = matching_files[0]
                driver_configs.append({
                    "type": "path",
                    "value": driver_path,
                    "description": f"Direct library path: {driver_path}"
                })
                print(f"  ✅ Found ODBC driver library: {driver_path}")
                print(f"     All matches for pattern: {matching_files}")
                break
            else:
                print(f"     ❌ No matches for pattern: {pattern}")
        
        if not driver_configs:
            print("⚠️ No ODBC driver library files found in standard locations")
            
    except Exception as e:
        print(f"❌ Could not check driver library paths: {e}")
    
    # Add driver names as fallback
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
    
    # Show all configurations
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
    
    return driver_configs

def test_connection_string_format():
    """Test the connection string format with the actual driver path"""
    
    print(f"\n🔧 Testing Connection String Format")
    print("=" * 50)
    
    # Use the known driver path
    driver_path = "/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so.0.9.6.473"
    
    if os.path.exists(driver_path):
        print(f"✅ Driver library exists: {driver_path}")
        
        # Test TOKEN authentication with direct path
        conn_str = f"DRIVER={driver_path};HOST=data.dremio.cloud;PORT=443;ssl=1;UseEncryption=true;disableCertificateVerification=true;token=YOUR_PAT"
        print(f"\n📝 Connection string with direct driver path:")
        print(f"   {conn_str}")
        
        # Compare with driver name format
        conn_str_name = f"DRIVER={{Arrow Flight SQL ODBC Driver}};HOST=data.dremio.cloud;PORT=443;ssl=1;UseEncryption=true;disableCertificateVerification=true;token=YOUR_PAT"
        print(f"\n📝 Connection string with driver name (old format):")
        print(f"   {conn_str_name}")
        
        print(f"\n🎯 Key Difference:")
        print(f"   Direct path: DRIVER={driver_path}")
        print(f"   Driver name: DRIVER={{Arrow Flight SQL ODBC Driver}}")
        
    else:
        print(f"❌ Driver library not found: {driver_path}")

def main():
    """Main test function"""
    
    print("🧪 Driver Path Detection Fix Test")
    print("Testing the enhanced driver path detection logic")
    
    # Test driver path detection
    driver_configs = test_driver_path_detection()
    
    # Test connection string format
    test_connection_string_format()
    
    # Summary
    print(f"\n📋 Summary:")
    if driver_configs and driver_configs[0]["type"] == "path":
        print("✅ Driver path detection is working correctly")
        print("✅ PyODBC should now use the direct driver library path")
        print(f"✅ First configuration uses: {driver_configs[0]['value']}")
        return 0
    else:
        print("⚠️ Driver path detection fell back to driver names")
        print("⚠️ PyODBC will use driver name instead of direct path")
        return 1

if __name__ == "__main__":
    sys.exit(main())
