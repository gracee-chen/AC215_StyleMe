#!/bin/bash
# Download model from GCS using gsutil (if available) or Python

set -e

BUCKET="styleme-production"
PROJECT="styleme-475201"
EXPERIMENT_ID="${1:-exp_004}"
LOCAL_DIR="src/models/train/experiments/${EXPERIMENT_ID}"

echo "📥 Downloading model from GCS"
echo "=============================="
echo "   Bucket: ${BUCKET}"
echo "   Experiment: ${EXPERIMENT_ID}"
echo "   Local: ${LOCAL_DIR}/best_model.pth"
echo ""

# Create local directory
mkdir -p "${LOCAL_DIR}"

# Try gsutil first (faster if available)
if command -v gsutil &> /dev/null; then
    echo "Using gsutil..."
    gsutil cp "gs://${BUCKET}/experiments/${EXPERIMENT_ID}/best_model.pth" \
        "${LOCAL_DIR}/best_model.pth"
    
    if [ $? -eq 0 ]; then
        echo "✅ Model downloaded successfully using gsutil"
        ls -lh "${LOCAL_DIR}/best_model.pth"
        exit 0
    fi
fi

# Fallback to Python script
echo "Using Python script..."
python3 scripts/download_model.py --experiment-id "${EXPERIMENT_ID}"

