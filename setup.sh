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

# Update system packages
update_system() {
    print_info "Updating system packages..."
    $SUDO apt-get update -qq
    print_status "System packages updated"
}

# Install Java (OpenJDK 17 - compatible with devcontainer)
install_java() {
    print_info "Checking Java installation..."

    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
        print_status "Java already installed: $JAVA_VERSION"

        # Detect JAVA_HOME automatically
        if [ -z "$JAVA_HOME" ]; then
            DETECTED_JAVA_HOME=$(readlink -f $(which java) | sed "s:/bin/java::")
            if [ -d "$DETECTED_JAVA_HOME" ]; then
                export JAVA_HOME="$DETECTED_JAVA_HOME"
                print_status "Auto-detected JAVA_HOME: $JAVA_HOME"
            fi
        fi
    else
        print_info "Installing OpenJDK 17..."
        $SUDO apt install -y openjdk-17-jdk openjdk-17-jre
        print_status "OpenJDK 17 installed successfully"

        # Set JAVA_HOME for new installation
        if [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
            export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
        elif [ -d "/usr/lib/jvm/java-17-openjdk-arm64" ]; then
            export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64"
        else
            # Auto-detect
            DETECTED_JAVA_HOME=$(readlink -f $(which java) | sed "s:/bin/java::")
            export JAVA_HOME="$DETECTED_JAVA_HOME"
        fi
    fi

    print_status "Using JAVA_HOME: $JAVA_HOME"

    # Persist JAVA_HOME to environment
    persist_java_home

    # Verify installation
    java -version
    if command -v javac &> /dev/null; then
        javac -version
    fi
    print_status "Java installation verified"
}

# Persist JAVA_HOME to environment files
persist_java_home() {
    if [ -n "$JAVA_HOME" ]; then
        print_info "Persisting JAVA_HOME to environment..."

        # Add to .bashrc if it exists and doesn't already contain JAVA_HOME
        if [ -f ~/.bashrc ] && ! grep -q "export JAVA_HOME=" ~/.bashrc; then
            echo "export JAVA_HOME=$JAVA_HOME" >> ~/.bashrc
            print_status "JAVA_HOME added to ~/.bashrc"
        fi

        # Add to .env file if it exists
        if [ -f .env ]; then
            if ! grep -q "JAVA_HOME=" .env; then
                echo "" >> .env
                echo "# Java Environment (auto-added by setup.sh)" >> .env
                echo "JAVA_HOME=$JAVA_HOME" >> .env
                print_status "JAVA_HOME added to .env file"
            fi
        fi

        # Create a setup_env.sh file for easy sourcing (always create)
        cat > setup_env.sh << EOF
#!/bin/bash
# Auto-generated environment setup for Dremio Reporting Server
export JAVA_HOME=$JAVA_HOME
export PATH=\$JAVA_HOME/bin:\$PATH
echo "✓ Java environment loaded: \$JAVA_HOME"
EOF
        chmod +x setup_env.sh
        print_status "Created setup_env.sh for easy environment loading"
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
        pip install flask pyarrow pandas adbc-driver-flightsql jaydebeapi jpype1 requests python-dotenv
        print_status "Core Python dependencies installed"
    fi
}

# Set up environment variables
setup_environment() {
    print_info "Setting up environment variables..."

    # Ensure JAVA_HOME is set from previous step
    if [ -z "$JAVA_HOME" ]; then
        # Try to auto-detect if not set
        if command -v java &> /dev/null; then
            DETECTED_JAVA_HOME=$(readlink -f $(which java) | sed "s:/bin/java::")
            export JAVA_HOME="$DETECTED_JAVA_HOME"
            print_status "Auto-detected JAVA_HOME: $JAVA_HOME"
        fi
    fi

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_info "Creating .env template..."
        cat > .env << EOF
# Dremio Configuration
DREMIO_CLOUD_URL=https://api.dremio.cloud
DREMIO_TYPE=cloud
DREMIO_USERNAME=your-username
DREMIO_PASSWORD=your-password
DREMIO_PAT=your-personal-access-token
DREMIO_PROJECT_ID=your-project-id

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true

# Java Configuration (auto-detected)
JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}
EOF
        print_status ".env template created"
        print_warning "Please edit .env file with your Dremio credentials"
    else
        print_status ".env file already exists"
    fi

    # Add to shell profile for persistence (only if not in container)
    if [ ! -f "/.dockerenv" ] && [ -n "$JAVA_HOME" ]; then
        SHELL_PROFILE=""
        if [ -f "$HOME/.bashrc" ]; then
            SHELL_PROFILE="$HOME/.bashrc"
        elif [ -f "$HOME/.zshrc" ]; then
            SHELL_PROFILE="$HOME/.zshrc"
        elif [ -f "$HOME/.profile" ]; then
            SHELL_PROFILE="$HOME/.profile"
        fi

        if [ -n "$SHELL_PROFILE" ]; then
            if ! grep -q "JAVA_HOME.*Dremio" "$SHELL_PROFILE"; then
                echo "" >> "$SHELL_PROFILE"
                echo "# Java Environment (added by Dremio Reporting Server setup)" >> "$SHELL_PROFILE"
                echo "export JAVA_HOME=$JAVA_HOME" >> "$SHELL_PROFILE"
                echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> "$SHELL_PROFILE"
                print_status "JAVA_HOME added to $SHELL_PROFILE"
            else
                print_status "JAVA_HOME already configured in shell profile"
            fi
        fi
    else
        print_info "Running in container - skipping shell profile update"
    fi
}

