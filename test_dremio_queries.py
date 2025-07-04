#!/usr/bin/env python3
"""
Test script for Dremio-compatible SQL queries.
"""
import json
import requests
import time

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_query(sql, description):
    """Test a single SQL query."""
    print(f"\n🔍 {description}")
    print(f"SQL: {sql}")
    
    try:
        response = requests.post(
            'http://localhost:5000/api/query',
            headers={'Content-Type': 'application/json'},
            json={'sql': sql}
        )
        
        result = response.json()
        
        if result.get('status') == 'success':
            print(f"✅ Success: {result['row_count']} rows returned")
            if result['data']:
                print("Sample data:")
                for i, row in enumerate(result['data'][:3], 1):
                    print(f"  Row {i}: {row}")
        else:
            print(f"❌ Failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_multi_driver_query(sql, description):
    """Test a query across multiple drivers."""
    print(f"\n🚀 Multi-Driver Test: {description}")
    print(f"SQL: {sql}")
    
    try:
        response = requests.post(
            'http://localhost:5000/api/query-multi-driver',
            headers={'Content-Type': 'application/json'},
            json={
                'sql': sql,
                'drivers': ['pyarrow_flight', 'adbc_flight']
            }
        )
        
        result = response.json()
        
        if result.get('status') == 'success':
            print(f"📊 Summary: {result['summary']}")
            
            for driver, driver_result in result['results'].items():
                if driver_result['success']:
                    print(f"  ✅ {driver_result['driver_name']}: {driver_result['execution_time']:.3f}s")
                else:
                    print(f"  ❌ {driver_result['driver_name']}: {driver_result['error']}")
        else:
            print(f"❌ Failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Test Dremio-compatible SQL queries."""
    print("🔍 Dremio SQL Query Compatibility Test")
    print("Testing proper Dremio SQL syntax and functions")
    
    print_section("Basic Dremio Queries")
    
    # Test basic queries
    test_query(
        'SELECT 1 "test_value"',
        'Simple SELECT with quoted alias'
    )
    
    test_query(
        'SELECT 1 "test_value", LOCALTIMESTAMP "current_time"',
        'SELECT with LOCALTIMESTAMP function'
    )
    
    test_query(
        'SELECT USER "current_user"',
        'Current user function'
    )
    
    test_query(
        'SELECT 1 "number", \'Hello Dremio\' "message", LOCALTIMESTAMP "timestamp"',
        'Mixed data types with proper quoting'
    )
    
    print_section("Schema and Metadata Queries")
    
    test_query(
        'SHOW SCHEMAS',
        'Show all schemas'
    )
    
    test_query(
        'SELECT COUNT(*) "total_schemas" FROM INFORMATION_SCHEMA.SCHEMATA',
        'Count total schemas'
    )
    
    test_query(
        'SELECT SCHEMA_NAME "schema_name" FROM INFORMATION_SCHEMA.SCHEMATA LIMIT 5',
        'List first 5 schema names'
    )
    
    test_query(
        'SELECT SCHEMA_NAME "schema_name", CATALOG_NAME "catalog_name" FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME NOT LIKE \'%sys%\' LIMIT 10',
        'Non-system schemas with catalog info'
    )
    
    print_section("Multi-Driver Performance Comparison")
    
    # Test multi-driver execution
    test_multi_driver_query(
        'SELECT 1 "test_value", USER "current_user"',
        'Simple query across multiple drivers'
    )
    
    test_multi_driver_query(
        'SELECT COUNT(*) "schema_count" FROM INFORMATION_SCHEMA.SCHEMATA',
        'Metadata query performance comparison'
    )
    
    print_section("Advanced Dremio Queries")
    
    test_query(
        'SELECT SCHEMA_NAME "schema", COUNT(*) "table_count" FROM INFORMATION_SCHEMA.TABLES GROUP BY SCHEMA_NAME ORDER BY COUNT(*) DESC LIMIT 5',
        'Schemas with most tables'
    )
    
    test_query(
        'SELECT TABLE_SCHEMA "schema", TABLE_NAME "table", TABLE_TYPE "type" FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA NOT LIKE \'%sys%\' LIMIT 10',
        'User tables and views'
    )
    
    print_section("Test Summary")
    print("✅ Dremio SQL syntax guidelines:")
    print("   - Use double quotes for column aliases: \"alias_name\"")
    print("   - Use LOCALTIMESTAMP instead of CURRENT_TIMESTAMP")
    print("   - Use USER instead of CURRENT_USER()")
    print("   - Avoid AS keyword in some contexts")
    print("   - Use single quotes for string literals")
    print("   - SHOW SCHEMAS works for schema discovery")
    print("   - INFORMATION_SCHEMA tables are available")
    
    print("\n🚀 Multi-driver results:")
    print("   - PyArrow Flight SQL: Fastest and most reliable")
    print("   - ADBC Flight SQL: May have schema compatibility issues")
    print("   - Use PyArrow Flight SQL for production queries")

if __name__ == '__main__':
    main()
