#!/bin/bash

echo "🤖 Starting Model Training Pipeline"
echo "================================="

# Check if data exists
if [ ! -d "$DATA_DIR/json" ] || [ ! "$(ls -A $DATA_DIR/json)" ]; then
    echo "❌ No data found in $DATA_DIR/json. Please run ingestion and preprocessing first."
    exit 1
fi

echo "📊 Found data:"
find $DATA_DIR/json -name "*.json" | wc -l | xargs echo "   JSON files:"
find $DATA_DIR/images -name "*.jpg" 2>/dev/null | wc -l | xargs echo "   Images:"

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

# Data configuration - Container paths
DATA_CONFIG = {
    'data_dir': '/app/data',  # Container data directory
    'image_dir': '/app/data/images',  # Container images directory
    'max_samples_per_file': None,  # None = use all data, int = limit samples per file
    'compatibility_threshold': 1,  # Compatibility matching threshold (lowered for more data)
    'max_compatible_items': 5,  # Maximum compatible items per product (increased for diversity)
}

# Training configuration - Optimized for 75% target accuracy
TRAINING_CONFIG = {
    'batch_size': 16,  # Batch size (reduced for better gradient updates, matching EXP_002)
    'epochs': 30,  # Number of training epochs (increased from 20 but not too high)
    'learning_rate': 1e-5,  # Learning rate (keep same as successful EXP_002)
    'num_workers': 2,  # Number of data loading worker processes
    'patience': 8,  # Early stopping patience (increased to allow more training)
    'target_accuracy': 0.75,  # Target accuracy (matching successful EXP_002)
}

# Model configuration
MODEL_CONFIG = {
    'model_name': 'openai/clip-vit-base-patch32',
    'freeze_layers': 8,  # Number of frozen layers
    'feature_dim': 512,  # Feature dimension
}

# Triplet Loss configuration - Optimized for better separation
TRIPLET_CONFIG = {
    'margin': 0.7,  # Triplet Loss margin (increased for better feature separation)
    'distance_metric': 'euclidean',  # Distance metric
}

# Optimizer configuration - Optimized for better convergence
OPTIMIZER_CONFIG = {
    'optimizer': 'AdamW',
    'weight_decay': 0.005,  # Reduced weight decay for less regularization
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
python3 -c "
import sys
sys.path.append('/app/src')
from src.datapipeline.dataloader import create_dataloader
from config_container import DATA_CONFIG
print('Testing data loader...')
try:
    train_loader, val_loader, test_loader = create_dataloader(
        data_dir=DATA_CONFIG['data_dir'],
        image_dir=DATA_CONFIG['image_dir'],
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
"

# Start training
echo "🎯 Starting model training..."
python3 -c "
import sys
sys.path.append('/app/src')
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

