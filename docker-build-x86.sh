#!/bin/bash

# Enhanced Dremio Reporting Server Docker Build Script
# Forces x86_64 architecture for ODBC driver compatibility

set -e  # Exit on any error

echo "🐳 Enhanced Dremio Reporting Server - x86_64 Docker Build"
echo "=========================================================="

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

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

print_status "Docker is available"

# Check if Docker Buildx is available (for multi-platform builds)
if ! docker buildx version &> /dev/null; then
    print_warning "Docker Buildx not available, using standard docker build"
    USE_BUILDX=false
else
    print_status "Docker Buildx is available"
    USE_BUILDX=true
fi

# Set image name and tag
IMAGE_NAME="dremio-reporting-server"
IMAGE_TAG="x86_64-latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

print_info "Building image: $FULL_IMAGE_NAME"
print_info "Target architecture: linux/amd64 (x86_64)"

# Build the Docker image with forced x86_64 architecture
if [ "$USE_BUILDX" = true ]; then
    print_info "Using Docker Buildx for multi-platform build..."
    
    # Create and use a new builder instance if it doesn't exist
    if ! docker buildx ls | grep -q "dremio-builder"; then
        print_info "Creating new buildx builder instance..."
        docker buildx create --name dremio-builder --use
    else
        print_info "Using existing buildx builder instance..."
        docker buildx use dremio-builder
    fi
    
    # Build with buildx
    docker buildx build \
        --platform linux/amd64 \
        --file .devcontainer/Dockerfile \
        --tag "$FULL_IMAGE_NAME" \
        --load \
        .
else
    print_info "Using standard docker build with platform flag..."
    
    # Build with standard docker build
    docker build \
        --platform linux/amd64 \
        --file .devcontainer/Dockerfile \
        --tag "$FULL_IMAGE_NAME" \
        .
fi

if [ $? -eq 0 ]; then
    print_status "Docker image built successfully!"
    
    # Show image information
    print_info "Image details:"
    docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Test the image architecture
    print_info "Verifying image architecture..."
    ARCH=$(docker run --rm --platform linux/amd64 "$FULL_IMAGE_NAME" uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        print_status "Image architecture verified: $ARCH"
    else
        print_warning "Unexpected architecture: $ARCH (expected x86_64)"
    fi
    
    echo ""
    print_status "Build completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "  1. Run with: docker run -p 5000:5000 $FULL_IMAGE_NAME"
    echo "  2. Or use: docker-compose up"
    echo "  3. Test ODBC: curl http://localhost:5000/api/drivers"
    echo ""
    print_info "The container will run on x86_64 architecture with:"
    echo "  ✅ Java 11 (OpenJDK) for JDBC support"
    echo "  ✅ unixODBC driver manager"
    echo "  ✅ Dremio Arrow Flight SQL ODBC driver (automatically installed)"
    echo "  ✅ PyODBC Python package"
    echo "  ✅ All Python dependencies"
    
else
    print_error "Docker build failed!"
    exit 1
fi
