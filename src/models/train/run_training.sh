#!/bin/bash

# Personal Wardrobe AI Stylist - Model Training Script

echo "🚀 Starting Personal Wardrobe AI Stylist Model Training"
echo "======================================================"

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not installed, please install Python3 first"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Test data loader
echo "🧪 Testing data loader..."
python3 -c "
import sys
sys.path.append('../../')
from src.datapipeline.dataloader import create_dataloader
from config import DATA_CONFIG
print('Testing data loader...')
try:
    train_loader, val_loader, test_loader = create_dataloader(
        gcp_bucket_name=DATA_CONFIG['gcp_bucket_name'],
        gcp_project_id=DATA_CONFIG['gcp_project_id'],
        data_prefix=DATA_CONFIG['data_prefix'],
        images_prefix=DATA_CONFIG['images_prefix'],
        batch_size=4
    )
    print('✅ Data loader test successful!')
except Exception as e:
    print(f'❌ Data loader test failed: {e}')
"

# Start training
echo "🎯 Starting model training..."
python3 model_training.py

echo "✅ Training completed!"
echo "📁 Checkpoints saved in: fashion_clip_checkpoints/"
echo "📊 Training curves: fashion_clip_checkpoints/training_curves.png"
