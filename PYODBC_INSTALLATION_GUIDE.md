# PyODBC Installation Guide for Dremio Reporting Server

## 🎯 Overview

This guide provides **comprehensive step-by-step instructions** to install and configure PyODBC with the Dremio ODBC driver for the Enhanced Dremio Reporting Server.

**Status**: ✅ **PyODBC Python package installed and working**  
**Requirement**: Install Dremio ODBC driver for full functionality  
**Compatibility**: Ubuntu/Debian, Docker, Windows, macOS  

## 📋 Prerequisites

### **System Requirements**
- **Operating System**: Ubuntu 20.04+, Debian 10+, or compatible
- **Python**: 3.8+ with pip
- **Memory**: 512MB+ available
- **Network**: Internet access for downloads

### **Current Status Check**
```bash
# Check if PyODBC is working
python -c "import pyodbc; print(f'✅ PyODBC v{pyodbc.version} available')"

# Check available ODBC drivers
python -c "import pyodbc; print(f'Drivers: {pyodbc.drivers()}')"
```

## 🚀 Installation Steps

### **Step 1: Install ODBC Driver Manager**

The ODBC driver manager (`unixODBC`) is required for PyODBC to function:

```bash
# Update package list
sudo apt update

# Install unixODBC and development headers
sudo apt install -y unixodbc unixodbc-dev

# Verify installation
odbcinst -j
```

**Expected Output:**
```
unixODBC 2.3.9
DRIVERS............: /etc/odbcinst.ini
SYSTEM DATA SOURCES: /etc/odbc.ini
FILE DATA SOURCES..: /etc/ODBCDataSources
USER DATA SOURCES..: /home/user/.odbc.ini
SQLULEN Size.......: 8
SQLLEN Size........: 8
SQLSETPOSIROW Size.: 8
```

### **Step 2: Verify PyODBC Installation**

PyODBC should now work properly:

```bash
# Test PyODBC import and functionality
python -c "
import pyodbc
print('✅ PyODBC imported successfully')
print(f'   Version: {pyodbc.version}')
print(f'   Available drivers: {pyodbc.drivers()}')
"
```

### **Step 3: Download Dremio ODBC Driver**

#### **Option A: Direct Download (Recommended)**

1. **Visit Dremio Downloads**: https://www.dremio.com/drivers/
2. **Select ODBC Driver**: Choose your platform (Linux x64)
3. **Download**: Get the latest version (e.g., `dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz`)

#### **Option B: Command Line Download**

```bash
# Create drivers directory
mkdir -p ~/dremio-drivers
cd ~/dremio-drivers

# Download Dremio ODBC driver (replace with latest version)
wget https://download.dremio.com/odbc-driver/1.5.1.1001/dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz

# Extract the driver
tar -xzf dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz
```

### **Step 4: Install Dremio ODBC Driver**

#### **Extract and Install**

```bash
# Navigate to extracted directory
cd dremio-odbc-1.5.1.1001-linux-x86_64

# Install the driver (requires sudo)
sudo ./install.sh

# Or manual installation:
sudo cp lib64/libdrillodbc64.so /usr/lib/x86_64-linux-gnu/
sudo cp setup/odbc.ini /etc/
sudo cp setup/odbcinst.ini /etc/
```

#### **Configure ODBC Driver**

Create or update `/etc/odbcinst.ini`:

```ini
[Dremio ODBC Driver]
Description=Dremio ODBC Driver
Driver=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so
Setup=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so
UsageCount=1
```

### **Step 5: Verify Dremio ODBC Driver Installation**

```bash
# Check if Dremio driver is registered
odbcinst -q -d

# Should show:
# [Dremio ODBC Driver]

# Test driver loading
python -c "
import pyodbc
drivers = pyodbc.drivers()
print('Available ODBC drivers:')
for driver in drivers:
    print(f'  - {driver}')
    
if 'Dremio ODBC Driver' in drivers:
    print('✅ Dremio ODBC Driver found!')
else:
    print('❌ Dremio ODBC Driver not found')
"
```

## 🧪 Testing PyODBC with Dremio

### **Step 6: Test Connection**

Use the provided testing script:

```bash
# Run PyODBC testing script
python test_pyodbc_installation.py
```

Or test manually:

```python
import pyodbc

# Connection string for Dremio Cloud
conn_str = (
    "DRIVER={Dremio ODBC Driver};"
    "HOST=data.dremio.cloud;"
    "PORT=443;"
    "SSL=1;"
    "AuthenticationType=Basic Authentication;"
    "UID=token;"  # Use 'token' for PAT authentication
    "PWD=your-personal-access-token"
)

try:
    # Test connection
    connection = pyodbc.connect(conn_str)
    print("✅ PyODBC connection successful!")
    
    # Test query
    cursor = connection.cursor()
    cursor.execute("SELECT 1 as test_value")
    result = cursor.fetchone()
    print(f"✅ Query result: {result}")
    
    connection.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### **Step 7: Test via API**

Test PyODBC through the Dremio Reporting Server:

```bash
# Start the server
python app.py

