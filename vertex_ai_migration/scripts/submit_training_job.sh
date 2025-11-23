#!/bin/bash
# Submit a custom training job to Vertex AI

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-styleme-475201}"
REGION="${GCP_REGION:-us-central1}"
BUCKET_NAME="${GCP_BUCKET_NAME:-styleme-data-bucket}"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/training:latest"
SERVICE_ACCOUNT="vertex-ai-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Training parameters
DATA_VERSION="${1:-catalog-v_men_women_20251123}"
EPOCHS="${2:-20}"
BATCH_SIZE="${3:-32}"
LEARNING_RATE="${4:-5e-6}"

# Create job name with timestamp
JOB_NAME="styleme-training-$(date +%Y%m%d-%H%M%S)"

echo "=========================================="
echo "Submitting Vertex AI Training Job"
echo "=========================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Job Name: $JOB_NAME"
echo "Image URI: $IMAGE_URI"
echo "Data Version: $DATA_VERSION"
echo "Epochs: $EPOCHS"
echo "Batch Size: $BATCH_SIZE"
echo "Learning Rate: $LEARNING_RATE"
echo "=========================================="

# Submit custom training job
gcloud ai custom-jobs create \
    --region=$REGION \
    --display-name="$JOB_NAME" \
    --worker-pool-spec=replica-count=1,machine-type=n1-standard-4,accelerator-type=nvidia-tesla-v100,accelerator-count=1,container-image-uri=$IMAGE_URI \
    --args="--data-version=$DATA_VERSION,--epochs=$EPOCHS,--batch-size=$BATCH_SIZE,--learning-rate=$LEARNING_RATE" \
    --service-account=$SERVICE_ACCOUNT \
    --env-vars="GCP_BUCKET_NAME=$BUCKET_NAME,GCP_PROJECT_ID=$PROJECT_ID" \
    --project=$PROJECT_ID

echo ""
echo "✅ Training job submitted successfully!"
echo "Monitor progress:"
echo "  gcloud ai custom-jobs list --region=$REGION"
echo "  gcloud ai custom-jobs describe $JOB_NAME --region=$REGION"

