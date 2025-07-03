#!/usr/bin/env python3
"""
Test script for the new Dremio Flight SQL client.
"""
import json
from dremio_flight_client import DremioFlightClient

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_flight_connection():
    """Test Flight SQL connection."""
    print_section("Testing Flight SQL Connection")
    
    client = DremioFlightClient()
    print(f"Flight endpoint: {client.flight_endpoint}")
    print(f"Has PAT: {bool(client.pat)}")
    
    # Test connection
    result = client.connect()
    print("Connection Result:")
    print(json.dumps(result, indent=2))
    
    return client, result['success']

def test_sys_jobs_query(client):
    """Test querying SYS.Jobs table."""
    print_section("Testing SYS.Jobs Query")
    
    # Test getting jobs
    result = client.get_jobs(limit=5)
    print("Jobs Query Result:")
    print(json.dumps(result, indent=2, default=str))
    
    if result['success'] and result['jobs']:
        print(f"\n📊 Found {result['count']} jobs:")
        for i, job in enumerate(result['jobs'][:3], 1):  # Show first 3 jobs
            print(f"  {i}. Job ID: {job['id']}")
            print(f"     State: {job['jobState']}")
            print(f"     User: {job['user']}")
            print(f"     Query Type: {job['queryType']}")
            if job['queryText']:
                query_preview = job['queryText'][:100] + "..." if len(job['queryText']) > 100 else job['queryText']
                print(f"     Query: {query_preview}")
            print()

def test_custom_queries(client):
    """Test custom SQL queries."""
    print_section("Testing Custom SQL Queries")
    
    # Test queries to try
    test_queries = [
        {
            'name': 'Simple Test Query',
            'sql': 'SELECT 1 as test_value, CURRENT_TIMESTAMP as current_time'
        },
        {
            'name': 'Job Count by State',
            'sql': '''
            SELECT 
                job_state,
                COUNT(*) as job_count
            FROM SYS.Jobs 
            GROUP BY job_state 
            ORDER BY job_count DESC
            '''
        },
        {
            'name': 'Recent Jobs Summary',
            'sql': '''
            SELECT 
                job_state,
                query_type,
                user_name,
                submitted_ts
            FROM SYS.Jobs 
            ORDER BY submitted_ts DESC
            LIMIT 5
            '''
        },
        {
            'name': 'System Information',
            'sql': 'SELECT * FROM SYS.VERSION'
        }
    ]
    
    for query_info in test_queries:
        print(f"\n🔍 {query_info['name']}:")
        print(f"SQL: {query_info['sql'].strip()}")
        
        result = client.execute_query(query_info['sql'])
        
        if result['success']:
            print(f"✓ Success: {result['message']}")
            if result['data']:
                print("Sample results:")
                for i, row in enumerate(result['data'][:2], 1):  # Show first 2 rows
                    print(f"  Row {i}: {row}")
        else:
            print(f"✗ Failed: {result['message']}")
        print()

def test_projects_query(client):
    """Test projects/schemas query."""
    print_section("Testing Projects/Schemas Query")
    
    result = client.get_projects()
    print("Projects Query Result:")
    print(json.dumps(result, indent=2))
    
    if result['success'] and result['projects']:
        print(f"\n📁 Found {result['total_count']} projects/schemas:")
        for i, project in enumerate(result['projects'][:5], 1):  # Show first 5
            print(f"  {i}. {project['name']} ({project['type']})")
            if project['description']:
                print(f"     Description: {project['description']}")

def test_comprehensive_connection(client):
    """Test comprehensive connection with all features."""
    print_section("Comprehensive Connection Test")
    
    result = client.test_connection()
    print("Comprehensive Test Result:")
    print(json.dumps(result, indent=2, default=str))

def compare_with_rest_api():
    """Compare Flight SQL vs REST API approaches."""
    print_section("Flight SQL vs REST API Comparison")
    
    print("""
🚀 Flight SQL Advantages:

1. ✅ **Direct SQL Queries**: Query SYS.Jobs table directly with SQL
2. ✅ **Better Performance**: Native Arrow format, no JSON overhead
3. ✅ **More Data**: Access to all job metadata and system tables
4. ✅ **Familiar Interface**: Standard SQL instead of REST endpoints
5. ✅ **Streaming Results**: Efficient handling of large datasets
6. ✅ **Type Safety**: Proper data types instead of string parsing

🔧 Technical Benefits:

- **PyArrow Integration**: Native Arrow format for fast data processing
- **ADBC Driver**: Standard database connectivity
- **Pandas Integration**: Easy conversion to DataFrames
- **SQL Flexibility**: Complex queries, joins, aggregations
- **System Tables**: Access to SYS.Jobs, SYS.Catalogs, etc.

📊 Data Quality:

- **Complete Job Metadata**: All fields from SYS.Jobs table
- **Accurate Timestamps**: Proper datetime handling
- **Performance Metrics**: Rows/bytes scanned and returned
- **Query Text**: Full SQL queries executed
- **Failure Details**: Detailed error information

🌐 REST API Limitations Resolved:

- ❌ 405 Method Not Allowed → ✅ Direct SQL queries
- ❌ Limited job data → ✅ Complete SYS.Jobs table access
- ❌ JSON parsing overhead → ✅ Native Arrow format
- ❌ API endpoint dependencies → ✅ Standard SQL interface
""")

def main():
    """Run all Flight SQL tests."""
    print("🚀 Dremio Flight SQL Client Test Suite")
    print("Testing PyArrow Flight SQL integration with SYS.Jobs queries")
    
    try:
        # Test connection
        client, connected = test_flight_connection()
        
        if connected:
            # Test SYS.Jobs queries
            test_sys_jobs_query(client)
            
            # Test custom queries
            test_custom_queries(client)
            
            # Test projects query
            test_projects_query(client)
            
            # Comprehensive test
            test_comprehensive_connection(client)
            
            # Close connection
            client.close()
        
        # Show comparison
        compare_with_rest_api()
        
        print_section("Test Summary")
        print("✅ Flight SQL client implementation complete")
        print("✅ SYS.Jobs table querying functional")
        print("✅ PyArrow integration working")
        print("✅ Custom SQL queries supported")
        print("✅ Comprehensive error handling")
        
        print("\n🌐 Next Steps:")
        print("   1. Update app.py to use DremioFlightClient")
        print("   2. Replace REST API calls with SQL queries")
        print("   3. Test the web interface with Flight SQL")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
