#!/usr/bin/env python3
"""
Fine-tuning script with data versioning support
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add to path
sys.path.append(os.path.dirname(__file__))

from model_training import FashionCLIPModel, TripletLoss, FashionTrainer
from config import DATA_CONFIG, TRAINING_CONFIG, MODEL_CONFIG, TRIPLET_CONFIG, OPTIMIZER_CONFIG, SAVE_CONFIG
import torch

def load_fine_tune_config(config_path: str = None):
    """Load fine-tuning config, fallback to default if not provided"""
    if config_path and os.path.exists(config_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("fine_tune_config", config_path)
        fine_tune_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fine_tune_config)
        return fine_tune_config
    return None

def create_experiment_record(config, data_version: str = None):
    """Create experiment record with data version reference"""
    experiment_id = f"fine_tune_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    record = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now().isoformat(),
        "data_version": data_version or DATA_CONFIG.get('data_version', 'unknown'),
        "config": {
            "model": {
                "architecture": MODEL_CONFIG['model_name'],
                "frozen_layers": MODEL_CONFIG['freeze_layers'],
                "feature_dimension": MODEL_CONFIG['feature_dim']
            },
            "training": {
                "epochs": TRAINING_CONFIG['epochs'],
                "batch_size": TRAINING_CONFIG['batch_size'],
                "learning_rate": TRAINING_CONFIG['learning_rate'],
                "optimizer": OPTIMIZER_CONFIG['optimizer'],
                "scheduler": OPTIMIZER_CONFIG['scheduler'],
                "patience": TRAINING_CONFIG['patience'],
                "target_accuracy": TRAINING_CONFIG['target_accuracy']
            },
            "triplet_loss": {
                "margin": TRIPLET_CONFIG['margin'],
                "distance_metric": TRIPLET_CONFIG['distance_metric']
            },
            "data": {
                "gcp_bucket": DATA_CONFIG['gcp_bucket_name'],
                "data_prefix": DATA_CONFIG['data_prefix'],
                "images_prefix": DATA_CONFIG['images_prefix']
            }
        }
    }
    
    return experiment_id, record

def main():
    """Main fine-tuning function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fine-tune FashionCLIP model')
    parser.add_argument('--config', default=None, help='Path to fine-tuning config file')
    parser.add_argument('--data-version', default=None, help='Data version tag')
    parser.add_argument('--resume', default=None, help='Resume from checkpoint')
    parser.add_argument('--device', default=None, help='Device to use (cuda/cpu). Default: auto-detect GPU')
    
    args = parser.parse_args()
    
    # Load fine-tuning config if provided
    fine_tune_config = load_fine_tune_config(args.config)
    if fine_tune_config:
        print("Using fine-tuning config from:", args.config)
        # Update configs
        globals()['TRAINING_CONFIG'].update(fine_tune_config.TRAINING_CONFIG)
        globals()['MODEL_CONFIG'].update(fine_tune_config.MODEL_CONFIG)
        globals()['TRIPLET_CONFIG'].update(fine_tune_config.TRIPLET_CONFIG)
        globals()['OPTIMIZER_CONFIG'].update(fine_tune_config.OPTIMIZER_CONFIG)
    
    # Create experiment record
    data_version = args.data_version or DATA_CONFIG.get('data_version', 'unknown')
    experiment_id, experiment_record = create_experiment_record(None, data_version)
    
    print("="*60)
    print("Fine-Tuning FashionCLIP Model")
    print("="*60)
    print(f"Experiment ID: {experiment_id}")
    print(f"Data Version: {data_version}")
    print(f"Config: {json.dumps(experiment_record['config'], indent=2)}")
    print("="*60)
    
    # Initialize model - prefer GPU
    if args.device:
        device = torch.device(args.device)
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        
        # Initialize cuDNN - disable if it fails (will use standard CUDA operations)
        try:
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = False
            # Test cuDNN initialization
            dummy = torch.zeros(1, 1, 1, 1).cuda()
            _ = torch.nn.functional.conv2d(dummy, torch.zeros(1, 1, 1, 1).cuda())
            del dummy
            torch.cuda.empty_cache()
            print("✅ cuDNN initialized successfully")
        except Exception as e:
            print(f"⚠️  cuDNN initialization failed: {e}")
            print("   Disabling cuDNN, using standard CUDA operations (may be slower)")
            torch.backends.cudnn.enabled = False
    else:
        print("❌ ERROR: GPU not available!")
        print("   CUDA is required for fine-tuning. Please ensure:")
        print("   1. CUDA is installed: nvidia-smi")
        print("   2. PyTorch with CUDA support is installed")
        print("   3. GPU is accessible")
        sys.exit(1)
    
    print(f"🚀 Using device: {device}")
    
    model = FashionCLIPModel(
        model_name=MODEL_CONFIG['model_name'],
        freeze_layers=MODEL_CONFIG['freeze_layers']
    ).to(device)
    
    # Resume from checkpoint if provided
    if args.resume and os.path.exists(args.resume):
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"Resumed from checkpoint: {args.resume}")
    
    # Create dataloaders
    from src.datapipeline.dataloader import create_dataloader
    
    train_loader, val_loader, test_loader = create_dataloader(
        gcp_bucket_name=DATA_CONFIG['gcp_bucket_name'],
        gcp_project_id=DATA_CONFIG['gcp_project_id'],
        data_prefix=DATA_CONFIG['data_prefix'],
        images_prefix=DATA_CONFIG['images_prefix'],
        batch_size=TRAINING_CONFIG['batch_size'],
        num_workers=TRAINING_CONFIG['num_workers'],
        max_samples_per_file=DATA_CONFIG.get('max_samples_per_file')
    )
    
    # Create experiments directory before training
    experiments_dir = Path(__file__).parent / "experiments" / experiment_id
    experiments_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = experiments_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize trainer
    loss_fn = TripletLoss(margin=TRIPLET_CONFIG['margin'])
    
    trainer = FashionTrainer(
        model=model,
        loss_fn=loss_fn,
        device=device,
        require_gpu=True  # Force GPU usage for fine-tuning
    )
    
    # Train
    print("\nStarting training...")
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=TRAINING_CONFIG['epochs'],
        learning_rate=TRAINING_CONFIG['learning_rate'],
        save_dir=str(checkpoints_dir)
    )
    
    # Get history from trainer
    history = {
        'train_losses': trainer.train_losses,
        'train_accuracies': trainer.train_accuracies,
        'val_losses': trainer.val_losses,
        'val_accuracies': trainer.val_accuracies
    }
    
    experiment_record['results'] = {
        'best_val_acc': max(history['val_accuracies']) if history['val_accuracies'] else 0,
        'final_train_loss': history['train_losses'][-1] if history['train_losses'] else 0,
        'final_val_loss': history['val_losses'][-1] if history['val_losses'] else 0,
        'final_train_acc': history['train_accuracies'][-1] if history['train_accuracies'] else 0,
        'final_val_acc': history['val_accuracies'][-1] if history['val_accuracies'] else 0,
        'epochs_trained': len(history['train_losses'])
    }
    
    with open(experiments_dir / "experiment_record.json", "w") as f:
        json.dump(experiment_record, f, indent=2)
    
    print(f"\nExperiment record saved to: {experiments_dir}/experiment_record.json")
    print(f"Best validation accuracy: {experiment_record['results']['best_val_acc']:.4f}")

if __name__ == "__main__":
    main()

