#!/bin/bash
# Script to fetch ci and containers directories from GitHub repository

set -e

REPO_URL="https://github.com/gracee-chen/AC215_StyleMe.git"
TEMP_DIR="/tmp/ac215_fetch_$$"
TARGET_DIR="$(pwd)"

echo "=========================================="
echo "Fetching ci and containers from GitHub"
echo "=========================================="
echo "Repository: $REPO_URL"
echo "Target directory: $TARGET_DIR"
echo ""

# Create temporary directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Try different methods to clone
echo "Attempting to clone repository..."

# Method 1: Try with sparse checkout (if supported)
if git clone --filter=blob:none --sparse "$REPO_URL" repo 2>/dev/null; then
    cd repo
    git sparse-checkout set ci containers
    echo "✅ Successfully cloned with sparse checkout"
elif git clone --depth 1 "$REPO_URL" repo 2>/dev/null; then
    cd repo
    echo "✅ Successfully cloned repository"
else
    echo "❌ Failed to clone repository"
    echo ""
    echo "Please try one of the following:"
    echo ""
    echo "Option 1: If you have SSH access:"
    echo "  git clone git@github.com:gracee-chen/AC215_StyleMe.git $TEMP_DIR/repo"
    echo ""
    echo "Option 2: If you have a personal access token:"
    echo "  git clone https://<token>@github.com/gracee-chen/AC215_StyleMe.git $TEMP_DIR/repo"
    echo ""
    echo "Option 3: Manual download:"
    echo "  1. Go to https://github.com/gracee-chen/AC215_StyleMe"
    echo "  2. Download the repository as ZIP"
    echo "  3. Extract ci/ and containers/ directories"
    echo ""
    exit 1
fi

# Check if directories exist
if [ ! -d "ci" ] && [ ! -d "containers" ]; then
    echo "❌ Neither 'ci' nor 'containers' directories found in repository"
    echo "Available directories:"
    ls -la
    exit 1
fi

# Copy ci directory if it exists
if [ -d "ci" ]; then
    echo ""
    echo "📁 Copying ci/ directory..."
    if [ -d "$TARGET_DIR/ci" ]; then
        echo "⚠️  ci/ already exists in target. Backing up to ci.backup"
        mv "$TARGET_DIR/ci" "$TARGET_DIR/ci.backup"
    fi
    cp -r ci "$TARGET_DIR/"
    echo "✅ ci/ copied successfully"
fi

# Copy containers directory if it exists
if [ -d "containers" ]; then
    echo ""
    echo "📁 Copying containers/ directory..."
    if [ -d "$TARGET_DIR/containers" ]; then
        echo "⚠️  containers/ already exists in target."
        echo "   Merging with existing containers/..."
        # Copy files that don't exist or are newer
        rsync -av --ignore-existing containers/ "$TARGET_DIR/containers/" || cp -r containers/* "$TARGET_DIR/containers/"
        echo "✅ containers/ merged successfully"
    else
        cp -r containers "$TARGET_DIR/"
        echo "✅ containers/ copied successfully"
    fi
fi

# Cleanup
cd "$TARGET_DIR"
rm -rf "$TEMP_DIR"

echo ""
echo "=========================================="
echo "✅ Done!"
echo "=========================================="
echo "Directories copied to: $TARGET_DIR"
if [ -d "ci" ]; then
    echo "  - ci/"
fi
if [ -d "containers" ]; then
    echo "  - containers/"
fi

