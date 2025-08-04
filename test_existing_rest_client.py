#!/usr/bin/env python3
"""
Test script to verify the existing REST API client works.
This will help us understand the correct approach for the PyArrow client.
"""
import json
from dremio_client import DremioClient

def test_existing_rest_client():
    """Test the existing REST client."""
    print("Testing Existing Dremio REST Client")
    print("=" * 50)
    
    try:
        client = DremioClient()
        print(f"Base URL: {client.base_url}")
        print(f"Project ID: {client.project_id}")
        print(f"Has PAT: {bool(client.pat)}")
        
        # Test getting jobs
        print("\n--- Testing get_jobs() method ---")
        jobs_result = client.get_jobs(limit=3)
        
        print("Jobs Result:")
        print(json.dumps(jobs_result, indent=2, default=str))
        
        if jobs_result['success']:
            print(f"\n✅ Successfully retrieved {len(jobs_result.get('jobs', []))} jobs")
        else:
            print(f"\n❌ Failed to retrieve jobs: {jobs_result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_existing_rest_client()
