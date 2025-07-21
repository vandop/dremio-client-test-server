#!/usr/bin/env python3

"""
Test script to verify ODBC driver download functionality
"""

import subprocess
import sys
import os
import tempfile
import requests


def test_download_url():
    """Test if the ODBC driver download URL is accessible"""
    url = "https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm"

    print(f"🔍 Testing download URL: {url}")

    try:
        # Test with HEAD request first, allow redirects
        response = requests.head(url, timeout=10, allow_redirects=True)
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(
            f"   Content-Length: {response.headers.get('Content-Length', 'Unknown')} bytes"
        )

        if response.status_code == 200:
            print("✅ URL is accessible and returns valid response")
            return True
        elif response.status_code in [301, 302, 303, 307, 308]:
            print(
                f"✅ URL redirects (status {response.status_code}) - this is normal for download URLs"
            )
            # Try to get the final URL after redirects
            if response.url != url:
                print(f"   Final URL: {response.url}")
            return True
        else:
            print(f"❌ URL returned status code: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to access URL: {e}")
        return False


def test_download_with_wget():
    """Test downloading with wget"""
    url = "https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm"

    print(f"📥 Testing download with wget...")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "test-driver.rpm")

        try:
            # Test wget download (just first 1MB to save time)
            result = subprocess.run(
                [
                    "wget",
                    "--quiet",
                    "--timeout=30",
                    "--tries=2",
                    f"--output-document={output_file}",
                    "--header=Range: bytes=0-1048576",  # Download first 1MB only
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0 and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ wget download successful (downloaded {file_size} bytes)")
                return True
            else:
                print(f"❌ wget download failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ wget download timed out")
            return False
        except FileNotFoundError:
            print("❌ wget command not found")
            return False
        except Exception as e:
            print(f"❌ wget download error: {e}")
            return False


def test_download_with_curl():
    """Test downloading with curl"""
    url = "https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm"

    print(f"📥 Testing download with curl...")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "test-driver.rpm")

        try:
            # Test curl download (just first 1MB to save time)
            result = subprocess.run(
                [
                    "curl",
                    "--silent",
                    "--location",
                    "--max-time",
                    "30",
                    "--retry",
                    "2",
                    "--output",
                    output_file,
                    "--range",
                    "0-1048576",  # Download first 1MB only
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0 and os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ curl download successful (downloaded {file_size} bytes)")
                return True
            else:
                print(f"❌ curl download failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ curl download timed out")
            return False
        except FileNotFoundError:
            print("❌ curl command not found")
            return False
        except Exception as e:
            print(f"❌ curl download error: {e}")
            return False


def check_system_requirements():
    """Check if system has required tools"""
    print("🔧 Checking system requirements...")

    tools = ["wget", "curl", "alien", "dpkg"]
    available = {}

    for tool in tools:
        try:
            result = subprocess.run(["which", tool], capture_output=True, text=True)
            if result.returncode == 0:
                available[tool] = True
                print(f"   ✅ {tool}: {result.stdout.strip()}")
            else:
                available[tool] = False
                print(f"   ❌ {tool}: Not found")
        except Exception:
            available[tool] = False
            print(f"   ❌ {tool}: Error checking")

    return available


def main():
    """Main test function"""
    print("🧪 ODBC Driver Download Test")
    print("=" * 50)

    # Check system requirements
    tools = check_system_requirements()
    print()

    # Test URL accessibility
    url_ok = test_download_url()
    print()

    # Test downloads if URL is accessible
    if url_ok:
        if tools.get("wget", False):
            wget_ok = test_download_with_wget()
            print()
        else:
            wget_ok = False
            print("⚠️ wget not available, skipping wget test")
            print()

        if tools.get("curl", False):
            curl_ok = test_download_with_curl()
            print()
        else:
            curl_ok = False
            print("⚠️ curl not available, skipping curl test")
            print()
    else:
        wget_ok = curl_ok = False

    # Summary
    print("📊 Test Summary:")
    print(f"   URL Accessible: {'✅' if url_ok else '❌'}")
    print(f"   wget Download: {'✅' if wget_ok else '❌'}")
    print(f"   curl Download: {'✅' if curl_ok else '❌'}")
    print(f"   alien Available: {'✅' if tools.get('alien', False) else '❌'}")
    print(f"   dpkg Available: {'✅' if tools.get('dpkg', False) else '❌'}")

    if (
        url_ok
        and (wget_ok or curl_ok)
        and tools.get("alien", False)
        and tools.get("dpkg", False)
    ):
        print("\n🎉 All tests passed! ODBC driver download should work.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Manual installation may be required.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
