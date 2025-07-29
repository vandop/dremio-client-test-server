#!/bin/bash
# Minimal setup script for GitHub Codespaces
# This runs if the main setup script is missing

echo "🔧 Running minimal Dremio Reporting Server setup..."

# Make scripts executable
chmod +x *.sh 2>/dev/null || true
chmod +x .devcontainer/*.sh 2>/dev/null || true

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Python dependencies installed"
    else
        echo "⚠️ Some Python dependencies may have failed"
    fi
else
    echo "⚠️ requirements.txt not found"
fi

# Create basic .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating basic .env file..."
    cat > .env << 'EOF'
# Dremio Configuration
# Fill these in through the web interface at http://localhost:5001/auth

# For Dremio Cloud:
# DREMIO_CLOUD_URL=https://api.dremio.cloud
# DREMIO_PROJECT_ID=your-project-id
# DREMIO_PAT=your-personal-access-token

# For Dremio Software:
# DREMIO_URL=https://your-dremio-server.com:9047
# DREMIO_USERNAME=your-username
# DREMIO_PASSWORD=your-password

# Server Configuration
FLASK_ENV=development
FLASK_DEBUG=true
EOF
    echo "✅ Basic .env file created"
fi

# Check Java installation
echo "☕ Checking Java installation..."
if command -v java >/dev/null 2>&1; then
    echo "✅ Java found: $(java -version 2>&1 | head -n1)"
    
    # Set JAVA_HOME if not set
    if [ -z "$JAVA_HOME" ]; then
        if [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
            export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
            echo "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> ~/.bashrc
        elif [ -d "/usr/lib/jvm/java-17-openjdk-arm64" ]; then
            export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-arm64"
            echo "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64" >> ~/.bashrc
        fi
        echo "✅ JAVA_HOME set to: $JAVA_HOME"
    fi
else
    echo "⚠️ Java not found - JDBC functionality may not work"
fi

# Create jdbc-drivers directory if it doesn't exist
if [ ! -d "jdbc-drivers" ]; then
    echo "📁 Creating jdbc-drivers directory..."
    mkdir -p jdbc-drivers
    echo "✅ jdbc-drivers directory created"
fi

# Test basic imports
echo "🧪 Testing Python imports..."
python3 -c "import flask; print('✅ Flask OK')" 2>/dev/null || echo "❌ Flask failed"
python3 -c "import pyarrow; print('✅ PyArrow OK')" 2>/dev/null || echo "❌ PyArrow failed"
python3 -c "import requests; print('✅ Requests OK')" 2>/dev/null || echo "❌ Requests failed"

echo ""
echo "🎉 Minimal setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Run: ./run.sh (to start the server)"
echo "  2. Open: http://localhost:5001 (in your browser)"
echo "  3. Configure: Your Dremio connection through the web interface"
echo ""
echo "🔧 For full setup, run: ./setup.sh"
echo "🐛 For diagnostics, run: ./debug_codespaces.sh"
