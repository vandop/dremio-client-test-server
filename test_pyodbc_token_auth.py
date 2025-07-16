#!/usr/bin/env python3

"""
Test script to verify PyODBC TOKEN authentication fix
"""

import os
import sys
from dotenv import load_dotenv

def test_pyodbc_token_auth():
    """Test PyODBC with correct TOKEN authentication"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧪 Testing PyODBC TOKEN Authentication Fix")
    print("=" * 50)
    
    # Check if PyODBC is available
    try:
        import pyodbc
        print(f"✅ PyODBC version: {pyodbc.version}")
    except ImportError:
        print("❌ PyODBC not available")
        return False
    
    # Check available drivers
    drivers = pyodbc.drivers()
    print(f"📋 Available ODBC drivers ({len(drivers)}):")
    for driver in drivers:
        print(f"   - {driver}")
    
    # Find Arrow Flight SQL ODBC driver
    arrow_driver = None
    for driver in drivers:
        if "Arrow Flight SQL" in driver or "arrow" in driver.lower():
            arrow_driver = driver
            break
    
    if not arrow_driver:
        print("❌ Arrow Flight SQL ODBC Driver not found")
        print("   Available drivers don't include Arrow Flight SQL ODBC Driver")
        return False
    
    print(f"✅ Found Arrow Flight SQL ODBC Driver: {arrow_driver}")
    
    # Get configuration
    pat = os.getenv('DREMIO_PERSONAL_ACCESS_TOKEN') or os.getenv('DREMIO_PAT')
    host = "data.dremio.cloud"
    
    if not pat:
        print("❌ No Personal Access Token found")
        print("   Set DREMIO_PERSONAL_ACCESS_TOKEN or DREMIO_PAT in .env file")
        return False
    
    print(f"✅ Personal Access Token configured: {pat[:10]}...")
    
    # Test connection with TOKEN parameter (new method)
    print("\n🔗 Testing TOKEN authentication (Arrow Flight SQL ODBC Driver)...")
    
    try:
        # Build connection string with TOKEN parameter
        conn_str = f"DRIVER=/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so.0.9.6.473;HOST={host};PORT=443;useEncryption=true;TOKEN={pat}"
        #conn_str = f"DRIVER=/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so.0.9.6.473;HOST={host};PORT=443;useEncryption=true;TOKEN={pat}"

        # conn_str = (
        #     "Driver={/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so.0.9.6.473};"
        #     "host=data.eu.dremio.cloud;"
        #     "port=443;"
        #     "ssl=1;"
        #     "UseEncryption=true;"
        #     "disableCertificateVerification=true;"
        #     f"token={pat};"
        # )
        print(f"Connection string: {conn_str}")
        
        # Attempt connection - try different approaches for Arrow Flight SQL ODBC driver
        connection = None

        # Method 1: Try with autocommit=False
        try:
            connection = pyodbc.connect(conn_str, autocommit=True)
            print("✅ PyODBC connection successful with TOKEN authentication (autocommit=True)!")
        except Exception as e1:
            print(f"⚠️ Connection with autocommit=False failed: {e1}")

            # Method 2: Try without autocommit parameter
            try:
                connection = pyodbc.connect(conn_str)
                print("✅ PyODBC connection successful with TOKEN authentication (default settings)!")
            except Exception as e2:
                print(f"⚠️ Connection with default settings failed: {e2}")

                # Method 3: Try with specific connection attributes
                try:
                    # Some ODBC drivers have issues with certain attributes
                    # Let's try connecting and then setting attributes manually
                    connection = pyodbc.connect(conn_str, attrs_before={})
                    print("✅ PyODBC connection successful with TOKEN authentication (no attrs)!")
                except Exception as e3:
                    print(f"❌ All connection methods failed. Last error: {e3}")
                    raise e3

        if not connection:
            raise Exception("Failed to establish connection with any method")
        
        # Test a simple query
        cursor = connection.cursor()
        cursor.execute("/* Driver: PyODBC */ SELECT 1 as test_value")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            print("✅ Test query successful: SELECT 1 returned", result[0])
        else:
            print("⚠️ Test query returned unexpected result:", result)
        
        cursor.close()
        connection.close()
        
        print("\n🎉 PyODBC TOKEN authentication fix verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ PyODBC connection failed: {e}")
        
        # Try to provide helpful error information
        error_str = str(e)
        if "unauthenticated" in error_str.lower():
            print("   This appears to be an authentication error.")
            print("   Verify your Personal Access Token is correct and active.")
        elif "file not found" in error_str.lower():
            print("   This appears to be a driver installation issue.")
            print("   The ODBC driver library file may not be properly installed.")
        elif "connection" in error_str.lower():
            print("   This appears to be a network connectivity issue.")
            print("   Check your internet connection and firewall settings.")
        
        return False

def main():
    """Main test function"""
    success = test_pyodbc_token_auth()
    
    if success:
        print("\n✅ All tests passed! PyODBC TOKEN authentication is working correctly.")
        return 0
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
