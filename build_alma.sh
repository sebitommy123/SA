#!/bin/bash

# SA Shell Build Script for Alma Linux
# Builds on zubatomic.com (x86_64) and uploads the results

set -e

echo "🚀 Building SA Shell for Alma Linux on zubatomic.com..."

# Create temporary build directory
BUILD_DIR="/tmp/sa-build-$(date +%s)"
mkdir -p "$BUILD_DIR"

# Copy source files to build directory
echo "📁 Copying source files..."
cp -r sa/ "$BUILD_DIR/"
cp requirements.txt "$BUILD_DIR/"

# Auto-increment version number in shell.py
echo "🔢 Auto-incrementing version number..."

# First, check if the main source file has a VERSION
SOURCE_SHELL_PY="sa/shell/shell.py"
if [ -f "$SOURCE_SHELL_PY" ]; then
    # Extract current version number from source
    CURRENT_VERSION=$(grep -o 'VERSION = [0-9]\+' "$SOURCE_SHELL_PY" | grep -o '[0-9]\+')
    if [ -z "$CURRENT_VERSION" ]; then
        CURRENT_VERSION=0
        # Add VERSION line if it doesn't exist
        echo "VERSION = 0" >> "$SOURCE_SHELL_PY"
    fi
    
    # Increment version
    NEW_VERSION=$((CURRENT_VERSION + 1))
    echo "📈 Version: $CURRENT_VERSION → $NEW_VERSION"
    
    # Update the version in the source file
    sed -i '' "s/VERSION = [0-9]*/VERSION = $NEW_VERSION/" "$SOURCE_SHELL_PY"
    
    # Verify the change in source
    echo "✅ Updated version in source $SOURCE_SHELL_PY:"
    grep "VERSION = " "$SOURCE_SHELL_PY"
else
    echo "⚠️  Warning: Source shell.py not found, starting with version 1"
    NEW_VERSION=1
fi

# Also update the copied file in build directory
SHELL_PY="$BUILD_DIR/shell/shell.py"
if [ -f "$SHELL_PY" ]; then
    # Update the version in the copied file
    sed -i '' "s/VERSION = [0-9]*/VERSION = $NEW_VERSION/" "$SHELL_PY"
    
    # Verify the change
    echo "✅ Updated version in build $SHELL_PY:"
    grep "VERSION = " "$SHELL_PY"
else
    echo "⚠️  Warning: Build shell.py not found, skipping version increment"
fi

# Create Python 3.5 compatible startup.py
cat > "$BUILD_DIR/startup.py" << 'EOF'
#!/usr/bin/env python3
"""
SA Shell Auto-Installer

This script downloads the SA Shell from zubatomic.com, installs it,
and ensures it's available in PATH.
"""

import os
import sys
import zipfile
import requests
import subprocess
import shutil

# PyInstaller detection
def is_pyinstaller_binary():
    """Check if this script is running as a PyInstaller binary."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_binary_path():
    """Get the path to the current binary (works for both script and PyInstaller binary)."""
    if is_pyinstaller_binary():
        return sys.executable
    else:
        return os.path.abspath(__file__)

def copy_binary_to_sa_dir():
    """Copy the current binary to ~/.sa/sa-installer for future use."""
    # Only copy if we're running as a PyInstaller binary
    if not is_pyinstaller_binary():
        print("ℹ️  Skipping installer copy (not running as PyInstaller binary)")
        return True
    
    print("📋 Copying installer to ~/.sa/sa-installer...")
    
    # Create ~/.sa directory if it doesn't exist
    sa_dir = os.path.expanduser("~/.sa")
    if not os.path.exists(sa_dir):
        os.makedirs(sa_dir)
    
    # Get the current binary path
    binary_path = get_binary_path()
    target_path = os.path.join(sa_dir, "sa-installer")
    
    try:
        # Copy the binary
        shutil.copy2(binary_path, target_path)
        
        # Make it executable
        os.chmod(target_path, 0o755)
        
        print("✅ Installer copied to: {}".format(target_path))
        print("💡 You can now run: ~/.sa/sa-installer")
        return True
        
    except Exception as e:
        print("❌ Failed to copy installer: {}".format(e))
        return False

# Configuration
DOWNLOAD_URL = "https://zubatomic.com/sa-alma.tar.gz"
INSTALL_DIR = os.path.expanduser("~/.sa/installation")
BIN_DIR = os.path.expanduser("~/.local/bin")
SHELL_NAME = "sa-shell"

def download_file(url, dest_path):
    """Download a file from URL to destination path."""
    print("📥 Downloading from {}...".format(url))
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("✅ Download complete: {}".format(dest_path))
        return True
        
    except Exception as e:
        print("❌ Download failed: {}".format(e))
        return False

def extract_archive(archive_path, extract_dir):
    """Extract archive file to directory."""
    print("📦 Extracting to {}...".format(extract_dir))
    
    try:
        if archive_path.endswith('.tar.gz'):
            import tarfile
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_dir)
        elif archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            print("❌ Unsupported archive format")
            return False
        
        print("✅ Extraction complete")
        return True
        
    except Exception as e:
        print("❌ Extraction failed: {}".format(e))
        return False

def find_shell_executable(install_dir):
    """Find the shell executable in the extracted directory."""
    print("🔍 Searching for shell executable in: {}".format(install_dir))
    
    # Look for the executable in the expected structure
    for root, dirs, files in os.walk(install_dir):
        for file in files:
            file_path = os.path.join(root, file)
            print("  Checking: {}".format(file_path))
            if file.startswith("sa-shell") and os.access(file_path, os.X_OK):
                print("✅ Found executable: {}".format(file_path))
                return file_path
    
    # If not found, try to find any executable with sa-shell in the name
    for root, dirs, files in os.walk(install_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if "sa-shell" in file and os.access(file_path, os.X_OK):
                print("✅ Found executable (fallback): {}".format(file_path))
                return file_path
    
    # If still not found, look for sa-shell files and make them executable
    for root, dirs, files in os.walk(install_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if "sa-shell" in file and not file.endswith('.so') and not file.endswith('.dylib') and not file.endswith('.zip'):
                print("🔧 Found potential shell file: {}".format(file_path))
                # Make it executable
                try:
                    os.chmod(file_path, 0o755)
                    print("✅ Made executable: {}".format(file_path))
                    return file_path
                except Exception as e:
                    print("⚠️  Could not make executable: {}".format(e))
                    continue
    
    print("❌ No shell executable found")
    return None

def install_shell(install_dir):
    """Install the shell to ~/.local/bin."""
    print("🔧 Installing shell...")
    
    # Create bin directory if it doesn't exist
    if not os.path.exists(BIN_DIR):
        os.makedirs(BIN_DIR)
    
    # Find the shell executable
    shell_exec = find_shell_executable(install_dir)
    if not shell_exec:
        print("❌ Could not find shell executable")
        return False
    
    # Create wrapper script
    wrapper_script = os.path.join(BIN_DIR, SHELL_NAME)
    wrapper_content = """#!/bin/bash
