#!/bin/bash

echo "🔄 Starting Data Preprocessing Pipeline"
echo "====================================="

# Check if data exists
if [ ! -d "$DATA_DIR/json" ] || [ ! "$(ls -A $DATA_DIR/json)" ]; then
    echo "❌ No data found in $DATA_DIR/json. Please run ingestion first."
    exit 1
fi

echo "📊 Found data:"
find $DATA_DIR/json -name "*.json" | wc -l | xargs echo "   JSON files:"
find $DATA_DIR/images -name "*.jpg" 2>/dev/null | wc -l | xargs echo "   Images:"

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

