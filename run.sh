#!/bin/bash

# Enhanced Dremio Reporting Server - Run Script
# ==============================================
# This script starts the Enhanced Dremio Reporting Server with proper
# environment setup and comprehensive error handling.

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${PURPLE}🚀 Enhanced Dremio Reporting Server${NC}"
    echo -e "${PURPLE}====================================${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_step() {
    echo -e "${CYAN}🔧${NC} $1"
}

# Check if port is available
check_port() {
    local port=$1
    if ss -tlnp | grep -q ":$port "; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Kill process on port
kill_port_process() {
    local port=$1
    print_step "Killing process on port $port..."
    
    local pids=$(ss -tlnp | grep ":$port " | awk '{print $6}' | cut -d',' -f2 | cut -d'=' -f2 | tr '\n' ' ')
    
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null
        sleep 2
        if check_port $port; then
            print_success "Port $port is now available"
            return 0
        else
            print_error "Failed to free port $port"
            return 1
        fi
    else
        print_warning "No process found on port $port"
        return 0
    fi
}

# Pre-flight checks
preflight_checks() {
    print_info "Running pre-flight checks..."
    
    # Check if Python is available and set PYTHON_CMD
    if command -v python &> /dev/null; then
        export PYTHON_CMD="python"
        print_success "Python is available"
    elif command -v python3 &> /dev/null; then
        export PYTHON_CMD="python3"
        print_success "Python3 is available"
    else
        print_error "Python is not installed or not in PATH"
        print_info "Please install Python 3.8+ or run the setup script: ./setup.sh"
        return 1
    fi
    
    # Check if app.py exists
    if [ ! -f "app.py" ]; then
        print_error "app.py not found in current directory"
        return 1
    fi
    print_success "app.py found"
    
    # Check if requirements are installed
    if ! $PYTHON_CMD -c "import flask" &> /dev/null; then
        print_error "Flask not installed. Run: pip install -r requirements.txt"
        print_info "Or run the setup script: ./setup.sh"
        return 1
    fi
    print_success "Python dependencies available"
    
    # Check Java environment
    if [ -z "$JAVA_HOME" ]; then
        # Try to auto-detect Java installation
        if [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
            export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
        elif [ -d "/usr/lib/jvm/java-11-openjdk-amd64" ]; then
            export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
        elif [ -d "/usr/lib/jvm/default-java" ]; then
            export JAVA_HOME=/usr/lib/jvm/default-java
        else
            print_error "No Java installation found. Please install Java 11 or 17."
            return 1
        fi
    fi
    
    if [ ! -d "$JAVA_HOME" ]; then
        print_error "JAVA_HOME directory not found: $JAVA_HOME"
        return 1
    fi
    print_success "Java environment configured"
    
    # Check JDBC driver
    if [ ! -f "jdbc-drivers/flight-sql-jdbc-driver-17.0.0.jar" ]; then
        print_warning "Arrow Flight SQL JDBC driver not found. Some functionality may be limited."
        print_info "Run './setup.sh' to download the JDBC driver"
    else
        print_success "Arrow Flight SQL JDBC driver available"
    fi

    # Check PyODBC environment
    if ! python -c "import pyodbc" &> /dev/null; then
        print_warning "PyODBC not available. Some functionality may be limited."
        print_info "Run './setup.sh' to install PyODBC dependencies"
    else
        print_success "PyODBC environment available"
    fi
    
    # Check .env file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Using default configuration."
        print_info "Create .env file with your Dremio credentials for full functionality"
    else
        print_success ".env file found"
    fi
    
    return 0
}

# Main server startup function
start_server() {
    local port=${FLASK_PORT:-5001}
    
    print_step "Setting up environment..."
    # Auto-detect Java if not set
    if [ -z "$JAVA_HOME" ]; then
        if [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
            export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
        elif [ -d "/usr/lib/jvm/java-11-openjdk-amd64" ]; then
            export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
        elif [ -d "/usr/lib/jvm/default-java" ]; then
            export JAVA_HOME=/usr/lib/jvm/default-java
        fi
    fi
    export FLASK_PORT=$port
    
    print_step "Starting Enhanced Dremio Reporting Server on port $port..."
    print_info "Server will be accessible at:"
    echo "  • Local:   http://127.0.0.1:$port"
    echo "  • Network: http://0.0.0.0:$port"
    echo ""
    print_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the server
    $PYTHON_CMD app.py
    local exit_code=$?
    
    return $exit_code
}

# Error handling and troubleshooting guide
handle_failure() {
    local exit_code=$1
    
    echo ""
    print_error "Server failed to start (exit code: $exit_code)"
    echo ""
    print_info "🔍 Troubleshooting Guide:"
    echo ""
    
    echo -e "${YELLOW}1. Port Issues:${NC}"
    echo "   • Check if port 5001 is in use: ss -tlnp | grep :5001"
    echo "   • Kill process on port: ./run.sh --kill-port"
    echo "   • Use different port: FLASK_PORT=5002 ./run.sh"
    echo ""
    
    echo -e "${YELLOW}2. Java Environment:${NC}"
    echo "   • Verify Java installation: java -version"
    echo "   • Test Java setup: python test_java_setup.py"
    echo "   • Re-run setup: ./setup.sh"
    echo ""
    
    echo -e "${YELLOW}3. Python Dependencies:${NC}"
    echo "   • Install requirements: pip install -r requirements.txt"
    echo "   • Check Flask: python -c 'import flask; print(flask.__version__)'"
    echo ""
    
    echo -e "${YELLOW}4. JDBC Driver:${NC}"
    echo "   • Download driver: ./setup.sh"
    echo "   • Check driver: ls -la jdbc-drivers/"
    echo ""

    echo -e "${YELLOW}5. PyODBC Environment:${NC}"
    echo "   • Test PyODBC: python test_pyodbc_installation.py"
    echo "   • Install ODBC: ./setup.sh"
    echo "   • Check drivers: python -c 'import pyodbc; print(pyodbc.drivers())'"
    echo ""
    
    echo -e "${YELLOW}6. Configuration:${NC}"
    echo "   • Create .env file with Dremio credentials"
    echo "   • Check configuration: curl http://localhost:5001/debug"
    echo ""

    echo -e "${YELLOW}7. Logs and Debugging:${NC}"
    echo "   • Run with verbose output: FLASK_DEBUG=1 ./run.sh"
    echo "   • Check system logs: journalctl -f"
    echo ""
    
    echo -e "${CYAN}💡 Quick Fixes:${NC}"
    echo "   • Full reset: ./setup.sh && ./run.sh"
    echo "   • Kill port and retry: ./run.sh --kill-port && ./run.sh"
    echo "   • Test Java: python test_java_setup.py"
    echo "   • Test PyODBC: python test_pyodbc_installation.py"
    echo ""
    
    echo -e "${GREEN}📚 Documentation:${NC}"
    echo "   • Setup guide: cat README.md"
    echo "   • JDBC guide: cat jdbc-drivers/README.md"
    echo "   • API docs: curl http://localhost:5001/ (when running)"
    echo ""
}

# Command line argument handling
case "${1:-}" in
    --kill-port)
        print_header
        port=${FLASK_PORT:-5001}
        print_info "Attempting to free port $port..."
        if kill_port_process $port; then
            print_success "Port $port is now available"
            print_info "You can now run: ./run.sh"
        else
            print_error "Failed to free port $port"
            print_info "Try manually: ss -tlnp | grep :$port"
        fi
        exit 0
        ;;
    --help|-h)
        print_header
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --kill-port    Kill any process using the server port"
        echo "  --help, -h     Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  FLASK_PORT     Port to run the server on (default: 5001)"
        echo "  FLASK_DEBUG    Enable debug mode (default: off)"
        echo ""
        echo "Examples:"
        echo "  ./run.sh                    # Start server on port 5001"
        echo "  FLASK_PORT=5002 ./run.sh    # Start server on port 5002"
        echo "  ./run.sh --kill-port        # Kill process on port and exit"
        echo ""
        exit 0
        ;;
esac

# Main execution
main() {
    print_header
    
    # Check if we need to kill port process first
    port=${FLASK_PORT:-5001}
    if ! check_port $port; then
        print_warning "Port $port is already in use"
        print_info "Attempting to free the port..."
        if ! kill_port_process $port; then
            print_error "Cannot free port $port"
            print_info "Run: ./run.sh --kill-port"
            exit 1
        fi
    fi
    
    # Run pre-flight checks
    if ! preflight_checks; then
        print_error "Pre-flight checks failed"
        handle_failure 1
        exit 1
    fi
    
    print_success "All pre-flight checks passed"
    echo ""
    
    # Start the server
    if ! start_server; then
        handle_failure $?
        exit 1
    fi
}

# Make sure we're in the right directory
if [ ! -f "app.py" ]; then
    print_error "Please run this script from the project root directory (where app.py is located)"
    exit 1
fi

# Run main function
main "$@"
