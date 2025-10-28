#!/bin/bash

echo "🔄 Starting Data Preprocessing Pipeline"
echo "====================================="

# GCS Configuration
echo "☁️  Using Google Cloud Storage:"
echo "   Bucket: $GCP_BUCKET_NAME"
echo "   Project: $GCP_PROJECT_ID"
echo "   Data Prefix: $DATA_PREFIX"
echo "   Images Prefix: $IMAGES_PREFIX"

# Test GCS connection
echo "🔍 Testing GCS connection..."
python3 -c "
import os
from google.cloud import storage

try:
    # Use default credentials
    client = storage.Client(project='$GCP_PROJECT_ID')
    bucket = client.bucket('$GCP_BUCKET_NAME')
    
    # List some blobs to test connection
    blobs = list(bucket.list_blobs(prefix='$DATA_PREFIX', max_results=5))
    print(f'✅ GCS connection successful. Found {len(blobs)} data files.')
    
    # List some images to test connection
    image_blobs = list(bucket.list_blobs(prefix='$IMAGES_PREFIX', max_results=5))
    print(f'✅ Found {len(image_blobs)} image files.')
    
except Exception as e:
    print(f'❌ GCS connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ GCS connection failed. Please check your configuration."
    exit 1
fi

echo "📊 GCS data confirmed:"

# Run background removal preprocessing
echo "🎨 Running background removal preprocessing..."
cd /app/src/datapipeline/bg_removal

# Test background removal functionality
python3 -c "
import sys
sys.path.append('/app/src')
from src.datapipeline.bg_removal.background_removal import BackgroundRemover
print('✅ Background removal module loaded successfully')
"

echo "✅ Data preprocessing completed"

echo "🎯 Preprocessing pipeline finished"

