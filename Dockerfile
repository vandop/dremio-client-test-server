# Enhanced Dremio Reporting Server Dockerfile with Java Support
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Set working directory
WORKDIR /app

# Install system dependencies including Java
RUN apt-get update && apt-get install -y \
    # Java Development Kit for JDBC driver support
    openjdk-11-jdk \
    openjdk-11-jre \
    # Build tools and utilities
    build-essential \
    curl \
    wget \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Java installation
RUN java -version && javac -version && echo "JAVA_HOME: $JAVA_HOME"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
