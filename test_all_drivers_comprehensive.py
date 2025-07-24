#!/usr/bin/env python3
"""
Comprehensive test of all 5 supported drivers including the new REST API driver.
This script demonstrates the multi-driver capabilities of the Enhanced Dremio Reporting Server.
"""

import time
import json
from dremio_multi_driver_client import DremioMultiDriverClient

def print_header(title):
    print(f"\n{'='*80}")
    print(f" {title}")
    print(f"{'='*80}")

def print_driver_status(drivers):
    """Print the status of all drivers."""
    print("\n🔧 Driver Availability Status:")
    print("-" * 50)
    
    for name, info in drivers.items():
        status = "✅ Available" if info["available"] else "❌ Not Available"
        print(f"  {status}: {info['name']}")
    
    available_count = sum(1 for info in drivers.values() if info["available"])
    print(f"\nTotal: {available_count}/{len(drivers)} drivers available")

def test_individual_drivers(client, sql):
    """Test each driver individually."""
    print_header("Individual Driver Testing")
    
    drivers = client.get_available_drivers()
    results = {}
    
    for driver_name, driver_info in drivers.items():
        if not driver_info["available"]:
            print(f"\n⏭️  Skipping {driver_info['name']} (not available)")
            continue
        
        print(f"\n🧪 Testing {driver_info['name']}...")
        start_time = time.time()
        
        try:
            result = client.execute_query_multi_driver(sql, [driver_name])
            execution_time = time.time() - start_time
            
            if driver_name in result and result[driver_name]["success"]:
                row_count = result[driver_name]["row_count"]
                driver_time = result[driver_name]["execution_time"]
                print(f"   ✅ Success: {row_count} rows in {driver_time:.3f}s")
                results[driver_name] = {
                    "success": True,
                    "time": driver_time,
                    "rows": row_count,
                    "name": driver_info['name']
                }
            else:
                error = result[driver_name]["error"] if driver_name in result else "Unknown error"
                print(f"   ❌ Failed: {error}")
                results[driver_name] = {
                    "success": False,
                    "error": error,
                    "name": driver_info['name']
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"   ❌ Exception: {e}")
            results[driver_name] = {
                "success": False,
                "error": str(e),
                "name": driver_info['name']
            }
    
    return results

def test_multi_driver_comparison(client, sql):
    """Test all drivers simultaneously for performance comparison."""
    print_header("Multi-Driver Performance Comparison")
    
    drivers = client.get_available_drivers()
    available_drivers = [name for name, info in drivers.items() if info["available"]]
    
    print(f"🚀 Running query on {len(available_drivers)} drivers simultaneously...")
    print(f"Query: {sql}")
    
    start_time = time.time()
    results = client.execute_query_multi_driver(sql, available_drivers)
    total_time = time.time() - start_time
    
    print(f"\n⏱️  Total execution time: {total_time:.3f}s")
    
    # Analyze results
    successful = []
    failed = []
    
    for driver_name, result in results.items():
        if result["success"]:
            successful.append((driver_name, result))
        else:
            failed.append((driver_name, result))
    
    # Sort successful results by execution time
    successful.sort(key=lambda x: x[1]["execution_time"])
    
    print(f"\n📊 Results Summary:")
    print(f"   ✅ Successful: {len(successful)}")
    print(f"   ❌ Failed: {len(failed)}")
    
    if successful:
        print(f"\n🏆 Performance Ranking:")
        for i, (driver_name, result) in enumerate(successful, 1):
            driver_info = drivers[driver_name]
            time_str = f"{result['execution_time']:.3f}s"
            rows_str = f"{result['row_count']} rows"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"   {medal} #{i}: {driver_info['name']} - {time_str} ({rows_str})")
    
    if failed:
        print(f"\n💥 Failed Drivers:")
        for driver_name, result in failed:
            driver_info = drivers[driver_name]
            print(f"   ❌ {driver_info['name']}: {result['error']}")
    
    return results

def demonstrate_rest_api_features(client):
    """Demonstrate specific REST API features."""
    print_header("REST API Driver Features Demo")
    
    # Test if REST API is available
    drivers = client.get_available_drivers()
    if not drivers.get("rest_api", {}).get("available", False):
        print("❌ REST API driver not available")
        return
    
    print("🌐 Testing REST API specific features...")
    
    # Test simple query
    print("\n1. Simple Query Test:")
    result = client.execute_query_multi_driver(
        "SELECT 'REST API Test' as source, CURRENT_TIMESTAMP as query_time", 
        ["rest_api"]
    )
    
    if "rest_api" in result and result["rest_api"]["success"]:
        print("   ✅ Simple query successful")
        print(f"   📊 Data: {result['rest_api']['data']}")
    else:
        print(f"   ❌ Simple query failed: {result.get('rest_api', {}).get('error', 'Unknown')}")
    
    # Test with different query types
    test_queries = [
        ("Math Operations", "SELECT 1+1 as sum, 2*3 as product, 10/2 as division"),
        ("String Functions", "SELECT UPPER('hello') as upper_text, LENGTH('world') as text_length"),
        ("Date Functions", "SELECT CURRENT_DATE as today, CURRENT_TIME as now"),
    ]
    
    print(f"\n2. Query Type Tests:")
    for test_name, query in test_queries:
        print(f"\n   🧪 {test_name}:")
        try:
            result = client.execute_query_multi_driver(query, ["rest_api"])
            if "rest_api" in result and result["rest_api"]["success"]:
                time_str = f"{result['rest_api']['execution_time']:.3f}s"
                print(f"      ✅ Success in {time_str}")
            else:
                error = result.get('rest_api', {}).get('error', 'Unknown')
                print(f"      ❌ Failed: {error}")
        except Exception as e:
            print(f"      ❌ Exception: {e}")

def main():
    """Run comprehensive driver testing."""
    print("🚀 Enhanced Dremio Reporting Server")
    print("Comprehensive Multi-Driver Test Suite")
    print("Including NEW REST API Driver Support! 🌐")
    
    # Initialize client
    print("\n🔧 Initializing multi-driver client...")
    client = DremioMultiDriverClient()
    
    # Check driver availability
    drivers = client.get_available_drivers()
    print_driver_status(drivers)
    
    # Test query
    test_sql = "SELECT 1 as test_id, 'Multi-Driver Test' as description, CURRENT_TIMESTAMP as timestamp"
    
    # Run individual driver tests
    individual_results = test_individual_drivers(client, test_sql)
    
    # Run multi-driver comparison
    comparison_results = test_multi_driver_comparison(client, test_sql)
    
    # Demonstrate REST API features
    demonstrate_rest_api_features(client)
    
    # Final summary
    print_header("Final Summary")
    
    available_count = sum(1 for info in drivers.values() if info["available"])
    successful_count = sum(1 for result in individual_results.values() if result["success"])
    
    print(f"🎯 Test Results:")
    print(f"   📊 Drivers Available: {available_count}/5")
    print(f"   ✅ Drivers Working: {successful_count}/{available_count}")
    print(f"   🌐 REST API: {'✅ Working' if drivers.get('rest_api', {}).get('available') else '❌ Not Available'}")
    
    if successful_count == available_count:
        print(f"\n🎉 All available drivers are working perfectly!")
        print(f"   The Enhanced Dremio Reporting Server is ready for production use!")
    else:
        print(f"\n⚠️  Some drivers had issues. Check the detailed output above.")
    
    print(f"\n🔗 Access the web interface at: http://localhost:5001")
    print(f"   Try the multi-driver query interface to see all drivers in action!")

if __name__ == "__main__":
    main()
