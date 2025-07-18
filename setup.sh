#!/bin/bash

# Enhanced Dremio Reporting Server Setup Script
# Downloads Arrow Flight SQL JDBC driver

set -e  # Exit on any error

echo "🚀 Enhanced Dremio Reporting Server Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running as root for system packages
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This is fine for Docker containers."
        SUDO=""
    else
        print_info "Checking sudo access for system package installation..."
        if sudo -n true 2>/dev/null; then
            print_status "Sudo access confirmed"
            SUDO="sudo"
        else
            print_error "This script requires sudo access to install system packages"
            echo "Please run: sudo -v"
            exit 1
        fi
    fi
}

# Update JDBC README with current driver information
update_jdbc_readme() {
    print_info "Updating JDBC README documentation..."
    # The README has already been updated to reflect Arrow Flight SQL JDBC driver
    print_status "JDBC README is up to date"
}

# Download Arrow Flight SQL JDBC driver if not present
download_jdbc_driver() {
    print_info "Checking Arrow Flight SQL JDBC driver availability..."

    # Create jdbc-drivers directory if it doesn't exist
    if [ ! -d "jdbc-drivers" ]; then
        mkdir -p jdbc-drivers
        print_status "Created jdbc-drivers directory"
    fi

    # Check if Arrow Flight SQL JDBC driver already exists
    if [ -f "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar" ]; then
        local file_size=$(stat -c%s "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 1000000 ]; then  # Check if file is larger than 1MB (valid JAR)
            print_status "Arrow Flight SQL JDBC driver already present ($(($file_size / 1024 / 1024))MB)"
            return 0
        else
            print_warning "JDBC driver file exists but appears corrupted, re-downloading..."
            rm -f "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
        fi
    fi

    # Remove old Dremio JDBC driver if present
    if [ -f "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" ]; then
        print_info "Removing old Dremio JDBC driver..."
        rm -f "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"
    fi

    print_info "Downloading Arrow Flight SQL JDBC driver..."

    # Check if wget is available
    if ! command -v wget &> /dev/null; then
        print_error "wget is required to download the JDBC driver"
        print_info "Installing wget..."
        $SUDO apt-get update -qq
        $SUDO apt-get install -y wget
    fi

    # Download the Arrow Flight SQL JDBC driver from Maven Central
    local download_url="https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/flight-sql-jdbc-driver-17.0.0.jar"
    local temp_file="jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar.tmp"

    print_info "Downloading from: $download_url"
    if wget -q --show-progress -O "$temp_file" "$download_url"; then
        # Verify the download
        local downloaded_size=$(stat -c%s "$temp_file" 2>/dev/null || echo "0")
        if [ "$downloaded_size" -gt 1000000 ]; then  # Check if downloaded file is larger than 1MB
            mv "$temp_file" "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
            print_status "Arrow Flight SQL JDBC driver downloaded successfully ($(($downloaded_size / 1024 / 1024))MB)"

            # Update README
            update_jdbc_readme
        else
            rm -f "$temp_file"
            print_error "Downloaded file appears to be corrupted or incomplete"
            return 1
        fi
    else
        rm -f "$temp_file"
        print_error "Failed to download Arrow Flight SQL JDBC driver"
        print_warning "You can manually download the driver from:"
        print_info "https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/flight-sql-jdbc-driver-17.0.0.jar"
        return 1
    fi
}

# Main setup function
main() {
    echo ""
    print_info "Starting Enhanced Dremio Reporting Server setup..."

    # Check system requirements
    check_sudo

    # Download JDBC driver
    download_jdbc_driver

    echo ""
    print_status "Setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Edit .env file with your Dremio credentials"
    echo "  2. Run: python test_java_setup.py (to test JDBC setup)"
    echo "  3. Run: ./run.sh (to start the server)"
    echo ""
}

# Run main function
main "$@"