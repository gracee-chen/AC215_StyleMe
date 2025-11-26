#!/bin/bash
# Create two data versions by recording different GCS snapshots
# Version 1: Men only
# Version 2: Men + Women

set -e

echo "📦 Creating Data Versions"
echo "=========================="
echo ""

# Use existing catalog directory
CATALOG_DIR="catalog/v_2025-10-24_model-b1"

if [ ! -d "$CATALOG_DIR" ]; then
    echo "❌ Error: $CATALOG_DIR does not exist"
    exit 1
fi

echo "📝 Version 1: Recording GCS snapshot for Men only..."
python data_versioning/gcs_snapshot_tracker.py \
    "$CATALOG_DIR/manifest.json" \
    --bucket styleme-data-bucket \
    --project styleme-475201 \
    --data-prefix json \
    --gender men

# Create a copy of manifest for version 1
cp "$CATALOG_DIR/manifest.json" "$CATALOG_DIR/manifest_men_only.json"

echo ""
echo "📝 Version 2: Recording GCS snapshot for Men + Women..."
python data_versioning/gcs_snapshot_tracker.py \
    "$CATALOG_DIR/manifest.json" \
    --bucket styleme-data-bucket \
    --project styleme-475201 \
    --data-prefix json \
    --gender all

# Create a copy of manifest for version 2
cp "$CATALOG_DIR/manifest.json" "$CATALOG_DIR/manifest_all.json"

echo ""
echo "✅ Both versions recorded!"
echo ""
echo "View version history:"
echo "  python data_versioning/dvc_manager.py history"
echo ""
echo "The manifest.json now contains the latest snapshot (Men + Women)"
echo "You can see both versions in the history"

