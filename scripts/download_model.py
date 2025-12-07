#!/usr/bin/env python3
"""
Download model from GCS to local experiments directory
"""
import os
import sys
from pathlib import Path

try:
    from google.cloud import storage
except ImportError:
    print("❌ google-cloud-storage not installed")
    print("   Install with: pip install google-cloud-storage")
    sys.exit(1)

def download_model(experiment_id="exp_004", local_experiments_dir=None):
    """Download model from GCS"""
    if local_experiments_dir is None:
        # Default to project experiments directory
        project_root = Path(__file__).parent.parent
        local_experiments_dir = project_root / "src" / "models" / "train" / "experiments"
    
    local_experiments_dir = Path(local_experiments_dir)
    experiment_dir = local_experiments_dir / experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=True)
    
    gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
    gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
    model_path = f"experiments/{experiment_id}/best_model.pth"
    
    print(f"📥 Downloading model from GCS...")
    print(f"   Bucket: {gcp_bucket_name}")
    print(f"   Path: {model_path}")
    print(f"   Local: {experiment_dir / 'best_model.pth'}")
    
    try:
        client = storage.Client(project=gcp_project_id)
        bucket = client.bucket(gcp_bucket_name)
        blob = bucket.blob(model_path)
        
        if not blob.exists():
            print(f"❌ Model not found at gs://{gcp_bucket_name}/{model_path}")
            print(f"   Trying to find available models...")
            
            # List available experiments
            prefix = "experiments/"
            blobs = list(bucket.list_blobs(prefix=prefix))
            experiments = set()
            for b in blobs:
                if "best_model.pth" in b.name:
                    exp = b.name.replace(prefix, "").split("/")[0]
                    experiments.add(exp)
            
            if experiments:
                print(f"   Available experiments: {sorted(experiments)}")
                if experiments:
                    latest_exp = sorted(experiments)[-1]
                    print(f"   Using latest: {latest_exp}")
                    model_path = f"experiments/{latest_exp}/best_model.pth"
                    blob = bucket.blob(model_path)
                    experiment_dir = local_experiments_dir / latest_exp
                    experiment_dir.mkdir(parents=True, exist_ok=True)
            else:
                print(f"❌ No models found in GCS")
                return False
        
        # Download model
        local_model_path = experiment_dir / "best_model.pth"
        print(f"   Downloading to {local_model_path}...")
        blob.download_to_filename(str(local_model_path))
        
        file_size = local_model_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Model downloaded successfully ({file_size:.2f} MB)")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print(f"   Make sure you have GCP credentials configured:")
        print(f"   - Run: gcloud auth application-default login")
        print(f"   - Or set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download model from GCS")
    parser.add_argument("--experiment-id", default="exp_004", help="Experiment ID (default: exp_004)")
    parser.add_argument("--experiments-dir", help="Local experiments directory")
    args = parser.parse_args()
    
    success = download_model(args.experiment_id, args.experiments_dir)
    sys.exit(0 if success else 1)

