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
    # Local cache for images (set to None to use GCS directly, or path to cache directory)
    'local_cache_dir': 'data/local_image_cache',  # Set to None to disable local cache
}

# Training configuration - Optimized for I/O safety (prevent SSH disconnection)
TRAINING_CONFIG = {
    'batch_size': 24,  # Balanced: faster than 16, safer than 32
    'epochs': 12,  # Reduced to complete in ~1 hour (was 50)
    'learning_rate': 2e-5,  # Slightly higher for fine-tuning
    'num_workers': 0,  # Keep 0 for VM safety (prevents CPU overload and I/O contention)
    'patience': 8,  # Reduced patience for faster training
    'target_accuracy': 0.70,  # Realistic target
    'gradient_accumulation_steps': 2,  # Reduced since batch_size increased
    'pin_memory': False,  # Disable to save memory and reduce I/O
    'prefetch_factor': 1,  # MINIMUM prefetch to reduce I/O pressure (was 2)
    'preload_images': True,  # Preload ALL images to memory before training
    'max_preload_images': None,  # Load ALL images (None = no limit) to avoid disk I/O during training
    'max_cache_size': 20000,  # Very large cache to hold all images in memory (was 8000)
    'io_throttle': True,  # Enable I/O throttling to prevent disk saturation
    'io_delay_ms': 0.1,  # Small delay between I/O operations during preload
    'monitor_resources': True,  # Enable resource monitoring
    'auto_adjust_batch_size': True,  # Auto-reduce batch_size if OOM
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

