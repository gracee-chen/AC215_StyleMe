#!/bin/bash
# Build and push training container using Cloud Build
# This builds on GCP, avoiding local platform issues

set -e

PROJECT_ID="styleme-475201"
REGION="us-central1"

echo "🏗️  Building training container with Cloud Build"
echo "================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Submit Cloud Build job
gcloud builds submit \
    --config=cloudbuild-training.yaml \
    --project=${PROJECT_ID} \
    --region=${REGION}

echo ""
echo "✅ Build complete! Image pushed to:"
echo "   us-central1-docker.pkg.dev/${PROJECT_ID}/styleme-repo/training:latest"

