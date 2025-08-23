#!/bin/bash

# SA Shell Build and Upload Script
# This script builds both binaries and uploads the distribution package

set -e

echo "🚀 Building SA Shell Distribution Package..."

# Configuration
DIST_NAME="sa-shell"
VERSION="0.1.0"
UPLOAD_URL="https://zubatomic.com/upload"  # Adjust this to your actual upload endpoint

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec

# Build the startup.py binary (--onefile for distribution)
echo "📦 Building startup binary (--onefile)..."
./sa_env/bin/python -m PyInstaller --onefile --name sa-installer startup.py

# Build the shell binary (--onedir for fast startup)
echo "📦 Building shell binary (--onedir)..."
./sa_env/bin/python -m PyInstaller --onedir --name sa-shell-fast sa/shell/shell.py

# Create distribution directory
echo "📁 Creating distribution package..."
DIST_DIR="dist/${DIST_NAME}-${VERSION}"
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
cat > "$DIST_DIR/README.md" << 'EOF'
# SA Shell

A fast, interactive shell for the SA Query Language.

## Installation

### Option 1: Auto-installer (Recommended)
```bash
# Download and run the auto-installer
curl -L https://zubatomic.com/sa-installer | python3 -
```

### Option 2: Manual installation
```bash
# Extract this package
unzip sa-shell-0.1.0.zip

# Run the installer
cd sa-shell-0.1.0
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
EOF

# Create the zip file
echo "📦 Creating distribution zip..."
cd dist
zip -r "${DIST_NAME}-${VERSION}.zip" "${DIST_NAME}-${VERSION}/"
cd ..

echo "✅ Distribution package created: dist/${DIST_NAME}-${VERSION}.zip"

# Upload to zubatomic.com
echo "📤 Uploading to zubatomic.com..."
echo "📤 Uploading distribution package..."

# Upload the zip file
if scp "dist/${DIST_NAME}-${VERSION}.zip" "root@zubatomic.com:/var/www/html/sa.zip"; then
    echo "✅ Distribution package uploaded to zubatomic.com/sa.zip"
else
    echo "❌ Failed to upload distribution package"
    exit 1
fi

# Upload the installer binary
if scp "dist/sa-installer" "root@zubatomic.com:/var/www/html/sa-installer"; then
    echo "✅ Installer binary uploaded to zubatomic.com/sa-installer"
else
    echo "❌ Failed to upload installer binary"
    exit 1
fi

echo ""
echo "🎉 Upload complete! Users can now install with:"
echo "   curl -L https://zubatomic.com/sa-installer | python3 -"
echo ""
echo "📋 Files created and uploaded:"
echo "  📦 dist/sa-installer          ← Single binary for distribution"
echo "  📁 dist/sa-shell-fast/        ← Fast shell (--onedir)"
echo "  📦 dist/${DIST_NAME}-${VERSION}.zip  ← Distribution package"
echo "  🌐 zubatomic.com/sa.zip       ← Distribution package (served)"
echo "  🌐 zubatomic.com/sa-installer ← Installer binary (served)"
