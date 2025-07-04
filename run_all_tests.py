#!/usr/bin/env python3
"""
Comprehensive test runner for Dremio Reporting Server.
Executes all test suites and provides detailed reporting.
"""
import subprocess
import sys
import os
import time
from datetime import datetime


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print("-" * 60)


def run_test_file(test_file, description=""):
    """Run a single test file and return results."""
    if not os.path.exists(test_file):
        return {
            'file': test_file,
            'status': 'SKIPPED',
            'reason': 'File not found',
            'passed': 0,
            'failed': 0,
            'total': 0,
            'duration': 0
        }
    
    print(f"\n🧪 Running {test_file}...")
    if description:
        print(f"   {description}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=120)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse output for test counts
        output_lines = result.stdout.split('\n')
        passed = 0
        failed = 0
        total = 0
        
        for line in output_lines:
            if 'passed' in line or 'failed' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part and i > 0:
                        try:
                            passed = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif 'failed' in part and i > 0:
                        try:
                            failed = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        
        total = passed + failed
        
        status = 'PASSED' if result.returncode == 0 else 'FAILED'
        
        if status == 'PASSED':
            print(f"   ✅ {passed} tests passed in {duration:.2f}s")
        else:
            print(f"   ❌ {failed} tests failed, {passed} passed in {duration:.2f}s")
        
        return {
            'file': test_file,
            'status': status,
            'passed': passed,
            'failed': failed,
            'total': total,
            'duration': duration,
            'output': result.stdout,
            'errors': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        duration = end_time - start_time
        print(f"   ⏰ Tests timed out after {duration:.2f}s")
        
        return {
            'file': test_file,
            'status': 'TIMEOUT',
            'passed': 0,
            'failed': 0,
            'total': 0,
            'duration': duration
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"   💥 Error running tests: {e}")
        
        return {
            'file': test_file,
            'status': 'ERROR',
            'passed': 0,
            'failed': 0,
            'total': 0,
            'duration': duration,
            'error': str(e)
        }


def main():
    """Run all tests and generate comprehensive report."""
    print_header("🚀 DREMIO REPORTING SERVER - COMPREHENSIVE TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test suites
    test_suites = [
        {
            'file': 'test_app.py',
            'name': 'Flask Application Tests',
            'description': 'Web routes, API endpoints, request handling'
        },
        {
            'file': 'test_config.py',
            'name': 'Configuration Tests',
            'description': 'Environment variables, validation, security'
        },
        {
            'file': 'test_reports.py',
            'name': 'Reports Tests',
            'description': 'Job reports, analytics, data processing'
        },
        {
            'file': 'test_dremio_clients.py',
            'name': 'Dremio Client Tests',
            'description': 'Connection handling, query execution, error handling'
        },
        {
            'file': 'test_performance.py',
            'name': 'Performance Tests',
            'description': 'Response times, concurrent requests, memory usage'
        }
    ]
    
    # Run all test suites
    results = []
    total_start_time = time.time()
    
    for suite in test_suites:
        print_section(f"{suite['name']} ({suite['file']})")
        print(f"Testing: {suite['description']}")
        
        result = run_test_file(suite['file'], suite['description'])
        results.append(result)
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Generate summary report
    print_header("📊 TEST EXECUTION SUMMARY")
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    successful_suites = 0
    
    print(f"{'Test Suite':<30} {'Status':<10} {'Passed':<8} {'Failed':<8} {'Duration':<10}")
    print("-" * 80)
    
    for result in results:
        status_icon = {
            'PASSED': '✅',
            'FAILED': '❌',
            'TIMEOUT': '⏰',
            'ERROR': '💥',
            'SKIPPED': '⚠️'
        }.get(result['status'], '❓')
        
        print(f"{result['file']:<30} {status_icon} {result['status']:<8} "
              f"{result['passed']:<8} {result['failed']:<8} {result['duration']:.2f}s")
        
        total_tests += result['total']
        total_passed += result['passed']
        total_failed += result['failed']
        
        if result['status'] == 'PASSED':
            successful_suites += 1
    
    print("-" * 80)
    print(f"{'TOTALS':<30} {'':<10} {total_passed:<8} {total_failed:<8} {total_duration:.2f}s")
    
    # Calculate success rates
    suite_success_rate = (successful_suites / len(results)) * 100 if results else 0
    test_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    print_header("🎯 DETAILED ANALYSIS")
    
    print(f"📈 Test Suite Statistics:")
    print(f"   • Total Test Suites: {len(results)}")
    print(f"   • Successful Suites: {successful_suites}")
    print(f"   • Suite Success Rate: {suite_success_rate:.1f}%")
    print(f"   • Total Execution Time: {total_duration:.2f} seconds")
    
    print(f"\n📊 Individual Test Statistics:")
    print(f"   • Total Tests: {total_tests}")
    print(f"   • Passed Tests: {total_passed}")
    print(f"   • Failed Tests: {total_failed}")
    print(f"   • Test Success Rate: {test_success_rate:.1f}%")
    
    # Quality assessment
    print(f"\n🏆 Quality Assessment:")
    if test_success_rate >= 95:
        print("   🌟 EXCELLENT - Outstanding test coverage and reliability!")
    elif test_success_rate >= 85:
        print("   🎉 VERY GOOD - Strong test coverage with minor issues")
    elif test_success_rate >= 75:
        print("   👍 GOOD - Decent test coverage, some improvements needed")
    elif test_success_rate >= 60:
        print("   ⚠️  FAIR - Moderate test coverage, significant improvements needed")
    else:
        print("   ❌ POOR - Low test coverage, major improvements required")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if total_failed > 0:
        print(f"   • Fix {total_failed} failing tests to improve reliability")
    if test_success_rate < 90:
        print("   • Add more test cases to improve coverage")
    if total_duration > 60:
        print("   • Consider optimizing slow tests for faster feedback")
    
    print("   • Run tests regularly during development")
    print("   • Set up automated testing in CI/CD pipeline")
    print("   • Monitor test performance and coverage over time")
    
    # Test infrastructure status
    print_header("🛠️  TEST INFRASTRUCTURE STATUS")
    
    infrastructure_files = [
        ('conftest.py', 'Shared test fixtures and configuration'),
        ('test_app.py', 'Flask application tests'),
        ('test_config.py', 'Configuration management tests'),
        ('test_reports.py', 'Report functionality tests'),
        ('test_dremio_clients.py', 'Dremio client tests'),
        ('test_performance.py', 'Performance and load tests')
    ]
    
    print("📁 Test Files:")
    for filename, description in infrastructure_files:
        status = "✅" if os.path.exists(filename) else "❌"
        print(f"   {status} {filename:<25} - {description}")
    
    # Final status
    print_header("🏁 FINAL STATUS")
    
    if total_failed == 0 and successful_suites == len(results):
        print("🎉 ALL TESTS PASSED! The Dremio Reporting Server test suite is healthy.")
        exit_code = 0
    elif test_success_rate >= 80:
        print("⚠️  MOSTLY SUCCESSFUL with some issues to address.")
        exit_code = 1
    else:
        print("❌ SIGNIFICANT ISSUES detected. Review and fix failing tests.")
        exit_code = 1
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total execution time: {total_duration:.2f} seconds")
    
    return exit_code


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
