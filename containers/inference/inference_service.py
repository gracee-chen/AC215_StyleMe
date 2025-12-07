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
                 bg_removal_enabled=True, bg_removal_model="briaai/RMBG-1.4"):
        self.catalog_dir = Path(catalog_dir)
        self.experiments_dir = Path(experiments_dir)
        self.wardrobes_dir = Path(wardrobes_dir)
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"🔧 Initializing Inference Service")
        print(f"   Device: {self.device}")
        
        # Initialize background remover
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
                print(f"   ⚠️  Failed to initialize background remover: {e}")
                print("   ⚠️  Continuing without background removal")
                self.bg_remover = None
                self.bg_removal_enabled = False
        else:
            self.bg_remover = None
            self.bg_removal_enabled = False
            print("   ⚠️  Background removal disabled")
        
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
        
        print(f"   Loading model from: {model_path}")
        
        model = FashionCLIPModel()
        checkpoint = torch.load(str(model_path), map_location=self.device)
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
            
            # Download to temp directory
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
            
            # Step 2: Remove background (if enabled)
            if self.bg_removal_enabled and self.bg_remover:
                try:
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
                        
                except Exception as e:
                    print(f"⚠️  Background removal failed: {e}, using original image")
                    # Fallback: reload original image
                    image = Image.open(image_path).convert('RGB')
            
            # Step 3: Transform and embed
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
            full_cat = ','.join([p.strip().lower() for p in parts[2:]]) if len(parts) > 2 else ""
            
            # Map to standard categories with more granular detection
            if 'dress' in main_cat or 'dress' in full_cat:
                return "Dresses"
            elif 'skirt' in main_cat or 'skirt' in full_cat:
                return "Skirts"
            elif 'short' in main_cat or 'short' in full_cat:
                return "Shorts"
            elif 'pant' in main_cat or 'jean' in main_cat or 'trouser' in main_cat or 'pant' in full_cat:
                return "Pants"
            elif 'shoe' in main_cat or 'sneaker' in main_cat or 'boot' in main_cat or 'sandal' in main_cat or 'heel' in main_cat:
                return "Shoes"
            elif 'bag' in main_cat or 'backpack' in main_cat or 'handbag' in main_cat or 'tote' in main_cat:
                return "Bags"
            elif 'shirt' in main_cat or 'top' in main_cat or 'tee' in main_cat or 't-shirt' in main_cat or 'blouse' in main_cat or 'sweater' in main_cat:
                return "Tops"
            elif 'jacket' in main_cat or 'coat' in main_cat or 'blazer' in main_cat or 'cardigan' in main_cat:
                return "Jackets"
            elif 'accessori' in main_cat or 'hat' in main_cat or 'scarf' in main_cat or 'jewelry' in main_cat:
                return "Accessories"
        
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
        Ensures at least one item per category when possible
        """
        category_counts = {}
        diverse_items = []
        category_to_items = {}  # Track items by category
        
        # First pass: Group items by category
        for item in items:
            category = self._extract_category(item.get('category', ''))
            if category not in category_to_items:
                category_to_items[category] = []
            category_to_items[category].append(item)
        
        # Second pass: Select items ensuring diversity
        # Prioritize getting at least one item from each category
        categories_seen = set()
        
        # First, get one item from each category (if we want minimum categories)
        if min_categories:
            for category in sorted(category_to_items.keys(), key=lambda c: len(category_to_items[c]), reverse=True):
                if len(diverse_items) >= min_categories:
                    break
                if category_to_items[category]:
                    best_item = max(category_to_items[category], key=lambda x: x.get('similarity', 0))
                    diverse_items.append(best_item)
                    category_counts[category] = 1
                    categories_seen.add(category)
                    category_to_items[category].remove(best_item)
        
        # Then, continue with standard diversity (max per category)
        for item in items:
            category = self._extract_category(item.get('category', ''))
            
            # Skip if already added in first pass
            if category in categories_seen and category_counts.get(category, 0) >= max_per_category:
                continue
            
            # Add item if we haven't reached the limit for this category
            if category_counts.get(category, 0) < max_per_category:
                diverse_items.append(item)
                category_counts[category] = category_counts.get(category, 0) + 1
                categories_seen.add(category)
        
        # Re-rank after filtering
        for idx, item in enumerate(diverse_items):
            item['rank'] = idx + 1
        
        return diverse_items
    
    def search_catalog(self, query_embedding: np.ndarray, k: int = 3, gender: str = None) -> List[Dict]:
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
        # Earlier matches (more similar) have higher weight
        query_category = None
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
            query_category = max(category_scores, key=category_scores.get)
            sorted_scores = dict(sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:3])
            print(f"   🔍 Inferred query category (weighted top 10): {query_category} (top scores: {sorted_scores})")
        
        # Step 2: Determine which categories to exclude
        categories_to_exclude = set()
        if query_category:
            categories_to_exclude.add(query_category)
            
            # Smart exclusion rules:
            # - If query is Tops, also exclude Dresses (dresses include tops)
            # - If query is Dresses, also exclude Tops and Pants (dresses are complete outfits)
            if query_category == "Tops":
                categories_to_exclude.add("Dresses")
            elif query_category == "Dresses":
                categories_to_exclude.add("Tops")
                categories_to_exclude.add("Pants")
                categories_to_exclude.add("Skirts")
                categories_to_exclude.add("Shorts")
            elif query_category == "Pants":
                categories_to_exclude.add("Dresses")  # Don't mix pants with dresses
        
        print(f"   🚫 Excluding categories: {sorted(categories_to_exclude)}")
        
        # Step 3: Group all items by category, excluding unwanted categories
        items_by_category = {}
        
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
                    
                    # Group by category
                    if item_category not in items_by_category:
                        items_by_category[item_category] = []
                    items_by_category[item_category].append(item)
        
        # Step 4: Find highest match from each category
        outfit_items = []
        for category, category_items in items_by_category.items():
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

