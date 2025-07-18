#!/bin/bash

# Enhanced Dremio Reporting Server DevContainer Setup Script
# Configures the development environment with all dependencies

set -e  # Exit on any error

echo "🚀 Enhanced Dremio Reporting Server DevContainer Setup"
echo "====================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Change to workspace directory
cd /workspace

print_info "Setting up Enhanced Dremio Reporting Server development environment..."

# Install Python dependencies
print_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
    print_status "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping Python dependencies"
fi

# Verify Java installation
print_info "Verifying Java installation..."
if java -version 2>&1 | grep -q "openjdk version"; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
    print_status "Java installed: $JAVA_VERSION"
    print_status "JAVA_HOME: $JAVA_HOME"
else
    print_warning "Java not found or not properly configured"
fi

# Verify ODBC installation
print_info "Verifying ODBC installation..."
if command -v odbcinst &> /dev/null; then
    print_status "unixODBC driver manager installed"
    
    # Check for installed drivers
    if odbcinst -q -d | grep -q "Arrow Flight SQL ODBC Driver"; then
        print_status "Dremio Arrow Flight SQL ODBC driver detected"
    else
        print_warning "Dremio ODBC driver not found in system configuration"
    fi
else
    print_warning "unixODBC not found"
fi

# Verify PyODBC functionality
print_info "Testing PyODBC installation..."
if python -c "import pyodbc; print(f'PyODBC version: {pyodbc.version}'); drivers = pyodbc.drivers(); print(f'Available drivers: {len(drivers)}'); [print(f'  - {d}') for d in drivers]" 2>/dev/null; then
    print_status "PyODBC is working correctly"
else
    print_warning "PyODBC test failed"
fi

# Set up environment file if it doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env file template..."
    cat > .env << 'EOF'
# Enhanced Dremio Reporting Server Configuration

# Dremio Cloud Configuration
DREMIO_CLOUD_HOST=data.dremio.cloud
DREMIO_CLOUD_PORT=443
DREMIO_PERSONAL_ACCESS_TOKEN=your_personal_access_token_here

# SSL Configuration
SSL_VERIFY=true
SSL_CERT_PATH=

# Multi-Driver Configuration
DEFAULT_DRIVER=pyarrow_flight
ENABLE_JDBC=true
ENABLE_PYODBC=true
ENABLE_ADBC=true

# JDBC Configuration
JDBC_DRIVER_PATH=jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar

# ODBC Configuration (for PyODBC)
ODBC_DRIVER_NAME=Arrow Flight SQL ODBC Driver
ODBC_DSN_NAME=Dremio Cloud Flight SQL

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=true
LOG_LEVEL=INFO
EOF
    print_status ".env file created with template configuration"
    print_warning "Remember to update DREMIO_PERSONAL_ACCESS_TOKEN with your actual token"
else
    print_status ".env file already exists"
fi

# Create JDBC drivers directory if it doesn't exist
if [ ! -d "jdbc-drivers" ]; then
    print_info "Creating jdbc-drivers directory..."
    mkdir -p jdbc-drivers
    print_status "jdbc-drivers directory created"
fi

# Set proper permissions
print_info "Setting proper permissions..."
chmod +x setup.sh setup_pyodbc.sh docker-build-x86.sh 2>/dev/null || true
print_status "Permissions set"

# Display system information
print_info "System Information:"
echo "  Architecture: $(uname -m)"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo "  Python: $(python --version)"
echo "  Java: $(java -version 2>&1 | head -n 1 | cut -d'"' -f2)"
echo "  unixODBC: $(odbcinst --version 2>/dev/null | head -n 1 || echo 'Not available')"

print_status "DevContainer setup completed successfully!"
echo ""
print_info "Next steps:"
echo "  1. Update .env file with your Dremio Personal Access Token"
echo "  2. Run: python app.py (to start the development server)"
echo "  3. Open: http://localhost:5000 (to access the web interface)"
echo "  4. Test: curl http://localhost:5000/api/drivers (to verify all drivers)"
echo ""
print_info "Available drivers in this environment:"
echo "  ✅ PyArrow Flight SQL (Primary - Native Python)"
echo "  ✅ Apache Arrow Flight SQL JDBC (Secondary - Modern JDBC)"
echo "  ✅ PyODBC with Arrow Flight SQL ODBC (Additional - Industry Standard)"
echo "  ✅ ADBC Flight SQL (Experimental - Limited compatibility)"
echo ""
print_status "Enhanced Dremio Reporting Server DevContainer is ready! 🎉"
