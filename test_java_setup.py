#!/usr/bin/env python3
"""
Test script to verify Java environment setup for Dremio Reporting Server.
"""
import os
import sys

def test_java_environment():
    """Test Java environment setup."""
    print("🧪 Testing Java Environment Setup")
    print("=" * 40)
    
    # Test 1: Check JAVA_HOME
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        print(f"✅ JAVA_HOME set: {java_home}")
        if os.path.exists(java_home):
            print(f"✅ JAVA_HOME directory exists")
        else:
            print(f"❌ JAVA_HOME directory not found")
            return False
    else:
        print("❌ JAVA_HOME not set")
        return False
    
    # Test 2: Check Java executable
    java_bin = os.path.join(java_home, 'bin', 'java')
    if os.path.exists(java_bin):
        print(f"✅ Java executable found: {java_bin}")
    else:
        print(f"❌ Java executable not found: {java_bin}")
        return False
    
    # Test 3: Test JPype import
    try:
        import jpype
        print(f"✅ JPype available for Java-Python bridge")
    except ImportError:
        print("❌ JPype not available")
        return False
    
    # Test 4: Test JayDeBeApi import
    try:
        import jaydebeapi
        print(f"✅ JayDeBeApi available: v{jaydebeapi.__version__}")
    except ImportError:
        print("❌ JayDeBeApi not available")
        return False
    
    # Test 5: Test JVM startup (without actually starting it)
    try:
        if not jpype.isJVMStarted():
            print("✅ JVM not started (ready for initialization)")
        else:
            print("✅ JVM already started")
    except Exception as e:
        print(f"❌ JVM test failed: {e}")
        return False
    
    print("\n🎉 All Java environment tests passed!")
    print("The system is ready for JDBC driver functionality.")
    return True

if __name__ == '__main__':
    success = test_java_environment()
    sys.exit(0 if success else 1)
