# Enhanced Dremio Reporting Server DevContainer with Java and PyODBC Support
# Force x86_64 architecture for ODBC driver compatibility
FROM --platform=linux/amd64 python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# ODBC environment variables
ENV ODBCSYSINI=/etc
ENV ODBCINI=/etc/odbc.ini

# Install system dependencies including Java and ODBC support
RUN apt-get update && apt-get install -y \
    # Development tools
    build-essential \
    curl \
    git \
    vim \
    nano \
    wget \
    unzip \
    sudo \
    # Java Development Kit for JDBC driver support
    openjdk-11-jdk \
    openjdk-11-jre \
    # ODBC components for PyODBC
    unixodbc \
    unixodbc-dev \
    odbcinst \
    # RPM to DEB conversion tool for ODBC driver
    alien \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Java and ODBC installation
RUN java -version && javac -version && echo "JAVA_HOME: $JAVA_HOME"
RUN odbcinst -j

# Install Dremio Arrow Flight SQL ODBC driver automatically
RUN cd /tmp && \
    # Download the latest Arrow Flight SQL ODBC driver
    wget -q https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm && \
    # Convert RPM to DEB and install
    alien -d arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm && \
    dpkg -i arrow-flight-sql-odbc-driver*.deb || apt-get install -f -y && \
    # Find the driver library
    DRIVER_LIB=$(find /opt -name "libarrow*.so*" 2>/dev/null | grep -E "(odbc|flight)" | head -1) && \
    # Register the ODBC driver
    if [ -n "$DRIVER_LIB" ] && [ -f "$DRIVER_LIB" ]; then \
        echo "[Arrow Flight SQL ODBC Driver]" >> /etc/odbcinst.ini && \
        echo "Description=Arrow Flight SQL ODBC Driver" >> /etc/odbcinst.ini && \
        echo "Driver=$DRIVER_LIB" >> /etc/odbcinst.ini && \
        echo "Setup=$DRIVER_LIB" >> /etc/odbcinst.ini && \
        echo "UsageCount=1" >> /etc/odbcinst.ini && \
        echo "" >> /etc/odbcinst.ini; \
    fi && \
    # Create sample DSN configuration
    echo "[Dremio Cloud Flight SQL]" >> /etc/odbc.ini && \
    echo "Description=Dremio Cloud via Arrow Flight SQL ODBC" >> /etc/odbc.ini && \
    echo "Driver=Arrow Flight SQL ODBC Driver" >> /etc/odbc.ini && \
    echo "HOST=data.dremio.cloud" >> /etc/odbc.ini && \
    echo "PORT=443" >> /etc/odbc.ini && \
    echo "useEncryption=true" >> /etc/odbc.ini && \
    echo "TOKEN=your_personal_access_token_here" >> /etc/odbc.ini && \
    echo "" >> /etc/odbc.ini && \
    # Cleanup
    rm -rf /tmp/arrow-flight-sql-odbc-driver*

# Create a non-root user
RUN useradd --create-home --shell /bin/bash vscode \
    && usermod -aG sudo vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /workspace

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional development tools
RUN pip install --no-cache-dir \
    black \
    flake8 \
    pytest \
    pytest-flask \
    ipython \
    jupyter

# Switch to non-root user
USER vscode

# Expose the Flask development port
EXPOSE 5000

# Default command
CMD ["python", "app.py"]
