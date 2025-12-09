#!/bin/bash
# Deploy StyleMe Frontend to Cloud Run
# This script builds the frontend and deploys it as a static site to Cloud Run

set -e

# Configuration
SERVICE_NAME="styleme-frontend"
REGION="us-central1"
PROJECT_ID="styleme-475201"
IMAGE_URI="us-central1-docker.pkg.dev/${PROJECT_ID}/styleme-repo/frontend:latest"
ARTIFACT_REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/styleme-repo"

# Get API URL (default to Cloud Run inference service)
API_URL="${1:-https://styleme-inference-nty2g5pcpa-uc.a.run.app}"

echo "🚀 Deploying StyleMe Frontend to Cloud Run"
echo "==========================================="
echo "Service Name: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "API URL: ${API_URL}"
echo ""

# Navigate to website directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WEBSITE_DIR="${PROJECT_ROOT}/website"

if [ ! -d "${WEBSITE_DIR}" ]; then
    echo "❌ Error: website directory not found at ${WEBSITE_DIR}"
    exit 1
fi

cd "${WEBSITE_DIR}"

# Create or update .env.production
# Note: OpenAI API key is now configured on the backend, not in frontend
echo "📝 Creating/updating .env.production file..."
cat > .env.production << EOF
# Production environment variables
# This file is used when building for production deployment
VITE_API_URL=${API_URL}
# Note: OpenAI API key is configured on the backend server, not in frontend
EOF

echo "✅ .env.production configured"
echo "   VITE_API_URL=${API_URL}"
echo "   (OpenAI API key is configured on backend, not needed in frontend)"
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Build the frontend
echo "🔨 Building frontend for production..."
npm run build

if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    echo "❌ Error: Build failed or dist directory is empty"
    exit 1
fi

echo "✅ Build complete!"
echo ""

# Build Docker image for linux/amd64 (Cloud Run requirement)
echo "🐳 Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -f Dockerfile.static -t ${IMAGE_URI} .

if [ $? -ne 0 ]; then
    echo "❌ Error: Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully!"
echo ""

# Push to Artifact Registry
echo "📤 Pushing image to Artifact Registry..."
docker push ${IMAGE_URI}

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to push image"
    exit 1
fi

echo "✅ Image pushed successfully!"
echo ""

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_URI} \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --project ${PROJECT_ID} \
    --port 8080

if [ $? -ne 0 ]; then
    echo "❌ Error: Deployment failed"
    exit 1
fi

echo ""
echo "✅ Deployment complete!"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --format="value(status.url)" \
    --project ${PROJECT_ID})

echo "📋 Service Details:"
echo "  URL: ${SERVICE_URL}"
echo ""
echo "🧪 Test the service:"
echo "  curl ${SERVICE_URL}"
echo ""
echo "🌐 Open in browser:"
echo "  ${SERVICE_URL}"
echo ""
echo "📊 Monitor the service:"
echo "  gcloud run services describe ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
echo ""
echo "📋 View logs:"
echo "  gcloud run services logs read ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
echo ""