# Test Java integration with Python
test_java_integration() {
    print_info "Testing Java integration with Python..."

    # Use the JAVA_HOME from environment or auto-detect
    CURRENT_JAVA_HOME="${JAVA_HOME}"
    if [ -z "$CURRENT_JAVA_HOME" ] && command -v java &> /dev/null; then
        CURRENT_JAVA_HOME=$(readlink -f $(which java) | sed "s:/bin/java::")
    fi

    python3 -c "
import sys
import os

# Set JAVA_HOME for this test
java_home = os.environ.get('JAVA_HOME', '$CURRENT_JAVA_HOME')
if java_home:
    os.environ['JAVA_HOME'] = java_home

try:
    import jpype
    print('✓ JPype (Java-Python bridge) available')

    # Test Java environment
    if os.path.exists(java_home):
        print(f'✓ JAVA_HOME found: {java_home}')
    else:
        print(f'✗ JAVA_HOME not found: {java_home}')
        # Try to find Java automatically
        import subprocess
        try:
            java_path = subprocess.check_output(['which', 'java']).decode().strip()
            auto_java_home = java_path.replace('/bin/java', '')
            if os.path.exists(auto_java_home):
                print(f'✓ Auto-detected Java: {auto_java_home}')
                os.environ['JAVA_HOME'] = auto_java_home
            else:
                sys.exit(1)
        except:
            sys.exit(1)

    # Test JayDeBeApi (JDBC driver)
    try:
        import jaydebeapi
        print(f'✓ JayDeBeApi available: v{jaydebeapi.__version__}')
    except ImportError:
        print('⚠ JayDeBeApi not available (install with: pip install jaydebeapi)')

    print('✓ Java integration test passed')

except ImportError as e:
    print(f'✗ Java integration test failed: {e}')
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        print_status "Java integration test passed"
    else
        print_error "Java integration test failed"
        exit 1
    fi
}

# Download JDBC drivers if not present
download_jdbc_driver() {
    print_info "Checking JDBC driver availability..."

    # Create jdbc-drivers directory if it doesn't exist
    if [ ! -d "jdbc-drivers" ]; then
        mkdir -p jdbc-drivers
        print_status "Created jdbc-drivers directory"
    fi

    # Download Apache Arrow Flight SQL JDBC driver (preferred)
    download_arrow_flight_sql_jdbc

    # Download legacy Dremio JDBC driver as backup
    download_legacy_dremio_jdbc
}

