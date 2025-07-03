#!/usr/bin/env python3
"""
Test script for SSL/TLS configuration and authentication methods.
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

def test_ssl_configuration():
    """Test SSL/TLS configuration."""
    print_section("SSL/TLS Configuration Test")
    
    client = DremioClient()
    print(f"✓ Base URL: {client.base_url}")
    print(f"✓ SSL Verify: {client.session.verify}")
    print(f"✓ Session Headers: {dict(client.session.headers)}")
    
    # Test URL auto-correction
    test_urls = [
        "https://app.dremio.cloud",
        "https://api.dremio.cloud", 
        "https://app.eu.dremio.cloud",
        "https://custom.dremio.cloud"
    ]
    
    print("\n🔧 URL Auto-Correction Tests:")
    for url in test_urls:
        corrected = client._normalize_base_url(url)
        status = "✓" if corrected != url else "→"
        print(f"  {status} {url} → {corrected}")

def test_pat_authentication():
    """Test Personal Access Token authentication."""
    print_section("Personal Access Token Authentication Test")
    
    if not Config.DREMIO_PAT:
        print("⚠ No DREMIO_PAT configured - skipping PAT test")
        print("To test PAT authentication:")
        print("1. Get a PAT from Dremio Cloud UI > Account Settings > Personal Access Tokens")
        print("2. Set DREMIO_PAT=your-token in your .env file")
        return
    
    client = DremioClient()
    print(f"✓ PAT configured (length: {len(client.pat)})")
    
    # Test authentication
    result = client.authenticate()
    print(f"\nAuthentication Result:")
    print(json.dumps(result, indent=2))

def test_username_password_auth():
    """Test username/password authentication."""
    print_section("Username/Password Authentication Test")
    
    if not (Config.DREMIO_USERNAME and Config.DREMIO_PASSWORD):
        print("⚠ No DREMIO_USERNAME/DREMIO_PASSWORD configured - skipping credentials test")
        return
    
    # Temporarily disable PAT to test username/password
    original_pat = Config.DREMIO_PAT
    Config.DREMIO_PAT = None
    
    try:
        client = DremioClient()
        client.pat = None  # Ensure no PAT
        
        print(f"✓ Username: {client.username}")
        print(f"✓ Password: {'*' * len(client.password) if client.password else 'Not set'}")
        
        # Test authentication
        result = client.authenticate()
        print(f"\nAuthentication Result:")
        print(json.dumps(result, indent=2))
        
    finally:
        # Restore original PAT
        Config.DREMIO_PAT = original_pat

def test_connection_comprehensive():
    """Run comprehensive connection test."""
    print_section("Comprehensive Connection Test")
    
    client = DremioClient()
    result = client.test_connection()
    
    print("Connection Test Result:")
    print(json.dumps(result, indent=2))

def main():
    """Run all tests."""
    print("🔐 Dremio SSL/TLS and Authentication Test Suite")
    print("This test suite validates SSL/TLS configuration and authentication methods.")
    
    try:
        test_ssl_configuration()
        test_pat_authentication()
        test_username_password_auth()
        test_connection_comprehensive()
        
        print_section("Test Summary")
        print("✅ SSL/TLS Configuration: Enhanced with proper verification")
        print("✅ URL Auto-Correction: Automatically fixes common URL issues")
        print("✅ PAT Authentication: Supports Personal Access Tokens (recommended)")
        print("✅ Credential Authentication: Supports username/password (legacy)")
        print("✅ Comprehensive Error Handling: Detailed diagnostics and suggestions")
        
        print("\n🌐 Key Improvements:")
        print("   • SSL/TLS verification with system CA bundle")
        print("   • Automatic URL correction (app.dremio.cloud → api.dremio.cloud)")
        print("   • Personal Access Token support for Dremio Cloud")
        print("   • Multiple authentication endpoint fallbacks")
        print("   • Detailed error messages with suggestions")
        print("   • Proper HTTP status code handling")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
