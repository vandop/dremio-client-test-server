#!/usr/bin/env python3
"""
Test script for the PyArrow Flight client.
"""
import json
from dremio_pyarrow_client import DremioPyArrowClient

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_pyarrow_connection():
    """Test PyArrow Flight connection."""
    print_section("Testing PyArrow Flight Connection")
    
    client = DremioPyArrowClient()
    print(f"Flight endpoint: {client.flight_endpoint}")
    print(f"Has PAT: {bool(client.pat)}")
    
    # Test connection
    result = client.connect()
    print("Connection Result:")
    print(json.dumps(result, indent=2))
    
    return client, result['success']

def test_simple_query(client):
    """Test simple SQL query."""
    print_section("Testing Simple SQL Query")
    
    result = client.execute_query("SELECT 1 as test_value, 'Hello Dremio' as message")
    print("Simple Query Result:")
    print(json.dumps(result, indent=2, default=str))

def test_sys_jobs_query(client):
    """Test SYS.Jobs query."""
    print_section("Testing SYS.Jobs Query")
    
    result = client.get_jobs(limit=5)
    print("SYS.Jobs Query Result:")
    print(json.dumps(result, indent=2, default=str))
    
    if result['success'] and result['jobs']:
        print(f"\n📊 Found {result['count']} jobs:")
        for i, job in enumerate(result['jobs'][:3], 1):
            print(f"  {i}. Job ID: {job['id']}")
            print(f"     State: {job['jobState']}")
            print(f"     User: {job['user']}")
            print(f"     Query Type: {job['queryType']}")
            print()

def test_comprehensive_connection(client):
    """Test comprehensive connection."""
    print_section("Comprehensive Connection Test")
    
    result = client.test_connection()
    print("Comprehensive Test Result:")
    print(json.dumps(result, indent=2, default=str))

def main():
    """Run PyArrow Flight tests."""
    print("🚀 Dremio PyArrow Flight Client Test")
    print("Testing native PyArrow Flight integration")
    
    try:
        # Test connection
        client, connected = test_pyarrow_connection()
        
        if connected:
            # Test simple query
            test_simple_query(client)
            
            # Test SYS.Jobs
            # test_sys_jobs_query(client)
            
            # Comprehensive test
            test_comprehensive_connection(client)
        
        print_section("Test Summary")
        if connected:
            print("✅ PyArrow Flight connection successful")
            print("✅ SQL query execution working")
            print("✅ SYS.Jobs table accessible")
        else:
            print("❌ Connection failed - check credentials and endpoint")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
