#!/bin/bash

# Enhanced Dremio Reporting Server Setup Script with PyODBC Support
# This script sets up the complete environment including PyODBC and ODBC drivers

set -e  # Exit on any error

echo "🚀 Enhanced Dremio Reporting Server Setup with PyODBC"
echo "======================================================"

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

# Update system packages
update_system() {
    print_info "Updating system packages..."
    $SUDO apt update -qq
    print_status "System packages updated"
}

# Install ODBC components for PyODBC
install_odbc_components() {
    print_info "Installing ODBC components for PyODBC..."
    
    # Install unixODBC driver manager and tools
    $SUDO apt install -y unixodbc unixodbc-dev odbcinst
    
    # Verify installation
    if command -v odbcinst &> /dev/null; then
        print_status "unixODBC driver manager installed successfully"
        print_info "ODBC Configuration:"
        odbcinst -j | sed 's/^/   /'
    else
        print_error "unixODBC installation failed"
        return 1
    fi
    
    # Check for ODBC configuration files
    if [ -f "/etc/odbcinst.ini" ]; then
        print_status "ODBC configuration files present"
    else
        print_warning "ODBC configuration files not found, creating basic structure..."
        $SUDO touch /etc/odbcinst.ini
        $SUDO touch /etc/odbc.ini
    fi
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command -v pip &> /dev/null; then
        print_info "Installing pip..."
        $SUDO apt install -y python3-pip
    fi
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Python dependencies installed from requirements.txt"
    else
        print_warning "requirements.txt not found, installing core dependencies..."
        pip install flask pyarrow pandas adbc-driver-flightsql jaydebeapi jpype1 requests python-dotenv pyodbc
        print_status "Core Python dependencies installed"
    fi
}

