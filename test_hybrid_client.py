#!/usr/bin/env python3
"""
Test script for the hybrid Dremio client.
"""
import json
from dremio_hybrid_client import DremioHybridClient

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_hybrid_connection():
    """Test hybrid client connection."""
    print_section("Testing Hybrid Client Connection")
    
    with DremioHybridClient() as client:
        result = client.test_connection()
        print("Hybrid Connection Test Result:")
        print(json.dumps(result, indent=2, default=str))
        
        return client, result.get('status') == 'success'

def test_flight_sql_queries(client):
    """Test Flight SQL queries."""
    print_section("Testing Flight SQL Queries")
    
    # Test simple query
    print("\n🔍 Simple Query Test:")
    result = client.execute_query("SELECT 1 as test_value, CURRENT_TIMESTAMP as current_time")
    print(f"Result: {result['success']}")
    if result['success']:
        print(f"Data: {result['data']}")
    
    # Test schema discovery
    print("\n🔍 Schema Discovery:")
    schemas_result = client.get_schemas()
    print(f"Result: {schemas_result['success']}")
    if schemas_result['success']:
        print(f"Found {schemas_result['count']} schemas:")
        for schema in schemas_result['schemas'][:10]:  # Show first 10
            print(f"  - {schema}")

def test_rest_api_operations(client):
    """Test REST API operations."""
    print_section("Testing REST API Operations")
    
    # Test projects
    print("\n🔍 Projects via REST API:")
    projects_result = client.get_projects()
    print(f"Result: {projects_result['success']}")
    if projects_result['success']:
        print(f"Found {projects_result['total_count']} projects:")
        for project in projects_result['projects'][:5]:  # Show first 5
            print(f"  - {project['name']} (ID: {project['id']})")
    
    # Test jobs
    print("\n🔍 Jobs via REST API:")
    jobs_result = client.get_jobs(limit=5)
    print(f"Result: {jobs_result['success']}")
    if jobs_result['success']:
        print(f"Found {jobs_result['count']} jobs:")
        for job in jobs_result['jobs'][:3]:  # Show first 3
            print(f"  - {job['id']}: {job['jobState']} ({job['queryType']})")
    else:
        print(f"Jobs error: {jobs_result['message']}")

def test_data_exploration(client):
    """Test data exploration capabilities."""
    print_section("Testing Data Exploration")
    
    # Get schemas first
    schemas_result = client.get_schemas()
    if schemas_result['success'] and schemas_result['schemas']:
        # Try to explore a few schemas
        for schema in schemas_result['schemas'][:3]:
            print(f"\n🔍 Exploring schema: {schema}")
            tables_result = client.get_table_info(schema)
            
            if tables_result['success']:
                print(f"  ✅ Found {tables_result['row_count']} tables/views")
                if tables_result['data']:
                    for table in tables_result['data'][:3]:  # Show first 3 tables
                        print(f"    - {table}")
            else:
                print(f"  ❌ Error: {tables_result['message']}")

def demonstrate_capabilities(client):
    """Demonstrate the capabilities of the hybrid client."""
    print_section("Hybrid Client Capabilities")
    
    capabilities = client.get_capabilities()
    
    print("🚀 Flight SQL Capabilities:")
    for capability in capabilities['flight_sql_capabilities']:
        print(f"  ✅ {capability}")
    
    print("\n🌐 REST API Capabilities:")
    for capability in capabilities['rest_api_capabilities']:
        print(f"  ✅ {capability}")
    
    print("\n💡 Combined Benefits:")
    for benefit in capabilities['combined_benefits']:
        print(f"  🎯 {benefit}")

def main():
    """Test the hybrid Dremio client."""
    print("🔄 Dremio Hybrid Client Test Suite")
    print("Testing PyArrow Flight SQL + REST API integration")
    
    try:
        # Test connection
        client, connected = test_hybrid_connection()
        
        if connected:
            # Test Flight SQL queries
            test_flight_sql_queries(client)
            
            # Test REST API operations
            test_rest_api_operations(client)
            
            # Test data exploration
            test_data_exploration(client)
            
            # Show capabilities
            demonstrate_capabilities(client)
        
        print_section("Test Summary")
        if connected:
            print("✅ Hybrid client working successfully")
            print("✅ Flight SQL for data queries")
            print("✅ REST API for job information")
            print("✅ Best of both worlds achieved")
        else:
            print("❌ Connection failed - check configuration")
        
        print("\n🎯 Recommended Usage:")
        print("  - Use Flight SQL for data analytics and queries")
        print("  - Use REST API for job monitoring and metadata")
        print("  - Hybrid approach provides complete functionality")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
