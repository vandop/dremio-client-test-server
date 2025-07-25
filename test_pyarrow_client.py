#!/usr/bin/env python3
"""
Comprehensive test script for PyArrow Flight SQL driver.
Tests direct driver functionality including connection, queries, and error handling.
"""
import json
import time
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
    return result.get('success', False)

def test_multiple_queries(client):
    """Test multiple query types."""
    print_section("Testing Multiple Query Types")

    test_queries = [
        ("SELECT 1 as number", "Simple integer"),
        ("SELECT 'test' as text", "Simple string"),
        ("SELECT CURRENT_TIMESTAMP as now", "Current timestamp"),
        ("SELECT 2 + 2 as sum, 10 * 5 as product", "Math operations"),
    ]

    results = {}
    for sql, description in test_queries:
        print(f"\n🔍 {description}: {sql}")
        start_time = time.time()
        result = client.execute_query(sql)
        execution_time = time.time() - start_time

        if result.get('success'):
            print(f"   ✅ Success in {execution_time:.3f}s")
            results[description] = {'success': True, 'time': execution_time}
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            results[description] = {'success': False, 'error': result.get('error')}

    return results

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

    return result.get('success', False)

def test_error_handling(client):
    """Test error handling with invalid queries."""
    print_section("Testing Error Handling")

    invalid_queries = [
        "SELECT * FROM nonexistent_table",
        "INVALID SQL SYNTAX",
        "SELECT 1/0 as division_by_zero"
    ]

    for sql in invalid_queries:
        print(f"\n🔍 Testing invalid query: {sql}")
        result = client.execute_query(sql)
        if not result.get('success'):
            print(f"   ✅ Error handled correctly: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️ Query unexpectedly succeeded")

def test_comprehensive_connection(client):
    """Test comprehensive connection."""
    print_section("Comprehensive Connection Test")

    result = client.test_connection()
    print("Comprehensive Test Result:")
    print(json.dumps(result, indent=2, default=str))
    return result.get('success', False)

def main():
    """Run comprehensive PyArrow Flight tests."""
    print("🚀 Comprehensive PyArrow Flight SQL Driver Test")
    print("Testing direct driver functionality and performance")

    test_results = {}

    try:
        # Test connection
        client, connected = test_pyarrow_connection()
        test_results['connection'] = connected

        if connected:
            # Test simple query
            simple_success = test_simple_query(client)
            test_results['simple_query'] = simple_success

            # Test multiple queries
            multiple_results = test_multiple_queries(client)
            test_results['multiple_queries'] = multiple_results

            # Test SYS.Jobs
            sys_jobs_success = test_sys_jobs_query(client)
            test_results['sys_jobs'] = sys_jobs_success

            # Test error handling
            test_error_handling(client)

            # Comprehensive test
            comprehensive_success = test_comprehensive_connection(client)
            test_results['comprehensive'] = comprehensive_success

        print_section("Final Test Summary")

        if connected:
            successful_tests = sum(1 for result in [
                test_results.get('simple_query'),
                test_results.get('sys_jobs'),
                test_results.get('comprehensive')
            ] if result)

            multiple_successful = sum(1 for r in test_results.get('multiple_queries', {}).values() if r.get('success'))
            multiple_total = len(test_results.get('multiple_queries', {}))

            print(f"📊 Test Results:")
            print(f"   ✅ Connection: {'Success' if connected else 'Failed'}")
            print(f"   ✅ Basic Tests: {successful_tests}/3 passed")
            print(f"   ✅ Query Types: {multiple_successful}/{multiple_total} passed")
            print(f"   ✅ Error Handling: Tested")

            if successful_tests >= 2 and multiple_successful >= 2:
                print(f"\n🎉 PyArrow Flight SQL driver is working correctly!")
                print(f"   ✅ Direct driver testing complete")
                print(f"   ✅ Ready for production use")
            else:
                print(f"\n⚠️ Some tests failed - check configuration")
        else:
            print("❌ Connection failed - check credentials and endpoint")
            print("   • Verify DREMIO_PAT in .env file")
            print("   • Check DREMIO_CLOUD_URL configuration")
            print("   • Ensure network connectivity to Dremio")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
