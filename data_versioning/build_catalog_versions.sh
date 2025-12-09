#!/bin/bash
# Build multiple catalog versions with different data subsets

set -e

GCP_BUCKET_NAME=${GCP_BUCKET_NAME:-"styleme-data-bucket"}
GCP_PROJECT_ID=${GCP_PROJECT_ID:-"styleme-475201"}
DATA_PREFIX=${DATA_PREFIX:-"json"}
IMAGES_PREFIX=${IMAGES_PREFIX:-"images"}
EXPERIMENTS_DIR=${EXPERIMENTS_DIR:-"src/models/train/experiments"}
OUTPUT_DIR=${OUTPUT_DIR:-"catalog"}

echo "🔨 Building Catalog Versions"
echo "=============================="
echo ""

# Version 1: Men only
echo "📦 Building Version 1: Men only"
VERSION1="v_men_only_$(date +%Y%m%d)"
python containers/inference/build_catalog_index.py \
    --gcp-bucket-name "$GCP_BUCKET_NAME" \
    --gcp-project-id "$GCP_PROJECT_ID" \
    --data-prefix "$DATA_PREFIX" \
    --images-prefix "$IMAGES_PREFIX" \
    --experiments-dir "$EXPERIMENTS_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --gender men

# Rename output directory
if [ -d "$OUTPUT_DIR/v_"* ]; then
    mv "$OUTPUT_DIR"/v_* "$OUTPUT_DIR/$VERSION1"
fi

echo ""
echo "✅ Version 1 built: $VERSION1"
echo ""

# Record GCS snapshot for version 1
echo "📝 Recording GCS snapshot for version 1..."
python data_versioning/gcs_snapshot_tracker.py \
    "$OUTPUT_DIR/$VERSION1/manifest.json" \
    --bucket "$GCP_BUCKET_NAME" \
    --project "$GCP_PROJECT_ID" \
    --data-prefix "$DATA_PREFIX"

# Add to DVC
echo "📦 Adding version 1 to DVC..."
python data_versioning/dvc_manager.py add-catalog "$VERSION1"

# Create tag
echo "🏷️  Creating tag for version 1..."
python data_versioning/dvc_manager.py tag "catalog-$VERSION1" -m "Catalog version: Men only"

echo ""
echo "📦 Building Version 2: Men + Women"
VERSION2="v_men_women_$(date +%Y%m%d)"

# Version 2: Men + Women
python containers/inference/build_catalog_index.py \
    --gcp-bucket-name "$GCP_BUCKET_NAME" \
    --gcp-project-id "$GCP_PROJECT_ID" \
    --data-prefix "$DATA_PREFIX" \
    --images-prefix "$IMAGES_PREFIX" \
    --experiments-dir "$EXPERIMENTS_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --gender all

# Rename output directory
if [ -d "$OUTPUT_DIR/v_"* ]; then
    mv "$OUTPUT_DIR"/v_* "$OUTPUT_DIR/$VERSION2"
fi

echo ""
echo "✅ Version 2 built: $VERSION2"
echo ""

# Record GCS snapshot for version 2
echo "📝 Recording GCS snapshot for version 2..."
python data_versioning/gcs_snapshot_tracker.py \
    "$OUTPUT_DIR/$VERSION2/manifest.json" \
    --bucket "$GCP_BUCKET_NAME" \
    --project "$GCP_PROJECT_ID" \
    --data-prefix "$DATA_PREFIX"

# Add to DVC
echo "📦 Adding version 2 to DVC..."
python data_versioning/dvc_manager.py add-catalog "$VERSION2"

# Create tag
echo "🏷️  Creating tag for version 2..."
python data_versioning/dvc_manager.py tag "catalog-$VERSION2" -m "Catalog version: Men + Women"

echo ""
echo "🎉 All versions built and added to DVC!"
echo ""
echo "View version history:"
echo "  python data_versioning/dvc_manager.py history"
echo ""
echo "List all tags:"
echo "  python data_versioning/dvc_manager.py list-tags"

