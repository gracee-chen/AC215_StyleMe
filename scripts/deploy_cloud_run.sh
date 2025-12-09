#!/bin/bash
# Deploy StyleMe Inference Service to Cloud Run
# This script deploys the inference container with all required configuration

set -e

# Configuration
SERVICE_NAME="styleme-inference"
REGION="us-central1"
PROJECT_ID="styleme-475201"
IMAGE_URI="us-central1-docker.pkg.dev/styleme-475201/styleme-repo/inference:latest"
SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"

# Resource configuration
MEMORY="${1:-4Gi}"  # Default: 4GB
CPU="${2:-2}"       # Default: 2 vCPU
TIMEOUT="${3:-600}" # Default: 600 seconds (10 minutes) - increased for async wardrobe rebuilds
MAX_INSTANCES="${4:-10}"  # Default: 10 max instances
MIN_INSTANCES="${5:-1}"   # Default: 1 min instance (reduce cold starts)

echo "🚀 Deploying StyleMe Inference Service to Cloud Run"
echo "===================================================="
echo "Service Name: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Image: ${IMAGE_URI}"
echo ""
echo "Resource Configuration:"
echo "  Memory: ${MEMORY}"
echo "  CPU: ${CPU}"
echo "  Timeout: ${TIMEOUT}s"
echo "  Max Instances: ${MAX_INSTANCES}"
echo "  Min Instances: ${MIN_INSTANCES}"
echo ""

# Set environment variables
# Note: PORT is automatically set by Cloud Run (defaults to 8080)
ENV_VARS=(
    "GCP_BUCKET_NAME=styleme-data-bucket"
    "GCP_PROJECT_ID=${PROJECT_ID}"
    "CATALOG_DIR=/gcs/styleme-production/catalog"
    "WARDROBES_DIR=/gcs/styleme-production/wardrobes"
    "EXPERIMENTS_DIR=/gcs/styleme-production/experiments"
    "QUERIES_DIR=/tmp/queries"
    "RESULTS_DIR=/tmp/results"
    "RUN_API_SERVER=true"
    "LOG_LEVEL=INFO"
    "GCS_BUCKET=styleme-production"
    "CLOUD_RUN=true"
)

# Check if OPENAI_API_KEY should be set from Secret Manager or env var
# Try to get from Secret Manager first (more secure)
if gcloud secrets versions access latest --secret="openai-api-key" --project=${PROJECT_ID} >/dev/null 2>&1; then
    echo "✅ Found OPENAI_API_KEY in Secret Manager"
    USE_SECRET_MANAGER=true
else
    echo "⚠️  OPENAI_API_KEY not found in Secret Manager"
    echo "   Will use environment variable if OPENAI_API_KEY is set in current shell"
    USE_SECRET_MANAGER=false
    if [ -n "$OPENAI_API_KEY" ]; then
        ENV_VARS+=("OPENAI_API_KEY=${OPENAI_API_KEY}")
        echo "   Using OPENAI_API_KEY from environment"
    else
        echo "   ⚠️  WARNING: OPENAI_API_KEY not set - automatic tagging will use defaults"
    fi
fi

# Build environment variables string for gcloud (after potential OPENAI_API_KEY addition)
ENV_VARS_STRING=$(IFS=,; echo "${ENV_VARS[*]}")

echo ""
echo "Environment Variables:"
for var in "${ENV_VARS[@]}"; do
    # Mask API key in output
    if [[ "$var" == OPENAI_API_KEY=* ]]; then
        echo "  - OPENAI_API_KEY=***hidden***"
    else
        echo "  - ${var}"
    fi
done
echo ""

# Build and push Docker image first
echo "🔨 Step 1: Building Docker image..."
docker build --platform linux/amd64 \
    -f containers/inference/Dockerfile \
    -t ${IMAGE_URI} \
    .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"
echo ""

# Push to Artifact Registry
echo "📤 Step 2: Pushing image to Artifact Registry..."
docker push ${IMAGE_URI}

if [ $? -ne 0 ]; then
    echo "❌ Docker push failed"
    exit 1
fi

echo "✅ Image pushed successfully"
echo ""

# Deploy to Cloud Run
echo "📤 Step 3: Deploying service to Cloud Run..."
echo "   Note: Using default Cloud Run service account (will grant permissions after deployment)"

# Build deploy command
if [ "$USE_SECRET_MANAGER" = true ]; then
    echo "   Using OPENAI_API_KEY from Secret Manager"
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_URI} \
        --region ${REGION} \
        --platform managed \
        --allow-unauthenticated \
        --memory ${MEMORY} \
        --cpu ${CPU} \
        --timeout ${TIMEOUT} \
        --max-instances ${MAX_INSTANCES} \
        --min-instances ${MIN_INSTANCES} \
        --set-env-vars ${ENV_VARS_STRING} \
        --update-secrets OPENAI_API_KEY=openai-api-key:latest \
        --project ${PROJECT_ID}
else
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_URI} \
        --region ${REGION} \
        --platform managed \
        --allow-unauthenticated \
        --memory ${MEMORY} \
        --cpu ${CPU} \
        --timeout ${TIMEOUT} \
        --max-instances ${MAX_INSTANCES} \
        --min-instances ${MIN_INSTANCES} \
        --set-env-vars ${ENV_VARS_STRING} \
        --project ${PROJECT_ID}
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Service Details:"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)" --project ${PROJECT_ID})
echo "  URL: ${SERVICE_URL}"
echo ""
echo "🧪 Test the service:"
echo "  curl ${SERVICE_URL}/health"
echo ""
echo "📊 Monitor the service:"
echo "  gcloud run services describe ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
echo ""
echo "📋 View logs:"
echo "  gcloud run services logs read ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
echo ""

