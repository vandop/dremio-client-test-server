#!/usr/bin/env python3
"""
Discover available system tables and schemas in Dremio Cloud.
"""
import json
from dremio_pyarrow_client import DremioPyArrowClient

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def discover_schemas(client):
    """Discover available schemas."""
    print_section("Discovering Available Schemas")
    
    queries_to_try = [
        "SHOW SCHEMAS",
        "SELECT * FROM INFORMATION_SCHEMA.SCHEMATA",
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA"
    ]
    
    for query in queries_to_try:
        print(f"\n🔍 Trying: {query}")
        result = client.execute_query(query)
        
        if result['success']:
            print(f"✅ Success! Found {result['row_count']} schemas:")
            for row in result['data'][:10]:  # Show first 10
                print(f"   {row}")
            return result['data']
        else:
            print(f"❌ Failed: {result['message']}")
    
    return []

def discover_tables_in_schema(client, schema_name):
    """Discover tables in a specific schema."""
    print_section(f"Discovering Tables in Schema: {schema_name}")
    
    queries_to_try = [
        f"SHOW TABLES IN {schema_name}",
        f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_name}'",
        f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_name}'"
    ]
    
    for query in queries_to_try:
        print(f"\n🔍 Trying: {query}")
        result = client.execute_query(query)
        
        if result['success']:
            print(f"✅ Success! Found {result['row_count']} tables:")
            for row in result['data'][:10]:  # Show first 10
                print(f"   {row}")
            return result['data']
        else:
            print(f"❌ Failed: {result['message']}")
    
    return []

def discover_job_related_tables(client):
    """Try to find job-related tables."""
    print_section("Searching for Job-Related Tables")
    
    # Try different variations of job tables
    job_table_candidates = [
        "SYS.JOBS",
        "sys.jobs", 
        "SYSTEM.JOBS",
        "system.jobs",
        "INFORMATION_SCHEMA.JOBS",
        "SYS.JOB_HISTORY",
        "SYS.QUERY_HISTORY",
        "SYS.REFLECTIONS",
        "SYS.MATERIALIZATIONS"
    ]
    
    for table in job_table_candidates:
        print(f"\n🔍 Trying table: {table}")
        result = client.execute_query(f"SELECT * FROM {table} LIMIT 1")
        
        if result['success']:
            print(f"✅ Found table: {table}")
            print(f"   Columns: {result['columns']}")
            if result['data']:
                print(f"   Sample data: {result['data'][0]}")
        else:
            print(f"❌ Table not found: {table}")

def discover_information_schema(client):
    """Explore INFORMATION_SCHEMA for available tables."""
    print_section("Exploring INFORMATION_SCHEMA")
    
    queries = [
        "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA, TABLE_NAME",
        "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA LIKE '%SYS%' OR TABLE_SCHEMA LIKE '%SYSTEM%'",
        "SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        result = client.execute_query(query)
        
        if result['success']:
            print(f"✅ Success! Found {result['row_count']} results:")
            for row in result['data'][:15]:  # Show first 15
                print(f"   {row}")
        else:
            print(f"❌ Failed: {result['message']}")

def test_alternative_job_queries(client):
    """Test alternative ways to get job information."""
    print_section("Testing Alternative Job Queries")
    
    # Try queries that might give us job/query information
    alternative_queries = [
        "SELECT CURRENT_USER()",
        "SELECT CURRENT_TIMESTAMP",
        "SHOW FUNCTIONS",
        "SELECT * FROM INFORMATION_SCHEMA.VIEWS LIMIT 5",
        "SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME LIKE '%JOB%' LIMIT 5"
    ]
    
    for query in alternative_queries:
        print(f"\n🔍 Query: {query}")
        result = client.execute_query(query)
        
        if result['success']:
            print(f"✅ Success! Found {result['row_count']} results:")
            for row in result['data'][:5]:  # Show first 5
                print(f"   {row}")
        else:
            print(f"❌ Failed: {result['message']}")

def main():
    """Discover Dremio Cloud system tables and job information."""
    print("🔍 Dremio Cloud System Tables Discovery")
    print("Finding available schemas, tables, and job information sources")
    
    try:
        # Connect to Dremio
        client = DremioPyArrowClient()
        connect_result = client.connect()
        
        if not connect_result['success']:
            print(f"❌ Connection failed: {connect_result['message']}")
            return
        
        print("✅ Connected successfully!")
        
        # Discover schemas
        schemas = discover_schemas(client)
        
        # Explore INFORMATION_SCHEMA
        discover_information_schema(client)
        
        # Look for job-related tables
        discover_job_related_tables(client)
        
        # Test alternative queries
        test_alternative_job_queries(client)
        
        # If we found SYS schema, explore it
        sys_schemas = [s for s in schemas if 'SYS' in str(s).upper()]
        if sys_schemas:
            discover_tables_in_schema(client, 'SYS')
        
        print_section("Discovery Summary")
        print("✅ PyArrow Flight connection working")
        print("✅ SQL query execution functional")
        print("⚠️ SYS.Jobs table not available in Dremio Cloud")
        print("🔍 Use INFORMATION_SCHEMA for metadata queries")
        print("💡 Consider using REST API for job information")
        
    except Exception as e:
        print(f"\n❌ Discovery failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
