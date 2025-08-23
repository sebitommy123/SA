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

# Copy the sa-shell-dev directory to the install location
if [ -d "dist/sa-shell-dev" ]; then
    cp -r "dist/sa-shell-dev" "$INSTALL_DIR"
    echo "✅ Files copied successfully"
else
    echo "❌ Error: dist/sa-shell-dev not found. Run the build first!"
    exit 1
fi

# Create a simple sa-shell command
WRAPPER_SCRIPT="$BIN_DIR/sa-shell"
cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# Simple wrapper for SA Shell
exec "$HOME/.local/bin/sa-shell-files/sa-shell-dev" "$@"
EOF

# Make it executable
chmod +x "$BIN_DIR/sa-shell"

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
