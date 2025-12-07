#!/bin/bash
# Submit Vertex AI Training Job
# This script submits a training job to Vertex AI with all required environment variables

set -e

# Configuration
REGION="us-central1"
PROJECT_ID="styleme-475201"
IMAGE_URI="us-central1-docker.pkg.dev/styleme-475201/styleme-repo/training:latest"
SERVICE_ACCOUNT="871771559501-compute@developer.gserviceaccount.com"

# Machine configuration
# Options: n1-standard-8, n1-highmem-8, n1-highmem-16
MACHINE_TYPE="${1:-n1-highmem-8}"

# GPU configuration
GPU_TYPE="${2:-NVIDIA_TESLA_V100}"
GPU_COUNT="${3:-1}"

# Environment variables - IMPORTANT: EXPERIMENTS_DIR is set here!
ENV_VARS=(
    "GCP_BUCKET_NAME=styleme-data-bucket"
    "GCP_PROJECT_ID=${PROJECT_ID}"
    "DATA_PREFIX=json"
    "IMAGES_PREFIX=images"
    "EXPERIMENTS_DIR=/gcs/styleme-production/experiments"
    "LOG_LEVEL=INFO"
)

# Generate job name with timestamp
JOB_NAME="styleme-training-$(date +%Y%m%d-%H%M%S)"

echo "🚀 Submitting Vertex AI Training Job"
echo "===================================="
echo "Job Name: ${JOB_NAME}"
echo "Region: ${REGION}"
echo "Machine Type: ${MACHINE_TYPE}"
echo "GPU Type: ${GPU_TYPE}"
echo "GPU Count: ${GPU_COUNT}"
echo "Image: ${IMAGE_URI}"
echo ""
echo "Environment Variables:"
for var in "${ENV_VARS[@]}"; do
    echo "  - ${var}"
done
echo ""
echo "⚠️  IMPORTANT: EXPERIMENTS_DIR is set to /gcs/styleme-production/experiments"
echo "   This ensures outputs are saved to GCS and persist after the job completes."
echo ""

# Create temporary YAML config file
CONFIG_FILE="/tmp/vertex_ai_job_${JOB_NAME}.yaml"

# Build YAML config with environment variables
cat > "${CONFIG_FILE}" << EOF
workerPoolSpecs:
  - machineSpec:
      machineType: ${MACHINE_TYPE}
EOF

# Add GPU if specified
if [ "${GPU_COUNT}" -gt 0 ]; then
    cat >> "${CONFIG_FILE}" << EOF
      acceleratorType: ${GPU_TYPE}
      acceleratorCount: ${GPU_COUNT}
EOF
fi

# Add container spec with environment variables
cat >> "${CONFIG_FILE}" << EOF
    replicaCount: 1
    containerSpec:
      imageUri: ${IMAGE_URI}
      env:
EOF

# Add each environment variable
for var in "${ENV_VARS[@]}"; do
    IFS='=' read -r key value <<< "${var}"
    cat >> "${CONFIG_FILE}" << EOF
        - name: ${key}
          value: "${value}"
EOF
done

echo "📄 Generated config file: ${CONFIG_FILE}"
echo ""

# Submit the job
echo "📤 Submitting job..."
gcloud ai custom-jobs create \
    --region=${REGION} \
    --display-name=${JOB_NAME} \
    --config="${CONFIG_FILE}" \
    --service-account=${SERVICE_ACCOUNT}

# Clean up config file
rm -f "${CONFIG_FILE}"

echo ""
echo "✅ Job submitted successfully!"
echo ""
echo "📋 To monitor the job:"
echo "   gcloud ai custom-jobs stream-logs ${JOB_NAME} --region=${REGION}"
echo ""
echo "📊 To check job status:"
echo "   gcloud ai custom-jobs describe ${JOB_NAME} --region=${REGION}"
echo ""
echo "📁 Outputs will be saved to:"
echo "   gs://styleme-production/experiments/temp_training_output/"
echo ""