# Test PyODBC installation
test_pyodbc_installation() {
    print_info "Testing PyODBC installation..."
    
    python3 -c "
import sys
try:
    import pyodbc
    print('✓ PyODBC imported successfully')
    print(f'   Version: {pyodbc.version}')
    
    drivers = pyodbc.drivers()
    print(f'   Available ODBC drivers: {len(drivers)}')
    for driver in drivers:
        print(f'     - {driver}')
    
    if not drivers:
        print('⚠ No ODBC drivers installed yet')
        print('   Install Dremio ODBC driver to enable full functionality')
    
    print('✓ PyODBC installation test passed')
    
except ImportError as e:
    print(f'✗ PyODBC import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'✗ PyODBC test failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_status "PyODBC installation test passed"
    else
        print_error "PyODBC installation test failed"
        exit 1
    fi
}

# Set up environment variables
setup_environment() {
    print_info "Setting up environment variables..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_info "Creating .env template..."
        cat > .env << 'EOF'
# Dremio Configuration
DREMIO_URL=https://api.dremio.cloud
DREMIO_TYPE=cloud
DREMIO_USERNAME=your-username
DREMIO_PASSWORD=your-password
DREMIO_PAT=your-personal-access-token
DREMIO_PROJECT_ID=your-project-id

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=true

# PyODBC Configuration
PYODBC_DRIVER_NAME=Dremio ODBC Driver
PYODBC_TIMEOUT=30

# ODBC Environment
ODBCSYSINI=/etc
ODBCINI=/etc/odbc.ini
EOF
        print_status ".env template created"
        print_warning "Please edit .env file with your Dremio credentials"
    else
        print_status ".env file already exists"
    fi
}

# Download and install Dremio ODBC Driver Flight SQL automatically
install_dremio_odbc_driver() {
    print_info "Downloading and installing Dremio ODBC Driver Flight SQL..."

    # Check if driver is already installed
    if python3 -c "import pyodbc; drivers = pyodbc.drivers(); exit(0 if any('dremio' in d.lower() or 'arrow' in d.lower() for d in drivers) else 1)" 2>/dev/null; then
        print_status "Dremio ODBC driver already installed"
        return 0
    fi

    # Create temporary directory for download
    local temp_dir=$(mktemp -d)
    cd "$temp_dir"

    print_info "Downloading Arrow Flight SQL ODBC driver from official source..."

    # Download the latest Arrow Flight SQL ODBC driver
    local download_url="https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm"
    local rpm_file="arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm"

    if command -v wget &> /dev/null; then
        if wget -q --show-progress -O "$rpm_file" "$download_url"; then
            print_status "ODBC driver downloaded successfully"
        else
            print_error "Failed to download ODBC driver with wget"
            cd - > /dev/null
            rm -rf "$temp_dir"
            return 1
        fi
    elif command -v curl &> /dev/null; then
        if curl -L --progress-bar -o "$rpm_file" "$download_url"; then
            print_status "ODBC driver downloaded successfully"
        else
            print_error "Failed to download ODBC driver with curl"
            cd - > /dev/null
            rm -rf "$temp_dir"
            return 1
        fi
    else
        print_error "Neither wget nor curl is available for downloading"
        cd - > /dev/null
        rm -rf "$temp_dir"
        return 1
    fi

    # Verify download
    if [ ! -f "$rpm_file" ] || [ ! -s "$rpm_file" ]; then
        print_error "Downloaded file is missing or empty"
        cd - > /dev/null
        rm -rf "$temp_dir"
        return 1
    fi

    # Install alien if not present (for converting RPM to DEB)
    if ! command -v alien &> /dev/null; then
        print_info "Installing alien package converter..."
        $SUDO apt-get update -qq
        $SUDO apt-get install -y alien
    fi

    # Convert RPM to DEB
    print_info "Converting RPM to DEB package..."
    if alien -d "$rpm_file"; then
        local deb_file=$(ls *.deb | head -1)
        if [ -n "$deb_file" ] && [ -f "$deb_file" ]; then
            print_status "Package converted successfully: $deb_file"
        else
            print_error "Failed to convert RPM to DEB"
            cd - > /dev/null
            rm -rf "$temp_dir"
            return 1
        fi
    else
        print_error "RPM to DEB conversion failed"
        cd - > /dev/null
        rm -rf "$temp_dir"
        return 1
    fi

    # Install the DEB package
    print_info "Installing Dremio ODBC Driver Flight SQL..."
    if $SUDO dpkg -i "$deb_file"; then
        print_status "Package installation completed"
    else
        print_warning "Package installation had issues, attempting to fix dependencies..."
        $SUDO apt-get install -f -y
    fi

    # Find and verify the driver library
    local driver_lib=""
    local search_paths=(
        "/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so"
        "/opt/arrow-flight-sql-odbc-driver/lib/libarrow-flight-sql-odbc.so"
        "/usr/lib/x86_64-linux-gnu/libarrow-odbc.so"
        "/usr/local/lib/libarrow-odbc.so"
    )

    for path in "${search_paths[@]}"; do
        if [ -f "$path" ]; then
            driver_lib="$path"
            break
        fi
    done

    # If not found in standard locations, search for it
    if [ -z "$driver_lib" ]; then
        driver_lib=$(find /opt /usr -name "libarrow*.so*" 2>/dev/null | grep -E "(odbc|flight)" | head -1)
    fi

    if [ -n "$driver_lib" ] && [ -f "$driver_lib" ]; then
        print_status "Driver library found at: $driver_lib"

        # Configure ODBC driver registration
        print_info "Configuring ODBC driver registration..."

        # Check if driver is already registered
        if ! grep -q "Arrow Flight SQL ODBC Driver" /etc/odbcinst.ini 2>/dev/null; then
            $SUDO tee -a /etc/odbcinst.ini > /dev/null << EOF

[Arrow Flight SQL ODBC Driver]
Description=Arrow Flight SQL ODBC Driver
Driver=$driver_lib
Setup=$driver_lib
UsageCount=1
EOF
            print_status "ODBC driver registered successfully"
        else
            print_status "ODBC driver already registered"
        fi

        # Create a sample DSN configuration
        if ! grep -q "Dremio Cloud Flight SQL" /etc/odbc.ini 2>/dev/null; then
            print_info "Creating sample DSN configuration..."
            $SUDO tee -a /etc/odbc.ini > /dev/null << EOF

[Dremio Cloud Flight SQL]
Description=Dremio Cloud via Arrow Flight SQL ODBC
Driver=Arrow Flight SQL ODBC Driver
HOST=data.dremio.cloud
PORT=443
useEncryption=true
TOKEN=your_personal_access_token_here
EOF
            print_status "Sample DSN configuration created"
            print_warning "Remember to update TOKEN in /etc/odbc.ini with your actual Personal Access Token"
        fi

    else
        print_error "Driver library not found after installation"
        cd - > /dev/null
        rm -rf "$temp_dir"
        return 1
    fi

    # Cleanup
    cd - > /dev/null
    rm -rf "$temp_dir"

    print_status "Dremio ODBC Driver Flight SQL installation completed successfully"
    return 0
}

# Provide manual installation instructions as fallback
provide_dremio_odbc_instructions() {
    print_info "Manual Dremio ODBC Driver Installation Instructions"
    echo ""
    echo "If automatic installation failed, you can install manually:"
    echo ""
    echo "📥 Download:"
    echo "   wget https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm"
    echo ""
    echo "🔧 Install:"
    echo "   sudo apt-get install -y alien"
    echo "   alien -d arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm"
    echo "   sudo dpkg -i arrow-flight-sql-odbc-driver*.deb"
    echo "   sudo apt-get install -f -y"
    echo ""
    echo "✅ Verify:"
    echo "   python test_pyodbc_installation.py"
    echo ""
    echo "📖 For detailed instructions, see: PYODBC_INSTALLATION_GUIDE.md"
}

# Create PyODBC testing script
create_pyodbc_test() {
    print_info "Creating PyODBC test script..."
    
    if [ ! -f "test_pyodbc_installation.py" ]; then
        print_warning "test_pyodbc_installation.py not found"
        print_info "This script should be created separately for comprehensive testing"
    else
        print_status "PyODBC test script already available: test_pyodbc_installation.py"
    fi
}

# Main setup function
main() {
    echo ""
    print_info "Starting Enhanced Dremio Reporting Server setup with PyODBC..."
    
    # Check system requirements
    check_sudo
    
    # Install system dependencies
    update_system
    install_odbc_components
    
    # Install Python dependencies
    install_python_deps
    
    # Test PyODBC
    test_pyodbc_installation

    # Set up environment
    setup_environment

    # Create test script reference
    create_pyodbc_test

    # Attempt to install Dremio ODBC driver automatically
    echo ""
    print_info "Attempting automatic Dremio ODBC Driver Flight SQL installation..."
    if install_dremio_odbc_driver; then
        print_status "✅ Automatic ODBC driver installation successful!"

        # Test again after driver installation
        print_info "Re-testing PyODBC with installed driver..."
        test_pyodbc_installation

        echo ""
        print_status "Setup completed successfully!"
        echo ""
        print_info "Current Status:"
        echo "  ✅ unixODBC driver manager installed"
        echo "  ✅ PyODBC Python package installed and working"
        echo "  ✅ Dremio ODBC Driver Flight SQL installed and configured"
        echo ""
        print_info "Next steps:"
        echo "  1. Edit .env file with your Dremio credentials"
        echo "  2. Run: python test_pyodbc_installation.py"
        echo "  3. Run: python app.py (to start the server)"
        echo ""
    else
        print_warning "⚠️ Automatic installation failed, providing manual instructions..."

        echo ""
        print_status "Setup completed successfully!"
        echo ""
        print_info "Current Status:"
        echo "  ✅ unixODBC driver manager installed"
        echo "  ✅ PyODBC Python package installed and working"
        echo "  ⚠️ Dremio ODBC driver needs manual installation"
        echo ""
        print_info "Next steps:"
        echo "  1. Install Dremio ODBC driver (see instructions below)"
        echo "  2. Edit .env file with your Dremio credentials"
        echo "  3. Run: python test_pyodbc_installation.py"
        echo "  4. Run: python app.py (to start the server)"
        echo ""

        # Provide manual installation instructions
        provide_dremio_odbc_instructions
    fi
}

# Run main function
main "$@"
