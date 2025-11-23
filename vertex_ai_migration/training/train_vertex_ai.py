#!/usr/bin/env python3
"""
Vertex AI Custom Training Entry Point
Adapts the existing fine-tuning script for Vertex AI
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "models" / "train"))

def main():
    parser = argparse.ArgumentParser(description="Vertex AI Custom Training Job")
    
    # Training arguments
    parser.add_argument('--data-version', required=True, help='Data version tag (e.g., catalog-v_men_women_20251123)')
    parser.add_argument('--epochs', type=int, default=20, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=5e-6, help='Learning rate')
    parser.add_argument('--patience', type=int, default=10, help='Early stopping patience')
    
    # Vertex AI specific paths (set by Vertex AI)
    parser.add_argument('--model-dir', type=str, default=None, 
                       help='Model output directory (defaults to AIP_MODEL_DIR env var)')
    parser.add_argument('--checkpoint-dir', type=str, default=None,
                       help='Checkpoint directory (defaults to AIP_CHECKPOINT_DIR env var)')
    
    args = parser.parse_args()
    
    # Get Vertex AI environment variables
    # AIP_MODEL_DIR: Directory for saving model artifacts
    # AIP_CHECKPOINT_DIR: Directory for saving checkpoints
    model_dir = args.model_dir or os.environ.get('AIP_MODEL_DIR', '/gcs/model')
    checkpoint_dir = args.checkpoint_dir or os.environ.get('AIP_CHECKPOINT_DIR', '/gcs/checkpoints')
    
    # GCS paths
    gcs_bucket = os.environ.get('GCP_BUCKET_NAME', 'styleme-data-bucket')
    gcs_project = os.environ.get('GCP_PROJECT_ID', 'styleme-475201')
    
    print("=" * 60)
    print("Vertex AI Custom Training Job")
    print("=" * 60)
    print(f"Data Version: {args.data_version}")
    print(f"Model Directory: {model_dir}")
    print(f"Checkpoint Directory: {checkpoint_dir}")
    print(f"GCS Bucket: {gcs_bucket}")
    print(f"GCS Project: {gcs_project}")
    print("=" * 60)
    
    # Ensure directories exist
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Import and run training
    # Use the existing run_fine_tuning.py logic
    from run_fine_tuning import main as run_training
    
    # Modify environment to use Vertex AI paths
    original_experiments_dir = os.environ.get('EXPERIMENTS_DIR')
    os.environ['EXPERIMENTS_DIR'] = checkpoint_dir
    
    try:
        # Run training with modified arguments
        # We'll need to adapt run_fine_tuning.py to accept these args
        import subprocess
        
        training_script = project_root / "src" / "models" / "train" / "run_fine_tuning.py"
        
        cmd = [
            sys.executable,
            str(training_script),
            "--data-version", args.data_version,
            "--epochs", str(args.epochs),
            "--batch-size", str(args.batch_size),
            "--learning-rate", str(args.learning_rate),
            "--patience", str(args.patience),
            "--output-dir", model_dir
        ]
        
        print(f"Running training command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        
        # Copy final model to model_dir
        # The training script should save to model_dir
        print(f"\n✅ Training completed successfully")
        print(f"Model saved to: {model_dir}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Training failed with error: {e}")
        sys.exit(1)
    finally:
        # Restore original environment
        if original_experiments_dir:
            os.environ['EXPERIMENTS_DIR'] = original_experiments_dir

if __name__ == "__main__":
    main()