# Download Apache Arrow Flight SQL JDBC driver
download_arrow_flight_sql_jdbc() {
    local arrow_jdbc_file="jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"

    # Check if Apache Arrow Flight SQL JDBC driver already exists
    if [ -f "$arrow_jdbc_file" ]; then
        local file_size=$(stat -c%s "$arrow_jdbc_file" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 100000 ]; then  # Check if file is larger than 100KB (valid JAR)
            print_status "Apache Arrow Flight SQL JDBC driver already present ($(($file_size / 1024 / 1024))MB)"
            return 0
        else
            print_warning "Apache Arrow Flight SQL JDBC driver file exists but appears corrupted, re-downloading..."
            rm -f "$arrow_jdbc_file"
        fi
    fi

    print_info "Downloading Apache Arrow Flight SQL JDBC driver..."

    # Check if wget is available
    if ! command -v wget &> /dev/null; then
        print_error "wget is required to download the JDBC driver"
        print_info "Installing wget..."
        $SUDO apt-get update -qq
        $SUDO apt-get install -y wget
    fi

    # Download the Apache Arrow Flight SQL JDBC driver
    local download_url="https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/flight-sql-jdbc-driver-17.0.0.jar"
    local temp_file="jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar.tmp"

    print_info "Downloading from: $download_url"
    if wget -q --show-progress -O "$temp_file" "$download_url"; then
        # Verify the download
        local downloaded_size=$(stat -c%s "$temp_file" 2>/dev/null || echo "0")
        if [ "$downloaded_size" -gt 100000 ]; then  # Check if downloaded file is larger than 100KB
            mv "$temp_file" "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
            print_status "Apache Arrow Flight SQL JDBC driver downloaded successfully ($(($downloaded_size / 1024 / 1024))MB)"

            # Create updated README
            create_jdbc_readme
        else
            rm -f "$temp_file"
            print_error "Downloaded Apache Arrow Flight SQL JDBC driver appears to be corrupted or incomplete"
            return 1
        fi
    else
        rm -f "$temp_file"
        print_error "Failed to download Apache Arrow Flight SQL JDBC driver"
        print_warning "You can manually download it from: $download_url"
        return 1
    fi
}

# Download legacy Dremio JDBC driver as backup
download_legacy_dremio_jdbc() {
    local dremio_jdbc_file="jdbc-drivers/dremio-jdbc-driver-LATEST.jar"

    # Check if legacy Dremio JDBC driver already exists
    if [ -f "$dremio_jdbc_file" ]; then
        local file_size=$(stat -c%s "$dremio_jdbc_file" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 1000000 ]; then  # Check if file is larger than 1MB (valid JAR)
            print_status "Legacy Dremio JDBC driver already present ($(($file_size / 1024 / 1024))MB)"
            return 0
        else
            print_warning "Legacy Dremio JDBC driver file exists but appears corrupted, re-downloading..."
            rm -f "$dremio_jdbc_file"
        fi
    fi

    print_info "Downloading legacy Dremio JDBC driver as backup..."

    # Download the legacy Dremio JDBC driver
    local download_url="https://download.dremio.com/jdbc-driver/dremio-jdbc-driver-LATEST.jar"
    local temp_file="jdbc-drivers/dremio-jdbc-driver-LATEST.jar.tmp"

    print_info "Downloading from: $download_url"
    if wget -q --show-progress -O "$temp_file" "$download_url"; then
        # Verify the download
        local downloaded_size=$(stat -c%s "$temp_file" 2>/dev/null || echo "0")
        if [ "$downloaded_size" -gt 1000000 ]; then  # Check if downloaded file is larger than 1MB
            mv "$temp_file" "$dremio_jdbc_file"
            print_status "Legacy Dremio JDBC driver downloaded successfully ($(($downloaded_size / 1024 / 1024))MB)"

            # Create updated README
            create_jdbc_readme
        else
            rm -f "$temp_file"
            print_warning "Downloaded legacy Dremio JDBC driver appears to be corrupted or incomplete"
        fi
    else
        rm -f "$temp_file"
        print_warning "Failed to download legacy Dremio JDBC driver (not critical)"
        print_info "Apache Arrow Flight SQL JDBC driver will be used instead"
    fi
}

