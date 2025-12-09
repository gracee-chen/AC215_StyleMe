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

# Try to import psutil for resource monitoring (optional)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️  psutil not installed. Resource monitoring disabled. Install with: pip install psutil")

from model_training import FashionCLIPModel, TripletLoss, FashionTrainer
from .config import DATA_CONFIG, TRAINING_CONFIG, MODEL_CONFIG, TRIPLET_CONFIG, OPTIMIZER_CONFIG, SAVE_CONFIG
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
    
    # Check system resources before training
    print("\n🔍 Checking System Resources...")
    resource_warnings = []
    
    if HAS_PSUTIL:
        import shutil
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / 1024**3
        memory_total_gb = memory.total / 1024**3
        memory_available_gb = memory.available / 1024**3
        print(f"   Memory: {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB ({memory.percent}% used)")
        print(f"   Available: {memory_available_gb:.1f}GB")
        
        if memory.percent > 85:
            resource_warnings.append(f"⚠️  CRITICAL: Memory usage is {memory.percent:.1f}%! System may crash.")
            print(f"   {resource_warnings[-1]}")
            print("   💡 Recommendation: Reduce batch_size or max_preload_images")
        elif memory.percent > 70:
            resource_warnings.append(f"⚠️  WARNING: Memory usage is {memory.percent:.1f}% (high)")
            print(f"   {resource_warnings[-1]}")
        
        # Check disk space
        disk = shutil.disk_usage('/')
        disk_used_gb = disk.used / 1024**3
        disk_total_gb = disk.total / 1024**3
        disk_percent = disk.used / disk.total * 100
        print(f"   Disk: {disk_used_gb:.1f}GB / {disk_total_gb:.1f}GB ({disk_percent:.1f}% used)")
        if disk_percent > 90:
            resource_warnings.append(f"⚠️  WARNING: Disk usage is {disk_percent:.1f}% (very high)")
            print(f"   {resource_warnings[-1]}")
        
        # Check CPU load
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        print(f"   CPU: {cpu_percent}% used ({cpu_count} cores)")
        if cpu_percent > 85:
            resource_warnings.append(f"⚠️  WARNING: CPU usage is {cpu_percent:.1f}% (very high)")
            print(f"   {resource_warnings[-1]}")
            print("   ✅ num_workers=0 should prevent further CPU overload")
        
        # Check GPU memory if available
        if torch.cuda.is_available():
            gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            gpu_memory_allocated = torch.cuda.memory_allocated() / 1024**3
            gpu_memory_reserved = torch.cuda.memory_reserved() / 1024**3
            gpu_memory_percent = (gpu_memory_reserved / gpu_memory_total) * 100
            print(f"   GPU Memory: {gpu_memory_reserved:.1f}GB / {gpu_memory_total:.1f}GB ({gpu_memory_percent:.1f}% reserved)")
            if gpu_memory_percent > 90:
                resource_warnings.append(f"⚠️  CRITICAL: GPU memory is {gpu_memory_percent:.1f}%! May cause OOM.")
                print(f"   {resource_warnings[-1]}")
                print("   💡 Recommendation: Reduce batch_size")
            elif gpu_memory_percent > 70:
                resource_warnings.append(f"⚠️  WARNING: GPU memory is {gpu_memory_percent:.1f}% (high)")
                print(f"   {resource_warnings[-1]}")
    else:
        print("   (Resource monitoring unavailable - install psutil for detailed info)")
        print("   💡 Install: pip install psutil")
    
    # Auto-adjust batch_size if resources are critical
    auto_adjust = TRAINING_CONFIG.get('auto_adjust_batch_size', True)
    if resource_warnings and auto_adjust and HAS_PSUTIL:
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            original_batch_size = batch_size
            batch_size = max(16, batch_size // 2)  # Reduce by half, minimum 16
            if batch_size != original_batch_size:
                print(f"\n   🔧 Auto-adjusting batch_size: {original_batch_size} → {batch_size} (memory safety)")
    
    if resource_warnings:
        print("\n" + "="*60)
        print("⚠️  RESOURCE WARNINGS DETECTED")
        print("="*60)
        print("Before starting training, consider:")
        print("  1. Close other heavy processes")
        print("  2. Reduce batch_size in fine_tune_config.py")
        print("  3. Reduce max_preload_images in fine_tune_config.py")
        print("  4. Monitor resources in another terminal:")
        print("     cd src/models/train && ./monitor_resources.sh")
        print("="*60)
        response = input("\nContinue with training? (y/n): ").strip().lower()
        if response != 'y':
            print("Training cancelled by user.")
            sys.exit(0)
    
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
    
    # Create dataloaders with optimized settings for speed
    from src.datapipeline.dataloader import create_dataloader, FashionTripletDataset
    
    batch_size = TRAINING_CONFIG.get('batch_size', 24)
    num_workers = TRAINING_CONFIG.get('num_workers', 0)  # 0 = single-threaded, safer for VM
    pin_memory = TRAINING_CONFIG.get('pin_memory', False)  # Disable to save memory
    prefetch_factor = TRAINING_CONFIG.get('prefetch_factor', 2)
    preload_images = TRAINING_CONFIG.get('preload_images', True)  # Preload images to cache
    
    print(f"\n📦 DataLoader Configuration (I/O Optimized to Prevent SSH Disconnection):")
    print(f"   Batch Size: {batch_size}")
    print(f"   Num Workers: {num_workers} (0 = single-threaded, prevents I/O contention)")
    print(f"   Pin Memory: {pin_memory} (disabled to save memory and reduce I/O)")
    print(f"   Prefetch Factor: {prefetch_factor} (reduced to minimize I/O pressure)")
    print(f"   Preload Images: {preload_images} (load ALL images to memory before training)")
    if TRAINING_CONFIG.get('io_throttle', False):
        print(f"   I/O Throttling: Enabled ({TRAINING_CONFIG.get('io_delay_ms', 0.1)*1000:.1f}ms delay)")
    print(f"   Max Cache Size: {TRAINING_CONFIG.get('max_cache_size', 20000)} (large enough for all images)")
    
    # Create dataset first (needed for preloading)
    local_cache_dir = DATA_CONFIG.get('local_cache_dir')
    if local_cache_dir:
        local_cache_dir = Path(local_cache_dir)
        if local_cache_dir.exists() and len(list(local_cache_dir.glob("*.jpg"))) > 0:
            print(f"✅ Found local image cache: {len(list(local_cache_dir.glob('*.jpg')))} images")
        else:
            print(f"⚠️  Local cache directory exists but is empty: {local_cache_dir}")
            print(f"   Run: python scripts/download_gcs_images.py --cache-dir {local_cache_dir}")
            response = input("   Continue with GCS download? (y/n): ").strip().lower()
            if response != 'y':
                print("Training cancelled.")
                sys.exit(0)
    
    dataset = FashionTripletDataset(
        gcp_bucket_name=DATA_CONFIG['gcp_bucket_name'],
        gcp_project_id=DATA_CONFIG['gcp_project_id'],
        data_prefix=DATA_CONFIG['data_prefix'],
        images_prefix=DATA_CONFIG['images_prefix'],
        max_samples_per_file=DATA_CONFIG.get('max_samples_per_file'),
        local_cache_dir=local_cache_dir
    )
    dataset._preload_images = preload_images
    dataset._max_preload_images = TRAINING_CONFIG.get('max_preload_images', 5000)
    # Update dataset's cache size limit (increase to hold all images in memory)
    dataset._max_cache_size = TRAINING_CONFIG.get('max_cache_size', 20000)
    # I/O throttling to prevent disk saturation and SSH disconnection
    dataset._io_throttle = TRAINING_CONFIG.get('io_throttle', False)
    dataset._io_delay_ms = TRAINING_CONFIG.get('io_delay_ms', 0.1)
    
    # Create dataloaders (pass dataset to enable preloading)
    train_loader, val_loader, test_loader = create_dataloader(
        gcp_bucket_name=DATA_CONFIG['gcp_bucket_name'],
        gcp_project_id=DATA_CONFIG['gcp_project_id'],
        data_prefix=DATA_CONFIG['data_prefix'],
        images_prefix=DATA_CONFIG['images_prefix'],
        batch_size=batch_size,
        num_workers=num_workers,
        max_samples_per_file=DATA_CONFIG.get('max_samples_per_file'),
        pin_memory=pin_memory,
        prefetch_factor=prefetch_factor,
        dataset=dataset  # Pass pre-created dataset for preloading
    )
    
    # Check if gradient accumulation is configured
    grad_accum = TRAINING_CONFIG.get('gradient_accumulation_steps', 1)
    if grad_accum > 1:
        print(f"   Gradient Accumulation: {grad_accum} steps (effective batch size: {batch_size * grad_accum})")
    
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
    
    # Clear initial memory
    print("\n🧹 Clearing initial memory...")
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    # Train
    print("\nStarting training...")
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=TRAINING_CONFIG['epochs'],
        learning_rate=TRAINING_CONFIG['learning_rate'],
        save_dir=str(checkpoints_dir)
    )
    
    # Final memory cleanup
    print("\n🧹 Final memory cleanup...")
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        print(f"   Final GPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f}GB")
    
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

