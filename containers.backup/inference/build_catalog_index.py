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
    def __init__(self, gcp_bucket_name, gcp_project_id, data_prefix, images_prefix, experiments_dir, output_dir):
        self.gcp_bucket_name = gcp_bucket_name or "styleme-data-bucket"
        self.gcp_project_id = gcp_project_id or "styleme-475201"
        self.data_prefix = data_prefix or "data/json"
        self.images_prefix = images_prefix or "data/images"
        self.experiments_dir = Path(experiments_dir)
        self.output_dir = Path(output_dir)
        
        # Initialize GCS client
        from google.cloud import storage
        self.gcs_client = storage.Client(project=self.gcp_project_id)
        self.bucket = self.gcs_client.bucket(self.gcp_bucket_name)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔧 Using device: {self.device}")
        
        # Load model
        self.model = self._load_model()
        self.transform = self._get_transform()
    
    def _load_model(self):
        """Load trained FashionCLIP model"""
        print("\n📦 Loading trained model...")
        
        # Find best model
        model_path = None
        for exp_dir in sorted(self.experiments_dir.glob("exp_*"), reverse=True):
            best_model = exp_dir / "best_model.pth"
            if best_model.exists():
                model_path = best_model
                break
        
        if model_path is None:
            raise FileNotFoundError("No trained model found in experiments directory")
        
        print(f"   Model: {model_path}")
        
        # Load model
        model = FashionCLIPModel()
        checkpoint = torch.load(model_path, map_location=self.device)
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
        
        # Load men's data from GCS
        men_prefix = f"{self.data_prefix}/men_data/"
        men_blobs = list(self.bucket.list_blobs(prefix=men_prefix))
        men_json_blobs = [blob for blob in men_blobs if blob.name.endswith('.json')]
        print(f"   Found {len(men_json_blobs)} men's data files in GCS")
        
        for blob in tqdm(men_json_blobs, desc="Loading men's data"):
            try:
                json_content = blob.download_as_text(encoding='utf-8')
                data = json.loads(json_content)
                
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
        
        # Load women's data from GCS
        women_prefix = f"{self.data_prefix}/women_data/"
        women_blobs = list(self.bucket.list_blobs(prefix=women_prefix))
        women_json_blobs = [blob for blob in women_blobs if blob.name.endswith('.json')]
        print(f"   Found {len(women_json_blobs)} women's data files in GCS")
        
        for blob in tqdm(women_json_blobs, desc="Loading women's data"):
            try:
                json_content = blob.download_as_text(encoding='utf-8')
                data = json.loads(json_content)
                
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
                # Try different image paths in GCS
                possible_paths = [
                    f"{self.images_prefix}/{row['image_path']}",
                    f"{self.images_prefix}/{row['id']}_index2.jpg",
                    f"{self.images_prefix}/{row['id']}.jpg"
                ]
                
                image_data = None
                for image_path in possible_paths:
                    try:
                        blob = self.bucket.blob(image_path)
                        if blob.exists():
                            image_data = blob.download_as_bytes()
                            break
                    except Exception:
                        continue
                
                if image_data is None:
                    continue
                
                try:
                    # Load image from bytes
                    from PIL import Image
                    import io
                    image = Image.open(io.BytesIO(image_data)).convert('RGB')
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
    
    parser = argparse.ArgumentParser(description='Build catalog index from GCS data')
    parser.add_argument('--gcp-bucket-name', default='styleme-data-bucket', help='GCS bucket name')
    parser.add_argument('--gcp-project-id', default='styleme-475201', help='GCP project ID')
    parser.add_argument('--data-prefix', default='data/json', help='Data prefix in GCS')
    parser.add_argument('--images-prefix', default='data/images', help='Images prefix in GCS')
    parser.add_argument('--experiments-dir', default='/app/experiments', help='Experiments directory')
    parser.add_argument('--output-dir', default='/app/catalog', help='Output directory')
    
    args = parser.parse_args()
    
    # Build catalog
    builder = CatalogIndexBuilder(
        gcp_bucket_name=args.gcp_bucket_name,
        gcp_project_id=args.gcp_project_id,
        data_prefix=args.data_prefix,
        images_prefix=args.images_prefix,
        experiments_dir=args.experiments_dir,
        output_dir=args.output_dir
    )
    
    catalog_dir = builder.build()
    
    print(f"\n✅ Catalog index ready at: {catalog_dir}")


if __name__ == "__main__":
    main()

