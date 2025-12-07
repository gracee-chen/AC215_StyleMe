#!/bin/bash
# Setup GCP Authentication for downloading models

echo "🔐 Setting up GCP Authentication"
echo "================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found"
    echo ""
    echo "Please install Google Cloud SDK:"
    echo "  macOS: brew install --cask google-cloud-sdk"
    echo "  Or download from: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "Alternatively, you can use a service account key file:"
    echo "  1. Create a service account in GCP Console"
    echo "  2. Download the JSON key file"
    echo "  3. Set: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
    exit 1
fi

echo "✅ gcloud CLI found"
echo ""

# Check if already authenticated
if gcloud auth application-default print-access-token &> /dev/null; then
    echo "✅ Application Default Credentials already configured"
    echo ""
    echo "Current account:"
    gcloud auth list --filter=status:ACTIVE --format="value(account)"
    echo ""
    read -p "Do you want to re-authenticate? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing credentials"
        exit 0
    fi
fi

echo "🔑 Authenticating with GCP..."
echo "   This will open a browser window for authentication"
echo ""

gcloud auth application-default login

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Authentication successful!"
    echo ""
    echo "You can now download models using:"
    echo "  python3 scripts/download_model.py"
else
    echo ""
    echo "❌ Authentication failed"
    exit 1
fi