# SA Shell wrapper
exec "{}" "$@"
""".format(shell_exec)
    
    with open(wrapper_script, 'w') as f:
        f.write(wrapper_content)
    
    # Make wrapper executable
    os.chmod(wrapper_script, 0o755)
    
    print("✅ Shell installed to {}".format(wrapper_script))
    return True

def add_to_path():
    """Add ~/.local/bin to PATH if not already there."""
    home_dir = os.path.expanduser("~")
    shell_rc = os.path.join(home_dir, ".bashrc")
    if not os.path.exists(shell_rc):
        shell_rc = os.path.join(home_dir, ".zshrc")
    
    if not os.path.exists(shell_rc):
        print("⚠️  Could not find .bashrc or .zshrc, please add manually:")
        print("   export PATH=\"$HOME/.local/bin:$PATH\"")
        return
    
    # Check if already in PATH
    with open(shell_rc, 'r') as f:
        content = f.read()
    
    path_export = 'export PATH="$HOME/.local/bin:$PATH"'
    if path_export not in content:
        print("📝 Adding to {}...".format(shell_rc))
        with open(shell_rc, 'a') as f:
            f.write("\n# SA Shell PATH addition\n{}\n".format(path_export))
        print("✅ Added to PATH configuration")
    else:
        print("✅ PATH already configured")

def run_shell():
    """Run the shell with --help to warm it up."""
    print("🚀 Running shell for first time (this may be slow)...")
    
    try:
        # Add current session to PATH
        os.environ['PATH'] = "{}:{}".format(BIN_DIR, os.environ.get('PATH', ''))
        
        # Run shell
        result = subprocess.run([SHELL_NAME, "--help"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Shell is working correctly!")
            print("🎯 You can now use 'sa-shell' from anywhere")
        else:
            print("⚠️  Shell ran but with errors")
            print("Error: {}".format(result.stderr))
            
    except subprocess.TimeoutExpired:
        print("⚠️  Shell startup timed out (this is normal for first run)")
    except Exception as e:
        print("❌ Error running shell: {}".format(e))

def main():
    """Main installation process."""
    print("🚀 SA Shell Auto-Installer")
    print("=" * 40)
    
    # Clean up any existing installation
    install_dir_str = str(INSTALL_DIR)
    if os.path.exists(install_dir_str):
        print("🧹 Cleaning up existing installation...")
        shutil.rmtree(install_dir_str)
    
    # Create fresh installation directory
    if not os.path.exists(install_dir_str):
        os.makedirs(install_dir_str)
    
    # Download the shell
    archive_path = os.path.join(install_dir_str, "sa.tar.gz")
    if not download_file(DOWNLOAD_URL, archive_path):
        sys.exit(1)
    
    # Extract the shell
    if not extract_archive(archive_path, install_dir_str):
        sys.exit(1)
    
    # Install the shell
    if not install_shell(install_dir_str):
        sys.exit(1)
    
    # Add to PATH
    add_to_path()
    
    # Copy installer binary to ~/.sa for future use
    copy_binary_to_sa_dir()
    
    # Clean up archive file
    os.unlink(archive_path)
    print("🧹 Cleaned up download file")
    
    # Run shell for first time
    run_shell()
    
    print("\n🎉 Installation complete!")
    print("📁 Shell installed to: {}".format(os.path.join(str(BIN_DIR), SHELL_NAME)))
    print("📁 Files location: {}".format(install_dir_str))
    print("📁 Installer copied to: {}".format(os.path.join(os.path.expanduser("~"), ".sa", "sa-installer")))
    print("\n💡 To use the shell in new terminals, restart your terminal or run:")
    home_dir = os.path.expanduser("~")
    zshrc_path = os.path.join(home_dir, '.zshrc')
    bashrc_path = os.path.join(home_dir, '.bashrc')
    if os.path.exists(zshrc_path):
        print("   source {}".format(zshrc_path))
    elif os.path.exists(bashrc_path):
        print("   source {}".format(bashrc_path))
    else:
        print("   # Add ~/.local/bin to your PATH manually")

if __name__ == "__main__":
    main()
EOF

# Transfer to zubatomic.com
echo "📤 Transferring to zubatomic.com..."
scp -r "$BUILD_DIR" root@zubatomic.com:/tmp/

# Build on zubatomic.com
echo "🔨 Building on zubatomic.com..."
ssh root@zubatomic.com << EOF
cd $BUILD_DIR

# Install dependencies
echo "📦 Installing dependencies..."
apt-get update
apt-get install -y python3-pip python3-dev gcc zip

# Install PyInstaller
python3 -m pip install pyinstaller

# Install requirements for Python 3.9
/usr/local/python3.9/bin/python3.9 -m pip install -r requirements.txt

# Build binaries
echo "🔨 Building binaries..."
/usr/local/python3.9/bin/python3.9 -m PyInstaller --onefile --name sa-installer startup.py
# Create proper sa module structure
mkdir -p sa
cp -r query_language sa/
cp -r core sa/
cp -r shell sa/

/usr/local/python3.9/bin/python3.9 -m PyInstaller --onedir --name sa-shell-fast --add-data "./sa:sa" ./shell/shell.py

# Verify build
echo "✅ Build complete!"
file dist/sa-installer[]
echo "Binary type: \$(file dist/sa-installer)"

# Create distribution package
echo "📦 Creating distribution package..."
mkdir -p sa-shell-0.1.0-alma
cp -r dist/sa-shell-fast sa-shell-0.1.0-alma/

# Create install script
cat > sa-shell-0.1.0-alma/install.sh << 'INNER_EOF'
#!/bin/bash
set -e
echo "🚀 Installing SA Shell..."
INSTALL_DIR="\$HOME/.local/bin/sa-shell-files"
BIN_DIR="\$HOME/.local/bin"
mkdir -p "\$BIN_DIR"
if [ -d "\$INSTALL_DIR" ]; then
    rm -rf "\$INSTALL_DIR"
fi
cp -r "sa-shell-fast" "\$INSTALL_DIR"
WRAPPER_SCRIPT="\$BIN_DIR/sa-shell"
cat > "\$WRAPPER_SCRIPT" << 'WRAPPER_EOF'
#!/bin/bash
exec "\$HOME/.local/bin/sa-shell-files/sa-shell-fast" "\$@"
WRAPPER_EOF
chmod +x "\$WRAPPER_SCRIPT"
echo "✅ Installation complete!"
echo "Usage: sa-shell"
INNER_EOF

chmod +x sa-shell-0.1.0-alma/install.sh

# Create tar package
tar -czf sa-shell-0.1.0-alma.tar.gz sa-shell-0.1.0-alma/

echo ""
echo "🎉 Build complete!"
echo "📦 Files created:"
echo "  📦 dist/sa-installer"
echo "  📁 dist/sa-shell-fast/"
echo "  📦 sa-shell-0.1.0-alma.tar.gz"
EOF

# Download the built files
echo "📥 Downloading built files..."
scp root@zubatomic.com:"$BUILD_DIR/dist/sa-installer" ./dist/
scp root@zubatomic.com:"$BUILD_DIR/sa-shell-0.1.0-alma.tar.gz" ./

# Upload to web server
echo "📤 Uploading to zubatomic.com web server..."
scp ./dist/sa-installer root@zubatomic.com:/var/www/html/sa-installer-alma
scp ./sa-shell-0.1.0-alma.tar.gz root@zubatomic.com:/var/www/html/sa-alma.tar.gz

# Clean up
echo "🧹 Cleaning up..."
rm -rf "$BUILD_DIR"
ssh root@zubatomic.com "rm -rf $BUILD_DIR"

echo ""
echo "✅ Build and upload complete!"
echo "🌐 Available at:"
echo "  https://zubatomic.com/sa-alma.tar.gz"
echo "  https://zubatomic.com/sa-installer-alma"
echo ""
echo "📋 Installation command:"
echo "  curl -L https://zubatomic.com/sa-installer-alma -o sa-installer && chmod +x sa-installer && ./sa-installer"
