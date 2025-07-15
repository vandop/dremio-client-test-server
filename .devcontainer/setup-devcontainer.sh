#!/bin/bash

# Devcontainer-specific setup script for Dremio Reporting Server
# This script is optimized for the devcontainer environment

set -e  # Exit on any error

echo "🐳 Devcontainer Setup for Dremio Reporting Server"
echo "================================================="

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
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
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
            print_status "JDBC driver already present ($(($file_size / 1024 / 1024))MB)"
            return 0
        else
            print_warning "JDBC driver file exists but appears corrupted, re-downloading..."
            rm -f "jdbc-drivers/dremio-jdbc-driver-LATEST.jar"
        fi
    fi
    
    print_info "Downloading Dremio JDBC driver..."
    
    # Download the JDBC driver
    local download_url="https://download.dremio.com/jdbc-driver/dremio-jdbc-driver-LATEST.jar"
    local temp_file="jdbc-drivers/dremio-jdbc-driver-LATEST.jar.tmp"
    
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
    
    # Set JAVA_HOME for this session
    export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-arm64}
    
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
