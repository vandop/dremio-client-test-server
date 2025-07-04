#!/usr/bin/env python3
"""
Comprehensive PyODBC installation testing and validation script.
"""
import os
import sys
import traceback
import subprocess
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_system_requirements():
    """Test system-level ODBC requirements."""
    print("\n🔍 Testing System Requirements")
    
    results = {}
    
    # Test 1: Check unixODBC installation
    try:
        result = subprocess.run(['odbcinst', '-j'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ unixODBC driver manager installed")
            print(f"   Configuration: {result.stdout.strip()}")
            results['unixodbc'] = True
        else:
            print("❌ unixODBC driver manager not found")
            results['unixodbc'] = False
    except FileNotFoundError:
        print("❌ odbcinst command not found - unixODBC not installed")
        results['unixodbc'] = False
    
    # Test 2: Check for ODBC development headers
    odbc_headers = [
        '/usr/include/sql.h',
        '/usr/include/sqlext.h',
        '/usr/include/sqltypes.h'
    ]
    
    headers_found = sum(1 for header in odbc_headers if os.path.exists(header))
    if headers_found >= 2:
        print(f"✅ ODBC development headers found ({headers_found}/3)")
        results['odbc_headers'] = True
    else:
        print(f"⚠️ ODBC development headers missing ({headers_found}/3)")
        print("   Install with: sudo apt install unixodbc-dev")
        results['odbc_headers'] = False
    
    return results

def test_pyodbc_import():
    """Test PyODBC Python package import."""
    print("\n🐍 Testing PyODBC Python Package")
    
    try:
        import pyodbc
        print(f"✅ PyODBC imported successfully")
        print(f"   Version: {pyodbc.version}")
        
        # Test basic functionality
        try:
            drivers = pyodbc.drivers()
            print(f"   Available drivers: {len(drivers)}")
            for driver in drivers:
                print(f"     - {driver}")
            
            return {
                'import_success': True,
                'version': pyodbc.version,
                'drivers': drivers
            }
            
        except Exception as e:
            print(f"⚠️ PyODBC imported but error getting drivers: {e}")
            return {
                'import_success': True,
                'version': pyodbc.version,
                'drivers': [],
                'driver_error': str(e)
            }
            
    except ImportError as e:
        print(f"❌ PyODBC import failed: {e}")
        print("   Install with: pip install pyodbc")
        return {'import_success': False, 'error': str(e)}

def test_dremio_odbc_driver():
    """Test Dremio ODBC driver installation."""
    print("\n🚀 Testing Dremio ODBC Driver")
    
    try:
        import pyodbc
        drivers = pyodbc.drivers()
        
        # Look for Dremio driver
        dremio_drivers = [d for d in drivers if 'dremio' in d.lower() or 'drill' in d.lower()]
        
        if dremio_drivers:
            print(f"✅ Dremio ODBC driver found: {dremio_drivers}")
            return {
                'driver_found': True,
                'driver_names': dremio_drivers
            }
        else:
            print("❌ Dremio ODBC driver not found")
            print("   Available drivers:")
            for driver in drivers:
                print(f"     - {driver}")
            print("\n   Install Dremio ODBC driver:")
            print("   1. Download from: https://www.dremio.com/drivers/")
            print("   2. Extract and run: sudo ./install.sh")
            print("   3. Or follow PYODBC_INSTALLATION_GUIDE.md")
            
            return {
                'driver_found': False,
                'available_drivers': drivers
            }
            
    except Exception as e:
        print(f"❌ Error checking drivers: {e}")
        return {'driver_found': False, 'error': str(e)}

def test_connection_configuration():
    """Test connection configuration and credentials."""
    print("\n🔐 Testing Connection Configuration")
    
    # Check environment variables
    dremio_url = os.environ.get('DREMIO_URL')
    dremio_pat = os.environ.get('DREMIO_PAT')
    dremio_username = os.environ.get('DREMIO_USERNAME')
    dremio_password = os.environ.get('DREMIO_PASSWORD')
    
    config_status = {}
    
    if dremio_url:
        print(f"✅ DREMIO_URL configured: {dremio_url}")
        config_status['url'] = True
    else:
        print("⚠️ DREMIO_URL not set")
        config_status['url'] = False
    
    if dremio_pat:
        print(f"✅ DREMIO_PAT configured: {dremio_pat[:10]}...")
        config_status['pat'] = True
    elif dremio_username and dremio_password:
        print(f"✅ Username/Password configured: {dremio_username}")
        config_status['credentials'] = True
    else:
        print("❌ No authentication configured")
        print("   Set DREMIO_PAT or DREMIO_USERNAME/DREMIO_PASSWORD")
        config_status['auth'] = False
    
    return config_status

def test_pyodbc_connection():
    """Test actual PyODBC connection to Dremio."""
    print("\n🔗 Testing PyODBC Connection")
    
    try:
        import pyodbc
        
        # Check if Dremio driver is available
        drivers = pyodbc.drivers()
        dremio_driver = None
        
        for driver in drivers:
            if 'dremio' in driver.lower():
                dremio_driver = driver
                break
        
        if not dremio_driver:
            print("❌ Dremio ODBC driver not available")
            return {'connection_success': False, 'error': 'Driver not found'}
        
        print(f"📡 Using driver: {dremio_driver}")
        
        # Get connection parameters
        dremio_url = os.environ.get('DREMIO_URL', 'https://api.dremio.cloud')
        dremio_pat = os.environ.get('DREMIO_PAT')
        
        if not dremio_pat:
            print("❌ DREMIO_PAT not configured")
            return {'connection_success': False, 'error': 'No PAT configured'}
        
        # Convert URL to host
        if 'api.dremio.cloud' in dremio_url:
            host = 'data.dremio.cloud'
        else:
            host = dremio_url.replace('https://', '').replace('http://', '')
        
        # Build connection string
        conn_str = (
            f"DRIVER={{{dremio_driver}}};"
            f"HOST={host};"
            "PORT=443;"
            "SSL=1;"
            "AuthenticationType=Basic Authentication;"
            "UID=token;"
            f"PWD={dremio_pat};"
            "ConnectionTimeout=30;"
            "QueryTimeout=300"
        )
        
        print(f"🔌 Connecting to: {host}")
        
        # Test connection
        connection = pyodbc.connect(conn_str)
        print("✅ PyODBC connection established")
        
        # Test simple query
        cursor = connection.cursor()
        cursor.execute("SELECT 1 as test_value")
        result = cursor.fetchone()
        
        print(f"✅ Query executed successfully: {result}")
        
        # Clean up
        cursor.close()
        connection.close()
        
        return {
            'connection_success': True,
            'driver_used': dremio_driver,
            'host': host,
            'query_result': result[0] if result else None
        }
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        traceback.print_exc()
        return {
            'connection_success': False,
            'error': str(e)
        }

def test_api_integration():
    """Test PyODBC integration with the API."""
    print("\n🌐 Testing API Integration")
    
    try:
        import requests
        
        # Test if server is running
        try:
            response = requests.get('http://localhost:5008/api/drivers', timeout=5)
            
            if response.status_code == 200:
                drivers = response.json()
                
                if 'pyodbc' in drivers.get('drivers', {}):
                    pyodbc_info = drivers['drivers']['pyodbc']
                    print(f"✅ PyODBC driver detected in API: {pyodbc_info.get('name')}")
                    print(f"   Available: {pyodbc_info.get('available')}")
                    
                    # Test query via API
                    query_response = requests.post(
                        'http://localhost:5008/api/query-multi-driver',
                        headers={'Content-Type': 'application/json'},
                        json={
                            'sql': 'SELECT 1 "test_value"',
                            'drivers': ['pyodbc']
                        },
                        timeout=30
                    )
                    
                    if query_response.status_code == 200:
                        result = query_response.json()
                        pyodbc_result = result.get('results', {}).get('pyodbc', {})
                        
                        if pyodbc_result.get('success'):
                            print(f"✅ API query successful: {pyodbc_result.get('execution_time', 0):.3f}s")
                            return {'api_success': True, 'execution_time': pyodbc_result.get('execution_time')}
                        else:
                            error = pyodbc_result.get('error', 'Unknown error')
                            print(f"❌ API query failed: {error}")
                            return {'api_success': False, 'error': error}
                    else:
                        print(f"❌ API query request failed: {query_response.status_code}")
                        return {'api_success': False, 'error': f'HTTP {query_response.status_code}'}
                else:
                    print("❌ PyODBC driver not found in API")
                    return {'api_success': False, 'error': 'Driver not in API'}
            else:
                print(f"❌ API not accessible: {response.status_code}")
                return {'api_success': False, 'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ API server not running: {e}")
            print("   Start server with: python app.py")
            return {'api_success': False, 'error': 'Server not running'}
            
    except ImportError:
        print("⚠️ requests library not available")
        return {'api_success': False, 'error': 'requests not installed'}

def provide_installation_guidance(test_results):
    """Provide installation guidance based on test results."""
    print("\n💡 Installation Guidance")
    
    system_ok = test_results.get('system', {}).get('unixodbc', False)
    pyodbc_ok = test_results.get('pyodbc', {}).get('import_success', False)
    driver_ok = test_results.get('driver', {}).get('driver_found', False)
    
    if not system_ok:
        print("\n🔧 Step 1: Install unixODBC")
        print("   sudo apt update")
        print("   sudo apt install -y unixodbc unixodbc-dev")
    
    if not pyodbc_ok:
        print("\n🐍 Step 2: Install PyODBC")
        print("   pip install pyodbc")
    
    if not driver_ok:
        print("\n🚀 Step 3: Install Dremio ODBC Driver")
        print("   1. Download from: https://www.dremio.com/drivers/")
        print("   2. Extract: tar -xzf dremio-odbc-*.tar.gz")
        print("   3. Install: sudo ./install.sh")
        print("   4. Or follow: PYODBC_INSTALLATION_GUIDE.md")
    
    if system_ok and pyodbc_ok and driver_ok:
        print("\n🎉 All components installed correctly!")
        print("   PyODBC is ready for use with Dremio")

def main():
    """Run comprehensive PyODBC installation testing."""
    print("🧪 Comprehensive PyODBC Installation Testing")
    print("Enhanced Dremio Reporting Server")
    
    test_results = {}
    
    # Test 1: System requirements
    print_section("System Requirements")
    test_results['system'] = test_system_requirements()
    
    # Test 2: PyODBC import
    print_section("PyODBC Package")
    test_results['pyodbc'] = test_pyodbc_import()
    
    # Test 3: Dremio ODBC driver
    print_section("Dremio ODBC Driver")
    test_results['driver'] = test_dremio_odbc_driver()
    
    # Test 4: Connection configuration
    print_section("Connection Configuration")
    test_results['config'] = test_connection_configuration()
    
    # Test 5: Actual connection (if driver available)
    if test_results['driver'].get('driver_found'):
        print_section("Connection Testing")
        test_results['connection'] = test_pyodbc_connection()
    
    # Test 6: API integration
    print_section("API Integration")
    test_results['api'] = test_api_integration()
    
    # Summary and guidance
    print_section("Summary and Guidance")
    
    # Calculate overall status
    system_ok = test_results['system'].get('unixodbc', False)
    pyodbc_ok = test_results['pyodbc'].get('import_success', False)
    driver_ok = test_results['driver'].get('driver_found', False)
    connection_ok = test_results.get('connection', {}).get('connection_success', False)
    
    print(f"📊 Test Results:")
    print(f"   System (unixODBC): {'✅' if system_ok else '❌'}")
    print(f"   PyODBC Package: {'✅' if pyodbc_ok else '❌'}")
    print(f"   Dremio Driver: {'✅' if driver_ok else '❌'}")
    print(f"   Connection: {'✅' if connection_ok else '❌'}")
    
    if system_ok and pyodbc_ok and driver_ok and connection_ok:
        print(f"\n🎉 PyODBC fully functional with Dremio!")
        print(f"   Ready for production use")
        return True
    else:
        provide_installation_guidance(test_results)
        return False

if __name__ == '__main__':
    success = main()
    print(f"\n{'='*60}")
    print(f"🏁 PyODBC Testing Complete")
    print(f"{'='*60}")
    sys.exit(0 if success else 1)
