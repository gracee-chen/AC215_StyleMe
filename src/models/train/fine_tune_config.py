"""
Fine-tuning configuration for improved model performance
References versioned datasets and tracks experiments
"""

# Data configuration - Reference versioned data
DATA_CONFIG = {
    'gcp_bucket_name': 'styleme-data-bucket',
    'gcp_project_id': 'styleme-475201',
    'data_prefix': 'json',
    'images_prefix': 'images',
    'max_samples_per_file': None,
    'compatibility_threshold': 1,
    'max_compatible_items': 5,
    # Data version reference
    'data_version': 'v_men_women_20251123',  # Reference to versioned catalog
    'gcs_snapshot_tag': 'catalog-v_men_women_20251123',  # DVC tag
}

# Training configuration - Optimized for fine-tuning
TRAINING_CONFIG = {
    'batch_size': 64,  # Increased for better gradient estimates
    'epochs': 50,  # More epochs for better convergence
    'learning_rate': 2e-5,  # Slightly higher for fine-tuning
    'num_workers': 4,
    'patience': 15,  # More patience
    'target_accuracy': 0.70,  # Realistic target
}

# Model configuration
MODEL_CONFIG = {
    'model_name': 'openai/clip-vit-base-patch32',
    'freeze_layers': 4,  # Fewer frozen layers for more fine-tuning
    'feature_dim': 512,
}

# Triplet Loss configuration
TRIPLET_CONFIG = {
    'margin': 0.5,  # Reduced margin for tighter clustering
    'distance_metric': 'euclidean',
}

# Optimizer configuration
OPTIMIZER_CONFIG = {
    'optimizer': 'AdamW',
    'weight_decay': 0.01,  # Increased regularization
    'scheduler': 'CosineAnnealingLR',
}

# Save configuration
SAVE_CONFIG = {
    'save_dir': 'temp_training_output',
    'save_best': True,
    'save_final': True,
    'save_history': True,
    'save_plots': True,
}

# Evaluation configuration
EVALUATION_CONFIG = {
    'eval_batches': 50,
    'full_eval_batches': 200,
    'recommendation_k': 10,
}

