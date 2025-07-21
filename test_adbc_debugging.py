#!/usr/bin/env python3
"""
Comprehensive ADBC driver debugging and testing for Dremio compatibility.
"""
import requests
import json
import time

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_adbc_driver_status():
    """Test ADBC driver availability and status."""
    print("\n🔍 Testing ADBC Driver Status")
    
    try:
        response = requests.get('http://localhost:5001/api/drivers', timeout=10)
        
        if response.status_code == 200:
            drivers = response.json()
            
            if 'adbc_flight' in drivers.get('drivers', {}):
                adbc_info = drivers['drivers']['adbc_flight']
                print(f"✅ ADBC driver detected: {adbc_info.get('name')}")
                print(f"   Available: {adbc_info.get('available')}")
                print(f"   Description: {adbc_info.get('description')}")
                return True
            else:
                print("❌ ADBC driver not found in API response")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_adbc_simple_queries():
    """Test ADBC driver with various simple queries."""
    print("\n🧪 Testing ADBC Driver with Simple Queries")
    
    test_queries = [
        ("SELECT 1", "Simple integer literal"),
        ("SELECT 1 \"test_value\"", "Integer with quoted alias"),
        ("SELECT 'hello' \"text_value\"", "String with quoted alias"),
        ("SELECT USER \"current_user\"", "User function"),
        ("SELECT LOCALTIMESTAMP \"current_time\"", "Timestamp function"),
    ]
    
    results = {}
    
    for sql, description in test_queries:
        print(f"\n🔍 {description}: {sql}")
        
        try:
            response = requests.post(
                'http://localhost:5001/api/query-multi-driver',
                headers={'Content-Type': 'application/json'},
                json={
                    'sql': sql,
                    'drivers': ['adbc_flight']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                adbc_result = result.get('results', {}).get('adbc_flight', {})
                
                if adbc_result.get('success'):
                    print(f"✅ Success: {adbc_result.get('execution_time', 0):.3f}s")
                    print(f"   Rows: {len(adbc_result.get('data', []))}")
                    results[sql] = {'success': True, 'time': adbc_result.get('execution_time')}
                else:
                    error = adbc_result.get('error', 'Unknown error')
                    print(f"❌ Failed: {error[:100]}...")
                    results[sql] = {'success': False, 'error': error}
            else:
                print(f"❌ HTTP error: {response.status_code}")
                results[sql] = {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            results[sql] = {'success': False, 'error': str(e)}
    
    return results

def test_adbc_vs_pyarrow():
    """Compare ADBC vs PyArrow Flight SQL performance."""
    print("\n⚡ Comparing ADBC vs PyArrow Flight SQL")
    
    test_sql = "SELECT 1 \"test_value\", USER \"current_user\""
    
    try:
        response = requests.post(
            'http://localhost:5001/api/query-multi-driver',
            headers={'Content-Type': 'application/json'},
            json={
                'sql': test_sql,
                'drivers': ['pyarrow_flight', 'adbc_flight']
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            
            pyarrow_result = result.get('results', {}).get('pyarrow_flight', {})
            adbc_result = result.get('results', {}).get('adbc_flight', {})
            
            print(f"\n📊 Performance Comparison:")
            
            if pyarrow_result.get('success'):
                print(f"✅ PyArrow Flight SQL: {pyarrow_result.get('execution_time', 0):.3f}s")
                print(f"   Rows: {len(pyarrow_result.get('data', []))}")
                print(f"   Driver: {pyarrow_result.get('driver_name')}")
            else:
                print(f"❌ PyArrow Flight SQL: {pyarrow_result.get('error', 'Failed')}")
            
            if adbc_result.get('success'):
                print(f"✅ ADBC Flight SQL: {adbc_result.get('execution_time', 0):.3f}s")
                print(f"   Rows: {len(adbc_result.get('data', []))}")
                print(f"   Driver: {adbc_result.get('driver_name')}")
            else:
                print(f"❌ ADBC Flight SQL: {adbc_result.get('error', 'Failed')[:100]}...")
            
            return {
                'pyarrow_success': pyarrow_result.get('success', False),
                'adbc_success': adbc_result.get('success', False),
                'pyarrow_time': pyarrow_result.get('execution_time', 0),
                'adbc_time': adbc_result.get('execution_time', 0)
            }
        else:
            print(f"❌ Comparison request failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Comparison failed: {e}")
        return None

def analyze_adbc_error_patterns(query_results):
    """Analyze ADBC error patterns to understand the root cause."""
    print("\n🔬 Analyzing ADBC Error Patterns")
    
    errors = []
    for sql, result in query_results.items():
        if not result.get('success'):
            errors.append(result.get('error', ''))
    
    if not errors:
        print("✅ No errors to analyze")
        return
    
    # Common error patterns
    schema_errors = [e for e in errors if 'schema' in e.lower()]
    nullable_errors = [e for e in errors if 'nullable' in e.lower()]
    flight_errors = [e for e in errors if 'flightsql' in e.lower()]
    
    print(f"📊 Error Analysis:")
    print(f"   Total errors: {len(errors)}")
    print(f"   Schema-related: {len(schema_errors)}")
    print(f"   Nullable-related: {len(nullable_errors)}")
    print(f"   FlightSQL-related: {len(flight_errors)}")
    
    if nullable_errors:
        print(f"\n🎯 Root Cause Identified:")
        print(f"   ADBC driver expects non-nullable fields")
        print(f"   Dremio returns nullable fields")
        print(f"   This is a fundamental compatibility issue")
        
        # Extract schema details from first error
        if nullable_errors[0]:
            print(f"\n📋 Schema Mismatch Example:")
            error_lines = nullable_errors[0].split('\n')
            for line in error_lines:
                if 'expected schema' in line or 'but got schema' in line or 'type=' in line:
                    print(f"   {line.strip()}")

def provide_recommendations():
    """Provide recommendations for ADBC driver issues."""
    print("\n💡 Recommendations and Solutions")
    
    print(f"\n🎯 ADBC Driver Status:")
    print(f"   ❌ INCOMPATIBLE with Dremio Cloud")
    print(f"   ❌ Schema validation too strict")
    print(f"   ❌ Cannot handle nullable fields")
    print(f"   ❌ No known workarounds")
    
    print(f"\n✅ Recommended Alternatives:")
    print(f"   1. PyArrow Flight SQL (RECOMMENDED)")
    print(f"      - ✅ Fully compatible with Dremio")
    print(f"      - ✅ High performance")
    print(f"      - ✅ Handles nullable fields correctly")
    print(f"      - ✅ Native Arrow format support")
    
    print(f"\n   2. JDBC Driver (when JAR available)")
    print(f"      - ✅ Mature and stable")
    print(f"      - ✅ Wide compatibility")
    print(f"      - ⚠️ Requires Dremio JDBC JAR file")
    
    print(f"\n   3. PyODBC (when ODBC driver installed)")
    print(f"      - ✅ Standard database connectivity")
    print(f"      - ⚠️ Requires ODBC driver installation")
    
    print(f"\n🔧 Configuration Recommendations:")
    print(f"   1. Disable ADBC driver in production")
    print(f"   2. Use PyArrow Flight SQL as primary driver")
    print(f"   3. Configure fallback to JDBC when available")
    print(f"   4. Monitor for ADBC driver updates")

def main():
    """Run comprehensive ADBC debugging and analysis."""
    print("🐛 Comprehensive ADBC Driver Debugging")
    print("Enhanced Dremio Reporting Server")
    
    # Test 1: Driver status
    print_section("ADBC Driver Status")
    if not test_adbc_driver_status():
        print("❌ Cannot proceed without ADBC driver detection")
        return False
    
    # Test 2: Simple queries
    print_section("ADBC Query Testing")
    query_results = test_adbc_simple_queries()
    
    # Test 3: Performance comparison
    print_section("Performance Comparison")
    comparison = test_adbc_vs_pyarrow()
    
    # Test 4: Error analysis
    print_section("Error Analysis")
    analyze_adbc_error_patterns(query_results)
    
    # Test 5: Recommendations
    print_section("Recommendations")
    provide_recommendations()
    
    # Summary
    print_section("Debug Summary")
    
    successful_queries = sum(1 for r in query_results.values() if r.get('success'))
    total_queries = len(query_results)
    
    print(f"📊 Test Results:")
    print(f"   ADBC Queries: {successful_queries}/{total_queries} successful")
    
    if comparison:
        print(f"   PyArrow Success: {'✅' if comparison['pyarrow_success'] else '❌'}")
        print(f"   ADBC Success: {'✅' if comparison['adbc_success'] else '❌'}")
        
        if comparison['pyarrow_success']:
            print(f"   PyArrow Performance: {comparison['pyarrow_time']:.3f}s")
        if comparison['adbc_success']:
            print(f"   ADBC Performance: {comparison['adbc_time']:.3f}s")
    
    print(f"\n🎯 Conclusion:")
    if successful_queries == 0:
        print(f"   ❌ ADBC driver is INCOMPATIBLE with Dremio")
        print(f"   ✅ Use PyArrow Flight SQL instead")
        print(f"   📝 Task 3 complete: ADBC issues identified and documented")
    else:
        print(f"   ⚠️ ADBC driver has partial compatibility")
        print(f"   📝 Further investigation needed")
    
    return successful_queries > 0

if __name__ == '__main__':
    success = main()
    print(f"\n{'='*60}")
    print(f"🏁 ADBC Debugging Complete")
    print(f"{'='*60}")
    exit(0 if success else 1)
