"""
Inference Service
Handles query image → search wardrobe → fallback to catalog → return recommendations
"""

import os
import sys
import json
import torch
import numpy as np
import pandas as pd
import faiss
import subprocess
from pathlib import Path
from PIL import Image
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from src.models.train.model_training import FashionCLIPModel

# Add src to path (support both container and local paths)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, project_root)


class InferenceService:
    def __init__(self, catalog_dir, experiments_dir, wardrobes_dir, device=None,
                 bg_removal_enabled=False, bg_removal_model="briaai/RMBG-1.4"):
        self.catalog_dir = Path(catalog_dir)
        self.experiments_dir = Path(experiments_dir)
        self.wardrobes_dir = Path(wardrobes_dir)
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"🔧 Initializing Inference Service")
        print(f"   Device: {self.device}")
        
        # Initialize background remover (optional, disabled by default)
        if bg_removal_enabled:
            print("🎨 Initializing background remover...")
            try:
                from src.datapipeline.bg_removal.background_removal import BackgroundRemover
                self.bg_remover = BackgroundRemover(
                    model_name=bg_removal_model,
                    device=str(self.device) if str(self.device) != 'cpu' else None
                )
                self.bg_removal_enabled = True
                print("   ✅ Background remover ready")
            except Exception as e:
                print(f"   ⚠️  Failed to initialize background remover: {str(e)}")
                print("   ⚠️  Continuing without background removal")
                self.bg_remover = None
                self.bg_removal_enabled = False
        else:
            self.bg_remover = None
            self.bg_removal_enabled = False
            print("   ℹ️  Background removal disabled (default)")
        
        # Load model
        self.model = self._load_model()
        self.transform = self._get_transform()
        
        # Load catalog
        self.catalog_index, self.catalog_meta, self.catalog_idmap = self._load_catalog()
        
        print(f"✅ Inference Service ready")
    
    def _load_model(self):
        """Load trained FashionCLIP model"""
        print("📦 Loading model...")
        
        # Check if using GCS path and download to local temp if needed
        experiments_path = str(self.experiments_dir)
        use_gcs_client = False
        local_experiments_dir = None
        
        # If path starts with /gcs/ or looks like GCS path, try to access via filesystem first
        if experiments_path.startswith('/gcs/'):
            # Check if gcsfuse mount worked
            if os.path.exists(experiments_path) and os.listdir(experiments_path):
                print(f"   Using GCS mount at {experiments_path}")
                local_experiments_dir = Path(experiments_path)
            else:
                # Mount failed, use GCS client library
                use_gcs_client = True
                print(f"   GCS mount not available, using GCS client library")
        elif 'gs://' in experiments_path or 'styleme-production' in experiments_path:
            # Explicit GCS path, use client library
            use_gcs_client = True
            print(f"   Using GCS client library for {experiments_path}")
        else:
            # Local path
            local_experiments_dir = Path(experiments_path)
        
        model_path = None
        
        if use_gcs_client:
            # Find and download model from GCS
            try:
                from google.cloud import storage
                from google.auth.exceptions import DefaultCredentialsError
                
                # Check for credentials - prefer service account key file, fall back to gcloud default credentials
                creds_path = '/app/gcs-credentials.json'
                if os.path.exists(creds_path):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
                    print(f"   Using service account key from {creds_path}")
                else:
                    # Will use Application Default Credentials (from gcloud auth application-default login)
                    print(f"   Using Application Default Credentials (gcloud)")
                
                gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
                gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
                
                print(f"   Attempting to connect to GCS bucket {gcp_bucket_name}...")
                client = storage.Client(project=gcp_project_id)
                bucket = client.bucket(gcp_bucket_name)
                
                # Extract prefix from experiments_dir path
                if experiments_path.startswith('/gcs/'):
                    prefix = experiments_path.replace('/gcs/', '').replace(gcp_bucket_name, '').lstrip('/')
                else:
                    prefix = 'experiments/'
                
                if not prefix.endswith('/'):
                    prefix += '/'
                
                print(f"   Searching GCS bucket {gcp_bucket_name} with prefix {prefix}")
                
                # List experiment directories
                exp_dirs = set()
                try:
                    for blob in bucket.list_blobs(prefix=prefix):
                        # Extract exp_XXX from path
                        path_parts = blob.name.replace(prefix, '').split('/')
                        if path_parts and path_parts[0].startswith('exp_'):
                            exp_dirs.add(path_parts[0])
                except Exception as e:
                    print(f"   ⚠️  Error listing blobs from GCS: {e}")
                    raise
                
                print(f"   Found experiment directories: {sorted(exp_dirs)}")
                
                # Sort experiment directories (highest number first)
                exp_numbers = []
                for exp_dir in exp_dirs:
                    try:
                        num = int(exp_dir.replace('exp_', ''))
                        exp_numbers.append((num, exp_dir))
                    except ValueError:
                        continue
                
                exp_numbers.sort(reverse=True)
                print(f"   Sorted experiments (highest first): {[exp_dir for _, exp_dir in exp_numbers]}")
                
                # Find first experiment with best_model.pth
                for exp_num, exp_dir in exp_numbers:
                    model_blob_path = f"{prefix}{exp_dir}/best_model.pth"
                    blob = bucket.blob(model_blob_path)
                    if blob.exists():
                        # Download to local temp file (ephemeral)
                        import tempfile
                        temp_dir = Path(tempfile.gettempdir()) / "styleme_models"
                        temp_dir.mkdir(exist_ok=True)
                        local_model_path = temp_dir / f"{exp_dir}_best_model.pth"
                        
                        # Check if already downloaded
                        if local_model_path.exists():
                            print(f"   ✅ Model already cached: {local_model_path}")
                        else:
                            print(f"   Downloading {model_blob_path} to {local_model_path}...")
                            blob.download_to_filename(str(local_model_path))
                        model_path = local_model_path
                        print(f"   ✅ Using model: {local_model_path}")
                        break
                    else:
                        print(f"   ⚠️  Model not found at {model_blob_path}")
            except DefaultCredentialsError as e:
                print(f"   ❌ GCS credentials not found: {e}")
                print(f"   ⚠️  Cannot access GCS bucket. Please configure GCP credentials.")
                raise FileNotFoundError("No trained model found - GCS credentials not configured")
            except Exception as e:
                print(f"   ❌ Error accessing GCS: {e}")
                raise
        else:
            # Use filesystem access (local or mounted)
            for exp_dir in sorted(local_experiments_dir.glob("exp_*"), reverse=True):
                best_model = exp_dir / "best_model.pth"
                if best_model.exists():
                    model_path = best_model
                    break
        
        if model_path is None:
            raise FileNotFoundError("No trained model found in experiments directory")
        
        print(f"   Loading model from: {model_path}")
        
        # Verify file exists and is readable
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        file_size = Path(model_path).stat().st_size
        print(f"   Model file size: {file_size / (1024**3):.2f} GB")
        
        if file_size < 1024 * 1024:  # Less than 1MB is suspicious
            raise ValueError(f"Model file seems too small: {file_size} bytes")
        
        # Load checkpoint with retry logic for network/IO issues
        max_retries = 3
        checkpoint = None
        for attempt in range(max_retries):
            try:
                checkpoint = torch.load(str(model_path), map_location='cpu')  # Load to CPU first to avoid meta tensor issues
                break
            except (EOFError, OSError, RuntimeError) as e:
                if attempt < max_retries - 1:
                    print(f"   ⚠️  Attempt {attempt + 1} failed to load model: {e}")
                    print(f"   Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    raise RuntimeError(f"Failed to load model after {max_retries} attempts: {e}")
        
        if checkpoint is None:
            raise RuntimeError("Failed to load checkpoint")
        
        # Verify checkpoint structure
        if 'model_state_dict' not in checkpoint:
            raise ValueError("Checkpoint missing 'model_state_dict' key")
        
        # Create model and move to device before loading state dict
        model = FashionCLIPModel()
        model = model.to(self.device)
        
        # Load state dict with strict=False to handle any mismatches
        try:
            model.load_state_dict(checkpoint['model_state_dict'], strict=False)
        except Exception as e:
            print(f"   ⚠️  Warning: State dict loading had issues: {e}")
            # Try loading with map_location to device as fallback
            try:
                checkpoint_device = torch.load(str(model_path), map_location=self.device)
                model.load_state_dict(checkpoint_device['model_state_dict'], strict=False)
            except Exception as e2:
                raise RuntimeError(f"Failed to load state dict with both methods: {e}, {e2}")
        
        model.eval()
        print(f"   ✅ Model loaded successfully")
        
        return model
    
    def _get_transform(self):
        """Get image transformation"""
        from torchvision import transforms
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def _load_catalog(self):
        """Load catalog FAISS index and metadata"""
        print("📚 Loading catalog...")
        
        catalog_path = str(self.catalog_dir)
        use_gcs_client = False
        local_catalog_dir = None
        
        # Check if using GCS path
        if catalog_path.startswith('/gcs/'):
            if os.path.exists(catalog_path) and os.listdir(catalog_path):
                print(f"   Using GCS mount at {catalog_path}")
                local_catalog_dir = Path(catalog_path)
            else:
                use_gcs_client = True
                print(f"   GCS mount not available, using GCS client library")
        elif 'gs://' in catalog_path or 'styleme-production' in catalog_path:
            use_gcs_client = True
            print(f"   Using GCS client library for {catalog_path}")
        else:
            local_catalog_dir = Path(catalog_path)
        
        if use_gcs_client:
            # Download catalog files from GCS to local temp
            from google.cloud import storage
            import tempfile
            import io
            
            gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
            gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
            
            client = storage.Client(project=gcp_project_id)
            bucket = client.bucket(gcp_bucket_name)
            
            # Extract prefix
            if catalog_path.startswith('/gcs/'):
                prefix = catalog_path.replace('/gcs/', '').replace(gcp_bucket_name, '').lstrip('/')
            else:
                prefix = 'catalog/'
            
            if not prefix.endswith('/'):
                prefix += '/'
            
            print(f"   Searching GCS bucket {gcp_bucket_name} with prefix {prefix}")
            
            # Find catalog versions
            catalog_versions = set()
            for blob in bucket.list_blobs(prefix=prefix):
                path_parts = blob.name.replace(prefix, '').split('/')
                if path_parts and path_parts[0].startswith('v_'):
                    catalog_versions.add(path_parts[0])
            
            if not catalog_versions:
                raise FileNotFoundError(f"No catalog versions found in GCS {gcp_bucket_name}/{prefix}")
            
            # Get latest version
            catalog_version_name = sorted(catalog_versions)[-1]
            print(f"   Version: {catalog_version_name}")
            
            # Download to temp directory (ephemeral, will be re-downloaded if needed)
            temp_catalog_dir = Path(tempfile.gettempdir()) / "styleme_catalog" / catalog_version_name
            temp_catalog_dir.mkdir(parents=True, exist_ok=True)
            
            # Files to download
            files_to_download = [
                'catalog.index.faiss',
                'catalog_meta.parquet',
                'idmap.npy'
            ]
            
            for filename in files_to_download:
                blob_path = f"{prefix}{catalog_version_name}/{filename}"
                blob = bucket.blob(blob_path)
                if not blob.exists():
                    raise FileNotFoundError(f"Catalog file not found: {blob_path}")
                
                local_path = temp_catalog_dir / filename
                print(f"   Downloading {filename}...")
                blob.download_to_filename(str(local_path))
            
            local_catalog_dir = temp_catalog_dir
            catalog_version = local_catalog_dir
        else:
            # Use filesystem access
            catalog_versions = [d for d in sorted(local_catalog_dir.glob("v_*")) if d.is_dir()]
            if not catalog_versions:
                raise FileNotFoundError(f"No catalog found in {self.catalog_dir}")
            catalog_version = catalog_versions[-1]
            print(f"   Version: {catalog_version.name}")
        
        # Load FAISS index
        index_path = catalog_version / "catalog.index.faiss"
        index = faiss.read_index(str(index_path))
        print(f"   Index: {index.ntotal} items")
        
        # Load metadata
        meta_path = catalog_version / "catalog_meta.parquet"
        meta = pd.read_parquet(meta_path)
        print(f"   Metadata: {len(meta)} items")
        
        # Load ID map
        idmap_path = catalog_version / "idmap.npy"
        idmap = np.load(idmap_path, allow_pickle=True)
        
        return index, meta, idmap
    
    def embed_image(self, image_path: str) -> np.ndarray:
        """Generate normalized embedding for an image"""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with torch.no_grad():
            # Step 1: Load image
            image = Image.open(image_path).convert('RGB')
            
            # Step 2: Remove background (REQUIRED if enabled)
            # Background removal is mandatory for all images when enabled
            if self.bg_removal_enabled and self.bg_remover:
                # Remove background (returns PIL Image with transparent bg)
                # This is REQUIRED - no fallback to original image
                image = self.bg_remover.remove_background(image)
                
                # Convert RGBA to RGB with white background
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if len(image.split()) == 4:  # Has alpha channel
                        background.paste(image, mask=image.split()[3])
                    else:
                        background.paste(image)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
            
            # Step 3: Transform and embed
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            embedding = self.model(image_tensor)
            
            # L2 normalize
            embedding = embedding / torch.norm(embedding, p=2, dim=1, keepdim=True)
            
            return embedding.cpu().numpy().astype('float32')
    
    def search_wardrobe(self, user_id: str, query_embedding: np.ndarray, k: int = 5, query_category: str = None, exclude_image_path: str = None) -> Tuple[Optional[List[Dict]], float]:
        """Search user's wardrobe FAISS index"""
        wardrobe_path = self.wardrobes_dir / user_id
        use_gcs_client = False
        local_wardrobe_path = None
        
        # Check if we're in Cloud Run (always use GCS client in Cloud Run)
        is_cloud_run = os.getenv('CLOUD_RUN', '').lower() == 'true' or os.getenv('K_SERVICE') is not None
        
        wardrobe_path_str = str(wardrobe_path)
        
        # Always use GCS client if:
        # 1. In Cloud Run (incremental updates save directly to GCS)
        # 2. Path starts with /gcs/ (incremental updates use GCS client, not mount)
        # 3. Path contains gs:// or styleme-production
        # This ensures we read from the same place we write (GCS client, not mount)
        if is_cloud_run:
            use_gcs_client = True
            print(f"   Cloud Run detected, using GCS client for wardrobe...")
        elif wardrobe_path_str.startswith('/gcs/'):
            # Even if mount exists, use GCS client to match incremental update behavior
            use_gcs_client = True
            print(f"   GCS path detected, using GCS client (incremental updates use client, not mount)...")
        elif 'gs://' in wardrobe_path_str or 'styleme-production' in wardrobe_path_str:
            use_gcs_client = True
        else:
            local_wardrobe_path = wardrobe_path
        
        # If local path doesn't exist, try GCS
        if not local_wardrobe_path or not local_wardrobe_path.exists():
            if use_gcs_client or wardrobe_path_str.startswith('/gcs/'):
                # Check GCS for wardrobe
                try:
                    from google.cloud import storage
                    import tempfile
                    
                    gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
                    gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
                    
                    client = storage.Client(project=gcp_project_id)
                    bucket = client.bucket(gcp_bucket_name)
                    
                    # Check if images exist in GCS
                    images_prefix = f"wardrobes/{user_id}/images/"
                    image_blobs = list(bucket.list_blobs(prefix=images_prefix))
                    image_files = [b for b in image_blobs if b.name.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    
                    if not image_files:
                        print(f"   ⚠️  No wardrobe images found in GCS for {user_id}")
                        return None, 0.0
                    
                    print(f"   📂 Found {len(image_files)} images in GCS for {user_id}")
                    
                    # Check if index exists in GCS
                    index_blob_path = f"wardrobes/{user_id}/wardrobe.index.faiss"
                    index_blob = bucket.blob(index_blob_path)
                    
                    # Check if index is stale (older than newest image) OR if it doesn't have category field
                    index_is_stale = False
                    if index_blob.exists():
                        index_updated = index_blob.updated
                        # Check if any image is newer than the index
                        if index_updated:
                            for img_blob in image_files:
                                if img_blob.updated and img_blob.updated > index_updated:
                                    index_is_stale = True
                                    print(f"   ⚠️  Wardrobe index is stale (newer images found)")
                                    break
                        
                        # Also check if index has category field (newer builds include it)
                        # Download parquet temporarily to check
                        try:
                            temp_check_dir = Path(tempfile.gettempdir()) / "styleme_wardrobe_check" / user_id
                            temp_check_dir.mkdir(parents=True, exist_ok=True)
                            parquet_blob = bucket.blob(f"wardrobes/{user_id}/wardrobe.parquet")
                            if parquet_blob.exists():
                                temp_parquet = temp_check_dir / "wardrobe.parquet"
                                parquet_blob.download_to_filename(str(temp_parquet))
                                check_meta = pd.read_parquet(temp_parquet)
                                if 'category' not in check_meta.columns:
                                    index_is_stale = True
                                    print(f"   ⚠️  Wardrobe index missing 'category' field - needs rebuild")
                                elif check_meta['category'].isna().all() or (check_meta['category'] == '').all():
                                    # Category field exists but all values are None/empty - needs rebuild
                                    index_is_stale = True
                                    print(f"   ⚠️  Wardrobe index has 'category' field but all values are empty - needs rebuild")
                        except Exception as check_error:
                            print(f"   ⚠️  Could not check index for category field: {check_error}")
                    
                    if not index_blob.exists() or index_is_stale:
                        # Index doesn't exist or is stale - don't build synchronously (causes timeout)
                        # Instead, return None and let async rebuild handle it
                        if index_is_stale:
                            print(f"   ⚠️  Wardrobe index is stale for {user_id} - async rebuild should handle this")
                        else:
                            print(f"   ⚠️  Wardrobe index not found for {user_id} - async rebuild should handle this")
                        print(f"   💡 Skipping wardrobe search (index will be built asynchronously)")
                        print(f"   📊 Returning catalog-only recommendations for now")
                        return None, 0.0
                    else:
                        # Index exists in GCS - download to temp and verify
                        print(f"   📥 Downloading wardrobe index from GCS...")
                        temp_wardrobe_dir = Path(tempfile.gettempdir()) / "styleme_wardrobes" / user_id
                        temp_wardrobe_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Download index files
                        index_files = {
                            'wardrobe.index.faiss': f"wardrobes/{user_id}/wardrobe.index.faiss",
                            'wardrobe.parquet': f"wardrobes/{user_id}/wardrobe.parquet",
                            'idmap.npy': f"wardrobes/{user_id}/idmap.npy"
                        }
                        
                        all_files_downloaded = True
                        for filename, gcs_path in index_files.items():
                            blob = bucket.blob(gcs_path)
                            if blob.exists():
                                local_path = temp_wardrobe_dir / filename
                                blob.download_to_filename(str(local_path))
                                # Verify parquet file is valid
                                if filename == 'wardrobe.parquet':
                                    try:
                                        test_meta = pd.read_parquet(local_path)
                                        if test_meta.empty:
                                            print(f"   ⚠️  Parquet file is empty, will rebuild")
                                            all_files_downloaded = False
                                            break
                                    except Exception as parquet_error:
                                        print(f"   ⚠️  Parquet file corrupted: {parquet_error}")
                                        print(f"   🔨 Will rebuild wardrobe index...")
                                        all_files_downloaded = False
                                        # Delete corrupted files
                                        for f in index_files.keys():
                                            (temp_wardrobe_dir / f).unlink(missing_ok=True)
                                        break
                            else:
                                print(f"   ⚠️  Index file {filename} not found in GCS")
                                all_files_downloaded = False
                                break
                        
                        # If download failed or files are corrupted, skip rebuild (async will handle it)
                        if not all_files_downloaded:
                            print(f"   ⚠️  Wardrobe index files corrupted or missing for {user_id}")
                            print(f"   💡 Skipping wardrobe search (async rebuild will handle this)")
                            print(f"   📊 Returning catalog-only recommendations for now")
                            return None, 0.0
                        else:
                            # Files downloaded successfully and verified - use them
                            local_wardrobe_path = temp_wardrobe_dir
                except Exception as gcs_error:
                    print(f"   ⚠️  Failed to access wardrobe from GCS: {gcs_error}")
                    return None, 0.0
            else:
                # Local path doesn't exist and not using GCS
                return None, 0.0
        
        index_path = local_wardrobe_path / "wardrobe.index.faiss"
        
        # Check if index exists - if not, skip build (async rebuild will handle it)
        # Don't build synchronously during recommendation requests (causes timeout)
        if not index_path.exists():
            # Check if we're in Cloud Run or using GCS - if so, async rebuild should handle it
            if is_cloud_run or use_gcs_client or wardrobe_path_str.startswith('/gcs/'):
                print(f"   ⚠️  Wardrobe index not found for {user_id}")
                print(f"   💡 Skipping wardrobe search (async rebuild will handle this)")
                print(f"   📊 Returning catalog-only recommendations for now")
            else:
                # Local filesystem - check if images exist
                images_dir = local_wardrobe_path / "images" if local_wardrobe_path else None
                if images_dir and images_dir.exists() and list(images_dir.glob("*.jpg")):
                    print(f"   ⚠️  Wardrobe index not found for {user_id} (local filesystem)")
                    print(f"   💡 Skipping synchronous build to avoid timeout")
                    print(f"   📊 Returning catalog-only recommendations for now")
            return None, 0.0
        
        try:
            # Load wardrobe index
            index = faiss.read_index(str(index_path))
            
            # Check if index is empty (wardrobe exists but has no items)
            if index.ntotal == 0:
                print(f"   ⚠️  Wardrobe index exists but is empty (0 items)")
                return [], 0.0
            
            # Load metadata with error handling for corrupted files
            meta_path = local_wardrobe_path / "wardrobe.parquet"
            try:
                meta = pd.read_parquet(meta_path)
            except Exception as parquet_error:
                print(f"   ⚠️  Error reading parquet file: {parquet_error}")
                # If corrupted and we're using GCS, try to rebuild
                if use_gcs_client:
                    print(f"   🔨 Attempting to rebuild corrupted wardrobe index...")
                    try:
                        from google.cloud import storage
                        import tempfile
                        
                        gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
                        gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
                        client = storage.Client(project=gcp_project_id)
                        bucket = client.bucket(gcp_bucket_name)
                        
                        # Download images again
                        images_prefix = f"wardrobes/{user_id}/images/"
                        image_blobs = list(bucket.list_blobs(prefix=images_prefix))
                        image_files = [b for b in image_blobs if b.name.lower().endswith(('.jpg', '.jpeg', '.png'))]
                        
                        if image_files:
                            temp_images_dir = local_wardrobe_path / "images"
                            temp_images_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Download images
                            for blob in image_files[:50]:
                                filename = blob.name.split('/')[-1]
                                local_img_path = temp_images_dir / filename
                                blob.download_to_filename(str(local_img_path))
                            
                            # Rebuild index
                            result = subprocess.run([
                                sys.executable,
                                "/app/build_user_wardrobe.py",
                                "--user-id", user_id,
                                "--wardrobe-dir", str(local_wardrobe_path),
                                "--experiments-dir", str(self.experiments_dir),
                                "--wardrobes-base-dir", str(local_wardrobe_path.parent)
                            ], capture_output=True, text=True, check=True, timeout=600)
                            
                            # Reload parquet
                            meta = pd.read_parquet(meta_path)
                            print(f"   ✅ Successfully rebuilt wardrobe index")
                        else:
                            raise Exception("No images found to rebuild index")
                    except Exception as rebuild_error:
                        print(f"   ❌ Failed to rebuild index: {rebuild_error}")
                        return None, 0.0
                else:
                    # Not using GCS, can't rebuild
                    raise parquet_error
            
            # Load ID map
            idmap_path = local_wardrobe_path / "idmap.npy"
            idmap = np.load(idmap_path, allow_pickle=True)
            # Unwrap if it's a 0-dimensional array containing a dict
            if isinstance(idmap, np.ndarray) and idmap.ndim == 0:
                idmap = idmap.item()
            # Ensure it's a dict (convert from list/array if needed)
            if not isinstance(idmap, dict):
                if isinstance(idmap, (list, np.ndarray)):
                    idmap = {i: item_id for i, item_id in enumerate(idmap)}
                else:
                    print(f"   ⚠️  Unexpected idmap type: {type(idmap)}, converting to dict")
                    idmap = {}
            
            # Search more items initially for diversity
            search_k = min(max(k * 3, 15), index.ntotal)
            distances, indices = index.search(query_embedding, search_k)
            
            # Convert distances to similarity scores (1 - normalized distance)
            # For L2 distance, closer is better (smaller distance)
            similarities = 1.0 / (1.0 + distances[0])
            
            # Get items
            items = []
            for idx, (faiss_idx, similarity) in enumerate(zip(indices[0], similarities)):
                if faiss_idx < len(idmap):
                    item_id = idmap[faiss_idx]
                    item_row = meta[meta['item_id'] == item_id]
                    
                    if not item_row.empty:
                        item = item_row.iloc[0].to_dict()
                        
                        # Exclude the query image itself if provided
                        if exclude_image_path:
                            item_img_path = item.get('img_path', '') or item.get('image_path', '') or item.get('filename', '')
                            query_filename = Path(exclude_image_path).name
                            if item_img_path and (query_filename in item_img_path or item_img_path.endswith(query_filename)):
                                print(f"   🚫 Excluding wardrobe item (same as query image: {item_img_path})")
                                continue
                        
                        # Exclude items with very high similarity (>0.99) which likely means it's the same image
                        if similarity > 0.99:
                            print(f"   🚫 Excluding wardrobe item (too similar, likely same image: similarity={similarity:.3f})")
                            continue
                        
                        # Filter out items of the same category as query
                        # Normalize both for comparison
                        if query_category:
                            item_category_raw = item.get('category', '')
                            if item_category_raw:
                                item_category = str(item_category_raw).lower().strip()
                                # Normalize query_category for comparison (it might be "Jackets" but item is "layers")
                                query_cat_lower = query_category.lower().strip()
                                # Map query category to wardrobe category format
                                query_to_wardrobe = {
                                    'jackets': ['layers', 'jacket', 'coat', 'blazer'],
                                    'pants': ['bottoms', 'pants', 'jeans', 'trousers'],
                                    'shoes': ['shoes', 'boots', 'sneakers'],
                                    'tops': ['tops', 'shirt', 'sweater'],
                                    'accessories': ['accessories', 'bag', 'hat'],
                                    'dresses': ['dresses'],
                                    'skirts': ['skirts'],
                                    'shorts': ['shorts']
                                }
                                # Check if item category matches query category
                                if query_cat_lower in query_to_wardrobe:
                                    if item_category in query_to_wardrobe[query_cat_lower]:
                                        print(f"   🚫 Excluding wardrobe item (same category: {item_category} matches {query_category})")
                                        continue
                                elif item_category == query_cat_lower:
                                    print(f"   🚫 Excluding wardrobe item (same category: {item_category})")
                                    continue
                        
                        item['similarity'] = float(similarity)
                        item['rank'] = idx + 1
                        items.append(item)
            
            print(f"   📊 Found {len(items)} wardrobe items after filtering (requested k={k})")
            
            # Log categories of found items for debugging
            if items:
                item_categories = {}
                for item in items:
                    raw_category = item.get('category', '')
                    # Use category directly (normalized to lowercase for grouping)
                    cat = str(raw_category).lower().strip() if raw_category and not pd.isna(raw_category) else 'other'
                    if cat not in item_categories:
                        item_categories[cat] = []
                    item_categories[cat].append(raw_category if raw_category else 'None')
                print(f"   📋 Items by category: {[(k, len(v)) for k, v in item_categories.items()]}")
                # Also log the raw category values to see what's in the parquet
                print(f"   🔍 Raw categories from items: {[item.get('category', 'None') for item in items[:3]]}")
            
            # Apply category diversity - 1 item per category (for categories different from query)
            # This ensures we get diverse recommendations (e.g., 1 shoe + 1 pant + 1 top = 3 items)
            # But only 1 item per category to avoid showing multiple similar items
            diverse_items = self._diversify_by_category(items, max_per_category=1)
            diverse_items = diverse_items[:k]  # Return top k after diversity (up to k different categories)
            
            print(f"   ✅ Returning {len(diverse_items)} diverse wardrobe items (1 per category)")
            
            best_score = float(diverse_items[0]['similarity']) if len(diverse_items) > 0 else 0.0
            
            return diverse_items, best_score
            
        except Exception as e:
            print(f"⚠️  Error searching wardrobe: {e}")
            return None, 0.0
    
    def add_item_to_wardrobe_index(self, user_id: str, image_path: str, item_id: str, 
                                   category: str = None, color: str = None, style: str = None) -> bool:
        """
        Incrementally add a single item to user's wardrobe index.
        Uses the already-loaded model to generate embedding, then updates FAISS index.
        
        Args:
            user_id: User identifier
            image_path: Path to the image file (local or GCS)
            item_id: Unique identifier for this item (filename without extension)
            category: Item category (optional, from metadata)
            color: Item color (optional, from metadata)
            style: Item style (optional, from metadata)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"   🔄 Adding item {item_id} to wardrobe index incrementally...")
            
            # Step 1: Generate embedding for the new image
            print(f"   📊 Generating embedding for {item_id}...")
            embedding = self.embed_image(image_path)
            
            # Ensure embedding is 2D array (1, dimension)
            if embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)
            
            # Step 2: Determine wardrobe path and whether to use GCS
            wardrobe_path = self.wardrobes_dir / user_id
            is_cloud_run = os.getenv('CLOUD_RUN', '').lower() == 'true' or os.getenv('K_SERVICE') is not None
            use_gcs_client = is_cloud_run or str(wardrobe_path).startswith('/gcs/') or 'gs://' in str(wardrobe_path)
            
            if use_gcs_client:
                # Use GCS client for Cloud Run
                from google.cloud import storage
                import tempfile
                import json
                
                gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
                gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
                
                client = storage.Client(project=gcp_project_id)
                bucket = client.bucket(gcp_bucket_name)
                
                # Create temp directory for this operation
                temp_wardrobe_dir = Path(tempfile.gettempdir()) / "styleme_wardrobes" / user_id
                temp_wardrobe_dir.mkdir(parents=True, exist_ok=True)
                
                # Check if index exists in GCS
                index_blob_path = f"wardrobes/{user_id}/wardrobe.index.faiss"
                index_blob = bucket.blob(index_blob_path)
                
                existing_index = None
                existing_meta = None
                existing_idmap = None
                dimension = embedding.shape[1]
                
                if index_blob.exists():
                    # Download existing index files
                    print(f"   📥 Downloading existing wardrobe index...")
                    
                    # Download FAISS index
                    temp_index_path = temp_wardrobe_dir / "wardrobe.index.faiss"
                    index_blob.download_to_filename(str(temp_index_path))
                    existing_index = faiss.read_index(str(temp_index_path))
                    dimension = existing_index.d
                    
                    # Download parquet metadata
                    parquet_blob = bucket.blob(f"wardrobes/{user_id}/wardrobe.parquet")
                    if parquet_blob.exists():
                        temp_parquet_path = temp_wardrobe_dir / "wardrobe.parquet"
                        parquet_blob.download_to_filename(str(temp_parquet_path))
                        existing_meta = pd.read_parquet(temp_parquet_path)
                    
                    # Download idmap
                    idmap_blob = bucket.blob(f"wardrobes/{user_id}/idmap.npy")
                    if idmap_blob.exists():
                        temp_idmap_path = temp_wardrobe_dir / "idmap.npy"
                        idmap_blob.download_to_filename(str(temp_idmap_path))
                        existing_idmap = np.load(temp_idmap_path, allow_pickle=True)
                        if isinstance(existing_idmap, np.ndarray) and existing_idmap.ndim == 0:
                            existing_idmap = existing_idmap.item()
                        if not isinstance(existing_idmap, dict):
                            # Convert array to dict if needed
                            existing_idmap = {i: item_id for i, item_id in enumerate(existing_idmap)}
                else:
                    # Create new index
                    print(f"   🆕 Creating new wardrobe index...")
                    existing_index = faiss.IndexFlatL2(dimension)
                    existing_meta = pd.DataFrame(columns=['item_id', 'img_path', 'filename', 'category', 'color', 'style', 'added_at'])
                    existing_idmap = {}
                
                # Step 3: Add embedding to FAISS index
                print(f"   ➕ Adding embedding to FAISS index...")
                existing_index.add(embedding.astype('float32'))
                
                # Step 4: Update metadata
                new_row = {
                    'item_id': item_id,
                    'img_path': f"wardrobes/{user_id}/images/{Path(image_path).name}",
                    'filename': Path(image_path).name,
                    'category': category,
                    'color': color,
                    'style': style,
                    'added_at': datetime.now().isoformat()
                }
                
                # Add to metadata DataFrame
                new_df = pd.DataFrame([new_row])
                if existing_meta is None or existing_meta.empty:
                    existing_meta = new_df
                else:
                    existing_meta = pd.concat([existing_meta, new_df], ignore_index=True)
                
                # Step 5: Update idmap
                new_index = existing_index.ntotal - 1  # Index of the newly added item
                if not isinstance(existing_idmap, dict):
                    existing_idmap = {}
                existing_idmap[new_index] = item_id
                
                # Step 6: Save updated files
                print(f"   💾 Saving updated wardrobe index...")
                
                # Save FAISS index
                temp_index_path = temp_wardrobe_dir / "wardrobe.index.faiss"
                faiss.write_index(existing_index, str(temp_index_path))
                
                # Save parquet
                temp_parquet_path = temp_wardrobe_dir / "wardrobe.parquet"
                existing_meta.to_parquet(temp_parquet_path, index=False)
                
                # Save idmap
                temp_idmap_path = temp_wardrobe_dir / "idmap.npy"
                np.save(temp_idmap_path, existing_idmap)
                
                # Step 7: Upload to GCS
                print(f"   📤 Uploading updated index to GCS...")
                
                # Upload FAISS index
                try:
                    index_blob.upload_from_filename(str(temp_index_path))
                    print(f"   ✅ Uploaded wardrobe.index.faiss to GCS ({temp_index_path.stat().st_size} bytes)")
                except Exception as e:
                    print(f"   ❌ Failed to upload wardrobe.index.faiss: {e}")
                    raise
                
                # Upload parquet
                try:
                    parquet_blob = bucket.blob(f"wardrobes/{user_id}/wardrobe.parquet")
                    parquet_blob.upload_from_filename(str(temp_parquet_path))
                    print(f"   ✅ Uploaded wardrobe.parquet to GCS ({temp_parquet_path.stat().st_size} bytes)")
                except Exception as e:
                    print(f"   ❌ Failed to upload wardrobe.parquet: {e}")
                    raise
                
                # Upload idmap
                try:
                    idmap_blob = bucket.blob(f"wardrobes/{user_id}/idmap.npy")
                    idmap_blob.upload_from_filename(str(temp_idmap_path))
                    print(f"   ✅ Uploaded idmap.npy to GCS ({temp_idmap_path.stat().st_size} bytes)")
                except Exception as e:
                    print(f"   ❌ Failed to upload idmap.npy: {e}")
                    raise
                
                # Update manifest if it exists
                manifest_blob = bucket.blob(f"wardrobes/{user_id}/manifest.json")
                if manifest_blob.exists():
                    manifest_data = json.loads(manifest_blob.download_as_text())
                else:
                    manifest_data = {
                        'user_id': user_id,
                        'model': 'FashionCLIP',
                        'dimension': int(dimension),
                        'index_type': 'IndexFlatL2'
                    }
                
                manifest_data['num_items'] = existing_index.ntotal
                manifest_data['last_updated'] = datetime.now().isoformat()
                manifest_blob.upload_from_string(
                    json.dumps(manifest_data, indent=2),
                    content_type='application/json'
                )
                
                print(f"   ✅ Successfully added {item_id} to wardrobe index ({existing_index.ntotal} items total)")
                return True
                
            else:
                # Local filesystem path
                wardrobe_path.mkdir(parents=True, exist_ok=True)
                index_path = wardrobe_path / "wardrobe.index.faiss"
                
                existing_index = None
                existing_meta = None
                existing_idmap = None
                dimension = embedding.shape[1]
                
                if index_path.exists():
                    # Load existing index
                    print(f"   📥 Loading existing wardrobe index...")
                    existing_index = faiss.read_index(str(index_path))
                    dimension = existing_index.d
                    
                    # Load metadata
                    meta_path = wardrobe_path / "wardrobe.parquet"
                    if meta_path.exists():
                        existing_meta = pd.read_parquet(meta_path)
                    
                    # Load idmap
                    idmap_path = wardrobe_path / "idmap.npy"
                    if idmap_path.exists():
                        existing_idmap = np.load(idmap_path, allow_pickle=True)
                        if isinstance(existing_idmap, np.ndarray) and existing_idmap.ndim == 0:
                            existing_idmap = existing_idmap.item()
                        if not isinstance(existing_idmap, dict):
                            existing_idmap = {i: item_id for i, item_id in enumerate(existing_idmap)}
                else:
                    # Create new index
                    print(f"   🆕 Creating new wardrobe index...")
                    existing_index = faiss.IndexFlatL2(dimension)
                    existing_meta = pd.DataFrame(columns=['item_id', 'img_path', 'filename', 'category', 'color', 'style', 'added_at'])
                    existing_idmap = {}
                
                # Add embedding to index
                print(f"   ➕ Adding embedding to FAISS index...")
                existing_index.add(embedding.astype('float32'))
                
                # Update metadata
                new_row = {
                    'item_id': item_id,
                    'img_path': str(Path(image_path).relative_to(self.wardrobes_dir)),
                    'filename': Path(image_path).name,
                    'category': category,
                    'color': color,
                    'style': style,
                    'added_at': datetime.now().isoformat()
                }
                
                new_df = pd.DataFrame([new_row])
                if existing_meta is None or existing_meta.empty:
                    existing_meta = new_df
                else:
                    existing_meta = pd.concat([existing_meta, new_df], ignore_index=True)
                
                # Update idmap
                new_index = existing_index.ntotal - 1
                if not isinstance(existing_idmap, dict):
                    existing_idmap = {}
                existing_idmap[new_index] = item_id
                
                # Save files
                print(f"   💾 Saving updated wardrobe index...")
                faiss.write_index(existing_index, str(index_path))
                existing_meta.to_parquet(wardrobe_path / "wardrobe.parquet", index=False)
                np.save(wardrobe_path / "idmap.npy", existing_idmap)
                
                # Update manifest
                manifest_path = wardrobe_path / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest_data = json.load(f)
                else:
                    manifest_data = {
                        'user_id': user_id,
                        'model': 'FashionCLIP',
                        'dimension': int(dimension),
                        'index_type': 'IndexFlatL2'
                    }
                
                manifest_data['num_items'] = existing_index.ntotal
                manifest_data['last_updated'] = datetime.now().isoformat()
                with open(manifest_path, 'w') as f:
                    json.dump(manifest_data, f, indent=2)
                
                print(f"   ✅ Successfully added {item_id} to wardrobe index ({existing_index.ntotal} items total)")
                return True
                
        except Exception as e:
            print(f"   ❌ Failed to add item to wardrobe index: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_category(self, category_str: str) -> str:
        """Normalize category string to standard category names"""
        if not category_str or pd.isna(category_str):
            return "Other"
        
        # Normalize to lowercase for matching
        category_lower = str(category_str).lower().strip()
        
        # Direct mapping from GPT-tagged categories (wardrobe items) to standard categories
        # GPT uses: "bottoms", "shoes", "accessories", "tops", "layers", "dresses"
        category_mapping = {
            'bottoms': 'Pants',
            'bottom': 'Pants',
            'pants': 'Pants',
            'pant': 'Pants',
            'jeans': 'Pants',
            'jean': 'Pants',
            'trousers': 'Pants',
            'trouser': 'Pants',
            'shoes': 'Shoes',
            'shoe': 'Shoes',
            'sneakers': 'Shoes',
            'sneaker': 'Shoes',
            'boots': 'Shoes',
            'boot': 'Shoes',
            'sandals': 'Shoes',
            'sandal': 'Shoes',
            'heels': 'Shoes',
            'heel': 'Shoes',
            'accessories': 'Accessories',
            'accessory': 'Accessories',
            'bags': 'Bags',
            'bag': 'Bags',
            'backpack': 'Bags',
            'handbag': 'Bags',
            'tote': 'Bags',
            'tops': 'Tops',
            'top': 'Tops',
            'shirts': 'Tops',
            'shirt': 'Tops',
            't-shirt': 'Tops',
            'tshirt': 'Tops',
            'tee': 'Tops',
            'blouse': 'Tops',
            'sweater': 'Tops',
            'sweaters': 'Tops',
            'layers': 'Jackets',
            'layer': 'Jackets',
            'jackets': 'Jackets',
            'jacket': 'Jackets',
            'coats': 'Jackets',
            'coat': 'Jackets',
            'blazers': 'Jackets',
            'blazer': 'Jackets',
            'cardigan': 'Jackets',
            'cardigans': 'Jackets',
            'dresses': 'Dresses',
            'dress': 'Dresses',
            'skirts': 'Skirts',
            'skirt': 'Skirts',
            'shorts': 'Shorts',
            'short': 'Shorts',
        }
        
        # Check direct mapping first (for GPT-tagged wardrobe items)
        if category_lower in category_mapping:
            return category_mapping[category_lower]
        
        # Handle comma-separated format (catalog items): "Men, Shoes, Sneakers, Low-Tops"
        if ',' in category_str:
            parts = [p.strip().lower() for p in category_str.split(',')]
            # Check each part for category matches
            for part in parts:
                if part in category_mapping:
                    return category_mapping[part]
                # Also check for partial matches
                for key, value in category_mapping.items():
                    if key in part:
                        return value
        
        # Fallback: check for partial matches in the category string
        for key, value in category_mapping.items():
            if key in category_lower:
                return value
        
        return "Other"
    
    def _get_complementary_categories(self, query_category: str) -> List[str]:
        """
        Get complementary categories needed for a complete outfit based on query category
        Returns categories that should be included in the outfit
        """
        # Fashion compatibility rules for complete outfit matching
        rules = {
            "Tops": {
                "required": ["Shoes", "Bags"],
                "bottom_options": ["Pants", "Skirts", "Shorts"]  # Need ONE of these
            },
            "Pants": {
                "required": ["Tops", "Shoes", "Bags"]
            },
            "Skirts": {
                "required": ["Tops", "Shoes", "Bags"]
            },
            "Shorts": {
                "required": ["Tops", "Shoes", "Bags"]
            },
            "Dresses": {
                "required": ["Shoes", "Bags"]  # Dresses are complete - no pants/skirts needed
            },
            "Shoes": {
                "required": ["Tops", "Bags"],
                "bottom_options": ["Pants", "Skirts", "Shorts"]  # Need ONE of these
            },
            "Bags": {
                "required": ["Tops", "Shoes"],
                "bottom_options": ["Pants", "Skirts", "Shorts"]  # Need ONE of these
            },
            "Jackets": {
                "required": ["Tops", "Shoes", "Bags"],
                "bottom_options": ["Pants", "Skirts", "Shorts"]  # Need ONE of these
            },
            "Accessories": {
                "required": ["Tops", "Shoes", "Bags"],
                "bottom_options": ["Pants", "Skirts", "Shorts"]  # Need ONE of these
            },
            "Other": {
                "required": ["Tops", "Pants", "Shoes", "Bags"]  # Default fallback
            }
        }
        
        rule = rules.get(query_category, rules["Other"])
        complementary = rule.get("required", []).copy()
        
        # For categories that need a bottom option, we'll try to get one
        # The search logic will prioritize getting at least one bottom type
        if "bottom_options" in rule:
            complementary.extend(rule["bottom_options"])
        
        return complementary
    
    def _detect_query_category(self, query_embedding: np.ndarray, gender: str = None) -> str:
        """Detect the category of the query item by finding most similar item in catalog"""
        # Search for top 10 most similar items to detect category (more samples for better accuracy)
        distances, indices = self.catalog_index.search(query_embedding, 10)
        
        category_counts = {}
        all_categories = []  # Track all categories seen
        
        for idx in indices[0]:
            if idx < len(self.catalog_idmap):
                product_id = self.catalog_idmap[idx]
                item_row = self.catalog_meta[self.catalog_meta['id'] == product_id]
                
                if not item_row.empty:
                    item = item_row.iloc[0].to_dict()
                    
                    # Don't filter by gender during detection - we want to detect category first
                    category = self._extract_category(item.get('category', ''))
                    category_counts[category] = category_counts.get(category, 0) + 1
                    all_categories.append((category, item.get('category', '')))
        
        # Return most common category among top matches
        if category_counts:
            detected_category = max(category_counts, key=category_counts.get)
            print(f"   📋 Category detection: {detected_category} (seen categories: {dict(category_counts)})")
            return detected_category
        
        print(f"   ⚠️  Category detection failed, using 'Other'")
        return "Other"
    
    def _diversify_by_category(self, items: List[Dict], max_per_category: int = 1, min_categories: int = None) -> List[Dict]:
        """
        Ensure outfit diversity by limiting items per category
        Uses category directly from metadata (GPT-tagged), no extraction needed
        """
        if not items:
            return []
        
        category_counts = {}
        diverse_items = []
        category_to_items = {}  # Track items by category
        
        # First pass: Group items by category (use category directly from metadata)
        for item in items:
            # Use category directly from metadata - GPT tags are consistent
            category = item.get('category', '')
            if not category or pd.isna(category) or category == '' or category == 'Unknown':
                category = 'Other'  # Fallback for items without category
            else:
                # Normalize to lowercase for consistent grouping
                category = str(category).lower().strip()
            
            if category not in category_to_items:
                category_to_items[category] = []
            category_to_items[category].append(item)
        
        print(f"   🔍 Diversity: Found {len(category_to_items)} unique categories: {list(category_to_items.keys())}")
        
        # ALWAYS prioritize getting one item from each category first
        # This ensures we get diverse recommendations across categories
        for category in sorted(category_to_items.keys(), key=lambda c: len(category_to_items[c]), reverse=True):
            if category_to_items[category]:
                # Get the best item (highest similarity) from this category
                best_item = max(category_to_items[category], key=lambda x: x.get('similarity', 0))
                diverse_items.append(best_item)
                category_counts[category] = 1
                print(f"   ✅ Added best item from '{category}' (similarity: {best_item.get('similarity', 0):.3f})")
        
        # Sort diverse_items by similarity (best first) to maintain quality
        diverse_items.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        # Re-rank after filtering
        for idx, item in enumerate(diverse_items):
            item['rank'] = idx + 1
        
        return diverse_items
    
    def search_catalog(self, query_embedding: np.ndarray, k: int = 3, gender: str = None, query_category: str = None) -> List[Dict]:
        """
        Search global catalog FAISS index - find highest match from each category
        Returns best matching item from each complementary category for complete outfit
        """
        # Search many items to ensure we find items from diverse categories
        search_k = max(k * 50, 100)  # Search many items
        distances, indices = self.catalog_index.search(query_embedding, search_k)
        
        # Convert distances to similarity scores
        similarities = 1.0 / (1.0 + distances[0])
        
        # Step 1: Infer query category from top N matches, weighted by similarity
        # Only if query_category not provided (fallback detection)
        detected_query_category = None
        if not query_category:
            category_scores = {}
            
            # Look at top 10 matches, weighted by similarity (first match counts most)
            for i in range(min(10, len(indices[0]))):
                if indices[0][i] < len(self.catalog_idmap):
                    product_id = self.catalog_idmap[indices[0][i]]
                    item_row = self.catalog_meta[self.catalog_meta['id'] == product_id]
                    
                    if not item_row.empty:
                        item = item_row.iloc[0].to_dict()
                        item_category = self._extract_category(item.get('category', ''))
                        
                        # Weight by similarity and position: first match (i=0) gets highest weight
                        # Weight = similarity_score * position_weight (10 for first, 9 for second, etc.)
                        position_weight = (10 - i)
                        weighted_score = similarities[i] * position_weight
                        
                        category_scores[item_category] = category_scores.get(item_category, 0) + weighted_score
            
            # Get highest scoring category (most similar items)
            if category_scores:
                detected_query_category = max(category_scores, key=category_scores.get)
                sorted_scores = dict(sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:3])
                print(f"   🔍 Inferred query category (weighted top 10): {detected_query_category} (top scores: {sorted_scores})")
                query_category = detected_query_category
        
        # Step 2: Determine which categories to exclude and prioritize
        categories_to_exclude = set()
        categories_to_prioritize = set()
        
        if query_category:
            # Use provided query_category directly (already normalized from frontend)
            categories_to_exclude.add(query_category)
            
            # Get complementary categories for this query
            complementary = self._get_complementary_categories(query_category)
            categories_to_prioritize = set(complementary)
            
            # Smart exclusion rules:
            # - If query is Tops, also exclude Dresses (dresses include tops)
            # - If query is Dresses, also exclude Tops and Pants (dresses are complete outfits)
            # - If query is Jackets, also exclude Tops (jackets are outerwear worn over tops)
            if query_category == "Tops":
                categories_to_exclude.add("Dresses")
            elif query_category == "Dresses":
                categories_to_exclude.add("Tops")
                categories_to_exclude.add("Pants")
                categories_to_exclude.add("Skirts")
                categories_to_exclude.add("Shorts")
            elif query_category == "Pants":
                categories_to_exclude.add("Dresses")  # Don't mix pants with dresses
            elif query_category == "Jackets":
                # Jackets are outerwear - recommend bottoms, bags, shoes, but NOT other tops or jackets
                categories_to_exclude.add("Tops")  # Don't recommend tops when query is a jacket
                # Prioritize: bottoms (Pants/Skirts/Shorts), Shoes, Bags
                # These are already in complementary categories
        
        print(f"   🚫 Excluding categories: {sorted(categories_to_exclude)}")
        if categories_to_prioritize:
            print(f"   ⭐ Prioritizing categories: {sorted(categories_to_prioritize)}")
        
        # Step 3: Group all items by category, excluding unwanted categories
        items_by_category = {}
        prioritized_items_by_category = {}  # Separate dict for prioritized categories
        
        for idx, (faiss_idx, similarity) in enumerate(zip(indices[0], similarities)):
            if faiss_idx < len(self.catalog_idmap):
                product_id = self.catalog_idmap[faiss_idx]
                item_row = self.catalog_meta[self.catalog_meta['id'] == product_id]
                
                if not item_row.empty:
                    item = item_row.iloc[0].to_dict()
                    
                    # Filter by gender if specified
                    if gender:
                        item_gender = str(item.get('gender', '')).lower()
                        if item_gender != gender.lower():
                            continue
                    
                    item_category = self._extract_category(item.get('category', ''))
                    
                    # Exclude unwanted categories
                    if item_category in categories_to_exclude:
                        continue
                    
                    item['similarity'] = float(similarity)
                    
                    # Separate prioritized vs non-prioritized categories
                    if categories_to_prioritize and item_category in categories_to_prioritize:
                        if item_category not in prioritized_items_by_category:
                            prioritized_items_by_category[item_category] = []
                        prioritized_items_by_category[item_category].append(item)
                    else:
                        # Group by category
                        if item_category not in items_by_category:
                            items_by_category[item_category] = []
                        items_by_category[item_category].append(item)
        
        # Step 4: Find highest match from each category, prioritizing complementary categories
        outfit_items = []
        
        # First, add best items from prioritized (complementary) categories
        for category in sorted(categories_to_prioritize):
            if category in prioritized_items_by_category and prioritized_items_by_category[category]:
                best_item = max(prioritized_items_by_category[category], key=lambda x: x['similarity'])
                outfit_items.append(best_item)
                print(f"   ⭐ Best match from {category} (prioritized): {best_item.get('title', 'Unknown')[:50]} (similarity: {best_item['similarity']:.3f})")
        
        # Then, add best items from other categories (if we haven't reached k yet)
        for category, category_items in items_by_category.items():
            if len(outfit_items) >= k:
                break
            if category_items:
                # Get best matching item from this category
                best_item = max(category_items, key=lambda x: x['similarity'])
                outfit_items.append(best_item)
                print(f"   ✅ Best match from {category}: {best_item.get('title', 'Unknown')[:50]} (similarity: {best_item['similarity']:.3f})")
        
        # Step 5: Sort by similarity and return top k
        outfit_items.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Re-rank
        for idx, item in enumerate(outfit_items[:k]):
            item['rank'] = idx + 1
        
        print(f"   🎯 Returning {len(outfit_items[:k])} items from {len(items_by_category)} different categories")
        return outfit_items[:k]
    
    def inference(self, user_id: str, query_image_path: str, 
                  threshold: float = 0.7, wardrobe_k: int = 5, catalog_k: int = 3, gender: str = None,
                  query_category: str = None) -> Dict:
        """
        Main inference flow
        
        Args:
            user_id: User identifier
            query_image_path: Path to query image
            threshold: Similarity threshold for wardrobe (default 0.7)
            wardrobe_k: Number of wardrobe items to return (default 5)
            catalog_k: Number of catalog items to return (default 3)
            gender: Gender filter for catalog items ('men' or 'women', optional)
        
        Returns:
            Dictionary with recommendations
        """
        print(f"\n🔮 Running inference for user: {user_id}")
        print(f"   Query: {query_image_path}")
        if query_category:
            print(f"   📋 Query category: {query_category} (will exclude same-category items)")
        
        # Step 1: Generate query embedding
        print("   📊 Generating query embedding...")
        query_embedding = self.embed_image(query_image_path)
        
        # Step 2: Search wardrobe (always if wardrobe_k > 0)
        wardrobe_items = []
        best_wardrobe_score = 0.0
        wardrobe_reason = None
        
        if wardrobe_k > 0:
            print("   👔 Searching user wardrobe...")
            wardrobe_result, best_wardrobe_score = self.search_wardrobe(
                user_id, query_embedding, k=wardrobe_k, 
                query_category=query_category, 
                exclude_image_path=query_image_path
            )
            
            # Check wardrobe results
            if wardrobe_result is None:
                wardrobe_reason = "empty_wardrobe"
                print(f"   ⚠️  No wardrobe found for user")
            elif len(wardrobe_result) == 0:
                # Wardrobe exists but no matches (could be due to category filtering or all items below threshold)
                wardrobe_reason = "no_matches"
                if query_category:
                    print(f"   ⚠️  No wardrobe matches found (all items filtered out - same category as query: {query_category})")
                else:
                    print(f"   ⚠️  No wardrobe matches found (all items below threshold or filtered)")
            elif best_wardrobe_score < threshold:
                wardrobe_reason = "low_score"
                print(f"   ⚠️  Best wardrobe score ({best_wardrobe_score:.3f}) < threshold ({threshold})")
            else:
                # Filter items that meet threshold
                wardrobe_items = [item for item in wardrobe_result if item.get('similarity', 0) >= threshold]
                if len(wardrobe_items) > 0:
                    print(f"   ✅ Found {len(wardrobe_items)} wardrobe items (best score: {best_wardrobe_score:.3f})")
                else:
                    wardrobe_reason = "low_score"
                    print(f"   ⚠️  No wardrobe items meet threshold ({threshold})")
        else:
            print("   ⏭️  Skipping wardrobe search (wardrobe_k=0)")
            wardrobe_reason = "wardrobe_disabled"
        
        # Step 3: Search catalog (always if catalog_k > 0)
        catalog_items = []
        catalog_reason = None
        
        if catalog_k > 0:
            print("   🛍️  Searching global catalog...")
            if gender:
                print(f"   🔍 Filtering by gender: {gender}")
            catalog_items = self.search_catalog(query_embedding, k=catalog_k, gender=gender, query_category=query_category)
            if len(catalog_items) > 0:
                print(f"   ✅ Found {len(catalog_items)} catalog items")
            else:
                catalog_reason = "no_catalog_matches"
                print(f"   ⚠️  No catalog matches found")
        else:
            print("   ⏭️  Skipping catalog search (catalog_k=0)")
            catalog_reason = "catalog_disabled"
        
        # Step 4: Build result with BOTH wardrobe and catalog items separately
        result = {
            'user_id': user_id,
            'query_image': str(query_image_path),
            'timestamp': datetime.now().isoformat(),
            'threshold': threshold,
            'wardrobe_items': wardrobe_items,
            'catalog_items': catalog_items,
            'wardrobe_count': len(wardrobe_items),
            'catalog_count': len(catalog_items),
            'num_results': len(wardrobe_items) + len(catalog_items)
        }
        
        # Add reasons for empty results
        if wardrobe_reason:
            result['wardrobe_reason'] = wardrobe_reason
        if catalog_reason:
            result['catalog_reason'] = catalog_reason
        
        # Keep best_wardrobe_score for reference
        if best_wardrobe_score > 0:
            result['best_wardrobe_score'] = best_wardrobe_score
        
        # For backward compatibility, also include 'items' and 'used_wardrobe'
        # 'items' will contain wardrobe items if available, otherwise catalog items
        if len(wardrobe_items) > 0:
            result['items'] = wardrobe_items
            result['used_wardrobe'] = True
        else:
            result['items'] = catalog_items
            result['used_wardrobe'] = False
            if wardrobe_reason:
                result['fallback_reason'] = wardrobe_reason
        
        print(f"\n   🎉 Inference complete: {len(wardrobe_items)} wardrobe + {len(catalog_items)} catalog = {result['num_results']} total recommendations")
        return result


def main():
    """Demo inference"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run inference on query image')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--query', required=True, help='Path to query image')
    parser.add_argument('--catalog-dir', default=os.getenv('CATALOG_DIR', '/gcs/styleme-production/catalog'), help='Catalog directory')
    parser.add_argument('--experiments-dir', default=os.getenv('EXPERIMENTS_DIR', '/gcs/styleme-production/experiments'), help='Experiments directory')
    parser.add_argument('--wardrobes-dir', default=os.getenv('WARDROBES_DIR', '/gcs/styleme-production/wardrobes'), help='Wardrobes directory')
    parser.add_argument('--output', help='Output JSON path')
    parser.add_argument('--threshold', type=float, default=0.7, help='Wardrobe similarity threshold')
    parser.add_argument('--wardrobe-k', type=int, default=5, help='Number of wardrobe items')
    parser.add_argument('--catalog-k', type=int, default=3, help='Number of catalog items')
    parser.add_argument('--gender', type=str, choices=['men', 'women'], help='Filter catalog by gender (men/women)')
    parser.add_argument('--disable-bg-removal', action='store_true', 
                       help='Disable background removal')
    parser.add_argument('--bg-removal-model', type=str, default='briaai/RMBG-1.4',
                       help='Background removal model name (default: briaai/RMBG-1.4)')
    
    args = parser.parse_args()
    
    # Initialize service
    service = InferenceService(
        catalog_dir=args.catalog_dir,
        experiments_dir=args.experiments_dir,
        wardrobes_dir=args.wardrobes_dir,
        bg_removal_enabled=not args.disable_bg_removal,
        bg_removal_model=args.bg_removal_model
    )
    
    # Run inference
    result = service.inference(
        user_id=args.user_id,
        query_image_path=args.query,
        threshold=args.threshold,
        wardrobe_k=args.wardrobe_k,
        catalog_k=args.catalog_k,
        gender=args.gender
    )
    
    # Save or print result
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
    else:
        print("\n📄 Results:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

