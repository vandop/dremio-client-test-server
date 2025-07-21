# Docker PyODBC Setup Guide

## 🐳 Overview

This guide provides instructions for setting up PyODBC with Dremio ODBC driver in Docker containers for the Enhanced Dremio Reporting Server.

**Status**: ✅ **Docker configuration ready for PyODBC**  
**Requirement**: Dremio ODBC driver for full functionality  
**Compatibility**: Linux containers, multi-architecture support  

## 📋 Prerequisites

- **Docker**: 20.10+ installed and running
- **Docker Compose**: 2.0+ (optional but recommended)
- **Dremio ODBC Driver**: Downloaded from https://www.dremio.com/drivers/
- **Network Access**: For downloading dependencies

## 🚀 Quick Start

### **Option 1: Basic Setup (PyODBC without Dremio driver)**

```bash
# Build and run with basic PyODBC support
docker-compose up --build

# PyODBC will be available but without Dremio driver
# Suitable for testing ODBC infrastructure
```

### **Option 2: Complete Setup (PyODBC with Dremio driver)**

```bash
# 1. Download Dremio ODBC driver
mkdir -p docker-assets
cd docker-assets
wget https://download.dremio.com/odbc-driver/1.5.1.1001/dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz

# 2. Build Docker image with Dremio driver
docker build -t dremio-reporting-server:pyodbc .

# 3. Run with full PyODBC support
docker run -p 5000:5000 --env-file .env dremio-reporting-server:pyodbc
```

## 🔧 Docker Configuration

### **Enhanced Dockerfile**

The Dockerfile includes PyODBC support:

```dockerfile
# Enhanced Dockerfile for Dremio Reporting Server with PyODBC Support
FROM python:3.11-slim

# ODBC environment variables
ENV ODBCSYSINI=/etc
ENV ODBCINI=/etc/odbc.ini

# Install ODBC components
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    curl wget \
    && apt-get clean

# Verify ODBC installation
RUN odbcinst -j

# Install Python dependencies (includes pyodbc)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### **docker-compose.yml Enhancement**

```yaml
version: '3.8'

