#!/bin/bash

echo "🔮 StyleMe 8.0 - Inference Container"
echo "======================================"

# Check if trained model exists
if [ ! -d "$EXPERIMENTS_DIR" ] || [ ! "$(ls -A $EXPERIMENTS_DIR)" ]; then
    echo "❌ No experiments found in $EXPERIMENTS_DIR"
    echo "   Please run training container first"
    exit 1
fi

echo "✅ Found experiments directory"

# Check if catalog index exists
CATALOG_EXISTS=false
if [ -d "$CATALOG_DIR" ] && [ "$(ls -A $CATALOG_DIR 2>/dev/null)" ]; then
    if ls $CATALOG_DIR/v_*/catalog.index.faiss 1> /dev/null 2>&1; then
        CATALOG_EXISTS=true
        echo "✅ Found existing catalog index"
    fi
fi

# Build catalog if it doesn't exist
if [ "$CATALOG_EXISTS" = false ]; then
    echo ""
    echo "📦 Catalog index not found - building now..."
    echo "   This may take 10-30 minutes depending on catalog size"
    echo ""
    
    python /app/build_catalog_index.py \
        --gcp-bucket-name $GCP_BUCKET_NAME \
        --gcp-project-id $GCP_PROJECT_ID \
        --data-prefix $DATA_PREFIX \
        --images-prefix $IMAGES_PREFIX \
        --experiments-dir /app/experiments \
        --output-dir /app/catalog
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to build catalog index"
        exit 1
    fi
    
    echo ""
    echo "✅ Catalog index built successfully"
fi

echo ""
echo "======================================"
echo "✅ Inference Container Ready"
echo "======================================"
echo ""
echo "💡 To run inference for a user query:"
echo ""
echo "   python /app/inference_service.py \\"
echo "     --user-id <user_id> \\"
echo "     --query /app/queries/<user>/<request_id>/<image>.jpg \\"
echo "     --output /app/results/<user>/<request_id>.json \\"
echo "     --threshold 0.3"
echo ""
echo "📂 Directories:"
echo "   Catalog:   $CATALOG_DIR"
echo "   Wardrobes: $WARDROBES_DIR"
echo "   Queries:   $QUERIES_DIR"
echo "   Results:   $RESULTS_DIR"
echo ""

# If arguments provided, run inference_service.py with those args
if [ $# -gt 0 ]; then
    echo "🔮 Running inference with provided arguments..."
    exec python /app/inference_service.py "$@"
else
    # Otherwise just keep container running
    exec tail -f /dev/null
fi
