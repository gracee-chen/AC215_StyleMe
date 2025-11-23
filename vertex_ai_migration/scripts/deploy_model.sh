#!/bin/bash
# Deploy model to Vertex AI Endpoint

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-styleme-475201}"
REGION="${GCP_REGION:-us-central1}"
BUCKET_NAME="${GCP_BUCKET_NAME:-styleme-data-bucket}"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/inference:latest"

# Model configuration
MODEL_DISPLAY_NAME="${1:-styleme-fashionclip-$(date +%Y%m%d)}"
ENDPOINT_DISPLAY_NAME="${2:-styleme-inference-endpoint}"
MACHINE_TYPE="${3:-n1-standard-4}"
MIN_REPLICAS="${4:-1}"
MAX_REPLICAS="${5:-3}"

echo "=========================================="
echo "Deploying Model to Vertex AI"
echo "=========================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Model Name: $MODEL_DISPLAY_NAME"
echo "Endpoint Name: $ENDPOINT_DISPLAY_NAME"
echo "Image URI: $IMAGE_URI"
echo "Machine Type: $MACHINE_TYPE"
echo "Replicas: $MIN_REPLICAS - $MAX_REPLICAS"
echo "=========================================="

# Step 1: Upload model to Vertex AI Model Registry
echo ""
echo "Step 1: Uploading model to Vertex AI Model Registry..."
MODEL_ID=$(gcloud ai models upload \
    --region=$REGION \
    --display-name="$MODEL_DISPLAY_NAME" \
    --container-image-uri=$IMAGE_URI \
    --container-env-vars="GCP_BUCKET_NAME=$BUCKET_NAME,GCP_PROJECT_ID=$PROJECT_ID,CATALOG_DIR=/gcs/catalog,EXPERIMENTS_DIR=/gcs/models,WARDROBES_DIR=/gcs/wardrobes" \
    --artifact-uri="gs://${BUCKET_NAME}/models/${MODEL_DISPLAY_NAME}" \
    --format="value(name)" \
    --project=$PROJECT_ID)

echo "✅ Model uploaded: $MODEL_ID"

# Step 2: Create endpoint (if it doesn't exist)
echo ""
echo "Step 2: Creating/checking endpoint..."
ENDPOINT_ID=$(gcloud ai endpoints list \
    --region=$REGION \
    --filter="displayName:$ENDPOINT_DISPLAY_NAME" \
    --format="value(name)" \
    --project=$PROJECT_ID)

if [ -z "$ENDPOINT_ID" ]; then
    echo "Creating new endpoint..."
    ENDPOINT_ID=$(gcloud ai endpoints create \
        --region=$REGION \
        --display-name="$ENDPOINT_DISPLAY_NAME" \
        --format="value(name)" \
        --project=$PROJECT_ID)
    echo "✅ Endpoint created: $ENDPOINT_ID"
else
    echo "✅ Endpoint exists: $ENDPOINT_ID"
fi

# Step 3: Deploy model to endpoint
echo ""
echo "Step 3: Deploying model to endpoint..."
DEPLOYED_MODEL_ID=$(gcloud ai endpoints deploy-model $ENDPOINT_ID \
    --region=$REGION \
    --model=$MODEL_ID \
    --display-name="$MODEL_DISPLAY_NAME" \
    --machine-type=$MACHINE_TYPE \
    --min-replica-count=$MIN_REPLICAS \
    --max-replica-count=$MAX_REPLICAS \
    --traffic-split=100 \
    --format="value(deployedModel.id)" \
    --project=$PROJECT_ID)

echo "✅ Model deployed: $DEPLOYED_MODEL_ID"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo "Endpoint ID: $ENDPOINT_ID"
echo "Model ID: $MODEL_ID"
echo "Deployed Model ID: $DEPLOYED_MODEL_ID"
echo ""
echo "Test prediction:"
echo "  python vertex_ai_migration/serving/predict_client.py --endpoint-id=$ENDPOINT_ID"