# Test PyODBC driver
curl -X POST http://localhost:5000/api/query-multi-driver \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 \"test_value\"", "drivers": ["pyodbc"]}'
```

## 🐳 Docker Installation

### **Enhanced Dockerfile**

Add PyODBC support to your Dockerfile:

```dockerfile
# Install ODBC driver manager
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install Dremio ODBC driver
RUN mkdir -p /tmp/dremio-odbc && \
    cd /tmp/dremio-odbc && \
    wget https://download.dremio.com/odbc-driver/1.5.1.1001/dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz && \
    tar -xzf dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz && \
    cd dremio-odbc-1.5.1.1001-linux-x86_64 && \
    cp lib64/libdrillodbc64.so /usr/lib/x86_64-linux-gnu/ && \
    rm -rf /tmp/dremio-odbc

# Configure ODBC driver
RUN echo '[Dremio ODBC Driver]\n\
Description=Dremio ODBC Driver\n\
Driver=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so\n\
Setup=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so\n\
UsageCount=1' > /etc/odbcinst.ini
```

### **docker-compose.yml Enhancement**

```yaml
services:
  dremio-reporting-server:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      # PyODBC Configuration
      - ODBCSYSINI=/etc
      - ODBCINI=/etc/odbc.ini
    volumes:
      # Mount ODBC configuration
      - ./odbc-config:/etc/odbc-config
```

## 🔧 Configuration

### **Environment Variables**

Set up your `.env` file:

```bash
# Dremio Configuration for PyODBC
DREMIO_URL=https://api.dremio.cloud
DREMIO_PAT=your-personal-access-token
DREMIO_USERNAME=your-username  # Alternative to PAT
DREMIO_PASSWORD=your-password  # Alternative to PAT

# PyODBC Specific
PYODBC_DRIVER_NAME=Dremio ODBC Driver
PYODBC_TIMEOUT=30
```

### **Connection String Options**

The PyODBC driver supports various connection options:

```python
# PAT Authentication (Recommended)
conn_str = (
    "DRIVER={Dremio ODBC Driver};"
    "HOST=data.dremio.cloud;"
    "PORT=443;"
    "SSL=1;"
    "AuthenticationType=Basic Authentication;"
    "UID=token;"
    "PWD=your-personal-access-token;"
    "ConnectionTimeout=30;"
    "QueryTimeout=300"
)

# Username/Password Authentication
conn_str = (
    "DRIVER={Dremio ODBC Driver};"
    "HOST=data.dremio.cloud;"
    "PORT=443;"
    "SSL=1;"
    "AuthenticationType=Basic Authentication;"
    "UID=your-username;"
    "PWD=your-password"
)
```

## 🚨 Troubleshooting

### **Common Issues**

#### **1. "libodbc.so.2: cannot open shared object file"**
```bash
# Solution: Install unixODBC
sudo apt install -y unixodbc unixodbc-dev
```

#### **2. "Can't open lib 'Dremio ODBC Driver' : file not found"**
```bash
# Solution: Install Dremio ODBC driver
# Follow Step 3-4 above

# Verify driver registration
odbcinst -q -d
```

#### **3. "Data source name not found"**
```bash
# Solution: Check driver name in connection string
python -c "import pyodbc; print(pyodbc.drivers())"

# Use exact driver name from the list
```

#### **4. "Connection timeout"**
```bash
# Solution: Check network connectivity and credentials
# Test with curl first:
curl -H "Authorization: Bearer YOUR_PAT" https://api.dremio.cloud/api/v3/user
```

### **Diagnostic Commands**

```bash
# Check ODBC configuration
odbcinst -j

# List available drivers
odbcinst -q -d

# Test driver loading
isql -v "Dremio ODBC Driver"

# Check PyODBC status
python test_pyodbc_installation.py
```

## 📊 Performance Considerations

### **Connection Pooling**
- PyODBC supports connection pooling
- Configure `ConnectionTimeout` and `QueryTimeout`
- Use connection context managers

### **Query Optimization**
- Use parameterized queries
- Implement proper error handling
- Monitor connection lifecycle

### **Resource Management**
- Always close connections and cursors
- Use try/finally blocks or context managers
- Monitor memory usage

## 🎯 Next Steps

1. **✅ Complete Installation**: Follow all steps above
2. **🧪 Run Tests**: Use `test_pyodbc_installation.py`
3. **🚀 Production Setup**: Configure Docker and environment
4. **📊 Performance Tuning**: Optimize connection settings
5. **🔄 Monitoring**: Set up logging and error tracking

---

*This guide completes TODO Task 4: Detail the steps to install PyODBC and then make it work as well.*  
*Enhanced Dremio Reporting Server - July 2025*
