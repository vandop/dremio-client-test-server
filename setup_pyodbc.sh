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

# Provide Dremio ODBC driver installation instructions
provide_dremio_odbc_instructions() {
    print_info "Dremio ODBC Driver Installation Instructions"
    echo ""
    echo "To complete PyODBC setup, install the Dremio ODBC driver:"
    echo ""
    echo "📥 Download:"
    echo "   1. Visit: https://www.dremio.com/drivers/"
    echo "   2. Select: ODBC Driver for Linux x64"
    echo "   3. Download: dremio-odbc-{version}-linux-x86_64.tar.gz"
    echo ""
    echo "🔧 Install:"
    echo "   mkdir -p ~/dremio-drivers"
    echo "   cd ~/dremio-drivers"
    echo "   wget {download-url}"
    echo "   tar -xzf dremio-odbc-*.tar.gz"
    echo "   cd dremio-odbc-*"
    echo "   sudo ./install.sh"
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
    
    # Provide Dremio ODBC driver instructions
    provide_dremio_odbc_instructions
}

# Run main function
main "$@"
