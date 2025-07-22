#!/usr/bin/env python3
"""
Test ADBC with real Dremio credentials from .env file.
"""
import os
import sys
from dotenv import load_dotenv

def test_adbc_real_connection():
    """Test ADBC with real Dremio credentials."""
    print("🚀 Testing ADBC with Real Dremio Connection")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    dremio_url = os.getenv('DREMIO_CLOUD_URL', '')
    dremio_pat = os.getenv('DREMIO_PAT', '')
    
    if not dremio_url or not dremio_pat:
        print("❌ Missing DREMIO_CLOUD_URL or DREMIO_PAT in .env file")
        return False
    
    print(f"✅ Loaded credentials from .env")
    print(f"   URL: {dremio_url}")
    print(f"   PAT: {'*' * (len(dremio_pat) - 4) + dremio_pat[-4:] if len(dremio_pat) > 4 else '***'}")
    
    try:
        import adbc_driver_flightsql.dbapi as flight_sql
        print("✅ ADBC Flight SQL driver imported")
        
        # Convert URL to Flight endpoint
        if 'api.dremio.cloud' in dremio_url:
            flight_endpoint = "grpc://data.dremio.cloud:443"
        else:
            # For other URLs, try to convert appropriately
            flight_endpoint = dremio_url.replace('https://', 'grpc://').replace('http://', 'grpc://')
            if ':443' not in flight_endpoint and ':32010' not in flight_endpoint:
                flight_endpoint += ':32010'  # Default Dremio Flight port
        
        print(f"✅ Flight endpoint: {flight_endpoint}")
        
        # Create connection
        print("\n🔗 Testing ADBC Connection...")
        conn = flight_sql.connect(
            uri=flight_endpoint,
            db_kwargs={
                "adbc.flight.sql.authorization_header": f"Bearer {dremio_pat}"
            }
        )
        print("✅ ADBC connection established successfully")
        
        # Test simple query
        print("\n📊 Testing Simple Query...")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test_value, 'Hello from ADBC' as message")
        results = cursor.fetchall()
        
        print(f"✅ Query executed successfully")
        print(f"   Results: {results}")
        
        # Test with pandas if available
        try:
            import pandas as pd
            print("\n🐼 Testing with Pandas...")
            df = pd.read_sql("SELECT 1 as test_value, 'Hello from ADBC' as message", conn)
            print(f"✅ Pandas integration working")
            print(f"   DataFrame shape: {df.shape}")
            print(f"   Data:\n{df}")
        except ImportError:
            print("⚠️  Pandas not available, skipping pandas test")
        except Exception as e:
            print(f"❌ Pandas test failed: {e}")
        
        # Clean up
        cursor.close()
        conn.close()
        print("\n✅ Connection closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ ADBC connection failed: {e}")
        return False

def main():
    """Run ADBC real connection test."""
    print("🧪 ADBC Real Connection Test")
    print("Enhanced Dremio Reporting Server")
    print("=" * 60)
    
    success = test_adbc_real_connection()
    
    print("\n" + "=" * 60)
    print("🏁 Test Summary")
    print("=" * 60)
    
    if success:
        print("🎉 ADBC real connection test PASSED!")
        print("   ✅ Connection established")
        print("   ✅ Query execution working")
        print("   ✅ Driver fully functional")
    else:
        print("❌ ADBC real connection test FAILED!")
        print("   Check credentials and network connectivity")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
