#!/usr/bin/env python3
"""
Test script to verify the REST API jobs functionality in the PyArrow client.
"""
import json
import time
from dremio_pyarrow_client import DremioPyArrowClient

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_rest_api_jobs():
    """Test REST API jobs functionality."""
    print_section("Testing REST API Jobs Functionality")

    client = DremioPyArrowClient()
    print(f"Base URL: {client.base_url}")
    print(f"Project ID: {client.project_id}")
    print(f"Has PAT: {bool(client.pat)}")

    # Test getting jobs via REST API
    print("\n--- Testing get_jobs() method ---")
    jobs_result = client.get_jobs(limit=5)
    
    print("Jobs Result:")
    print(json.dumps(jobs_result, indent=2, default=str))
    
    if jobs_result['success']:
        print(f"\n✅ Successfully retrieved {jobs_result['count']} jobs via {jobs_result['query_method']}")
        
        if jobs_result['jobs']:
            print("\nFirst job details:")
            first_job = jobs_result['jobs'][0]
            for key, value in first_job.items():
                print(f"  {key}: {value}")
    else:
        print(f"\n❌ Failed to retrieve jobs: {jobs_result['message']}")
        if 'error_type' in jobs_result:
            print(f"Error type: {jobs_result['error_type']}")

def test_full_connection():
    """Test full connection including jobs."""
    print_section("Testing Full Connection with Jobs")
    
    client = DremioPyArrowClient()
    
    # Test full connection
    result = client.test_connection()
    
    print("Full Connection Test Result:")
    print(json.dumps(result, indent=2, default=str))
    
    if result['status'] == 'success':
        print(f"\n✅ Full connection test successful!")
        print(f"Jobs method: {result['details'].get('jobs_method', 'unknown')}")
        print(f"Jobs count: {result['details'].get('jobs_count', 0)}")
    else:
        print(f"\n❌ Connection test failed: {result.get('message', 'Unknown error')}")

def main():
    """Main test function."""
    print("Testing Dremio PyArrow Client with REST API Jobs")
    print("=" * 60)
    
    try:
        # Test REST API jobs functionality
        test_rest_api_jobs()
        
        # Test full connection
        test_full_connection()
        
        print("\n" + "=" * 60)
        print("Test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
