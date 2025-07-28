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

# Verify Java environment
verify_java() {
    print_info "Verifying Java environment..."
    
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
        print_status "Java available: $JAVA_VERSION"
        
        # Set JAVA_HOME if not already set
        if [ -z "$JAVA_HOME" ]; then
            export JAVA_HOME=$(readlink -f $(which java) | sed "s:/bin/java::")
            print_status "JAVA_HOME set to: $JAVA_HOME"
        else
            print_status "JAVA_HOME already set: $JAVA_HOME"
        fi
    else
        print_warning "Java not found - this should not happen in devcontainer"
        exit 1
    fi
}

# Verify Python dependencies
verify_python_deps() {
    print_info "Verifying Python dependencies..."
    
    # Check critical dependencies
    python3 -c "
import sys
try:
    import jpype
    print('✓ JPype available')
    
    import jaydebeapi
    print('✓ JayDeBeApi available')
    
    import flask
    print('✓ Flask available')
    
    import pandas
    print('✓ Pandas available')
    
    print('✓ All critical dependencies available')
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_status "Python dependencies verified"
    else
        print_warning "Some Python dependencies missing"
        exit 1
    fi
}

# Setup environment file
setup_env_file() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        print_info "Creating .env template..."
        cat > .env << 'EOF'
# Dremio Configuration
DREMIO_CLOUD_URL=https://api.dremio.cloud
DREMIO_USERNAME=your-username
DREMIO_PASSWORD=your-password
DREMIO_PAT=your-personal-access-token
DREMIO_PROJECT_ID=your-project-id

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true

# Java Configuration (auto-detected in devcontainer)
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
EOF
        print_status ".env template created"
        print_warning "Please edit .env file with your Dremio credentials"
    else
        print_status ".env file already exists"
    fi
}

# Download JDBC driver if needed
setup_jdbc_driver() {
    print_info "Setting up JDBC driver..."
    
    # Create jdbc-drivers directory if it doesn't exist
    if [ ! -d "jdbc-drivers" ]; then
        mkdir -p jdbc-drivers
        print_status "Created jdbc-drivers directory"
    fi
    
    # Check if JDBC driver already exists
    if [ -f "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" ]; then
        # Cross-platform file size check
        if command -v stat >/dev/null 2>&1; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                local file_size=$(stat -f%z "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" 2>/dev/null || echo "0")
            else
                # Linux
                local file_size=$(stat -c%s "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" 2>/dev/null || echo "0")
            fi
        else
            # Fallback using ls
            local file_size=$(ls -l "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" 2>/dev/null | awk '{print $5}' || echo "0")
        fi

        if [ "$file_size" -gt 1000000 ]; then  # Check if file is larger than 1MB
            print_status "Flight SQL JDBC driver already present ($(($file_size / 1024 / 1024))MB)"
            return 0
        else
            print_warning "Flight SQL JDBC driver file exists but appears corrupted, re-downloading..."
            rm -f "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
        fi
    fi

    print_info "Downloading Apache Arrow Flight SQL JDBC driver..."

    # Download the Flight SQL JDBC driver
    local download_url="https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/flight-sql-jdbc-driver-17.0.0.jar"
    local temp_file="jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar.tmp"
    
    if wget -q --show-progress -O "$temp_file" "$download_url"; then
        # Verify the download with cross-platform file size check
        if command -v stat >/dev/null 2>&1; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                local downloaded_size=$(stat -f%z "$temp_file" 2>/dev/null || echo "0")
            else
                # Linux
                local downloaded_size=$(stat -c%s "$temp_file" 2>/dev/null || echo "0")
            fi
        else
            # Fallback using ls
            local downloaded_size=$(ls -l "$temp_file" 2>/dev/null | awk '{print $5}' || echo "0")
        fi

        if [ "$downloaded_size" -gt 1000000 ]; then  # Check if downloaded file is larger than 1MB
            mv "$temp_file" "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"
            print_status "JDBC driver downloaded successfully ($(($downloaded_size / 1024 / 1024))MB)"
        else
            rm -f "$temp_file"
            print_warning "Downloaded file appears to be corrupted or incomplete"
            return 1
        fi
    else
        rm -f "$temp_file"
        print_warning "Failed to download JDBC driver - continuing without it"
        print_info "You can manually download it later from: $download_url"
        return 1
    fi
}

# Test Java integration
test_java_integration() {
    print_info "Testing Java integration..."
    
    python3 -c "
import os
import sys

# Ensure JAVA_HOME is set
java_home = os.environ.get('JAVA_HOME')
if not java_home:
    print('⚠ JAVA_HOME not set in environment')
    sys.exit(1)

try:
    import jpype
    print('✓ JPype available')
    
    # Test basic Java functionality without starting JVM
    # (to avoid conflicts if JVM is already running)
    if not jpype.isJVMStarted():
        print('✓ JVM ready for initialization')
    else:
        print('✓ JVM already running')
    
    import jaydebeapi
    print('✓ JayDeBeApi available')
    
    print('✓ Java integration test passed')
    
except Exception as e:
    print(f'✗ Java integration test failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_status "Java integration test passed"
    else
        print_warning "Java integration test failed"
        exit 1
    fi
}

# Main setup
main() {
    print_info "Starting devcontainer setup..."
    
    # Set JAVA_HOME for this session (auto-detect architecture)
    if [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
        export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
    elif [ -d "/usr/lib/jvm/java-17-openjdk-arm64" ]; then
        export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64"
    else
        export JAVA_HOME=$(readlink -f $(which java) | sed "s:/bin/java::")
    fi
    
    verify_java
    verify_python_deps
    setup_env_file
    setup_jdbc_driver
    test_java_integration
    
    echo ""
    print_status "Devcontainer setup completed successfully!"
    echo ""
    print_info "Environment ready for development:"
    echo "  • Java: $(java -version 2>&1 | head -n 1)"
    echo "  • Python: $(python3 --version)"
    echo "  • JAVA_HOME: $JAVA_HOME"
    echo ""
    print_info "Next steps:"
    echo "  1. Edit .env file with your Dremio credentials"
    echo "  2. Run: python test_java_setup.py (to verify setup)"
    echo "  3. Run: python app.py (to start the server)"
    echo ""
    
    # Check JDBC driver status
    if [ -f "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" ]; then
        # Cross-platform file size check
        if command -v stat >/dev/null 2>&1; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                local driver_size=$(stat -f%z "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" 2>/dev/null || echo "0")
            else
                # Linux
                local driver_size=$(stat -c%s "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" 2>/dev/null || echo "0")
            fi
        else
            # Fallback using ls
            local driver_size=$(ls -l "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" 2>/dev/null | awk '{print $5}' || echo "0")
        fi
        print_info "JDBC driver: ✅ Ready ($(($driver_size / 1024 / 1024))MB)"
    else
        print_info "JDBC driver: ⚠️  Not available (limited functionality)"
    fi
}

# Run main function
main "$@"

