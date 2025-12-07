#!/bin/bash
# Script to build and push all StyleMe Docker images to GCR

set -e  # Exit on error

# Configuration
PROJECT_ID="styleme-475201"
REGION="us-central1"
REPO_NAME="styleme-repo"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

echo "🏗️  Building and pushing StyleMe Docker images"
echo "================================================"
echo "Registry: $REGISTRY"
echo ""

# Enable Artifact Registry API (if not already enabled)
echo "📋 Enabling Artifact Registry API..."
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID 2>&1 || echo "API may already be enabled"

# Create repository if it doesn't exist
echo "📦 Checking Artifact Registry repository..."
gcloud artifacts repositories create ${REPO_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --project=${PROJECT_ID} 2>&1 || echo "Repository may already exist"

# Configure Docker to use gcloud as credential helper
echo "🔐 Configuring Docker credentials..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build and push each image
IMAGES=(
    "ingestion:containers/ingestion/Dockerfile"
    "preprocessing:containers/preprocessing/Dockerfile"
    "training:containers/training/Dockerfile"
    "inference:containers/inference/Dockerfile"
)

for image_spec in "${IMAGES[@]}"; do
    IFS=':' read -r image_name dockerfile <<< "$image_spec"
    full_image_name="${REGISTRY}/styleme-${image_name}:latest"
    
    echo ""
    echo "🔨 Building ${image_name} (linux/amd64)..."
    docker build --platform linux/amd64 -f "$dockerfile" -t "$full_image_name" .
    
    echo "📤 Pushing ${image_name}..."
    docker push "$full_image_name"
    
    echo "✅ ${image_name} pushed successfully"
done

echo ""
echo "================================================"
echo "✅ All images built and pushed!"
echo "================================================"
echo ""
echo "Image registry: $REGISTRY"
echo ""
echo "Next step: Update image names in k8s/*.yaml files"
echo "  Run: ./scripts/update_image_names.sh"