services:
  dremio-reporting-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dremio-reporting-server
    ports:
      - "5000:5000"
    environment:
      # ODBC Configuration
      - ODBCSYSINI=/etc
      - ODBCINI=/etc/odbc.ini
      
      # PyODBC Configuration
      - PYODBC_DRIVER_NAME=Dremio ODBC Driver
      - PYODBC_TIMEOUT=30
      
      # Dremio Configuration
      - DREMIO_URL=${DREMIO_URL:-https://api.dremio.cloud}
      - DREMIO_PAT=${DREMIO_PAT}
      
    env_file:
      - .env
    
    volumes:
      # Development volume mount
      - .:/app
      # ODBC configuration
      - ./odbc-config:/etc/odbc-config
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 📦 Dremio ODBC Driver Installation

### **Method 1: Build-time Installation (Recommended)**

1. **Download Dremio ODBC Driver**:
   ```bash
   mkdir -p docker-assets
   cd docker-assets
   wget https://download.dremio.com/odbc-driver/1.5.1.1001/dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz
   ```

2. **Modify Dockerfile**:
   Uncomment the Dremio ODBC driver installation section:
   ```dockerfile
   # Copy Dremio ODBC driver
   COPY docker-assets/dremio-odbc-*.tar.gz /tmp/
   
   # Install Dremio ODBC driver
   RUN cd /tmp && \
       tar -xzf dremio-odbc-*.tar.gz && \
       cd dremio-odbc-* && \
       cp lib64/libdrillodbc64.so /usr/lib/x86_64-linux-gnu/ && \
       echo '[Dremio ODBC Driver]\n\
   Description=Dremio ODBC Driver\n\
   Driver=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so\n\
   Setup=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so\n\
   UsageCount=1' > /etc/odbcinst.ini && \
       rm -rf /tmp/dremio-odbc-*
   ```

3. **Build and Run**:
   ```bash
   docker build -t dremio-reporting-server:pyodbc .
   docker run -p 5000:5000 --env-file .env dremio-reporting-server:pyodbc
   ```

### **Method 2: Runtime Installation (Volume Mount)**

1. **Create ODBC configuration directory**:
   ```bash
   mkdir -p odbc-config
   ```

2. **Download and extract Dremio driver**:
   ```bash
   cd odbc-config
   wget https://download.dremio.com/odbc-driver/1.5.1.1001/dremio-odbc-1.5.1.1001-linux-x86_64.tar.gz
   tar -xzf dremio-odbc-*.tar.gz
   ```

3. **Create odbcinst.ini**:
   ```bash
   cat > odbc-config/odbcinst.ini << 'EOF'
   [Dremio ODBC Driver]
   Description=Dremio ODBC Driver
   Driver=/etc/odbc-config/dremio-odbc-1.5.1.1001-linux-x86_64/lib64/libdrillodbc64.so
   Setup=/etc/odbc-config/dremio-odbc-1.5.1.1001-linux-x86_64/lib64/libdrillodbc64.so
   UsageCount=1
   EOF
   ```

4. **Update docker-compose.yml**:
   ```yaml
   volumes:
     - ./odbc-config:/etc/odbc-config
   environment:
     - ODBCSYSINI=/etc/odbc-config
     - ODBCINI=/etc/odbc-config/odbc.ini
   ```

## 🧪 Testing PyODBC in Docker

### **Test Container Build**

```bash
# Build the container
docker build -t dremio-reporting-server:test .

# Test PyODBC installation
docker run --rm dremio-reporting-server:test python -c "
import pyodbc
print(f'✅ PyODBC v{pyodbc.version} available')
print(f'Drivers: {pyodbc.drivers()}')
"
```

### **Test ODBC Configuration**

```bash
# Test ODBC configuration
docker run --rm dremio-reporting-server:test odbcinst -j

# Test driver registration
docker run --rm dremio-reporting-server:test odbcinst -q -d
```

### **Test API Integration**

```bash
# Start the container
docker run -d -p 5000:5000 --name test-pyodbc --env-file .env dremio-reporting-server:test

# Test PyODBC driver availability
curl http://localhost:5000/api/drivers | jq '.drivers.pyodbc'

# Test PyODBC query
curl -X POST http://localhost:5000/api/query-multi-driver \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 \"test\"", "drivers": ["pyodbc"]}'

# Cleanup
docker stop test-pyodbc && docker rm test-pyodbc
```

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file for Docker:

```bash
# Dremio Configuration
DREMIO_URL=https://api.dremio.cloud
DREMIO_PAT=your-personal-access-token

# PyODBC Configuration
PYODBC_DRIVER_NAME=Dremio ODBC Driver
PYODBC_TIMEOUT=30

# ODBC Environment
ODBCSYSINI=/etc
ODBCINI=/etc/odbc.ini

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=false
```

### **ODBC Configuration Files**

**odbcinst.ini** (Driver registration):
```ini
[Dremio ODBC Driver]
Description=Dremio ODBC Driver
Driver=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so
Setup=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so
UsageCount=1
```

**odbc.ini** (Data source configuration):
```ini
[DremioCloud]
Driver=Dremio ODBC Driver
HOST=data.dremio.cloud
PORT=443
SSL=1
AuthenticationType=Basic Authentication
```

## 🚨 Troubleshooting

### **Common Issues**

#### **1. "odbcinst: command not found"**
```bash
# Solution: Ensure odbcinst package is installed
RUN apt-get install -y odbcinst
```

#### **2. "libdrillodbc64.so: cannot open shared object file"**
```bash
# Solution: Verify driver file location and permissions
docker run --rm your-image ls -la /usr/lib/x86_64-linux-gnu/libdrillodbc64.so
```

#### **3. "No data source name found"**
```bash
# Solution: Check ODBC configuration
docker run --rm your-image odbcinst -q -d
docker run --rm your-image cat /etc/odbcinst.ini
```

### **Debugging Commands**

```bash
# Check ODBC installation
docker run --rm your-image odbcinst -j

# List available drivers
docker run --rm your-image odbcinst -q -d

# Test PyODBC import
docker run --rm your-image python -c "import pyodbc; print(pyodbc.drivers())"

# Check file permissions
docker run --rm your-image ls -la /usr/lib/x86_64-linux-gnu/libdrillodbc64.so

# Test ODBC connection (interactive)
docker run -it --env-file .env your-image bash
```

## 📊 Performance Considerations

### **Image Size Optimization**

- **Multi-stage builds**: Separate build and runtime stages
- **Minimal base images**: Use slim or alpine variants
- **Layer caching**: Optimize Dockerfile layer order
- **Cleanup**: Remove unnecessary files and packages

### **Runtime Optimization**

- **Connection pooling**: Configure PyODBC connection pooling
- **Resource limits**: Set appropriate memory and CPU limits
- **Health checks**: Monitor container health
- **Logging**: Configure appropriate log levels

## 🎯 Production Deployment

### **Production Dockerfile**

```dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    unixodbc \
    odbcinst \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . /app
WORKDIR /app

# Install Dremio ODBC driver
COPY docker-assets/dremio-odbc-*.tar.gz /tmp/
RUN cd /tmp && \
    tar -xzf dremio-odbc-*.tar.gz && \
    cd dremio-odbc-* && \
    cp lib64/libdrillodbc64.so /usr/lib/x86_64-linux-gnu/ && \
    echo '[Dremio ODBC Driver]...' > /etc/odbcinst.ini

# Create non-root user
RUN useradd --create-home --shell /bin/bash dremio
USER dremio

CMD ["python", "app.py"]
```

---

*This guide completes Docker setup for PyODBC as part of TODO Task 4.*  
*Enhanced Dremio Reporting Server - July 2025*
