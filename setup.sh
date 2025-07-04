#!/bin/bash

# Enhanced Dremio Reporting Server Setup Script
# This script sets up the complete environment including Java support

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

# Update system packages
update_system() {
    print_info "Updating system packages..."
    $SUDO apt update -qq
    print_status "System packages updated"
}

# Install Java (OpenJDK 11)
install_java() {
    print_info "Checking Java installation..."
    
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
        print_status "Java already installed: $JAVA_VERSION"
    else
        print_info "Installing OpenJDK 11..."
        $SUDO apt install -y openjdk-11-jdk openjdk-11-jre
        print_status "OpenJDK 11 installed successfully"
    fi
    
    # Set JAVA_HOME
    export JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
    
    # Verify installation
    java -version
    javac -version
    print_status "Java installation verified"
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

# Java Configuration
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
EOF
        print_status ".env template created"
        print_warning "Please edit .env file with your Dremio credentials"
    else
        print_status ".env file already exists"
    fi
    
    # Add JAVA_HOME to current session
    export JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
    
    # Add to shell profile for persistence
    SHELL_PROFILE=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_PROFILE="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [ -f "$HOME/.profile" ]; then
        SHELL_PROFILE="$HOME/.profile"
    fi
    
    if [ -n "$SHELL_PROFILE" ]; then
        if ! grep -q "JAVA_HOME" "$SHELL_PROFILE"; then
            echo "" >> "$SHELL_PROFILE"
            echo "# Java Environment (added by Dremio Reporting Server setup)" >> "$SHELL_PROFILE"
            echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> "$SHELL_PROFILE"
            echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> "$SHELL_PROFILE"
            print_status "JAVA_HOME added to $SHELL_PROFILE"
        else
            print_status "JAVA_HOME already configured in shell profile"
        fi
    fi
}

# Test Java integration with Python
test_java_integration() {
    print_info "Testing Java integration with Python..."
    
    python3 -c "
import sys
try:
    import jpype
    print('✓ JPype (Java-Python bridge) available')
    
    # Test Java environment
    import os
    java_home = os.environ.get('JAVA_HOME', '/usr/lib/jvm/java-11-openjdk-amd64')
    if os.path.exists(java_home):
        print(f'✓ JAVA_HOME found: {java_home}')
    else:
        print(f'✗ JAVA_HOME not found: {java_home}')
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

# Main setup function
main() {
    echo ""
    print_info "Starting Enhanced Dremio Reporting Server setup..."
    
    # Check system requirements
    check_sudo
    
    # Install system dependencies
    update_system
    install_java
    
    # Install Python dependencies
    install_python_deps
    
    # Set up environment
    setup_environment
    
    # Test Java integration
    test_java_integration
    
    # Create test script
    create_java_test
    
    echo ""
    print_status "Setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Edit .env file with your Dremio credentials"
    echo "  2. Run: python test_java_setup.py (to verify Java setup)"
    echo "  3. Run: python app.py (to start the server)"
    echo ""
    print_info "Java Environment:"
    echo "  JAVA_HOME: $JAVA_HOME"
    echo "  Java Version: $(java -version 2>&1 | head -n 1)"
    echo ""
    print_info "For Docker deployment, see Dockerfile for container setup"
}

# Run main function
main "$@"
