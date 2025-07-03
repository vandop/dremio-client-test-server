#!/usr/bin/env python3
"""
Demo script to showcase the enhanced error handling in Dremio Reporting Server.
"""
import os
import json
from dremio_client import DremioClient

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(result):
    """Pretty print a result dictionary."""
    print(json.dumps(result, indent=2))

def demo_no_config():
    """Demo with no configuration."""
    print_section("Demo 1: No Configuration")
    
    # Clear environment variables
    for var in ['DREMIO_CLOUD_URL', 'DREMIO_USERNAME', 'DREMIO_PASSWORD', 'DREMIO_PROJECT_ID']:
        if var in os.environ:
            del os.environ[var]
    
    # Reload config
    import importlib
    import config
    importlib.reload(config)
    
    client = DremioClient()
    result = client.test_connection()
    print_result(result)

def demo_invalid_url():
    """Demo with invalid URL."""
    print_section("Demo 2: Invalid URL")
    
    os.environ.update({
        'DREMIO_CLOUD_URL': 'https://invalid-url-that-does-not-exist.com',
        'DREMIO_USERNAME': 'test@example.com',
        'DREMIO_PASSWORD': 'testpass',
        'DREMIO_PROJECT_ID': 'test-project'
    })
    
    # Reload config
    import importlib
    import config
    importlib.reload(config)
    
    client = DremioClient()
    result = client.test_connection()
    print_result(result)

def demo_wrong_endpoint():
    """Demo with wrong endpoint (valid domain but wrong path)."""
    print_section("Demo 3: Wrong Endpoint")
    
    os.environ.update({
        'DREMIO_CLOUD_URL': 'https://httpbin.org',  # Valid URL but not Dremio
        'DREMIO_USERNAME': 'test@example.com',
        'DREMIO_PASSWORD': 'testpass',
        'DREMIO_PROJECT_ID': 'test-project'
    })
    
    # Reload config
    import importlib
    import config
    importlib.reload(config)
    
    client = DremioClient()
    result = client.test_connection()
    print_result(result)

def main():
    """Run all demos."""
    print("🔍 Dremio Reporting Server - Enhanced Error Handling Demo")
    print("This demo shows detailed error messages and suggestions for common issues.")
    
    try:
        demo_no_config()
    except Exception as e:
        print(f"Error in demo_no_config: {e}")
    
    try:
        demo_invalid_url()
    except Exception as e:
        print(f"Error in demo_invalid_url: {e}")
    
    try:
        demo_wrong_endpoint()
    except Exception as e:
        print(f"Error in demo_wrong_endpoint: {e}")
    
    print_section("Demo Complete")
    print("✅ Enhanced error handling provides:")
    print("   • Detailed error messages")
    print("   • Specific error types")
    print("   • Helpful suggestions")
    print("   • Console logging")
    print("   • Web UI error display")
    print("\n🌐 To see the web UI error display:")
    print("   1. Run: python app.py")
    print("   2. Open: http://localhost:5000")
    print("   3. Click 'Test Dremio Connection'")

if __name__ == '__main__':
    main()
