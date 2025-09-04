#!/bin/bash

# Build script to run on Alma Linux
set -e

echo "🔨 Building SA Shell on Alma Linux..."

# Install dependencies
echo "📦 Installing dependencies..."
sudo dnf update -y
sudo dnf install -y python3 python3-pip python3-devel gcc

# Install PyInstaller
python3 -m pip install --user pyinstaller

# Install requirements
python3 -m pip install --user -r requirements.txt

# Build binaries
echo "🔨 Building binaries..."
python3 -m PyInstaller --onefile --name sa-installer startup.py
python3 -m PyInstaller --onedir --name sa-shell-fast sa/shell/shell.py

# Verify build
echo "✅ Build complete!"
file dist/sa-installer
echo "Binary type: $(file dist/sa-installer)"

# Create distribution
echo "📦 Creating distribution package..."
mkdir -p sa-shell-0.1.0-alma
cp -r dist/sa-shell-fast sa-shell-0.1.0-alma/

# Create install script
cat > sa-shell-0.1.0-alma/install.sh << 'INNER_EOF'
#!/bin/bash
set -e
echo "🚀 Installing SA Shell..."
INSTALL_DIR="$HOME/.local/bin/sa-shell-files"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
fi
cp -r "sa-shell-fast" "$INSTALL_DIR"
WRAPPER_SCRIPT="$BIN_DIR/sa-shell"
cat > "$WRAPPER_SCRIPT" << 'WRAPPER_EOF'
#!/bin/bash
exec "$HOME/.local/bin/sa-shell-files/sa-shell-fast" "$@"
WRAPPER_EOF
chmod +x "$WRAPPER_SCRIPT"
echo "✅ Installation complete!"
echo "Usage: sa-shell"
INNER_EOF

chmod +x sa-shell-0.1.0-alma/install.sh

# Create zip
zip -r sa-shell-0.1.0-alma.zip sa-shell-0.1.0-alma/

echo ""
echo "🎉 Build complete!"
echo "📦 Files created:"
echo "  📦 dist/sa-installer"
echo "  📁 dist/sa-shell-fast/"
echo "  📦 sa-shell-0.1.0-alma.zip"
echo ""
echo "📤 Uploading to zubatomic.com..."
scp sa-shell-0.1.0-alma.zip root@zubatomic.com:/var/www/html/sa-alma.zip
scp dist/sa-installer root@zubatomic.com:/var/www/html/sa-installer-alma
echo "✅ Upload complete!"
echo ""
echo "🌐 Available at:"
echo "  https://zubatomic.com/sa-alma.zip"
echo "  https://zubatomic.com/sa-installer-alma"
