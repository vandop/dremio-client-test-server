#!/usr/bin/env python3
"""
Quick test status checker for Dremio Reporting Server.
Provides a fast overview of test health.
"""
import subprocess
import sys
import os


def quick_test_check():
    """Run a quick test check and provide status."""
    print("🔍 Dremio Reporting Server - Quick Test Status Check")
    print("=" * 60)
    
    # Check if test files exist
    test_files = [
        'test_app.py',
        'test_config.py', 
        'test_reports.py',
        'test_dremio_clients.py',
        'test_performance.py',
        'conftest.py'
    ]
    
    print("\n📁 Test Infrastructure:")
    missing_files = []
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"   ✅ {test_file}")
        else:
            print(f"   ❌ {test_file} (missing)")
            missing_files.append(test_file)
    
    if missing_files:
        print(f"\n⚠️  Missing test files: {missing_files}")
        return False
    
    # Run a quick test to check basic functionality
    print("\n🧪 Running Quick Test Check...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 'test_app.py::test_health_check', '-v'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Basic functionality test passed")
            
            # Try to get a count of all tests
            count_result = subprocess.run([
                sys.executable, '-m', 'pytest', '--collect-only', '-q'
            ], capture_output=True, text=True, timeout=30)
            
            if count_result.returncode == 0:
                lines = count_result.stdout.split('\n')
                for line in lines:
                    if 'test session starts' in line:
                        continue
                    if 'tests collected' in line or 'test collected' in line:
                        print(f"   📊 {line.strip()}")
                        break
            
            print("\n🎉 Test infrastructure is healthy!")
            print("\n💡 To run full test suite:")
            print("   python run_all_tests.py")
            print("\n💡 To run specific tests:")
            print("   python -m pytest test_app.py -v")
            print("   python -m pytest test_config.py -v")
            print("   python -m pytest test_reports.py -v")
            
            return True
        else:
            print("   ❌ Basic functionality test failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⏰ Test check timed out")
        return False
    except Exception as e:
        print(f"   💥 Error running test check: {e}")
        return False


def show_test_commands():
    """Show useful test commands."""
    print("\n🛠️  Useful Test Commands:")
    print("=" * 60)
    
    commands = [
        ("Run all tests", "python run_all_tests.py"),
        ("Run Flask app tests", "python -m pytest test_app.py -v"),
        ("Run config tests", "python -m pytest test_config.py -v"),
        ("Run reports tests", "python -m pytest test_reports.py -v"),
        ("Run client tests", "python -m pytest test_dremio_clients.py -v"),
        ("Run performance tests", "python -m pytest test_performance.py -v"),
        ("Run with coverage", "python -m pytest --cov=. --cov-report=html"),
        ("Run specific test", "python -m pytest test_app.py::test_health_check -v"),
        ("List all tests", "python -m pytest --collect-only"),
        ("Run tests in parallel", "python -m pytest -n auto")
    ]
    
    for description, command in commands:
        print(f"   {description:<25}: {command}")


def main():
    """Main function."""
    success = quick_test_check()
    show_test_commands()
    
    if success:
        print("\n✅ Test infrastructure is ready!")
        return 0
    else:
        print("\n❌ Test infrastructure needs attention!")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
