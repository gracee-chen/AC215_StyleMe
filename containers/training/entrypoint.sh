#!/bin/bash

echo "🤖 Starting Model Training Pipeline"
echo "================================="

# GCS Configuration
GCP_BUCKET_NAME=${GCP_BUCKET_NAME:-"styleme-data-bucket"}
GCP_PROJECT_ID=${GCP_PROJECT_ID:-"styleme-475201"}
DATA_PREFIX=${DATA_PREFIX:-"json"}
IMAGES_PREFIX=${IMAGES_PREFIX:-"images"}

echo "☁️ Using GCS data source:"
echo "   Bucket: $GCP_BUCKET_NAME"
echo "   Project: $GCP_PROJECT_ID"
echo "   Data prefix: $DATA_PREFIX"
echo "   Images prefix: $IMAGES_PREFIX"

# Check GPU availability
echo "🎮 Checking GPU availability..."
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'Current GPU: {torch.cuda.get_device_name(0)}')
"

# Update config to use container paths
echo "⚙️ Updating configuration for container environment..."
cd /app/src/models/train

# Create a temporary config that uses container paths
cat > config_container.py << 'EOF'
"""
Training configuration file - Container version
"""
import os

# Data configuration - GCS configuration
DATA_CONFIG = {
    'gcp_bucket_name': 'styleme-data-bucket',  # GCS bucket name
    'gcp_project_id': 'styleme-475201',  # GCP project ID
    'data_prefix': 'json',  # JSON data prefix in GCS (actual structure)
    'images_prefix': 'images',  # Images prefix in GCS (actual structure)
    'max_samples_per_file': None,  # None = use all data, int = limit samples per file
    'compatibility_threshold': 1,  # Compatibility matching threshold (lowered for more data)
    'max_compatible_items': 5,  # Maximum compatible items per product (increased for diversity)
}

# Training configuration - Optimized for training
TRAINING_CONFIG = {
    'batch_size': 32,  # Larger batch size for faster training
    'epochs': 20,  # Training epochs
    'learning_rate': 5e-6,  # Learning rate
    'num_workers': 0,  # Disabled to avoid shm issues (can't use parallel loading in Docker)
    'patience': 10,  # Early stopping patience
    'target_accuracy': 0.85,  # Target accuracy
}

# Model configuration
MODEL_CONFIG = {
    'model_name': 'openai/clip-vit-base-patch32',
    'freeze_layers': 4,  # Fewer frozen layers for better adaptation
    'feature_dim': 512,  # Feature dimension
}

# Triplet Loss configuration - Optimized for better separation
TRIPLET_CONFIG = {
    'margin': 1.0,  # Higher margin for better feature separation
    'distance_metric': 'euclidean',  # Distance metric
}

# Optimizer configuration - Optimized for better convergence
OPTIMIZER_CONFIG = {
    'optimizer': 'AdamW',
    'weight_decay': 0.001,  # Lower weight decay for less regularization
    'scheduler': 'CosineAnnealingLR',
}

# Save configuration - Container experiments directory
SAVE_CONFIG = {
    'save_dir': '/app/experiments/temp_training_output',  # Container experiments directory
    'save_best': True,
    'save_final': True,
    'save_history': True,
    'save_plots': True,
}

# Evaluation configuration
EVALUATION_CONFIG = {
    'eval_batches': 20,  # Number of batches for quick evaluation
    'full_eval_batches': 100,  # Number of batches for full evaluation
    'recommendation_k': 5,  # Number of recommendations
}
EOF

# Test data loader
echo "🧪 Testing data loader..."
export PYTHONPATH="/app/src:$PYTHONPATH"
python3 -c "
import sys
sys.path.insert(0, '/app/src')
from datapipeline.dataloader import create_dataloader
from config_container import DATA_CONFIG
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
    print(f'Train batches: {len(train_loader)}')
    print(f'Val batches: {len(val_loader)}')
    print(f'Test batches: {len(test_loader)}')
except Exception as e:
    print(f'❌ Data loader test failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

# Start training
echo "🎯 Starting model training..."
export PYTHONPATH="/app/src:$PYTHONPATH"
python3 -c "
import sys
sys.path.insert(0, '/app/src')
import os
os.chdir('/app/src/models/train')

# Import with container config
import importlib.util
spec = importlib.util.spec_from_file_location('config', 'config_container.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

# Import training modules
from model_training import main as train_main

# Override the config import in model_training
import model_training
model_training.DATA_CONFIG = config.DATA_CONFIG
model_training.TRAINING_CONFIG = config.TRAINING_CONFIG
model_training.MODEL_CONFIG = config.MODEL_CONFIG
model_training.TRIPLET_CONFIG = config.TRIPLET_CONFIG
model_training.SAVE_CONFIG = config.SAVE_CONFIG

# Run training
train_main()
"

echo "✅ Model training completed!"
echo "📁 Checkpoints saved in: $EXPERIMENTS_DIR/"
echo "🎯 Training pipeline finished"

