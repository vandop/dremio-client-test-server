#!/usr/bin/env python3
"""
Test script to demonstrate correct Dremio Cloud authentication.
"""
import os
import json
import requests
from dremio_client import DremioClient
from config import Config

def test_direct_api_call():
    """Test direct API call to understand the correct authentication method."""
    print("=== Testing Direct Dremio Cloud API Call ===")
    
    # Test without authentication
    print("\n1. Testing without authentication:")
    try:
        response = requests.get("https://api.dremio.cloud/v0/projects", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code == 401:
            print("✓ Expected 401 - authentication required")
        else:
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with PAT if available
    if Config.DREMIO_PAT:
        print(f"\n2. Testing with PAT (length: {len(Config.DREMIO_PAT)}):")
        try:
            headers = {
                'Authorization': f'Bearer {Config.DREMIO_PAT}',
                'Content-Type': 'application/json'
            }
            response = requests.get("https://api.dremio.cloud/v0/projects", 
                                  headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✓ PAT authentication successful!")
                data = response.json()
                print(f"Projects found: {len(data.get('data', []))}")
            else:
                print(f"Response: {response.text[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\n2. No PAT configured - skipping PAT test")

def test_client_authentication():
    """Test our client authentication."""
    print("\n=== Testing DremioClient Authentication ===")
    
    client = DremioClient()
    print(f"Base URL: {client.base_url}")
    print(f"Has PAT: {bool(client.pat)}")
    print(f"Has Username/Password: {bool(client.username and client.password)}")
    
    # Test authentication
    result = client.authenticate()
    print(f"\nAuthentication Result:")
    print(json.dumps(result, indent=2))

def test_configuration_validation():
    """Test configuration validation."""
    print("\n=== Testing Configuration Validation ===")
    
    try:
        Config.validate_dremio_config()
        print("✓ Configuration validation passed")
    except ValueError as e:
        print(f"✗ Configuration validation failed: {e}")

def explain_405_errors():
    """Explain why we were getting 405 errors."""
    print("\n=== Why We Got 405 Errors ===")
    print("""
The 405 "Method Not Allowed" errors occurred because:

1. ❌ We were trying to POST to login endpoints that don't exist in Dremio Cloud
   - /v0/login (404 - doesn't exist)
   - /api/v3/login (405 - wrong method)
   - /apiv2/login (405 - wrong method)
   - /login (405 - wrong method)

2. ✅ Dremio Cloud uses Personal Access Tokens (PAT) with Bearer authentication
   - No login endpoint needed
   - Use: Authorization: Bearer <your-pat>
   - Direct API access to endpoints like /v0/projects

3. 🔧 Correct approach:
   - Get PAT from Dremio Cloud UI
   - Set DREMIO_PAT in .env file
   - Use Bearer token in Authorization header
   - Test with /v0/projects endpoint
""")

def main():
    """Run all tests."""
    print("🔍 Dremio Cloud Authentication Analysis")
    print("This script analyzes the correct authentication method for Dremio Cloud.")
    
    test_configuration_validation()
    test_direct_api_call()
    test_client_authentication()
    explain_405_errors()
    
    print("\n🎯 Summary:")
    print("- Dremio Cloud requires Personal Access Token (PAT)")
    print("- No username/password login endpoints available")
    print("- Use Bearer token authentication for all API calls")
    print("- Get your PAT from Dremio Cloud UI > Account Settings > Personal Access Tokens")

if __name__ == '__main__':
    main()
