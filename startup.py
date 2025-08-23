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
from pathlib import Path

# Configuration
DOWNLOAD_URL = "https://zubatomic.com/sa.zip"
INSTALL_DIR = Path.home() / ".sa" / "installation"
BIN_DIR = Path.home() / ".local" / "bin"
SHELL_NAME = "sa-shell"

def download_file(url, dest_path):
    """Download a file from URL to destination path."""
    print(f"📥 Downloading from {url}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Download complete: {dest_path}")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def extract_zip(zip_path, extract_dir):
    """Extract zip file to directory."""
    print(f"📦 Extracting to {extract_dir}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"✅ Extraction complete")
        return True
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def find_shell_executable(install_dir):
    """Find the shell executable in the extracted directory."""
    print(f"🔍 Searching for shell executable in: {install_dir}")
    
    # Look for the executable in the expected structure
    for root, dirs, files in os.walk(install_dir):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"  Checking: {file_path}")
            if file.startswith("sa-shell") and os.access(file_path, os.X_OK):
                print(f"✅ Found executable: {file_path}")
                return file_path
    
    # If not found, try to find any executable with sa-shell in the name
    for root, dirs, files in os.walk(install_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if "sa-shell" in file and os.access(file_path, os.X_OK):
                print(f"✅ Found executable (fallback): {file_path}")
                return file_path
    
    # If still not found, look for sa-shell files and make them executable
    for root, dirs, files in os.walk(install_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if "sa-shell" in file and not file.endswith('.so') and not file.endswith('.dylib') and not file.endswith('.zip'):
                print(f"🔧 Found potential shell file: {file_path}")
                # Make it executable
                try:
                    os.chmod(file_path, 0o755)
                    print(f"✅ Made executable: {file_path}")
                    return file_path
                except Exception as e:
                    print(f"⚠️  Could not make executable: {e}")
                    continue
    
    print("❌ No shell executable found")
    return None

def install_shell(install_dir):
    """Install the shell to ~/.local/bin."""
    print(f"🔧 Installing shell...")
    
    # Create bin directory if it doesn't exist
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find the shell executable
    shell_exec = find_shell_executable(install_dir)
    if not shell_exec:
        print("❌ Could not find shell executable")
        return False
    
    # Create wrapper script
    wrapper_script = BIN_DIR / SHELL_NAME
    wrapper_content = f"""#!/bin/bash
# SA Shell wrapper
exec "{shell_exec}" "$@"
"""
    
    with open(wrapper_script, 'w') as f:
        f.write(wrapper_content)
    
    # Make wrapper executable
    os.chmod(wrapper_script, 0o755)
    
    print(f"✅ Shell installed to {wrapper_script}")
    return True

def add_to_path():
    """Add ~/.local/bin to PATH if not already there."""
    shell_rc = Path.home() / ".zshrc"
    if not shell_rc.exists():
        shell_rc = Path.home() / ".bashrc"
    
    if not shell_rc.exists():
        print("⚠️  Could not find .zshrc or .bashrc, please add manually:")
        print(f"   export PATH=\"$HOME/.local/bin:$PATH\"")
        return
    
    # Check if already in PATH
    with open(shell_rc, 'r') as f:
        content = f.read()
    
    path_export = 'export PATH="$HOME/.local/bin:$PATH"'
    if path_export not in content:
        print(f"📝 Adding to {shell_rc}...")
        with open(shell_rc, 'a') as f:
            f.write(f"\n# SA Shell PATH addition\n{path_export}\n")
        print("✅ Added to PATH configuration")
    else:
        print("✅ PATH already configured")

def run_shell():
    """Run the shell with --help to warm it up."""
    print("🚀 Running shell for first time (this may be slow)...")
    
    try:
        # Add current session to PATH
        os.environ['PATH'] = f"{BIN_DIR}:{os.environ.get('PATH', '')}"
        
        # Run shell
        result = subprocess.run([SHELL_NAME, "--help"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Shell is working correctly!")
            print("🎯 You can now use 'sa-shell' from anywhere")
        else:
            print("⚠️  Shell ran but with errors")
            print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Shell startup timed out (this is normal for first run)")
    except Exception as e:
        print(f"❌ Error running shell: {e}")

def main():
    """Main installation process."""
    print("🚀 SA Shell Auto-Installer")
    print("=" * 40)
    
    # Clean up any existing installation
    if INSTALL_DIR.exists():
        print(f"🧹 Cleaning up existing installation...")
        shutil.rmtree(INSTALL_DIR)
    
    # Create fresh installation directory
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download the shell
    zip_path = INSTALL_DIR / "sa.zip"
    if not download_file(DOWNLOAD_URL, zip_path):
        sys.exit(1)
    
    # Extract the shell
    if not extract_zip(zip_path, INSTALL_DIR):
        sys.exit(1)
    
    # Install the shell
    if not install_shell(INSTALL_DIR):
        sys.exit(1)
    
    # Add to PATH
    add_to_path()
    
    # Clean up zip file
    zip_path.unlink()
    print("🧹 Cleaned up download file")
    
    # Run shell for first time
    run_shell()
    
    print("\n🎉 Installation complete!")
    print(f"📁 Shell installed to: {BIN_DIR / SHELL_NAME}")
    print(f"📁 Files location: {INSTALL_DIR}")
    print("\n💡 To use the shell in new terminals, restart your terminal or run:")
    zshrc_path = Path.home() / '.zshrc'
    bashrc_path = Path.home() / '.bashrc'
    if zshrc_path.exists():
        print(f"   source {zshrc_path}")
    elif bashrc_path.exists():
        print(f"   source {bashrc_path}")
    else:
        print("   # Add ~/.local/bin to your PATH manually")

if __name__ == "__main__":
    main()
