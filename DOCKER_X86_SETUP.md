# Docker x86_64 Setup for Enhanced Dremio Reporting Server

## 🎯 **Overview**

This guide explains how to build and run the Enhanced Dremio Reporting Server using Docker with **forced x86_64 architecture** to ensure compatibility with the Dremio Arrow Flight SQL ODBC driver.

## ⚠️ **Why x86_64 Architecture?**

The official Dremio Arrow Flight SQL ODBC driver is only available for x86_64 architecture:
- **Official URL**: `https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm`
- **Architecture**: x86_64 only (no ARM64 version available)
- **Solution**: Force Docker containers to run on x86_64 architecture using platform flags

## 🚀 **Quick Start**

### **Method 1: Using the Build Script (Recommended)**

```bash
# Build the x86_64 Docker image
./docker-build-x86.sh

# Run with docker-compose (automatically uses x86_64)
docker-compose up
```

### **Method 2: Manual Docker Commands**

```bash
# Build with forced x86_64 architecture
docker build --platform linux/amd64 -t dremio-reporting-server:x86_64 .

# Run with forced x86_64 architecture
docker run --platform linux/amd64 -p 5000:5000 dremio-reporting-server:x86_64
```

### **Method 3: Docker Compose**

```bash
# The docker-compose.yml is already configured for x86_64
docker-compose up --build
```

## 🔧 **Configuration Details**

### **Dockerfile Changes**

```dockerfile
# Force x86_64 architecture for ODBC driver compatibility
FROM --platform=linux/amd64 python:3.11-slim

# Install alien for RPM to DEB conversion
RUN apt-get update && apt-get install -y \
    alien \
    # ... other packages

# Automated ODBC driver installation
RUN cd /tmp && \
    wget -q https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm && \
    alien -d arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm && \
    dpkg -i arrow-flight-sql-odbc-driver*.deb
```

### **Docker Compose Changes**

```yaml
services:
  dremio-reporting-server:
    build:
      context: .
      dockerfile: Dockerfile
      platforms:
        - linux/amd64
    platform: linux/amd64  # Force runtime platform
    environment:
      - ODBCSYSINI=/etc
      - ODBCINI=/etc/odbc.ini
```

## 🧪 **Testing the Setup**

### **1. Verify Architecture**

```bash
# Check container architecture
docker run --rm dremio-reporting-server:x86_64 uname -m
# Expected output: x86_64
```

### **2. Test ODBC Driver Installation**

```bash
# Check installed ODBC drivers
docker run --rm dremio-reporting-server:x86_64 odbcinst -q -d
# Expected output: [Arrow Flight SQL ODBC Driver]
```

### **3. Test PyODBC Integration**

```bash
# Test PyODBC driver detection
docker run --rm dremio-reporting-server:x86_64 python -c "import pyodbc; print(pyodbc.drivers())"
# Expected output: ['Arrow Flight SQL ODBC Driver']
```

### **4. Test Multi-Driver API**

```bash
# Start the container
docker-compose up -d

# Test driver detection
curl http://localhost:5000/api/drivers

# Expected response should include PyODBC
```

## 🔍 **Troubleshooting**

### **Issue: "exec format error"**

**Problem**: Running ARM64 image on x86_64 or vice versa

**Solution**:
```bash
# Always specify platform
docker run --platform linux/amd64 -p 5000:5000 dremio-reporting-server:x86_64
```

### **Issue: ODBC Driver Not Found**

**Problem**: `"Can't open lib 'Arrow Flight SQL ODBC Driver' : file not found"`

**Solution**:
```bash
# Rebuild with x86_64 architecture
./docker-build-x86.sh

# Verify driver installation
docker run --rm dremio-reporting-server:x86_64 ls -la /opt/arrow-flight-sql-odbc-driver/
```

### **Issue: Slow Performance on ARM64 Hosts**

**Problem**: x86_64 emulation on ARM64 hosts (like Apple Silicon) may be slower

**Expected**: This is normal - x86_64 emulation on ARM64 will have performance overhead but ensures compatibility

## 🏗️ **Build Process Details**

### **What Happens During Build**

1. **Base Image**: `python:3.11-slim` with `--platform=linux/amd64`
2. **System Packages**: Java 11, unixODBC, alien, build tools
3. **ODBC Driver Download**: Automatic download from official Dremio source
4. **RPM Conversion**: `alien -d` converts RPM to DEB format
5. **Driver Installation**: `dpkg -i` installs the converted package
6. **Driver Registration**: Automatic registration in `/etc/odbcinst.ini`
7. **Python Dependencies**: All packages from `requirements.txt`

### **Installed Components**

- ✅ **Java 11**: OpenJDK for JDBC support
- ✅ **unixODBC**: Driver manager (v2.3.11+)
- ✅ **PyODBC**: Python ODBC interface (v5.2.0+)
- ✅ **Dremio ODBC Driver**: Arrow Flight SQL ODBC driver (latest)
- ✅ **All Python Dependencies**: Flask, PyArrow, pandas, etc.

## 🌐 **Production Deployment**

### **Docker Swarm**

```yaml
version: '3.8'
services:
  dremio-reporting-server:
    image: dremio-reporting-server:x86_64
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.platform.arch == x86_64
    ports:
      - "5000:5000"
```

### **Kubernetes**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dremio-reporting-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dremio-reporting-server
  template:
    metadata:
      labels:
        app: dremio-reporting-server
    spec:
      nodeSelector:
        kubernetes.io/arch: amd64
      containers:
      - name: dremio-reporting-server
        image: dremio-reporting-server:x86_64
        ports:
        - containerPort: 5000
```

## 📊 **Performance Considerations**

### **Architecture Emulation Impact**

| Host Architecture | Container Architecture | Performance Impact |
|-------------------|----------------------|-------------------|
| x86_64 | x86_64 | ✅ Native (100%) |
| ARM64 (Apple Silicon) | x86_64 | ⚠️ Emulated (~70-80%) |
| ARM64 (AWS Graviton) | x86_64 | ⚠️ Emulated (~70-80%) |

### **Optimization Tips**

1. **Use x86_64 hosts** for production deployment when possible
2. **Enable BuildKit** for faster builds: `export DOCKER_BUILDKIT=1`
3. **Use multi-stage builds** to reduce image size
4. **Cache layers** effectively by ordering Dockerfile commands properly

## 🎉 **Success Indicators**

When everything is working correctly, you should see:

```bash
# 1. Correct architecture
$ docker run --rm dremio-reporting-server:x86_64 uname -m
x86_64

# 2. ODBC driver installed
$ docker run --rm dremio-reporting-server:x86_64 odbcinst -q -d
[Arrow Flight SQL ODBC Driver]

# 3. PyODBC detects driver
$ docker run --rm dremio-reporting-server:x86_64 python -c "import pyodbc; print(len(pyodbc.drivers()))"
1

# 4. API shows all drivers
$ curl http://localhost:5000/api/drivers | jq '.count'
4
```

## 🚀 **Next Steps**

1. **Build the image**: `./docker-build-x86.sh`
2. **Start the service**: `docker-compose up`
3. **Configure credentials**: Edit `.env` file with your Dremio PAT
4. **Test all drivers**: Visit `http://localhost:5000/query`
5. **Deploy to production**: Use x86_64 hosts for optimal performance

The Enhanced Dremio Reporting Server now runs with complete multi-driver support including PyODBC with the official Dremio Arrow Flight SQL ODBC driver! 🎉
