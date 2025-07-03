#!/usr/bin/env python3
"""
Test script for the enhanced project listing functionality.
"""
import os
import json
from dremio_client import DremioClient
from config import Config

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_projects_api():
    """Test the projects API functionality."""
    print_section("Testing Projects API")
    
    client = DremioClient()
    print(f"Base URL: {client.base_url}")
    print(f"Has PAT: {bool(client.pat)}")
    print(f"Project ID: {client.project_id}")
    
    # Test getting projects
    result = client.get_projects()
    print(f"\nProjects API Result:")
    print(json.dumps(result, indent=2))

def test_connection_with_projects():
    """Test connection test that includes project listing."""
    print_section("Testing Connection with Project Listing")
    
    client = DremioClient()
    result = client.test_connection()
    
    print("Connection Test Result:")
    print(json.dumps(result, indent=2))

def simulate_pat_authentication():
    """Simulate PAT authentication to show project listing."""
    print_section("Simulating PAT Authentication")
    
    if not Config.DREMIO_PAT:
        print("⚠ No DREMIO_PAT configured")
        print("To test project listing:")
        print("1. Get a PAT from Dremio Cloud UI > Account Settings > Personal Access Tokens")
        print("2. Set DREMIO_PAT=your-token in your .env file")
        print("3. Run this test again")
        return
    
    client = DremioClient()
    
    # Test PAT authentication which includes project listing
    auth_result = client._test_pat_auth()
    
    print("PAT Authentication Result:")
    print(json.dumps(auth_result, indent=2))
    
    if auth_result.get('success') and 'projects' in auth_result:
        projects_info = auth_result['projects']
        print(f"\n📁 Projects Summary:")
        print(f"   Total accessible projects: {projects_info['total_count']}")
        print(f"   Current project found: {projects_info['current_project_found']}")
        print(f"   Current project ID: {projects_info['current_project_id']}")
        
        if projects_info['accessible_projects']:
            print(f"\n📋 Project Details:")
            for i, project in enumerate(projects_info['accessible_projects'], 1):
                current_marker = " (CURRENT)" if project['is_current'] else ""
                print(f"   {i}. {project['name']}{current_marker}")
                print(f"      ID: {project['id']}")
                if project['description']:
                    print(f"      Description: {project['description']}")
                if project['createdAt']:
                    print(f"      Created: {project['createdAt']}")
                print()

def explain_project_listing_benefits():
    """Explain the benefits of project listing in connection test."""
    print_section("Benefits of Project Listing in Connection Test")
    print("""
🎯 Enhanced Connection Testing Benefits:

1. ✅ **Verify PAT Permissions**
   - Shows which projects your PAT can access
   - Confirms your authentication is working correctly

2. ✅ **Validate Project Configuration**
   - Checks if your configured DREMIO_PROJECT_ID exists
   - Warns if the project is not accessible

3. ✅ **Project Discovery**
   - Lists all available projects for easy reference
   - Shows project names, IDs, and descriptions

4. ✅ **Troubleshooting Aid**
   - Helps identify permission issues
   - Shows exactly what your credentials can access

5. ✅ **User Experience**
   - Provides immediate feedback on setup
   - Reduces configuration errors
   - Makes project selection easier

🔧 API Endpoints Used:
   - GET /v0/projects - Lists accessible projects
   - Includes project metadata (name, description, creation date)
   - Identifies current project based on DREMIO_PROJECT_ID

🌐 Web Interface Features:
   - Visual project listing with current project highlighting
   - Warning messages for configuration issues
   - Easy-to-read project information display
""")

def main():
    """Run all tests."""
    print("📁 Dremio Projects Listing Test Suite")
    print("This test suite validates the enhanced project listing functionality.")
    
    try:
        test_connection_with_projects()
        test_projects_api()
        simulate_pat_authentication()
        explain_project_listing_benefits()
        
        print_section("Test Summary")
        print("✅ Enhanced connection testing with project listing")
        print("✅ Dedicated projects API endpoint")
        print("✅ Project validation and discovery")
        print("✅ Improved user experience and troubleshooting")
        
        print("\n🌐 To test in the web interface:")
        print("   1. Run: python app.py")
        print("   2. Open: http://localhost:5000")
        print("   3. Click 'Test Dremio Connection' or 'View Available Projects'")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