# Create JDBC drivers README
create_jdbc_readme() {
    if [ ! -f "jdbc-drivers/README.md" ]; then
        cat > "jdbc-drivers/README.md" << 'EOF'
# JDBC Drivers Directory

This directory contains JDBC driver JAR files for database connectivity.

## Apache Arrow Flight SQL JDBC Driver (Preferred)

The `flight-sql-jdbc-driver-17.0.0.jar` file is the Apache Arrow Flight SQL JDBC driver that provides modern, efficient connectivity to Dremio using the Flight SQL protocol.

### Features
- **Better Performance**: Uses Apache Arrow for efficient data transfer
- **SSL Compatibility**: Resolves SSL negotiation issues with Dremio Cloud
- **Modern Protocol**: Built on gRPC and Flight SQL standards
- **Java 17+ Support**: Optimized for modern Java environments

### Download Information
- **Source**: https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/
- **Auto-downloaded**: This file is automatically downloaded by the setup script
- **Size**: ~3-5MB
- **Version**: 17.0.0

## Legacy Dremio JDBC Driver (Backup)

The `dremio-jdbc-driver-LATEST.jar` file is the legacy Dremio JDBC driver, kept as a backup option.

### Download Information
- **Source**: https://download.dremio.com/jdbc-driver/
- **Auto-downloaded**: Downloaded as backup by the setup script
- **Size**: ~45-50MB
- **Version**: Latest available from Dremio

### Usage
The Enhanced Dremio Reporting Server automatically detects and prioritizes the Apache Arrow Flight SQL JDBC driver when available. The legacy driver is used as a fallback if needed.

### Manual Download
If you need to manually download or update the drivers:

```bash
cd jdbc-drivers
# Apache Arrow Flight SQL JDBC driver (preferred)
wget https://repo1.maven.org/maven2/org/apache/arrow/flight-sql-jdbc-driver/17.0.0/flight-sql-jdbc-driver-17.0.0.jar

# Legacy Dremio JDBC driver (backup)
wget https://download.dremio.com/jdbc-driver/dremio-jdbc-driver-LATEST.jar
```

### Verification
To verify the drivers are working:
```bash
python test_arrow_flight_sql_jdbc.py
```

### Troubleshooting
- Ensure the JAR files are not corrupted
- Verify Java 17+ is installed and JAVA_HOME is set
- Check that JPype and JayDeBeApi Python packages are installed
- For Java 17+, ensure proper module access is configured
EOF
        print_status "Created updated JDBC drivers README"
    fi
}

