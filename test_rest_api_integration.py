#!/usr/bin/env python3
"""
Test REST API integration with the multi-driver client.
"""

import sys
from dremio_multi_driver_client import DremioMultiDriverClient

def test_rest_api_driver():
    """Test REST API driver integration."""
    print("🧪 Testing REST API Driver Integration")
    print("=" * 50)
    
    # Initialize multi-driver client
    client = DremioMultiDriverClient()
    
    # Check available drivers
    available_drivers = client.get_available_drivers()
    print("Available drivers:")
    for name, info in available_drivers.items():
        status = "✅" if info["available"] else "❌"
        print(f"  {status} {name}: {info['name']}")
    
    # Test REST API specifically
    if "rest_api" in available_drivers and available_drivers["rest_api"]["available"]:
        print("\n🔗 Testing REST API connection...")
        try:
            result = client.execute_query_multi_driver("SELECT 1 as test_value, 'Hello from REST API' as message", ["rest_api"])
            if "rest_api" in result and result["rest_api"]["success"]:
                print("✅ REST API query successful!")
                print(f"   Result: {result['rest_api']}")
            else:
                print(f"❌ REST API query failed: {result}")
        except Exception as e:
            print(f"❌ REST API query failed: {e}")
    else:
        print("\n⚠️  REST API driver not available")

    # Test multi-driver execution including REST API
    print("\n🔄 Testing multi-driver execution...")
    try:
        # Get list of available driver names
        available_driver_names = [name for name, info in available_drivers.items() if info["available"]]
        results = client.execute_query_multi_driver("SELECT 1 as test_value, 'Multi-driver test' as message", available_driver_names)
        print("Multi-driver results:")
        for driver, result in results.items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {driver}: {result.get('driver_name', driver)}")
            if result["success"]:
                print(f"      Rows: {result['row_count']}, Time: {result['execution_time']:.2f}s")
            else:
                print(f"      Error: {result['error']}")
    except Exception as e:
        print(f"❌ Multi-driver execution failed: {e}")

if __name__ == "__main__":
    test_rest_api_driver()
