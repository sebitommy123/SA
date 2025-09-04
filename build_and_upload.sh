#!/bin/bash

# SA Shell Build and Upload Script
# This script builds both binaries and uploads the distribution package

set -e

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

echo "🚀 Building SA Shell Distribution Package for $PLATFORM..."

# Configuration
DIST_NAME="sa-shell"
VERSION="0.1.0"
UPLOAD_URL="https://zubatomic.com/upload"  # Adjust this to your actual upload endpoint

# Platform-specific naming
if [ "$PLATFORM" = "alma" ]; then
    PLATFORM_SUFFIX="-alma"
    PLATFORM_DISPLAY="Alma Linux"
else
    PLATFORM_SUFFIX="-mac"
    PLATFORM_DISPLAY="macOS"
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec

# Build based on platform
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
FROM --platform linux/amd64 ubuntu:20.04
RUN apt-get update && apt-get install -y python3 python3-pip python3-dev gcc
WORKDIR /app
COPY . .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install pyinstaller
RUN python3 -m PyInstaller --onefile --name sa-installer startup.py
RUN python3 -m PyInstaller --onedir --name sa-shell-fast sa/shell/shell.py
EOF
    
    # Build using Docker with platform specification
    echo "🐳 Building Docker image for x86_64..."
    docker build --platform linux/amd64 -f Dockerfile.build -t sa-builder .
    
    # Extract the built binaries
    echo "📦 Extracting built binaries..."
    docker run --rm -v "$(pwd)/dist:/output" sa-builder sh -c "cp -r dist/* /output/"
    
    # Clean up Dockerfile
    rm -f Dockerfile.build
    
    echo "✅ Alma Linux binaries built successfully"
else
    echo "📦 Building startup binary (--onefile) for macOS..."
    ./sa_env/bin/python -m PyInstaller --onefile --name sa-installer startup.py
    
    echo "📦 Building shell binary (--onedir) for macOS..."
    ./sa_env/bin/python -m PyInstaller --onedir --name sa-shell-fast sa/shell/shell.py
fi

# Create distribution directory
echo "📁 Creating distribution package..."
DIST_DIR="dist/${DIST_NAME}-${VERSION}${PLATFORM_SUFFIX}"
mkdir -p "$DIST_DIR"

# Copy the shell files to distribution
cp -r "dist/sa-shell-fast" "$DIST_DIR/"

# Create a simple install script
cat > "$DIST_DIR/install.sh" << 'EOF'
#!/bin/bash
# SA Shell Installer
# This script installs the SA Shell to ~/.local/bin for fast startup

set -e

echo "🚀 Installing SA Shell..."

# Determine installation directory
INSTALL_DIR="$HOME/.local/bin/sa-shell-files"
BIN_DIR="$HOME/.local/bin"

# Create directories if they don't exist
mkdir -p "$BIN_DIR"

echo "📁 Installing to: $INSTALL_DIR"

# Remove existing installation if it exists
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "🗑️  Removed existing installation"
fi

# Copy the shell files to the install location
cp -r "sa-shell-fast" "$INSTALL_DIR"
echo "✅ Files copied successfully"

# Create a simple sa-shell command
WRAPPER_SCRIPT="$BIN_DIR/sa-shell"
cat > "$WRAPPER_SCRIPT" << 'INNER_EOF'
#!/bin/bash
# SA Shell wrapper
exec "$HOME/.local/bin/sa-shell-files/sa-shell-fast" "$@"
INNER_EOF

# Make wrapper executable
chmod +x "$WRAPPER_SCRIPT"

echo "✅ Installation complete!"
echo ""
echo "🎯 Usage:"
echo "  sa-shell                    # Start interactive shell"
echo "  sa-shell --help            # Show help"
echo "  sa-shell -q '.count()'     # Run a query"
echo ""
echo "📁 Files installed to: $INSTALL_DIR"
echo "🔗 Command available at: $BIN_DIR/sa-shell"
echo ""
echo "💡 Note: Make sure ~/.local/bin is in your PATH:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "  # Add this to your ~/.zshrc or ~/.bashrc"
EOF

chmod +x "$DIST_DIR/install.sh"

# Create README
cat > "$DIST_DIR/README.md" << EOF
# SA Shell

A fast, interactive shell for the SA Query Language.

## Platform: $PLATFORM_DISPLAY

## Installation

### Option 1: Auto-installer (Recommended)
```bash
# Download and run the auto-installer for $PLATFORM_DISPLAY
curl -L https://zubatomic.com/sa-installer$PLATFORM_SUFFIX -o sa-installer
chmod +x sa-installer
./sa-installer
```

### Option 2: Manual installation
```bash
# Extract this package
unzip sa-shell-${VERSION}${PLATFORM_SUFFIX}.zip

# Run the installer
cd sa-shell-${VERSION}${PLATFORM_SUFFIX}
./install.sh
```

## Usage
```bash
sa-shell                    # Start interactive shell
sa-shell --help            # Show help
sa-shell -q '.count()'     # Run a query
```

## Features
- **Fast startup**: 0.14 seconds after first run
- **Interactive mode**: Full-featured shell
- **Query mode**: Run single queries
- **Provider support**: Connect to data providers

## Requirements
- Python 3.8+ (for auto-installer)
- ~/.local/bin in PATH
- Compatible with $PLATFORM_DISPLAY
EOF

# Create the zip file
echo "📦 Creating distribution zip..."
cd dist
zip -r "${DIST_NAME}-${VERSION}${PLATFORM_SUFFIX}.zip" "${DIST_NAME}-${VERSION}${PLATFORM_SUFFIX}/"
cd ..

echo "✅ Distribution package created: dist/${DIST_NAME}-${VERSION}${PLATFORM_SUFFIX}.zip"

# Upload to zubatomic.com
echo "📤 Uploading to zubatomic.com..."
echo "📤 Uploading distribution package..."

# Upload the zip file
if scp "dist/${DIST_NAME}-${VERSION}${PLATFORM_SUFFIX}.zip" "root@zubatomic.com:/var/www/html/sa${PLATFORM_SUFFIX}.zip"; then
    echo "✅ Distribution package uploaded to zubatomic.com/sa${PLATFORM_SUFFIX}.zip"
else
    echo "❌ Failed to upload distribution package"
    exit 1
fi

# Upload the installer binary
if scp "dist/sa-installer" "root@zubatomic.com:/var/www/html/sa-installer${PLATFORM_SUFFIX}"; then
    echo "✅ Installer binary uploaded to zubatomic.com/sa-installer${PLATFORM_SUFFIX}"
else
    echo "❌ Failed to upload installer binary"
    exit 1
fi

echo ""
echo "🎉 Upload complete! Users can now install with:"
echo "   curl -L https://zubatomic.com/sa-installer${PLATFORM_SUFFIX} -o sa-installer && chmod +x sa-installer && ./sa-installer"
echo ""
echo "📋 Files created and uploaded:"
echo "  📦 dist/sa-installer          ← Single binary for distribution"
echo "  📁 dist/sa-shell-fast/        ← Fast shell (--onedir)"
echo "  📦 dist/${DIST_NAME}-${VERSION}${PLATFORM_SUFFIX}.zip  ← Distribution package"
echo "  🌐 zubatomic.com/sa${PLATFORM_SUFFIX}.zip       ← Distribution package (served)"
echo "  🌐 zubatomic.com/sa-installer${PLATFORM_SUFFIX} ← Installer binary (served)"