# Create test script for Java functionality
create_java_test() {
    print_info "Creating Java functionality test script..."
    
    cat > test_java_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify Java environment setup for Dremio Reporting Server.
"""
import os
import sys

def test_java_environment():
    """Test Java environment setup."""
    print("🧪 Testing Java Environment Setup")
    print("=" * 40)
    
    # Test 1: Check JAVA_HOME
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        print(f"✅ JAVA_HOME set: {java_home}")
        if os.path.exists(java_home):
            print(f"✅ JAVA_HOME directory exists")
        else:
            print(f"❌ JAVA_HOME directory not found")
            return False
    else:
        print("❌ JAVA_HOME not set")
        return False
    
    # Test 2: Check Java executable
    java_bin = os.path.join(java_home, 'bin', 'java')
    if os.path.exists(java_bin):
        print(f"✅ Java executable found: {java_bin}")
    else:
        print(f"❌ Java executable not found: {java_bin}")
        return False
    
    # Test 3: Test JPype import
    try:
        import jpype
        print(f"✅ JPype available for Java-Python bridge")
    except ImportError:
        print("❌ JPype not available")
        return False
    
    # Test 4: Test JayDeBeApi import
    try:
        import jaydebeapi
        print(f"✅ JayDeBeApi available: v{jaydebeapi.__version__}")
    except ImportError:
        print("❌ JayDeBeApi not available")
        return False
    
    # Test 5: Test JVM startup (without actually starting it)
    try:
        if not jpype.isJVMStarted():
            print("✅ JVM not started (ready for initialization)")
        else:
            print("✅ JVM already started")
    except Exception as e:
        print(f"❌ JVM test failed: {e}")
        return False
    
    print("\n🎉 All Java environment tests passed!")
    print("The system is ready for JDBC driver functionality.")
    return True

if __name__ == '__main__':
    success = test_java_environment()
    sys.exit(0 if success else 1)
EOF
    
    chmod +x test_java_setup.py
    print_status "Java test script created: test_java_setup.py"
}

# Devcontainer-specific setup
setup_devcontainer() {
    print_info "Detected devcontainer environment"

    # In devcontainer, Java should already be installed
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
        print_status "Java already available in devcontainer: $JAVA_VERSION"

        # Auto-detect JAVA_HOME
        if [ -z "$JAVA_HOME" ]; then
            DETECTED_JAVA_HOME=$(readlink -f $(which java) | sed "s:/bin/java::")
            export JAVA_HOME="$DETECTED_JAVA_HOME"
            print_status "Auto-detected JAVA_HOME: $JAVA_HOME"
        fi

        # Persist JAVA_HOME to environment files
        persist_java_home
    else
        print_warning "Java not found in devcontainer - this is unexpected"
        install_java
    fi

    # Python dependencies should already be installed, but verify
    print_info "Verifying Python dependencies in devcontainer..."
    if ! python3 -c "import jpype, jaydebeapi" &> /dev/null; then
        print_warning "Python dependencies missing - installing..."
        install_python_deps
    else
        print_status "Python dependencies already available"
    fi
}

# Main setup function
main() {
    echo ""
    print_info "Starting Enhanced Dremio Reporting Server setup..."

    # Detect environment
    if [ -f "/.dockerenv" ] || [ -n "$DEVCONTAINER" ]; then
        # Running in container/devcontainer
        setup_devcontainer
    else
        # Running on host system
        check_sudo
        update_system
        install_java
        install_python_deps
    fi

    # Common setup for all environments
    setup_environment
    test_java_integration
    download_jdbc_driver
    create_java_test

    echo ""
    print_status "Setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Edit .env file with your Dremio credentials"
    echo "  2. Load Java environment: source setup_env.sh (if needed)"
    echo "  3. Run: python test_java_setup.py (to test JDBC setup)"
    echo "  4. Run: ./run.sh (to start the server)"
    echo ""
    print_info "JDBC Driver Status:"
    if [ -f "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar" ]; then
        local driver_size=$(stat -c%s "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar" 2>/dev/null || echo "0")
        echo "  ✅ Apache Arrow Flight SQL JDBC driver installed ($(($driver_size / 1024 / 1024))MB)"
        echo "  📁 Location: jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar"
    fi
    if [ -f "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" ]; then
        local driver_size=$(stat -c%s "jdbc-drivers/dremio-jdbc-driver-LATEST.jar" 2>/dev/null || echo "0")
        echo "  ✅ Legacy Dremio JDBC driver installed ($(($driver_size / 1024 / 1024))MB)"
        echo "  📁 Location: jdbc-drivers/dremio-jdbc-driver-LATEST.jar"
    fi
    echo ""
    print_info "Java Environment:"
    echo "  JAVA_HOME: $JAVA_HOME"
    echo "  Java Version: $(java -version 2>&1 | head -n 1)"
    echo "  Environment Files: setup_env.sh created for easy loading"
    echo ""
    print_info "Environment Loading:"
    echo "  • Current session: JAVA_HOME is set"
    echo "  • New sessions: Run 'source setup_env.sh' or restart terminal"
    echo "  • Persistent: Added to ~/.bashrc and .env files"
    echo ""
    if [ -f "/.dockerenv" ] || [ -n "$DEVCONTAINER" ]; then
        print_info "Running in container - setup optimized for containerized environment"
    else
        print_info "For Docker deployment, see Dockerfile for container setup"
    fi
}

# Run main function
main "$@"