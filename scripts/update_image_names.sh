#!/bin/bash
# Script to update image names in Kubernetes manifests

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-styleme-475201}"
REGION="${GCP_REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-styleme-repo}"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

echo "🔄 Updating image names in Kubernetes manifests"
echo "================================================"
echo "Registry: $REGISTRY"
echo ""

# Update image names in all k8s YAML files
cd k8s

for file in *.yaml; do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        # Use sed to replace image names
        sed -i '' "s|styleme-ingestion:latest|${REGISTRY}/styleme-ingestion:latest|g" "$file"
        sed -i '' "s|styleme-preprocessing:latest|${REGISTRY}/styleme-preprocessing:latest|g" "$file"
        sed -i '' "s|styleme-training:latest|${REGISTRY}/styleme-training:latest|g" "$file"
        sed -i '' "s|styleme-inference:latest|${REGISTRY}/styleme-inference:latest|g" "$file"
        echo "✅ $file updated"
    fi
done

cd ..

echo ""
echo "================================================"
echo "✅ All manifests updated!"
echo "================================================"
echo ""
echo "Updated image paths:"
echo "  - ${REGISTRY}/styleme-ingestion:latest"
echo "  - ${REGISTRY}/styleme-preprocessing:latest"
echo "  - ${REGISTRY}/styleme-training:latest"
echo "  - ${REGISTRY}/styleme-inference:latest"

