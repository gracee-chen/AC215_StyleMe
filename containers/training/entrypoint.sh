#!/bin/bash

echo "🤖 Starting Model Training Pipeline"
echo "================================="

# Check if test mode
if [ "${TEST_MODE}" = "true" ]; then
    echo "🧪 TEST MODE ENABLED"
    echo "  - Epochs: ${TEST_EPOCHS:-1}"
    echo "  - Max Samples: ${MAX_SAMPLES_PER_FILE:-unlimited}"
    echo "  - Purpose: Verify GCS output works correctly"
    echo ""
fi

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
# Set PYTHONPATH to include src directory
export PYTHONPATH=/app/src:/app:$PYTHONPATH
cd /app/src/models/train

# Create a temporary config that uses container paths
cat > config_container.py << 'EOF'
"""
Training configuration file - Container version
"""
import os

# Data configuration - Use GCS for data access (datasets load from GCS bucket directly)
# For Vertex AI, data is accessed via google-cloud-storage, not local filesystem
import os
DATA_CONFIG = {
    'gcp_bucket_name': os.getenv('GCP_BUCKET_NAME', 'styleme-data-bucket'),  # GCS bucket name
    'gcp_project_id': os.getenv('GCP_PROJECT_ID', 'styleme-475201'),  # GCP project ID
    'data_prefix': os.getenv('DATA_PREFIX', 'json'),  # JSON data prefix in GCS
    'images_prefix': os.getenv('IMAGES_PREFIX', 'images'),  # Images prefix in GCS
    'max_samples_per_file': int(os.getenv('MAX_SAMPLES_PER_FILE')) if os.getenv('MAX_SAMPLES_PER_FILE') else None,  # Limit samples for test mode
    'compatibility_threshold': 1,  # Compatibility matching threshold (lowered for more data)
    'max_compatible_items': 5,  # Maximum compatible items per product (increased for diversity)
}

# Training configuration - Optimized for 75% target accuracy
# Check for test mode (1 epoch for quick testing)
test_epochs = os.getenv('TEST_EPOCHS')
test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
epochs = int(test_epochs) if test_epochs else (1 if test_mode else 30)

TRAINING_CONFIG = {
    'batch_size': 24,  # Increased batch size for more stable gradients
    'epochs': epochs,  # Number of training epochs (1 for test mode, 30 for production)
    'learning_rate': 2e-5,  # Increased learning rate to escape plateau (was 1e-5)
    'num_workers': 2,  # Number of data loading worker processes
    'patience': 12,  # Increased patience to allow model to escape plateau (was 8)
    'target_accuracy': 0.75,  # Target accuracy (matching successful EXP_002)
}

# Model configuration
MODEL_CONFIG = {
    'model_name': 'openai/clip-vit-base-patch32',
    'freeze_layers': 4,  # Reduced frozen layers for more fine-tuning capacity (was 8)
    'feature_dim': 512,  # Feature dimension
}

# Triplet Loss configuration - Optimized for better learning
TRIPLET_CONFIG = {
    'margin': 0.3,  # Very tight margin to force better feature separation and escape plateau (was 0.5, originally 0.7)
    'distance_metric': 'euclidean',  # Distance metric
}

# Optimizer configuration - Optimized for better convergence
OPTIMIZER_CONFIG = {
    'optimizer': 'AdamW',
    'weight_decay': 0.01,  # Increased weight decay for better regularization (was 0.005)
    'scheduler': 'CosineAnnealingLR',
}

# Save configuration - Use EXPERIMENTS_DIR if set, otherwise use GCS path for Vertex AI
# Vertex AI mounts GCS buckets at /gcs/{bucket-name}/
import os
experiments_base = os.getenv('EXPERIMENTS_DIR', '/gcs/styleme-production/experiments')
SAVE_CONFIG = {
    'save_dir': os.path.join(experiments_base, 'temp_training_output'),  # Use GCS path for Vertex AI
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

# Test data loader (using GCS)
echo "🧪 Testing data loader with GCS..."
python3 -c "
import sys
import os
# Ensure src is in path
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')
from datapipeline.dataloader import create_dataloader
from config_container import DATA_CONFIG
print('Testing data loader with GCS...')
print(f'GCS Bucket: {DATA_CONFIG.get(\"gcp_bucket_name\", \"N/A\")}')
try:
    # create_dataloader supports GCS via gcp_bucket_name parameter
    train_loader, val_loader, test_loader = create_dataloader(
        gcp_bucket_name=DATA_CONFIG.get('gcp_bucket_name'),
        gcp_project_id=DATA_CONFIG.get('gcp_project_id'),
        data_prefix=DATA_CONFIG.get('data_prefix', 'json'),
        images_prefix=DATA_CONFIG.get('images_prefix', 'images'),
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
import os
# Ensure src is in path
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')
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
model_training.OPTIMIZER_CONFIG = config.OPTIMIZER_CONFIG
model_training.SAVE_CONFIG = config.SAVE_CONFIG

# Run training
train_main()
"

echo "✅ Model training completed!"
if [ -n "$EXPERIMENTS_DIR" ]; then
    echo "📁 Checkpoints saved in: $EXPERIMENTS_DIR/"
else
    echo "📁 Checkpoints saved in: /gcs/styleme-production/experiments/"
fi
echo "🎯 Training pipeline finished"

