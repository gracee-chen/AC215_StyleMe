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

# Add src to path
sys.path.append('/app/src')
from src.models.train.model_training import FashionCLIPModel


class InferenceService:
    def __init__(self, catalog_dir, experiments_dir, wardrobes_dir, device=None):
        self.catalog_dir = Path(catalog_dir)
        self.experiments_dir = Path(experiments_dir)
        self.wardrobes_dir = Path(wardrobes_dir)
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"🔧 Initializing Inference Service")
        print(f"   Device: {self.device}")
        
        # Load model
        self.model = self._load_model()
        self.transform = self._get_transform()
        
        # Load catalog
        self.catalog_index, self.catalog_meta, self.catalog_idmap = self._load_catalog()
        
        print(f"✅ Inference Service ready")
    
    def _load_model(self):
        """Load trained FashionCLIP model"""
        print("📦 Loading model...")
        
        # Find best model
        model_path = None
        for exp_dir in sorted(self.experiments_dir.glob("exp_*"), reverse=True):
            best_model = exp_dir / "best_model.pth"
            if best_model.exists():
                model_path = best_model
                break
        
        if model_path is None:
            raise FileNotFoundError("No trained model found")
        
        print(f"   Model: {model_path}")
        
        model = FashionCLIPModel()
        checkpoint = torch.load(model_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
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
    
    def _load_catalog(self):
        """Load catalog FAISS index and metadata"""
        print("📚 Loading catalog...")
        
        # Find latest catalog version
        catalog_versions = sorted(self.catalog_dir.glob("v_*"))
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
            # Load and transform
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            embedding = self.model(image_tensor)
            
            # L2 normalize
            embedding = embedding / torch.norm(embedding, p=2, dim=1, keepdim=True)
            
            return embedding.cpu().numpy().astype('float32')
    
    def search_wardrobe(self, user_id: str, query_embedding: np.ndarray, k: int = 5) -> Tuple[Optional[List[Dict]], float]:
        """Search user's wardrobe FAISS index"""
        wardrobe_path = self.wardrobes_dir / user_id
        
        # Check if wardrobe exists
        if not wardrobe_path.exists():
            return None, 0.0
        
        index_path = wardrobe_path / "wardrobe.index.faiss"
        
        # Auto-build wardrobe index if images exist but index doesn't
        if not index_path.exists():
            images_dir = wardrobe_path / "images"
            if images_dir.exists() and list(images_dir.glob("*.jpg")):
                print(f"   🔨 Building wardrobe index for {user_id}...")
                try:
                    # Build the wardrobe index
                    result = subprocess.run([
                        sys.executable,
                        "/app/build_user_wardrobe.py",
                        "--user-id", user_id,
                        "--wardrobe-dir", str(wardrobe_path),
                        "--experiments-dir", str(self.experiments_dir),
                        "--wardrobes-base-dir", str(self.wardrobes_dir)
                    ], capture_output=True, text=True, check=True)
                    print(f"   ✅ Wardrobe index built for {user_id}")
                except subprocess.CalledProcessError as e:
                    print(f"   ❌ Failed to build wardrobe index: {e.stderr}")
                    return None, 0.0
            else:
                return None, 0.0
        
        if not index_path.exists():
            return None, 0.0
        
        try:
            # Load wardrobe index
            index = faiss.read_index(str(index_path))
            
            # Load metadata
            meta_path = wardrobe_path / "wardrobe.parquet"
            meta = pd.read_parquet(meta_path)
            
            # Load ID map
            idmap_path = wardrobe_path / "idmap.npy"
            idmap = np.load(idmap_path, allow_pickle=True)
            
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
                        item['similarity'] = float(similarity)
                        item['rank'] = idx + 1
                        items.append(item)
            
            # Apply category diversity
            diverse_items = self._diversify_by_category(items, max_per_category=1)
            diverse_items = diverse_items[:k]  # Return top k after diversity
            
            best_score = float(diverse_items[0]['similarity']) if len(diverse_items) > 0 else 0.0
            
            return diverse_items, best_score
            
        except Exception as e:
            print(f"⚠️  Error searching wardrobe: {e}")
            return None, 0.0
    
    def _extract_category(self, category_str: str) -> str:
        """Extract main category from category string"""
        if not category_str or pd.isna(category_str):
            return "Other"
        
        # Category string format: "Men, Shoes, Sneakers, Low-Tops"
        # Extract the main category (second level)
        parts = [p.strip() for p in category_str.split(',')]
        
        if len(parts) >= 2:
            main_cat = parts[1].lower()
            
            # Map to standard categories
            if 'shoe' in main_cat or 'sneaker' in main_cat or 'boot' in main_cat:
                return "Shoes"
            elif 'pant' in main_cat or 'jean' in main_cat or 'trouser' in main_cat:
                return "Pants"
            elif 'shirt' in main_cat or 'top' in main_cat or 'tee' in main_cat or 't-shirt' in main_cat:
                return "Tops"
            elif 'jacket' in main_cat or 'coat' in main_cat or 'blazer' in main_cat:
                return "Jackets"
            elif 'bag' in main_cat or 'backpack' in main_cat:
                return "Bags"
            elif 'accessori' in main_cat or 'hat' in main_cat or 'scarf' in main_cat:
                return "Accessories"
            elif 'dress' in main_cat or 'skirt' in main_cat:
                return "Dresses"
        
        return "Other"
    
    def _diversify_by_category(self, items: List[Dict], max_per_category: int = 1) -> List[Dict]:
        """Ensure outfit diversity by limiting items per category"""
        category_counts = {}
        diverse_items = []
        
        for item in items:
            category = self._extract_category(item.get('category', ''))
            
            # Add item if we haven't reached the limit for this category
            if category_counts.get(category, 0) < max_per_category:
                diverse_items.append(item)
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Re-rank after filtering
        for idx, item in enumerate(diverse_items):
            item['rank'] = idx + 1
        
        return diverse_items
    
    def search_catalog(self, query_embedding: np.ndarray, k: int = 3, gender: str = None) -> List[Dict]:
        """Search global catalog FAISS index with category diversity and gender filtering"""
        # Search more items initially to ensure diversity after filtering
        search_k = max(k * 10, 30)  # Get 10x items or at least 30
        distances, indices = self.catalog_index.search(query_embedding, search_k)
        
        # Convert distances to similarity scores
        similarities = 1.0 / (1.0 + distances[0])
        
        # Get items
        items = []
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
                    
                    item['similarity'] = float(similarity)
                    item['rank'] = idx + 1
                    items.append(item)
        
        # Apply category diversity (max 1 item per category)
        diverse_items = self._diversify_by_category(items, max_per_category=1)
        
        # Return top k diverse items
        return diverse_items[:k]
    
    def inference(self, user_id: str, query_image_path: str, 
                  threshold: float = 0.7, wardrobe_k: int = 5, catalog_k: int = 3, gender: str = None) -> Dict:
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
        
        # Step 1: Generate query embedding
        print("   📊 Generating query embedding...")
        query_embedding = self.embed_image(query_image_path)
        
        # Step 2: Search wardrobe first
        print("   👔 Searching user wardrobe...")
        wardrobe_items, best_wardrobe_score = self.search_wardrobe(user_id, query_embedding, k=wardrobe_k)
        
        # Step 3: Decide source
        used_wardrobe = False
        items = []
        reason = None
        
        if wardrobe_items is None:
            reason = "empty_wardrobe"
            print(f"   ⚠️  No wardrobe found, falling back to catalog")
        elif best_wardrobe_score < threshold:
            reason = "low_score"
            print(f"   ⚠️  Best wardrobe score ({best_wardrobe_score:.3f}) < threshold ({threshold}), falling back to catalog")
        else:
            used_wardrobe = True
            items = wardrobe_items
            print(f"   ✅ Using wardrobe results (best score: {best_wardrobe_score:.3f})")
        
        # Step 4: Fallback to catalog if needed
        if not used_wardrobe:
            print("   🛍️  Searching global catalog...")
            if gender:
                print(f"   🔍 Filtering by gender: {gender}")
            items = self.search_catalog(query_embedding, k=catalog_k, gender=gender)
            print(f"   ✅ Found {len(items)} catalog items")
        
        # Step 5: Build result
        result = {
            'user_id': user_id,
            'query_image': str(query_image_path),
            'timestamp': datetime.now().isoformat(),
            'used_wardrobe': used_wardrobe,
            'threshold': threshold,
            'items': items,
            'num_results': len(items)
        }
        
        if reason:
            result['fallback_reason'] = reason
        
        if used_wardrobe:
            result['best_wardrobe_score'] = best_wardrobe_score
        
        print(f"\n   🎉 Inference complete: {len(items)} recommendations")
        return result


def main():
    """Demo inference"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run inference on query image')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--query', required=True, help='Path to query image')
    parser.add_argument('--catalog-dir', default='/app/catalog', help='Catalog directory')
    parser.add_argument('--experiments-dir', default='/app/experiments', help='Experiments directory')
    parser.add_argument('--wardrobes-dir', default='/app/wardrobes', help='Wardrobes directory')
    parser.add_argument('--output', help='Output JSON path')
    parser.add_argument('--threshold', type=float, default=0.7, help='Wardrobe similarity threshold')
    parser.add_argument('--wardrobe-k', type=int, default=5, help='Number of wardrobe items')
    parser.add_argument('--catalog-k', type=int, default=3, help='Number of catalog items')
    parser.add_argument('--gender', type=str, choices=['men', 'women'], help='Filter catalog by gender (men/women)')
    
    args = parser.parse_args()
    
    # Initialize service
    service = InferenceService(
        catalog_dir=args.catalog_dir,
        experiments_dir=args.experiments_dir,
        wardrobes_dir=args.wardrobes_dir
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

