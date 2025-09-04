#!/bin/bash

# Build script for SA Shell binary
# Usage: ./build_binary.sh [--platform mac|alma]

# Parse command line arguments
PLATFORM=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--platform mac|alma]"
            echo "  --platform mac   Build for macOS (default)"
            echo "  --platform alma  Build for Alma Linux"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set default platform to mac if not specified
if [ -z "$PLATFORM" ]; then
    PLATFORM="mac"
fi

# Validate platform
if [ "$PLATFORM" != "mac" ] && [ "$PLATFORM" != "alma" ]; then
    echo "❌ Invalid platform: $PLATFORM"
    echo "Valid platforms: mac, alma"
    exit 1
fi

echo "Building SA Shell binary with PyInstaller for $PLATFORM..."

# Clean up previous builds
rm -rf build dist sa-shell.spec

# Build the binary with platform-specific options
if [ "$PLATFORM" = "alma" ]; then
    echo "📦 Building for Alma Linux using Docker..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is required to build for Alma Linux from macOS"
        echo "Please install Docker and try again"
        exit 1
    fi
    
    # Check if Docker daemon is running, if not try to start Colima
    if ! docker info &> /dev/null; then
        echo "🐳 Docker daemon not running, attempting to start Colima..."
        
        # Check if Colima is installed
        if command -v colima &> /dev/null; then
            echo "🚀 Starting Colima..."
            colima start
            echo "✅ Colima started successfully"
        else
            echo "❌ Colima not found. Installing Colima..."
            if command -v brew &> /dev/null; then
                brew install colima
                echo "🚀 Starting Colima..."
                colima start
                echo "✅ Colima installed and started successfully"
            else
                echo "❌ Homebrew not found. Please install Colima manually:"
                echo "   brew install colima"
                echo "   colima start"
                exit 1
            fi
        fi
        
        # Verify Docker is now working
        if ! docker info &> /dev/null; then
            echo "❌ Failed to start Docker daemon. Please check your Docker/Colima installation."
            exit 1
        fi
    else
        echo "✅ Docker daemon is running"
    fi
    
    # Create a temporary Dockerfile for building
    cat > Dockerfile.build << 'EOF'
FROM --platform linux/amd64 almalinux:9
RUN dnf update -y && dnf install -y python3 python3-pip python3-devel gcc
WORKDIR /app
COPY . .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install pyinstaller
RUN python3 -m PyInstaller --onefile --name sa-shell sa/shell/shell.py
EOF
    
    # Build using Docker
    echo "🐳 Building Docker image..."
    docker build -f Dockerfile.build -t sa-builder .
    
    # Extract the built binary
    echo "📦 Extracting built binary..."
    docker run --rm -v "$(pwd)/dist:/output" sa-builder sh -c "cp -r dist/* /output/"
    
    # Clean up Dockerfile
    rm -f Dockerfile.build
    
    echo "✅ Alma Linux binary built successfully"
else
    echo "📦 Building for macOS..."
    pyinstaller --onefile --name sa-shell sa/shell/shell.py
fi

# Check if build was successful
if [ -f "dist/sa-shell" ]; then
    echo "✅ Build successful! Binary created at dist/sa-shell"
    echo "📏 Binary size: $(du -h dist/sa-shell | cut -f1)"
    echo "🚀 You can now run: ./dist/sa-shell"
else
    echo "❌ Build failed!"
    exit 1
fi

# Clean up build artifacts (keep only the binary)
rm -rf build sa-shell.spec
echo "🧹 Build artifacts cleaned up"
