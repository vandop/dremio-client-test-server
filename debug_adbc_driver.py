#!/usr/bin/env python3
"""
Debug script for ADBC Flight SQL driver issues with Dremio.
"""
import os
import sys
import traceback
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_adbc_import():
    """Test ADBC driver import."""
    print("\n🔍 Testing ADBC Driver Import")
    
    try:
        import adbc_driver_flightsql
        print(f"✅ ADBC Flight SQL driver available: v{adbc_driver_flightsql.__version__}")
        
        import adbc_driver_flightsql.dbapi as flight_sql
        print("✅ ADBC Flight SQL dbapi module imported")
        
        return True
    except ImportError as e:
        print(f"❌ ADBC import failed: {e}")
        return False

def test_adbc_connection():
    """Test ADBC connection to Dremio."""
    print("\n🔗 Testing ADBC Connection")
    
    try:
        import adbc_driver_flightsql.dbapi as flight_sql
        
        # Get configuration
        dremio_url = os.environ.get('DREMIO_URL', 'https://api.dremio.cloud')
        pat = os.environ.get('DREMIO_PAT')
        
        if not pat:
            print("❌ DREMIO_PAT not found in environment")
            return None
        
        # Convert URL to Flight endpoint
        if 'api.dremio.cloud' in dremio_url:
            endpoint = 'grpc+tls://data.dremio.cloud:443'
        else:
            endpoint = dremio_url.replace('https://', 'grpc+tls://').replace('http://', 'grpc+tls://') + ':443'
        
        print(f"📡 Connecting to: {endpoint}")

        # Create connection with basic configuration
        connection = flight_sql.connect(
            endpoint,
            db_kwargs={
                "adbc.flight.sql.authorization_header": f"Bearer {pat}",
                "adbc.flight.sql.client_option.tls_skip_verify": "false"
            }
        )
        
        print("✅ ADBC connection established")
        return connection
        
    except Exception as e:
        print(f"❌ ADBC connection failed: {e}")
        traceback.print_exc()
        return None

