#!/bin/bash

# Build Catalog Index from GCS Data
# Downloads data from GCS, builds catalog using exp_004 model, uploads result

set -e

echo "🏗️  Building Catalog Index from GCS Data"
echo "=========================================="

PROJECT_ID="styleme-475201"
DATA_BUCKET="styleme-data-bucket"
PROD_BUCKET="styleme-production"
TEMP_DIR="/tmp/styleme_catalog_build_$(date +%s)"

# Create temp directory
mkdir -p "$TEMP_DIR"
echo "📁 Temp directory: $TEMP_DIR"

# Step 1: Download JSON metadata files
echo ""
echo "📥 Step 1: Downloading JSON metadata files..."
JSON_DIR="$TEMP_DIR/data/json"
mkdir -p "$JSON_DIR/men_data" "$JSON_DIR/women_data"
gsutil -m cp -r "gs://${DATA_BUCKET}/json/men_data/"* "$JSON_DIR/men_data/" 2>&1 | head -20
gsutil -m cp -r "gs://${DATA_BUCKET}/json/women_data/"* "$JSON_DIR/women_data/" 2>&1 | head -20
echo "   ✅ JSON files downloaded"

# Step 2: Download images
echo ""
echo "📥 Step 2: Downloading product images..."
IMAGE_DIR="$TEMP_DIR/data/images"
mkdir -p "$IMAGE_DIR"
# Download images (this might take a while)
gsutil -m cp "gs://${DATA_BUCKET}/images/"*.jpg "$IMAGE_DIR/" 2>&1 | tail -5
echo "   ✅ Images downloaded"

# Step 3: Download model from exp_004
echo ""
echo "📥 Step 3: Downloading exp_004 model..."
EXPERIMENTS_DIR="$TEMP_DIR/experiments/exp_004"
mkdir -p "$EXPERIMENTS_DIR"
gsutil cp "gs://${PROD_BUCKET}/experiments/exp_004/best_model.pth" "$EXPERIMENTS_DIR/" 2>&1
echo "   ✅ Model downloaded"

# Step 4: Build catalog using Docker
echo ""
echo "🔨 Step 4: Building catalog index..."
echo "   This may take 10-30 minutes depending on data size..."

# Use docker run with the inference container image
IMAGE_NAME="styleme-inference:latest"
if ! docker images | grep -q "styleme-inference"; then
    echo "   Building inference container first..."
    cd /home/chufeip/styleme12.0
    docker compose build inference 2>&1 | tail -5
    cd - > /dev/null
fi

echo "   Running catalog build in container..."
# Bypass entrypoint and run Python script directly
docker run --rm \
    --entrypoint python \
    -v "${TEMP_DIR}/data:/tmp/data:ro" \
    -v "${TEMP_DIR}/experiments:/tmp/experiments:ro" \
    -v "${TEMP_DIR}/catalog:/tmp/catalog:rw" \
    "${IMAGE_NAME}" \
    /app/build_catalog_index.py \
        --data-dir /tmp/data \
        --image-dir /tmp/data/images \
        --experiments-dir /tmp/experiments \
        --output-dir /tmp/catalog

if [ $? -ne 0 ]; then
    echo "❌ Catalog build failed"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Step 5: Upload catalog to GCS
echo ""
echo "📤 Step 5: Uploading catalog to GCS..."
# Find the versioned catalog directory
CATALOG_VERSION_DIR=$(find "$TEMP_DIR/catalog" -type d -name "v_*" | head -1)
if [ -z "$CATALOG_VERSION_DIR" ]; then
    echo "❌ No catalog version directory found"
    exit 1
fi

VERSION_NAME=$(basename "$CATALOG_VERSION_DIR")
echo "   Catalog version: $VERSION_NAME"

# Upload all catalog files
gsutil -m cp -r "$CATALOG_VERSION_DIR" "gs://${PROD_BUCKET}/catalog/" 2>&1 | tail -5

if [ $? -ne 0 ]; then
    echo "❌ Failed to upload catalog"
    exit 1
fi

echo "   ✅ Catalog uploaded to gs://${PROD_BUCKET}/catalog/${VERSION_NAME}/"

# Step 6: Cleanup
echo ""
echo "🧹 Cleaning up temporary files..."
rm -rf "$TEMP_DIR"
echo "   ✅ Cleanup complete"

echo ""
echo "✅ Catalog build complete!"
echo "   Location: gs://${PROD_BUCKET}/catalog/${VERSION_NAME}/"
echo ""
echo "The inference service will automatically use this catalog."

