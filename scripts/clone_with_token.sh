#!/bin/bash
# Clone repository using Personal Access Token

echo "=========================================="
echo "Clone Repository with Token"
echo "=========================================="
echo ""
echo "If you have a GitHub Personal Access Token, you can use it to clone:"
echo ""
echo "Usage:"
echo "  ./scripts/clone_with_token.sh <your_token>"
echo ""
echo "Or set it as environment variable:"
echo "  export GITHUB_TOKEN=your_token_here"
echo "  ./scripts/clone_with_token.sh"
echo ""

TOKEN="${1:-${GITHUB_TOKEN}}"

if [ -z "$TOKEN" ]; then
    echo "❌ No token provided"
    echo ""
    echo "To get a token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Generate new token (classic) with 'repo' scope"
    echo "3. Run: ./scripts/clone_with_token.sh <token>"
    exit 1
fi

REPO="gracee-chen/AC215_StyleMe"
TEMP_DIR="/tmp/ac215_clone_$$"
TARGET_DIR="$(pwd)"

echo "Cloning repository..."
git clone "https://${TOKEN}@github.com/${REPO}.git" "$TEMP_DIR" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Repository cloned successfully"
    echo ""
    
    # Copy ci directory
    if [ -d "$TEMP_DIR/ci" ]; then
        echo "📁 Copying ci/ directory..."
        if [ -d "$TARGET_DIR/ci" ]; then
            mv "$TARGET_DIR/ci" "$TARGET_DIR/ci.backup"
        fi
        cp -r "$TEMP_DIR/ci" "$TARGET_DIR/"
        echo "✅ ci/ copied"
    else
        echo "⚠️  ci/ directory not found"
    fi
    
    # Copy containers directory
    if [ -d "$TEMP_DIR/containers" ]; then
        echo "📁 Copying containers/ directory..."
        if [ -d "$TARGET_DIR/containers" ]; then
            echo "   Merging with existing containers/..."
            rsync -av --ignore-existing "$TEMP_DIR/containers/" "$TARGET_DIR/containers/" || \
            cp -r "$TEMP_DIR/containers"/* "$TARGET_DIR/containers/"
        else
            cp -r "$TEMP_DIR/containers" "$TARGET_DIR/"
        fi
        echo "✅ containers/ copied/merged"
    else
        echo "⚠️  containers/ directory not found"
    fi
    
    # Show what was found
    echo ""
    echo "Repository contents:"
    ls -la "$TEMP_DIR" | head -20
    
    # Cleanup
    echo ""
    echo "🧹 Cleaning up..."
    rm -rf "$TEMP_DIR"
    
    echo ""
    echo "=========================================="
    echo "✅ Done!"
    echo "=========================================="
else
    echo "❌ Clone failed"
    echo ""
    echo "Possible reasons:"
    echo "1. Invalid token"
    echo "2. Token doesn't have 'repo' scope"
    echo "3. Repository doesn't exist or you don't have access"
    echo "4. Repository path is incorrect"
    exit 1
fi

