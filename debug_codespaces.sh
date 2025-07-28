#!/bin/bash
# Debug script for GitHub Codespaces setup issues

echo "🔍 Dremio Reporting Server - Codespaces Diagnostics"
echo "=================================================="

# System Information
echo ""
echo "📊 System Information:"
echo "  Architecture: $(uname -m)"
echo "  OS: $(uname -s)"
echo "  Kernel: $(uname -r)"
echo "  Distribution: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"

# Python Environment
echo ""
echo "🐍 Python Environment:"
echo "  Python version: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "  Pip version: $(pip3 --version 2>/dev/null || echo 'Not found')"
echo "  Virtual env: ${VIRTUAL_ENV:-'Not activated'}"

# Java Environment
echo ""
echo "☕ Java Environment:"
echo "  Java version: $(java -version 2>&1 | head -n1 || echo 'Not found')"
echo "  JAVA_HOME: ${JAVA_HOME:-'Not set'}"
echo "  Java paths found:"
find /usr/lib/jvm -name "java-*-openjdk*" -type d 2>/dev/null | head -5 || echo "    None found"

# Network Connectivity
echo ""
echo "🌐 Network Connectivity:"
echo "  Internet: $(curl -s --max-time 5 https://google.com >/dev/null && echo 'OK' || echo 'Failed')"
echo "  Dremio Cloud: $(curl -s --max-time 10 https://api.dremio.cloud >/dev/null && echo 'OK' || echo 'Failed')"
echo "  ODBC Driver URL: $(curl -s --max-time 10 -I https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm | head -n1 | grep -q '200' && echo 'OK' || echo 'Failed')"

# Port Status
echo ""
echo "🔌 Port Status:"
echo "  Port 5000: $(netstat -ln 2>/dev/null | grep ':5000' >/dev/null && echo 'In use' || echo 'Available')"
echo "  Port 5001: $(netstat -ln 2>/dev/null | grep ':5001' >/dev/null && echo 'In use' || echo 'Available')"

# File System
echo ""
echo "📁 File System:"
echo "  Current directory: $(pwd)"
echo "  Workspace permissions: $(ls -la . | head -n2 | tail -n1)"
echo "  .env file: $([ -f .env ] && echo 'Exists' || echo 'Missing')"
echo "  requirements.txt: $([ -f requirements.txt ] && echo 'Exists' || echo 'Missing')"

# Python Dependencies
echo ""
echo "📦 Python Dependencies:"
if [ -f requirements.txt ]; then
    echo "  Installing dependencies..."
    pip3 install -r requirements.txt >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Dependencies installed successfully"
    else
        echo "  ❌ Dependencies installation failed"
        echo "  Trying individual packages..."
        pip3 install flask pyarrow adbc-driver-flightsql jaydebeapi pyodbc requests python-dotenv >/dev/null 2>&1
    fi
else
    echo "  ❌ requirements.txt not found"
fi

# Test imports
echo ""
echo "🧪 Python Import Tests:"
python3 -c "import flask; print('  ✅ Flask:', flask.__version__)" 2>/dev/null || echo "  ❌ Flask: Failed"
python3 -c "import pyarrow; print('  ✅ PyArrow:', pyarrow.__version__)" 2>/dev/null || echo "  ❌ PyArrow: Failed"
python3 -c "import adbc_driver_flightsql; print('  ✅ ADBC Flight SQL: OK')" 2>/dev/null || echo "  ❌ ADBC Flight SQL: Failed"
python3 -c "import jaydebeapi; print('  ✅ JayDeBeApi: OK')" 2>/dev/null || echo "  ❌ JayDeBeApi: Failed"
python3 -c "import pyodbc; print('  ✅ PyODBC: OK')" 2>/dev/null || echo "  ❌ PyODBC: Failed"

# JDBC Drivers
echo ""
echo "🚗 JDBC Drivers:"
if [ -d "jdbc-drivers" ]; then
    echo "  JDBC drivers directory: Exists"
    echo "  JAR files found: $(find jdbc-drivers -name "*.jar" | wc -l)"
    find jdbc-drivers -name "*.jar" | head -3 | sed 's/^/    /'
else
    echo "  ❌ JDBC drivers directory: Missing"
fi

# ODBC Configuration
echo ""
echo "🔧 ODBC Configuration:"
echo "  ODBC drivers: $(odbcinst -q -d 2>/dev/null | wc -l || echo '0')"
echo "  Dremio ODBC driver: $(odbcinst -q -d 2>/dev/null | grep -i dremio >/dev/null && echo 'Installed' || echo 'Not found')"

# Application Test
echo ""
echo "🚀 Application Test:"
if [ -f "app.py" ]; then
    echo "  app.py: Exists"
    python3 -c "import app; print('  ✅ App imports successfully')" 2>/dev/null || echo "  ❌ App import failed"
else
    echo "  ❌ app.py: Missing"
fi

# Recommendations
echo ""
echo "💡 Recommendations:"
echo "  1. If Python dependencies failed, run: pip3 install -r requirements.txt"
echo "  2. If JDBC drivers missing, run: ./setup.sh"
echo "  3. If ODBC issues, check: odbcinst -q -d"
echo "  4. To start server, run: ./run.sh"
echo "  5. Server should be accessible on port 5001"

echo ""
echo "✅ Diagnostics complete!"
