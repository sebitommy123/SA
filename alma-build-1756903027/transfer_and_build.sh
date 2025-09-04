#!/bin/bash

# Script to transfer and build on Alma Linux
# Usage: ./transfer_and_build.sh user@your-alma-server

if [ -z "$1" ]; then
    echo "Usage: $0 user@your-alma-server"
    exit 1
fi

SERVER="$1"
echo "🚀 Transferring files to $SERVER..."

# Transfer the build directory
scp -r . "$SERVER:/tmp/sa-build/"

echo "🔨 Building on remote server..."
ssh "$SERVER" "cd /tmp/sa-build && ./build.sh"

echo "✅ Build complete on remote server!"
echo "📁 Files are in /tmp/sa-build/ on the remote server"
