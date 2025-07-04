# Enhanced Dremio Reporting Server Dockerfile with Java and PyODBC Support
FROM python:3.11-slim

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

# Set working directory
WORKDIR /app

# Install system dependencies including Java and ODBC support
RUN apt-get update && apt-get install -y \
    # Java Development Kit for JDBC driver support
    openjdk-11-jdk \
    openjdk-11-jre \
    # ODBC components for PyODBC
    unixodbc \
    unixodbc-dev \
    odbcinst \
    # Build tools and utilities
    build-essential \
    curl \
    wget \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Java and ODBC installation
RUN java -version && javac -version && echo "JAVA_HOME: $JAVA_HOME"
RUN odbcinst -j

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Install Dremio ODBC driver (uncomment to enable)
# Note: This requires the Dremio ODBC driver tar.gz file to be available
# COPY dremio-odbc-*.tar.gz /tmp/
# RUN cd /tmp && \
#     tar -xzf dremio-odbc-*.tar.gz && \
#     cd dremio-odbc-* && \
#     cp lib64/libdrillodbc64.so /usr/lib/x86_64-linux-gnu/ && \
#     echo '[Dremio ODBC Driver]\n\
# Description=Dremio ODBC Driver\n\
# Driver=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so\n\
# Setup=/usr/lib/x86_64-linux-gnu/libdrillodbc64.so\n\
# UsageCount=1' > /etc/odbcinst.ini && \
#     rm -rf /tmp/dremio-odbc-*

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dremio \
    && chown -R dremio:dremio /app
USER dremio

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py"]