def test_simple_queries(connection):
    """Test simple queries to identify schema issues."""
    print("\n🧪 Testing Simple Queries")
    
    test_queries = [
        ("SELECT 1", "Simple integer literal"),
        ("SELECT 1 \"test_value\"", "Integer with alias"),
        ("SELECT CAST(1 AS INTEGER)", "Explicit integer cast"),
        ("SELECT CAST(1 AS INTEGER) \"test_value\"", "Explicit cast with alias"),
        ("SELECT 'hello' \"text_value\"", "String literal"),
        ("SELECT USER", "User function"),
        ("SELECT LOCALTIMESTAMP", "Timestamp function"),
    ]
    
    results = {}
    
    for sql, description in test_queries:
        print(f"\n🔍 {description}: {sql}")
        
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            
            # Try to get schema information
            try:
                arrow_table = cursor.fetch_arrow_table()
                schema = arrow_table.schema
                print(f"✅ Success - Schema: {schema}")

                # Convert to pandas and check data
                df = arrow_table.to_pandas()

            except Exception as schema_error:
                print(f"❌ Schema error: {schema_error}")
                results[sql] = {
                    'success': False,
                    'error': str(schema_error),
                    'error_type': 'schema_error'
                }
                continue

            # Process successful results
            print(f"   Data shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
            print(f"   Data types: {df.dtypes.to_dict()}")

            if len(df) > 0:
                print(f"   Sample data: {df.iloc[0].to_dict()}")

            results[sql] = {
                'success': True,
                'schema': str(schema),
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': df.dtypes.to_dict()
            }
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
            results[sql] = {
                'success': False,
                'error': str(e),
                'error_type': 'query_error'
            }
    
    return results

def test_schema_handling_options(connection):
    """Test different approaches to handle schema inconsistencies."""
    print("\n🔧 Testing Schema Handling Options")
    
    sql = "SELECT 1 \"test_value\""
    
    # Option 1: Try with different fetch methods
    print("\n1. Testing different fetch methods:")
    
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        
        # Try fetch_arrow_table with different options
        try:
            print("   Trying fetch_arrow_table()...")
            arrow_table = cursor.fetch_arrow_table()
            print(f"   ✅ fetch_arrow_table() worked: {arrow_table.schema}")
        except Exception as e:
            print(f"   ❌ fetch_arrow_table() failed: {e}")
        
        # Try fetchall
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            print("   Trying fetchall()...")
            rows = cursor.fetchall()
            print(f"   ✅ fetchall() worked: {len(rows)} rows")
            if rows:
                print(f"   Sample row: {rows[0]}")
        except Exception as e:
            print(f"   ❌ fetchall() failed: {e}")
            
        # Try fetchone
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            print("   Trying fetchone()...")
            row = cursor.fetchone()
            print(f"   ✅ fetchone() worked: {row}")
        except Exception as e:
            print(f"   ❌ fetchone() failed: {e}")
            
    except Exception as e:
        print(f"❌ Cursor execution failed: {e}")

def test_workarounds(connection):
    """Test potential workarounds for schema issues."""
    print("\n🛠️ Testing Workarounds")
    
    workarounds = [
        # Try explicit casting to make fields non-nullable
        ("SELECT CAST(1 AS INTEGER) \"test_value\"", "Explicit INTEGER cast"),
        ("SELECT COALESCE(1, 0) \"test_value\"", "COALESCE to handle nullability"),
        ("SELECT CASE WHEN 1 IS NOT NULL THEN 1 ELSE 0 END \"test_value\"", "CASE statement"),
        
        # Try different data types
        ("SELECT CAST(1 AS BIGINT) \"test_value\"", "BIGINT cast"),
        ("SELECT CAST(1 AS SMALLINT) \"test_value\"", "SMALLINT cast"),
        ("SELECT CAST(1.0 AS DOUBLE) \"test_value\"", "DOUBLE cast"),
        
        # Try string values (often more compatible)
        ("SELECT CAST('1' AS VARCHAR) \"test_value\"", "VARCHAR cast"),
        ("SELECT '1' \"test_value\"", "String literal"),
    ]
    
    working_queries = []
    
    for sql, description in workarounds:
        print(f"\n🔍 {description}: {sql}")
        
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            
            # Try to fetch as Arrow table
            arrow_table = cursor.fetch_arrow_table()
            df = arrow_table.to_pandas()
            
            print(f"✅ Success - Schema: {arrow_table.schema}")
            print(f"   Data: {df.iloc[0].to_dict()}")
            
            working_queries.append((sql, description, str(arrow_table.schema)))
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    return working_queries

def main():
    """Run comprehensive ADBC debugging."""
    print("🐛 ADBC Flight SQL Driver Debugging")
    print("Investigating schema inconsistency issues with Dremio")
    
    # Test 1: Import
    if not test_adbc_import():
        print("❌ Cannot proceed without ADBC driver")
        return False
    
    # Test 2: Connection
    connection = test_adbc_connection()
    if not connection:
        print("❌ Cannot proceed without connection")
        return False
    
    try:
        # Test 3: Simple queries
        print_section("Simple Query Testing")
        query_results = test_simple_queries(connection)
        
        # Test 4: Schema handling
        print_section("Schema Handling Options")
        test_schema_handling_options(connection)
        
        # Test 5: Workarounds
        print_section("Workaround Testing")
        working_queries = test_workarounds(connection)
        
        # Summary
        print_section("Debug Summary")
        
        successful_queries = [sql for sql, result in query_results.items() if result.get('success')]
        failed_queries = [sql for sql, result in query_results.items() if not result.get('success')]
        
        print(f"📊 Query Results:")
        print(f"   ✅ Successful: {len(successful_queries)}")
        print(f"   ❌ Failed: {len(failed_queries)}")
        
        if working_queries:
            print(f"\n🛠️ Working Workarounds:")
            for sql, desc, schema in working_queries:
                print(f"   ✅ {desc}: {sql}")
                print(f"      Schema: {schema}")
        
        if failed_queries:
            print(f"\n❌ Failed Queries:")
            for sql in failed_queries:
                error = query_results[sql].get('error', 'Unknown error')
                print(f"   • {sql}: {error}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if working_queries:
            print("   1. Use explicit casting to avoid nullable field issues")
            print("   2. Consider using COALESCE for null handling")
            print("   3. Test with string types for better compatibility")
        else:
            print("   1. ADBC driver may have fundamental compatibility issues")
            print("   2. Consider using PyArrow Flight SQL instead")
            print("   3. Check ADBC driver version compatibility")
        
        return len(working_queries) > 0
        
    finally:
        try:
            connection.close()
            print("\n🔌 Connection closed")
        except:
            pass

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
