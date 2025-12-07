"""
Build Catalog Index from Farfetch Data
Creates: catalog_meta.parquet, catalog.vecs.npy, catalog.index.faiss, idmap.npy
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

class CatalogIndexBuilder:
    def __init__(self, data_dir, image_dir, experiments_dir, output_dir):
        self.data_dir = Path(data_dir)
        self.image_dir = Path(image_dir)
        self.experiments_dir = Path(experiments_dir)
        self.output_dir = Path(output_dir)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 Using device: {self.device}")
        
        # Load model
        self.model = self._load_model()
        self.transform = self._get_transform()
    
    def _load_model(self):
        """Load trained FashionCLIP model"""
        print("\n📦 Loading trained model...")
        
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
            from google.cloud import storage
            gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
            gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
            
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
            for blob in bucket.list_blobs(prefix=prefix):
                # Extract exp_XXX from path
                path_parts = blob.name.replace(prefix, '').split('/')
                if path_parts and path_parts[0].startswith('exp_'):
                    exp_dirs.add(path_parts[0])
            
            # Sort experiment directories (highest number first)
            exp_numbers = []
            for exp_dir in exp_dirs:
                try:
                    num = int(exp_dir.replace('exp_', ''))
                    exp_numbers.append((num, exp_dir))
                except ValueError:
                    continue
            
            exp_numbers.sort(reverse=True)
            
            # Find first experiment with best_model.pth
            for exp_num, exp_dir in exp_numbers:
                model_blob_path = f"{prefix}{exp_dir}/best_model.pth"
                blob = bucket.blob(model_blob_path)
                if blob.exists():
                    # Download to local temp file
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir()) / "styleme_models"
                    temp_dir.mkdir(exist_ok=True)
                    local_model_path = temp_dir / f"{exp_dir}_best_model.pth"
                    
                    print(f"   Downloading {model_blob_path} to {local_model_path}...")
                    blob.download_to_filename(str(local_model_path))
                    model_path = local_model_path
                    print(f"   ✅ Downloaded model: {local_model_path}")
                    break
        else:
            # Use filesystem access (local or mounted)
            for exp_dir in sorted(local_experiments_dir.glob("exp_*"), reverse=True):
                best_model = exp_dir / "best_model.pth"
                if best_model.exists():
                    model_path = best_model
                    break
        
        if model_path is None:
            raise FileNotFoundError("No trained model found in experiments directory")
        
        print(f"   Model: {model_path}")
        
        # Load model
        model = FashionCLIPModel()
        checkpoint = torch.load(str(model_path), map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()
        
        print("   ✅ Model loaded successfully")
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
    
    def load_catalog_metadata(self):
        """Load metadata from JSON files"""
        print("\n📂 Loading catalog metadata from JSON files...")
        
        items = []
        
        # Load men's data
        men_dir = self.data_dir / "json" / "men_data"
        if men_dir.exists():
            json_files = list(men_dir.glob("*.json"))
            print(f"   Found {len(json_files)} men's data files")
            
            for json_file in tqdm(json_files, desc="Loading men's data"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    item_id = item.get('source', {}).get('id')
                    if not item_id:
                        continue
                    
                    # Extract metadata
                    items.append({
                        'id': item_id,
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'brand': item.get('brand', ''),
                        'price': item.get('price', {}).get('currentFormatted', ''),
                        'url': item.get('source', {}).get('crawlUrl', ''),
                        'category': ', '.join(item.get('categories', [])),
                        'gender': 'men',
                        'image_path': f"{item_id}_index1.jpg"
                    })
        
        # Load women's data
        women_dir = self.data_dir / "json" / "women_data"
        if women_dir.exists():
            json_files = list(women_dir.glob("*.json"))
            print(f"   Found {len(json_files)} women's data files")
            
            for json_file in tqdm(json_files, desc="Loading women's data"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    item_id = item.get('source', {}).get('id')
                    if not item_id:
                        continue
                    
                    # Extract metadata
                    items.append({
                        'id': item_id,
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'brand': item.get('brand', ''),
                        'price': item.get('price', {}).get('currentFormatted', ''),
                        'url': item.get('source', {}).get('crawlUrl', ''),
                        'category': ', '.join(item.get('categories', [])),
                        'gender': 'women',
                        'image_path': f"{item_id}_index1.jpg"
                    })
        
        df = pd.DataFrame(items)
        print(f"   ✅ Loaded {len(df)} catalog items (before deduplication)")
        
        if len(df) == 0:
            print("   ⚠️  No catalog items found - catalog will be empty")
            # Return empty dataframe with expected columns
            return pd.DataFrame(columns=['id', 'title', 'description', 'brand', 'price', 'url', 'category', 'gender', 'image_path'])
        
        # Deduplicate by product ID (keep first occurrence)
        df = df.drop_duplicates(subset='id', keep='first').reset_index(drop=True)
        print(f"   ✅ After deduplication: {len(df)} unique items")
        
        return df
    
    def generate_embeddings(self, df):
        """Generate embeddings for all catalog items"""
        print("\n🔮 Generating embeddings...")
        
        embeddings = []
        valid_indices = []
        
        with torch.no_grad():
            for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing images"):
                image_path = self.image_dir / row['image_path']
                
                # Try alternative image paths
                if not image_path.exists():
                    image_path = self.image_dir / f"{row['id']}_index2.jpg"
                if not image_path.exists():
                    image_path = self.image_dir / f"{row['id']}.jpg"
                
                if not image_path.exists():
                    continue
                
                try:
                    # Load and transform image
                    image = Image.open(image_path).convert('RGB')
                    image_tensor = self.transform(image).unsqueeze(0).to(self.device)
                    
                    # Generate embedding
                    embedding = self.model(image_tensor)
                    
                    # L2 normalize
                    embedding = embedding / torch.norm(embedding, p=2, dim=1, keepdim=True)
                    
                    embeddings.append(embedding.cpu().numpy()[0])
                    valid_indices.append(idx)
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing {image_path}: {e}")
                    continue
        
        embeddings = np.array(embeddings).astype('float32')
        print(f"   ✅ Generated {len(embeddings)} embeddings (shape: {embeddings.shape})")
        
        # Filter dataframe to only valid items
        df_valid = df.iloc[valid_indices].reset_index(drop=True)
        
        return embeddings, df_valid
    
    def build_faiss_index(self, embeddings):
        """Build FAISS index for fast similarity search"""
        print("\n🔍 Building FAISS index...")
        
        # Handle empty embeddings case
        if len(embeddings) == 0 or embeddings.shape[0] == 0:
            print("   ⚠️  No embeddings to index - returning empty index")
            # Return a dummy index with expected dimension (512 for CLIP)
            dimension = 512
            index = faiss.IndexFlatL2(dimension)
            print(f"   ✅ Empty FAISS index created (dimension: {dimension})")
            return index
        
        dimension = embeddings.shape[1]
        
        # Use flat L2 index for exact search (can upgrade to IVF for large catalogs)
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        print(f"   ✅ FAISS index built: {index.ntotal} vectors")
        return index
    
    def save_catalog(self, df, embeddings, index):
        """Save all catalog artifacts"""
        print("\n💾 Saving catalog files...")
        
        # Create versioned directory
        version = f"v_{datetime.now().strftime('%Y-%m-%d')}_model-b1"
        catalog_dir = self.output_dir / version
        catalog_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        meta_path = catalog_dir / "catalog_meta.parquet"
        df.to_parquet(meta_path, index=False)
        print(f"   ✅ Saved: {meta_path}")
        
        # Save embeddings
        vecs_path = catalog_dir / "catalog.vecs.npy"
        np.save(vecs_path, embeddings)
        print(f"   ✅ Saved: {vecs_path}")
        
        # Save FAISS index
        index_path = catalog_dir / "catalog.index.faiss"
        faiss.write_index(index, str(index_path))
        print(f"   ✅ Saved: {index_path}")
        
        # Save ID mapping
        idmap_path = catalog_dir / "idmap.npy"
        idmap = df['id'].values
        np.save(idmap_path, idmap)
        print(f"   ✅ Saved: {idmap_path}")
        
        # Create manifest
        manifest = {
            'version': version,
            'built_at': datetime.now().isoformat(),
            'model': 'FashionCLIP',
            'dimension': int(embeddings.shape[1]),
            'num_items': int(len(df)),
            'index_type': 'IndexFlatL2'
        }
        
        manifest_path = catalog_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"   ✅ Saved: {manifest_path}")
        
        print(f"\n🎉 Catalog index built successfully!")
        print(f"   Version: {version}")
        print(f"   Location: {catalog_dir}")
        print(f"   Items: {len(df):,}")
        print(f"   Dimension: {embeddings.shape[1]}")
        
        return catalog_dir
    
    def build(self):
        """Main build process"""
        print("="*60)
        print("🏗️  Building Catalog Index")
        print("="*60)
        
        # Step 1: Load metadata
        df = self.load_catalog_metadata()
        
        # Step 2: Generate embeddings
        embeddings, df_valid = self.generate_embeddings(df)
        
        # Step 3: Build FAISS index
        index = self.build_faiss_index(embeddings)
        
        # Step 4: Save everything
        catalog_dir = self.save_catalog(df_valid, embeddings, index)
        
        return catalog_dir


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build catalog index from Farfetch data')
    parser.add_argument('--data-dir', default='/app/data', help='Data directory')
    parser.add_argument('--image-dir', default='/app/data/images', help='Image directory')
    parser.add_argument('--experiments-dir', default=os.getenv('EXPERIMENTS_DIR', '/gcs/styleme-production/experiments'), help='Experiments directory')
    parser.add_argument('--output-dir', default=os.getenv('CATALOG_DIR', '/gcs/styleme-production/catalog'), help='Output directory')
    
    args = parser.parse_args()
    
    # Build catalog
    builder = CatalogIndexBuilder(
        data_dir=args.data_dir,
        image_dir=args.image_dir,
        experiments_dir=args.experiments_dir,
        output_dir=args.output_dir
    )
    
    catalog_dir = builder.build()
    
    print(f"\n✅ Catalog index ready at: {catalog_dir}")


if __name__ == "__main__":
    main()

