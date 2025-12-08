"""
Build User Wardrobe Index
Creates per-user FAISS index from their uploaded wardrobe images
"""

import os
import sys
import json
import torch
import numpy as np
import pandas as pd
import faiss
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from datetime import datetime

# Add src to path
sys.path.append('/app/src')
from src.models.train.model_training import FashionCLIPModel


class WardrobeIndexBuilder:
    def __init__(self, user_id, wardrobe_dir, experiments_dir, wardrobes_base_dir):
        self.user_id = user_id
        self.wardrobe_dir = Path(wardrobe_dir)
        self.experiments_dir = Path(experiments_dir)
        self.wardrobes_base_dir = Path(wardrobes_base_dir)
        
        self.output_dir = self.wardrobes_base_dir / user_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 Building wardrobe for user: {user_id}")
        print(f"   Device: {self.device}")
        
        # Initialize background remover (optional, disabled by default)
        self.bg_remover = None
        self.bg_removal_enabled = False
        print("   ℹ️  Background removal disabled (default)")
        
        # Load model
        self.model = self._load_model()
        self.transform = self._get_transform()
    
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
        
        # Load checkpoint first to check device info
        checkpoint = torch.load(str(model_path), map_location='cpu')  # Load to CPU first to avoid meta tensor issues
        
        # Create model and move to device before loading state dict
        model = FashionCLIPModel()
        model = model.to(self.device)
        
        # Load state dict with strict=False to handle any mismatches
        try:
            model.load_state_dict(checkpoint['model_state_dict'], strict=False)
        except Exception as e:
            print(f"   ⚠️  Warning: State dict loading had issues: {e}")
            # Try loading with map_location to device
            checkpoint_device = torch.load(str(model_path), map_location=self.device)
            model.load_state_dict(checkpoint_device['model_state_dict'], strict=False)
        
        model.eval()
        
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
    
    def scan_wardrobe_images(self):
        """Scan user's wardrobe images"""
        print(f"\n📂 Scanning wardrobe: {self.wardrobe_dir}")
        
        images_dir = self.wardrobe_dir / "images"
        if not images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {images_dir}")
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(images_dir.glob(f"*{ext}"))
            image_files.extend(images_dir.glob(f"*{ext.upper()}"))
        
        print(f"   Found {len(image_files)} images")
        
        # Build metadata - read category, color, style from JSON metadata files
        items = []
        for img_path in image_files:
            item_id = img_path.stem
            
            # Try to load metadata from JSON file
            metadata_filename = item_id + '_metadata.json'
            metadata_path = self.wardrobe_dir / metadata_filename
            
            category = None
            color = None
            style = None
            
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        category = metadata.get('category', None)
                        color = metadata.get('color', None)
                        style = metadata.get('style', None)
                except Exception as e:
                    print(f"   ⚠️  Failed to load metadata for {img_path.name}: {e}")
            
            items.append({
                'item_id': item_id,
                'img_path': str(img_path.relative_to(self.wardrobes_base_dir)),
                'filename': img_path.name,
                'category': category,  # Include category from GPT metadata
                'color': color,  # Include color from GPT metadata
                'style': style,  # Include style from GPT metadata
                'added_at': datetime.now().isoformat()
            })
        
        df = pd.DataFrame(items)
        return df, image_files
    
    def generate_embeddings(self, image_files):
        """Generate embeddings for wardrobe images"""
        print("\n🔮 Generating embeddings...")
        
        embeddings = []
        valid_files = []
        
        with torch.no_grad():
            for img_path in tqdm(image_files, desc="Processing images"):
                try:
                    # Step 1: Load image
                    image = Image.open(img_path).convert('RGB')
                    
                    # Step 2: Optional background removal (if enabled)
                    # Background removal is optional - images are processed as-is if disabled
                    if self.bg_removal_enabled and self.bg_remover:
                        # Remove background (returns PIL Image with transparent bg)
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
                    
                    # Step 3: Transform and generate embedding
                    image_tensor = self.transform(image).unsqueeze(0).to(self.device)
                    
                    # Generate embedding
                    embedding = self.model(image_tensor)
                    
                    # L2 normalize
                    embedding = embedding / torch.norm(embedding, p=2, dim=1, keepdim=True)
                    
                    embeddings.append(embedding.cpu().numpy()[0])
                    valid_files.append(img_path)
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing {img_path}: {e}")
                    continue
        
        embeddings = np.array(embeddings).astype('float32')
        print(f"   ✅ Generated {len(embeddings)} embeddings (shape: {embeddings.shape})")
        
        return embeddings, valid_files
    
    def build_faiss_index(self, embeddings):
        """Build FAISS index"""
        print("\n🔍 Building FAISS index...")
        
        dimension = embeddings.shape[1]
        
        # Use flat L2 index for exact search
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        print(f"   ✅ FAISS index built: {index.ntotal} vectors")
        return index
    
    def save_wardrobe(self, df, embeddings, index, valid_files):
        """Save wardrobe artifacts"""
        print("\n💾 Saving wardrobe files...")
        
        # Filter metadata to only valid items
        valid_ids = [f.stem for f in valid_files]
        df_valid = df[df['item_id'].isin(valid_ids)].reset_index(drop=True)
        
        # Save metadata
        meta_path = self.output_dir / "wardrobe.parquet"
        df_valid.to_parquet(meta_path, index=False)
        print(f"   ✅ Saved: {meta_path}")
        
        # Save embeddings
        vecs_path = self.output_dir / "wardrobe.vecs.npy"
        np.save(vecs_path, embeddings)
        print(f"   ✅ Saved: {vecs_path}")
        
        # Save FAISS index
        index_path = self.output_dir / "wardrobe.index.faiss"
        faiss.write_index(index, str(index_path))
        print(f"   ✅ Saved: {index_path}")
        
        # Save ID mapping
        idmap_path = self.output_dir / "idmap.npy"
        idmap = df_valid['item_id'].values
        np.save(idmap_path, idmap)
        print(f"   ✅ Saved: {idmap_path}")
        
        # Create manifest
        manifest = {
            'user_id': self.user_id,
            'built_at': datetime.now().isoformat(),
            'model': 'FashionCLIP',
            'dimension': int(embeddings.shape[1]),
            'num_items': int(len(df_valid)),
            'index_type': 'IndexFlatL2'
        }
        
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"   ✅ Saved: {manifest_path}")
        
        print(f"\n🎉 Wardrobe index built successfully!")
        print(f"   User: {self.user_id}")
        print(f"   Location: {self.output_dir}")
        print(f"   Items: {len(df_valid)}")
        print(f"   Dimension: {embeddings.shape[1]}")
        
        return self.output_dir
    
    def build(self):
        """Main build process"""
        print("="*60)
        print(f"🏗️  Building Wardrobe Index for {self.user_id}")
        print("="*60)
        
        # Step 1: Scan images
        df, image_files = self.scan_wardrobe_images()
        
        if len(image_files) == 0:
            raise ValueError("No images found in wardrobe")
        
        # Step 2: Generate embeddings
        embeddings, valid_files = self.generate_embeddings(image_files)
        
        if len(embeddings) == 0:
            raise ValueError("No valid embeddings generated")
        
        # Step 3: Build FAISS index
        index = self.build_faiss_index(embeddings)
        
        # Step 4: Save everything
        output_dir = self.save_wardrobe(df, embeddings, index, valid_files)
        
        return output_dir


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build user wardrobe index')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--wardrobe-dir', required=True, help='User wardrobe directory with images/ subfolder')
    parser.add_argument('--experiments-dir', default=os.getenv('EXPERIMENTS_DIR', '/gcs/styleme-production/experiments'), help='Experiments directory')
    parser.add_argument('--wardrobes-base-dir', default=os.getenv('WARDROBES_DIR', '/gcs/styleme-production/wardrobes'), help='Base wardrobes directory')
    
    args = parser.parse_args()
    
    # Build wardrobe
    builder = WardrobeIndexBuilder(
        user_id=args.user_id,
        wardrobe_dir=args.wardrobe_dir,
        experiments_dir=args.experiments_dir,
        wardrobes_base_dir=args.wardrobes_base_dir
    )
    
    output_dir = builder.build()
    
    print(f"\n✅ Wardrobe index ready at: {output_dir}")


if __name__ == "__main__":
    main()

