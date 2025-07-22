#!/usr/bin/env python3
"""
Test script to verify complete setup is working correctly.
This script tests all the components that were set up.
"""
import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_status(message, success=True):
    status = "✅" if success else "❌"
    print(f"{status} {message}")

def test_environment_files():
    """Test that environment files were created correctly."""
    print_header("Testing Environment Files")
    
    # Test .env file
    env_file = Path(".env")
    if env_file.exists():
        print_status(".env file exists")
        
        # Check for JAVA_HOME in .env
        with open(env_file) as f:
            content = f.read()
            if "JAVA_HOME=" in content:
                print_status("JAVA_HOME found in .env file")
            else:
                print_status("JAVA_HOME not found in .env file", False)
    else:
        print_status(".env file not found", False)
    
    # Test setup_env.sh file
    setup_env = Path("setup_env.sh")
    if setup_env.exists():
        print_status("setup_env.sh file exists")
        
        # Check if it's executable
        if os.access(setup_env, os.X_OK):
            print_status("setup_env.sh is executable")
        else:
            print_status("setup_env.sh is not executable", False)
    else:
        print_status("setup_env.sh file not found", False)

def test_java_environment():
    """Test Java environment setup."""
    print_header("Testing Java Environment")
    
    # Test JAVA_HOME environment variable
    java_home = os.getenv('JAVA_HOME')
    if java_home:
        print_status(f"JAVA_HOME is set: {java_home}")
        
        # Check if JAVA_HOME directory exists
        if Path(java_home).exists():
            print_status("JAVA_HOME directory exists")
        else:
            print_status("JAVA_HOME directory does not exist", False)
    else:
        print_status("JAVA_HOME is not set", False)
    
    # Test Java command
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stderr.split('\n')[0]
            print_status(f"Java is available: {version_line}")
        else:
            print_status("Java command failed", False)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_status("Java command not found or timed out", False)

def test_jdbc_drivers():
    """Test JDBC driver files."""
    print_header("Testing JDBC Drivers")
    
    jdbc_dir = Path("jdbc-drivers")
    if jdbc_dir.exists():
        print_status("jdbc-drivers directory exists")
        
        # Test Apache Arrow Flight SQL JDBC driver
        arrow_driver = jdbc_dir / "flight-sql-jdbc-driver-17.0.0.jar"
        if arrow_driver.exists():
            size_mb = arrow_driver.stat().st_size / (1024 * 1024)
            print_status(f"Apache Arrow Flight SQL JDBC driver found ({size_mb:.1f}MB)")
        else:
            print_status("Apache Arrow Flight SQL JDBC driver not found", False)
        
        # Test legacy Dremio JDBC driver
        dremio_driver = jdbc_dir / "dremio-jdbc-driver-LATEST.jar"
        if dremio_driver.exists():
            size_mb = dremio_driver.stat().st_size / (1024 * 1024)
            print_status(f"Legacy Dremio JDBC driver found ({size_mb:.1f}MB)")
        else:
            print_status("Legacy Dremio JDBC driver not found", False)
    else:
        print_status("jdbc-drivers directory not found", False)

def test_python_dependencies():
    """Test Python dependencies."""
    print_header("Testing Python Dependencies")
    
    dependencies = [
        ("flask", "Flask"),
        ("pyarrow", "PyArrow"),
        ("jpype", "JPype1"),
        ("jaydebeapi", "JayDeBeApi"),
        ("pyodbc", "PyODBC"),
        ("adbc_driver_flightsql", "ADBC Flight SQL"),
        ("dotenv", "python-dotenv")
    ]
    
    for module, name in dependencies:
        try:
            __import__(module)
            print_status(f"{name} is available")
        except ImportError:
            print_status(f"{name} is not available", False)

def test_run_script():
    """Test that run.sh script exists and is executable."""
    print_header("Testing Run Script")
    
    run_script = Path("run.sh")
    if run_script.exists():
        print_status("run.sh script exists")
        
        if os.access(run_script, os.X_OK):
            print_status("run.sh is executable")
        else:
            print_status("run.sh is not executable", False)
    else:
        print_status("run.sh script not found", False)

def main():
    """Run all tests."""
    print("🧪 Complete Setup Verification Test")
    print("Enhanced Dremio Reporting Server")
    
    # Run all tests
    test_environment_files()
    test_java_environment()
    test_jdbc_drivers()
    test_python_dependencies()
    test_run_script()
    
    print_header("Test Summary")
    print("🎉 Setup verification complete!")
    print("\nIf all tests passed, your environment is ready to use:")
    print("  1. Edit .env with your Dremio credentials")
    print("  2. Run: ./run.sh")
    print("  3. Access: http://localhost:5001")
    
    print("\nIf any tests failed:")
    print("  1. Run: ./setup.sh")
    print("  2. Check the troubleshooting guide in README.md")

if __name__ == "__main__":
    main()
