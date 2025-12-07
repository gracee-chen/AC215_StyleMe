#!/bin/bash

echo "🔮 StyleMe 8.0 - Inference Container"
echo "======================================"

# In Cloud Run, skip gcsfuse mount (not supported, use GCS client library directly)
if [ -n "$K_SERVICE" ] || [ -n "$CLOUD_RUN" ]; then
    echo "☁️  Running in Cloud Run - skipping gcsfuse mount"
    echo "   Will use GCS client library for all GCS access"
elif [ -n "$GCS_BUCKET" ] && [ ! -d "/gcs/${GCS_BUCKET}" ]; then
    echo "📦 Mounting GCS bucket: ${GCS_BUCKET}"
    echo "   This allows reading catalog, experiments, and wardrobes from GCS"
    
    # Create mount point
    mkdir -p "/gcs/${GCS_BUCKET}"
    
    # Mount GCS bucket with timeout (non-blocking, continue if mount fails)
    timeout 5 gcsfuse --implicit-dirs --only-dir / "${GCS_BUCKET}" "/gcs/${GCS_BUCKET}" 2>&1 | tee /tmp/gcsfuse.log || {
        echo "⚠️  GCS mount failed or timed out (this is expected in some environments)"
        echo "   Will attempt to use GCS client library directly"
    }
    
    # Check if mount was successful
    if [ -d "/gcs/${GCS_BUCKET}" ] && [ "$(ls -A /gcs/${GCS_BUCKET} 2>/dev/null)" ]; then
        echo "✅ GCS bucket mounted successfully"
    else
        echo "⚠️  GCS bucket not mounted, will use GCS client library"
    fi
fi

# Skip filesystem checks in Cloud Run - code will use GCS client library
if [ -n "$K_SERVICE" ] || [ -n "$CLOUD_RUN" ]; then
    echo "☁️  Cloud Run environment detected"
    echo "   Skipping filesystem checks - code will load from GCS directly"
elif [ -d "$EXPERIMENTS_DIR" ] && [ "$(ls -A $EXPERIMENTS_DIR 2>/dev/null)" ]; then
    echo "✅ Found experiments directory at $EXPERIMENTS_DIR"
else
    echo "⚠️  Experiments directory not found at $EXPERIMENTS_DIR"
    echo "   Code will attempt to load from GCS using client library"
fi

# Skip catalog check in Cloud Run and Kubernetes - will be loaded from GCS on demand
# In Kubernetes, catalog should already exist in GCS, so we don't need to build it locally
# Check for Kubernetes by looking for service account token (more reliable than env var)
if [ -z "$K_SERVICE" ] && [ -z "$CLOUD_RUN" ] && [ ! -f /var/run/secrets/kubernetes.io/serviceaccount/token ]; then
    # Only check catalog locally
    CATALOG_EXISTS=false
    if [ -d "$CATALOG_DIR" ] && [ "$(ls -A $CATALOG_DIR 2>/dev/null)" ]; then
        if ls $CATALOG_DIR/v_*/catalog.index.faiss 1> /dev/null 2>&1; then
            CATALOG_EXISTS=true
            echo "✅ Found existing catalog index"
        fi
    fi
    
    # Build catalog if it doesn't exist (only locally)
    if [ "$CATALOG_EXISTS" = false ]; then
        echo ""
        echo "📦 Catalog index not found - attempting to build..."
        echo "   This may take 10-30 minutes depending on catalog size"
        echo "   Note: If no data is available, catalog will be empty and loaded from GCS on demand"
        echo ""
        
        python /app/build_catalog_index.py \
            --data-dir /app/data \
            --image-dir /app/data/images \
            --experiments-dir "$EXPERIMENTS_DIR" \
            --output-dir "$CATALOG_DIR"
        
        if [ $? -ne 0 ]; then
            echo "⚠️  Failed to build catalog index (this is OK if no local data exists)"
            echo "   Catalog will be loaded from GCS on first use"
        else
            echo ""
            echo "✅ Catalog index built successfully"
        fi
    fi
else
    echo "☁️  Cloud Run: Catalog will be loaded from GCS on first use"
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

# Check if we should run API server
if [ "$RUN_API_SERVER" = "true" ] || [ "$1" = "api" ]; then
    echo ""
    echo "🚀 Starting API Server..."
    echo "   API will be available at http://0.0.0.0:${PORT:-5000}"
    echo ""
    exec python /app/api_server.py
elif [ $# -gt 0 ]; then
    echo "🔮 Running inference with provided arguments..."
    exec python /app/inference_service.py "$@"
else
    # Otherwise just keep container running
    exec tail -f /dev/null
fi
