#!/bin/bash

echo "🚀 Starting Data Ingestion Pipeline"
echo "=================================="

# In Kubernetes, data is loaded directly from GCS by the dataloader
# This job just ensures the data directory structure exists
# The actual data loading happens when training/inference runs

# Create target directories
mkdir -p $DATA_DIR/json
mkdir -p $DATA_DIR/images

# Check if data directory structure is ready
if [ -d "$DATA_DIR" ]; then
    echo "✅ Data directory structure created: $DATA_DIR"
    echo "📁 Directories:"
    echo "   - $DATA_DIR/json"
    echo "   - $DATA_DIR/images"
    echo ""
    echo "ℹ️  Note: Data will be loaded from GCS bucket '$GCP_BUCKET_NAME'"
    echo "   when training/inference services run."
    echo ""
    echo "✅ Ingestion pipeline finished (data structure ready)"
else
    echo "❌ Failed to create data directory"
    exit 1
fi

echo "🎯 Ingestion pipeline finished"
