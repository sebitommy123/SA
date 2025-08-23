#!/bin/bash

# Build script for SA Shell binary
echo "Building SA Shell binary with PyInstaller..."

# Clean up previous builds
rm -rf build dist sa-shell.spec

# Build the binary
pyinstaller --onefile --name sa-shell sa/shell/shell.py

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
