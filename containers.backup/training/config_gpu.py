# GPU-optimized training config
DATA_CONFIG = {
    'gcp_bucket_name': 'styleme-data-bucket',
    'gcp_project_id': 'styleme-475201',
    'data_prefix': 'json',
    'images_prefix': 'images',
    'max_samples_per_file': None,
    'compatibility_threshold': 1,
    'max_compatible_items': 5,
}

# GPU Training configuration
TRAINING_CONFIG = {
    'batch_size': 64,  # Large batch size for GPU
    'epochs': 20,  # Training epochs
    'learning_rate': 5e-6,  # Learning rate
    'num_workers': 8,  # Multi-threaded data loading
    'patience': 10,  # Early stopping patience
    'target_accuracy': 0.85,  # Target accuracy
}

MODEL_CONFIG = {
    'model_name': 'openai/clip-vit-base-patch32',
    'freeze_layers': 8,
    'feature_dim': 512,
}

TRIPLET_CONFIG = {
    'margin': 0.7,
    'distance_metric': 'euclidean',
}

OPTIMIZER_CONFIG = {
    'optimizer': 'AdamW',
    'weight_decay': 0.005,
    'scheduler': 'CosineAnnealingLR',
}

SAVE_CONFIG = {
    'save_dir': 'temp_training_output',
    'save_best': True,
    'save_final': True,
    'save_history': True,
    'save_plots': True,
}

EVALUATION_CONFIG = {
    'eval_batches': 20,
    'full_eval_batches': 100,
    'recommendation_k': 5,
}
