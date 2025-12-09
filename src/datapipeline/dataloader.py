"""
FashionCLIP Dataloader for Triplet Loss Training
Process Farfetch data and build triplet pairs for fashion compatibility learning
Supports both local filesystem and Google Cloud Storage
"""

import json
import os
import random
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as transforms
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path
from tqdm import tqdm
from google.cloud import storage
import io
import tempfile


class FashionTripletDataset(Dataset):
    """
    Fashion Triplet Dataset for learning clothing combinations
    
    Each sample contains:
    - anchor: main product image
    - positive: compatible product image (from complete_the_look)
    - negative: incompatible product image (randomly selected)
    """
    
    def __init__(self, gcp_bucket_name: str = None, gcp_project_id: str = None, 
                 data_prefix: str = "data/json", images_prefix: str = "data/images",
                 transform=None, max_samples_per_file: int = None,
                 local_cache_dir: str = None):
        """
        Args:
            gcp_bucket_name: GCS bucket name
            gcp_project_id: GCP project ID
            data_prefix: prefix for JSON data files in GCS
            images_prefix: prefix for image files in GCS
            transform: image transformations
            max_samples_per_file: maximum samples per file (None = use all data)
            local_cache_dir: Local directory to cache images (if None, uses memory cache only)
        """
        self.gcp_bucket_name = gcp_bucket_name or "styleme-data-bucket"
        self.gcp_project_id = gcp_project_id or "styleme-475201"
        self.data_prefix = data_prefix
        self.images_prefix = images_prefix
        self.transform = transform or self._get_default_transform()
        self.max_samples_per_file = max_samples_per_file
        
        # Local cache directory for images
        self.local_cache_dir = local_cache_dir
        if self.local_cache_dir:
            self.local_cache_dir = Path(self.local_cache_dir)
            self.local_cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Using local image cache: {self.local_cache_dir}")
        
        # Initialize GCS client (only if needed)
        self.gcs_client = None
        self.bucket = None
        if not self.local_cache_dir or not self._is_cache_complete():
            self.gcs_client = storage.Client(project=self.gcp_project_id)
            self.bucket = self.gcs_client.bucket(self.gcp_bucket_name)
        
        # Load all data
        self.items = self._load_all_data()
        self.item_ids = list(self.items.keys())
        
        # Build compatibility graph
        self.compatibility_graph = self._build_compatibility_graph()
        
        # Image cache to avoid re-downloading from GCS (large cache for speed)
        self._image_cache = {}
        self._max_cache_size = 8000  # Large but safe cache size (configurable)
        
        print(f"\n🎉 Dataset initialization complete!")
        print(f"📦 Total items: {len(self.items):,}")
        print(f"🔗 Compatibility relationships: {len(self.compatibility_graph):,}")
        print(f"☁️ Using GCS bucket: {self.gcp_bucket_name}")
    
    def _get_default_transform(self):
        """Default image transformations"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def _load_all_data(self) -> Dict:
        """Load all JSON data files from GCS"""
        items = {}
        
        print("🔄 Loading fashion data from GCS...")
        
        # Load men_data
        men_data_prefix = f"{self.data_prefix}/men_data/"
        men_blobs = list(self.bucket.list_blobs(prefix=men_data_prefix))
        men_json_blobs = [blob for blob in men_blobs if blob.name.endswith('.json')]
        
        print(f"📁 Found {len(men_json_blobs)} men's data files in GCS")
        
        for blob in tqdm(men_json_blobs, desc="Loading men's data", unit="file"):
            file_items = self._load_json_from_gcs(blob)
            items.update(file_items)
        
        # Load women_data
        women_data_prefix = f"{self.data_prefix}/women_data/"
        women_blobs = list(self.bucket.list_blobs(prefix=women_data_prefix))
        women_json_blobs = [blob for blob in women_blobs if blob.name.endswith('.json')]
        
        print(f"📁 Found {len(women_json_blobs)} women's data files in GCS")
        
        for blob in tqdm(women_json_blobs, desc="Loading women's data", unit="file"):
            file_items = self._load_json_from_gcs(blob)
            items.update(file_items)
        
        print(f"✅ Total items loaded: {len(items):,}")
        return items
    
    def _load_json_from_gcs(self, blob) -> Dict:
        """Load single JSON file from GCS"""
        items = {}
        try:
            # Download JSON content from GCS
            json_content = blob.download_as_text(encoding='utf-8')
            data = json.loads(json_content)
            
            # Use all data if max_samples_per_file is None, otherwise limit
            items_to_process = data if self.max_samples_per_file is None else data[:self.max_samples_per_file]
            
            for item in items_to_process:
                item_id = item.get('source', {}).get('id')
                if item_id and 'complete_the_look' in item:
                    # Add gender information based on file path
                    if 'men_data' in blob.name:
                        item['gender'] = 'men'
                    elif 'women_data' in blob.name:
                        item['gender'] = 'women'
                    else:
                        item['gender'] = 'unknown'
                    
                    items[item_id] = item
                    
        except Exception as e:
            print(f"❌ Error loading {blob.name} from GCS: {e}")
        
        return items
    
    def _build_compatibility_graph(self) -> Dict:
        """Build compatibility relationship graph"""
        compatibility_graph = {}
        total_items = len(self.items)
        
        print(f"🔗 Building compatibility graph for {total_items:,} items...")
        
        # Statistics tracking
        total_relationships = 0
        items_with_relationships = 0
        
        # Use tqdm for progress bar
        for item_id, item in tqdm(self.items.items(), 
                                 desc="Building compatibility graph", 
                                 unit="item",
                                 total=total_items):
            if 'complete_the_look' in item:
                compatible_items = []
                for look_item in item['complete_the_look']:
                    # Find compatible items based on description
                    compatible_ids = self._find_compatible_items(look_item, item_id)
                    compatible_items.extend(compatible_ids)
                
                if compatible_items:
                    compatibility_graph[item_id] = compatible_items
                    items_with_relationships += 1
                    total_relationships += len(compatible_items)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 COMPATIBILITY GRAPH SUMMARY")
        print("="*60)
        print(f"📦 Total items processed: {total_items:,}")
        print(f"🔗 Items with relationships: {items_with_relationships:,}")
        print(f"📈 Total compatibility relationships: {total_relationships:,}")
        print(f"📊 Average relationships per item: {total_relationships/items_with_relationships:.1f}" if items_with_relationships > 0 else "📊 Average relationships per item: 0")
        print(f"📋 Coverage: {(items_with_relationships/total_items)*100:.1f}%")
        print("="*60)
        
        return compatibility_graph
    
    def _find_compatible_items(self, look_item: Dict, exclude_id: str) -> List[str]:
        """Find compatible items based on complete_the_look description with improved constraints"""
        compatible_ids = []
        target_item = look_item.get('item', '').lower()
        target_color = look_item.get('color', '').lower()
        target_texture = look_item.get('texture', '').lower()
        
        # Early exit if no meaningful target
        if not target_item:
            return compatible_ids
        
        # Get the category of the target item to avoid same-category matches
        target_category = self._get_item_category(target_item)
        
        # Get gender of the anchor item
        anchor_item = self.items.get(exclude_id, {})
        anchor_gender = anchor_item.get('gender', 'unknown')
        
        # Use all items for better compatibility matching
        items_to_search = list(self.items.items())
        
        for item_id, item in items_to_search:
            if item_id == exclude_id:
                continue
            
            # 1. Gender consistency check
            item_gender = item.get('gender', 'unknown')
            if anchor_gender != 'unknown' and item_gender != 'unknown' and anchor_gender != item_gender:
                continue
            
            # Check if product description matches
            description = item.get('description', '').lower()
            categories = [cat.lower() for cat in item.get('categories', [])]
            
            # 2. Category consistency check (stricter)
            item_category = self._get_item_category(description)
            if target_category and item_category and target_category == item_category:
                continue
            
            # Additional category consistency checks
            if self._is_same_category_strict(target_item, description, categories):
                continue
            
            # Improved matching logic with more flexible matching
            match_score = 0
            
            # Product type matching (most important) - more flexible
            target_words = target_item.split()
            for word in target_words:
                if len(word) > 2:  # Only consider words longer than 2 characters
                    if word in description or any(word in cat for cat in categories):
                        match_score += 1
            
            # Color matching - more flexible
            if target_color:
                color_words = target_color.split()
                for color_word in color_words:
                    if len(color_word) > 2 and (color_word in description or color_word in ' '.join(categories)):
                        match_score += 1
            
            # Texture matching - more flexible
            if target_texture:
                texture_words = target_texture.split()
                for texture_word in texture_words:
                    if len(texture_word) > 2 and texture_word in description:
                        match_score += 1
            
            # Category-based matching (additional boost)
            if any(cat in description for cat in ['shirt', 'pants', 'shoes', 'bag', 'jacket', 'dress']):
                match_score += 0.5
            
            # Accept matches with score >= 0.5 for more training data
            if match_score >= 0.5:
                compatible_ids.append(item_id)
                
                # Early exit if we have enough matches
                if len(compatible_ids) >= 3:  # Limit to 3 matches
                    break
        
        return compatible_ids[:3]  # Return exactly 3 compatible items
    
    def _get_item_category(self, item_description: str) -> str:
        """Get the main category of an item based on its description"""
        description = item_description.lower()
        
        # Define category keywords
        categories = {
            'shirt': ['shirt', 't-shirt', 'blouse', 'top', 'tee', 'polo'],
            'pants': ['pants', 'trousers', 'jeans', 'leggings', 'shorts', 'trousers'],
            'shoes': ['shoes', 'sneakers', 'boots', 'sandals', 'heels', 'flats'],
            'bag': ['bag', 'handbag', 'backpack', 'purse', 'tote', 'clutch'],
            'jacket': ['jacket', 'blazer', 'coat', 'cardigan', 'hoodie', 'sweater'],
            'dress': ['dress', 'gown', 'skirt', 'jumpsuit', 'romper'],
            'accessories': ['belt', 'scarf', 'hat', 'watch', 'jewelry', 'sunglasses']
        }
        
        # Find the best matching category
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in description:
                    return category
        
        return 'unknown'
    
    def _is_same_category_strict(self, target_item: str, description: str, categories: List[str]) -> bool:
        """Strict category consistency check to prevent same-category matches"""
        target_lower = target_item.lower()
        desc_lower = description.lower()
        cats_lower = [cat.lower() for cat in categories]
        
        # Define strict category mappings
        category_groups = {
            'tops': ['shirt', 't-shirt', 'blouse', 'top', 'tee', 'polo', 'tank', 'camisole', 'crop'],
            'bottoms': ['pants', 'trousers', 'jeans', 'leggings', 'shorts', 'skirt', 'culottes'],
            'shoes': ['shoes', 'sneakers', 'boots', 'sandals', 'heels', 'flats', 'loafers', 'oxfords'],
            'bags': ['bag', 'handbag', 'backpack', 'purse', 'tote', 'clutch', 'satchel', 'crossbody'],
            'outerwear': ['jacket', 'blazer', 'coat', 'cardigan', 'hoodie', 'sweater', 'vest'],
            'dresses': ['dress', 'gown', 'jumpsuit', 'romper', 'maxi', 'mini', 'midi'],
            'accessories': ['belt', 'scarf', 'hat', 'watch', 'jewelry', 'sunglasses', 'gloves']
        }
        
        # Check if target and item belong to the same category group
        target_group = None
        item_group = None
        
        for group_name, keywords in category_groups.items():
            # Check target item
            if any(keyword in target_lower for keyword in keywords):
                target_group = group_name
            
            # Check item description and categories
            if any(keyword in desc_lower for keyword in keywords) or \
               any(keyword in ' '.join(cats_lower) for keyword in keywords):
                item_group = group_name
        
        # If both items belong to the same category group, they are incompatible
        if target_group and item_group and target_group == item_group:
            return True
        
        # Additional specific checks
        specific_checks = [
            ('pants', 'trousers'), ('shirt', 'blouse'), ('shoes', 'boots'),
            ('bag', 'handbag'), ('dress', 'gown'), ('jacket', 'blazer')
        ]
        
        for check1, check2 in specific_checks:
            if (check1 in target_lower and check2 in desc_lower) or \
               (check2 in target_lower and check1 in desc_lower):
                return True
        
        return False
    
    def _is_cache_complete(self) -> bool:
        """Check if local cache has all required images"""
        if not self.local_cache_dir:
            return False
        # Simple check: if cache dir exists and has files, assume it might be complete
        # Full check would require scanning all item_ids, which is expensive
        return self.local_cache_dir.exists() and len(list(self.local_cache_dir.glob("*.jpg"))) > 100
    
    def _get_image_from_gcs(self, item_id: str) -> Optional[Image.Image]:
        """Get product image from local cache or GCS with fallback"""
        # Check memory cache first
        if item_id in self._image_cache:
            return self._image_cache[item_id]
        
        # Try local cache if available
        if self.local_cache_dir:
            local_paths = [
                self.local_cache_dir / f"{item_id}_index1.jpg",
                self.local_cache_dir / f"{item_id}_index2.jpg",
                self.local_cache_dir / f"{item_id}.jpg"
            ]
            for local_path in local_paths:
                if local_path.exists():
                    try:
                        image = Image.open(local_path).convert('RGB')
                        # Add to memory cache for faster access
                        if len(self._image_cache) < self._max_cache_size:
                            self._image_cache[item_id] = image
                        return image
                    except Exception as e:
                        continue
        
        # Fallback to GCS download (if GCS client is available)
        if not self.bucket:
            return None
        
        # Try different image naming formats in GCS
        possible_paths = [
            f"{self.images_prefix}/{item_id}_index1.jpg",
            f"{self.images_prefix}/{item_id}_index2.jpg",
            f"{self.images_prefix}/{item_id}.jpg"
        ]
        
        for image_path in possible_paths:
            try:
                blob = self.bucket.blob(image_path)
                if blob.exists():
                    # Download image data
                    image_data = blob.download_as_bytes()
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(image_data)).convert('RGB')
                    
                    # Save to local cache if available
                    if self.local_cache_dir:
                        # Determine which filename to use
                        if "_index1" in image_path:
                            local_path = self.local_cache_dir / f"{item_id}_index1.jpg"
                        elif "_index2" in image_path:
                            local_path = self.local_cache_dir / f"{item_id}_index2.jpg"
                        else:
                            local_path = self.local_cache_dir / f"{item_id}.jpg"
                        
                        try:
                            image.save(local_path, 'JPEG', quality=95)
                        except Exception as e:
                            pass  # Ignore save errors, continue with in-memory cache
                    
                    # Cache the image in memory
                    # Limit cache size - remove oldest entries if cache is full
                    if len(self._image_cache) >= self._max_cache_size:
                        # Remove oldest 20% of cache entries
                        keys_to_remove = list(self._image_cache.keys())[:self._max_cache_size // 5]
                        for key in keys_to_remove:
                            del self._image_cache[key]
                    self._image_cache[item_id] = image
                    return image
            except Exception as e:
                continue
        
        return None
    
    def _create_dummy_sample(self):
        """Create a dummy sample when no valid image is found"""
        import torch
        dummy_image = torch.zeros(3, 224, 224)
        return dummy_image, dummy_image, dummy_image
    
    def __len__(self):
        return len(self.compatibility_graph)
    
    def __getitem__(self, idx):
        """Get triplet sample"""
        # Find a valid sample with available images
        max_attempts = len(self.compatibility_graph)
        for attempt in range(max_attempts):
            current_idx = (idx + attempt) % len(self.compatibility_graph)
            anchor_id = list(self.compatibility_graph.keys())[current_idx]
            anchor_item = self.items[anchor_id]
            
            # Get anchor image from GCS
            anchor_image = self._get_image_from_gcs(anchor_id)
            if anchor_image is not None:
                break
        else:
            # If no valid image found, create a dummy sample
            return self._create_dummy_sample()
        
        anchor_image = self.transform(anchor_image)
        
        # Get positive sample (compatible items)
        positive_ids = self.compatibility_graph[anchor_id]
        if not positive_ids:
            # If no compatible items, return next sample
            return self.__getitem__((idx + 1) % len(self))
        
        positive_id = random.choice(positive_ids)
        positive_image = self._get_image_from_gcs(positive_id)
        
        if positive_image is None:
            return self.__getitem__((idx + 1) % len(self))
        
        positive_image = self.transform(positive_image)
        
        # Get negative sample (incompatible items) - try multiple times for better diversity
        negative_image = None
        for _ in range(5):  # Try up to 5 times to find a good negative sample
            negative_id = self._get_negative_sample(anchor_id, positive_ids)
            negative_image = self._get_image_from_gcs(negative_id)
            
            if negative_image is not None:
                negative_image = self.transform(negative_image)
                break
        
        if negative_image is None:
            # If no valid negative image, return next sample
            return self.__getitem__((idx + 1) % len(self))
        
        return anchor_image, positive_image, negative_image
    
    def _get_negative_sample(self, anchor_id: str, positive_ids: List[str]) -> str:
        """Get negative sample"""
        # Randomly select from all items, excluding anchor and positive
        available_ids = [id for id in self.item_ids 
                        if id != anchor_id and id not in positive_ids]
        
        if not available_ids:
            # If no available negative samples, randomly select one
            available_ids = [id for id in self.item_ids if id != anchor_id]
        
        return random.choice(available_ids)


def create_dataloader(gcp_bucket_name: str = "styleme-data-bucket", 
                     gcp_project_id: str = "styleme-475201",
                     data_prefix: str = "data/json",
                     images_prefix: str = "data/images",
                     batch_size: int = 32, 
                     num_workers: int = 4, 
                     shuffle: bool = True, 
                     max_samples_per_file: int = None,
                     train_split: float = 0.7,
                     val_split: float = 0.05,
                     pin_memory: bool = True,
                     prefetch_factor: int = 2,
                     dataset: FashionTripletDataset = None) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Create DataLoader for training, validation and test using GCS data
    
    Args:
        gcp_bucket_name: GCS bucket name
        gcp_project_id: GCP project ID
        data_prefix: prefix for JSON data files in GCS
        images_prefix: prefix for image files in GCS
        batch_size: batch size
        num_workers: number of worker processes
        shuffle: whether to shuffle data
        max_samples_per_file: maximum samples per file (None = use all data)
        train_split: fraction of data for training
        val_split: fraction of data for validation
    
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    # Create dataset using GCS (or use provided one)
    if dataset is None:
        dataset = FashionTripletDataset(
            gcp_bucket_name=gcp_bucket_name,
            gcp_project_id=gcp_project_id,
            data_prefix=data_prefix,
            images_prefix=images_prefix,
            max_samples_per_file=max_samples_per_file
        )
    
    # Split dataset into train, validation and test
    total_size = len(dataset)
    train_size = int(train_split * total_size)
    val_size = int(val_split * total_size)
    test_size = total_size - train_size - val_size
    
    train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size, test_size]
    )
    
    # Preload images to cache if requested (for faster training)
    # This downloads all images once before training starts
    preload_images = getattr(dataset, '_preload_images', False)
    max_preload = getattr(dataset, '_max_preload_images', 5000)  # Limit preload count (None = all)
    io_throttle = getattr(dataset, '_io_throttle', False)
    io_delay_ms = getattr(dataset, '_io_delay_ms', 0.1)
    
    if preload_images:
        import time
        print("\n🔄 Preloading images to cache (this may take a few minutes)...")
        if max_preload is None:
            print("   ⚠️  Loading ALL images to memory to avoid disk I/O during training")
        else:
            print(f"   This will download up to {max_preload} images once to avoid GCS delays")
            print("   Monitoring memory usage to prevent overflow...")
        if io_throttle:
            print(f"   🛡️  I/O throttling enabled ({io_delay_ms*1000:.1f}ms delay) to prevent disk saturation")
        
        # Check available memory before preloading
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / 1024**3
            print(f"   📊 Available memory: {available_gb:.1f}GB")
            if available_gb < 2.0 and max_preload is None:
                print("   ⚠️  WARNING: Low memory! Limiting preload to 5000 images.")
                max_preload = 5000
        except ImportError:
            pass
        
        # Get ALL unique item IDs from dataset (not just train)
        all_item_ids = set(dataset.item_ids)
        
        # Also get IDs from compatibility graph (positive items)
        for anchor_id, compatible_items in dataset.compatibility_graph.items():
            all_item_ids.add(anchor_id)
            for compat_item in compatible_items:
                if isinstance(compat_item, dict) and 'id' in compat_item:
                    all_item_ids.add(compat_item['id'])
                elif isinstance(compat_item, str):
                    all_item_ids.add(compat_item)
        
        # Limit to max_preload if specified
        if max_preload is not None:
            all_item_ids = list(all_item_ids)[:max_preload]
            print(f"   📋 Loading {len(all_item_ids)} unique images (limited by max_preload_images)")
        else:
            all_item_ids = list(all_item_ids)
            print(f"   📋 Loading ALL {len(all_item_ids)} unique images to memory")
        
        # Preload images with memory monitoring and I/O throttling
        preloaded = 0
        skipped = 0
        for item_id in tqdm(all_item_ids, desc="Preloading images"):
            # I/O throttling to prevent disk saturation
            if io_throttle and preloaded > 0:
                time.sleep(io_delay_ms)
            
            # Check memory periodically
            if preloaded % 500 == 0 and preloaded > 0:
                try:
                    import psutil
                    memory = psutil.virtual_memory()
                    if memory.percent > 85:  # Stop if memory > 85%
                        print(f"\n   ⚠️  Memory usage high ({memory.percent:.1f}%), stopping preload early")
                        break
                except:
                    pass
            
            if item_id not in dataset._image_cache:
                image = dataset._get_image_from_gcs(item_id)
                if image is not None:
                    # Check cache size before adding
                    if dataset._max_cache_size and len(dataset._image_cache) >= dataset._max_cache_size:
                        # Remove oldest 10% if cache is full
                        keys_to_remove = list(dataset._image_cache.keys())[:len(dataset._image_cache)//10]
                        for key in keys_to_remove:
                            del dataset._image_cache[key]
                    dataset._image_cache[item_id] = image
                    preloaded += 1
                else:
                    skipped += 1
        
        print(f"   ✅ Preloaded {preloaded} images to cache")
        if skipped > 0:
            print(f"   ⚠️  Skipped {skipped} images (not found or failed)")
        print(f"   📦 Cache size: {len(dataset._image_cache)} images")
        print(f"   💾 All images now in memory - training will use zero disk I/O!")
    
    # VM-safe: disable pin_memory if num_workers is 0 (saves memory)
    effective_pin_memory = pin_memory and num_workers > 0
    
    # Create train dataloader with VM-safe settings
    train_loader_kwargs = {
        'dataset': train_dataset,
        'batch_size': batch_size,
        'shuffle': shuffle,
        'num_workers': num_workers,  # Use configured value (0 for VM safety)
        'pin_memory': effective_pin_memory,  # Disable if num_workers=0
        'drop_last': True,
        'persistent_workers': False
    }
    if num_workers > 0:
        train_loader_kwargs['prefetch_factor'] = min(prefetch_factor, 2)  # Limit prefetch
    train_loader = DataLoader(**train_loader_kwargs)
    
    # Create validation dataloader
    val_loader_kwargs = {
        'dataset': val_dataset,
        'batch_size': batch_size,
        'shuffle': False,
        'num_workers': num_workers,
        'pin_memory': effective_pin_memory,
        'drop_last': True,
        'persistent_workers': False
    }
    if num_workers > 0:
        val_loader_kwargs['prefetch_factor'] = min(prefetch_factor, 2)
    val_loader = DataLoader(**val_loader_kwargs)
    
    # Create test dataloader
    test_loader_kwargs = {
        'dataset': test_dataset,
        'batch_size': batch_size,
        'shuffle': False,
        'num_workers': num_workers,
        'pin_memory': effective_pin_memory,
        'drop_last': True,
        'persistent_workers': False
    }
    if num_workers > 0:
        test_loader_kwargs['prefetch_factor'] = min(prefetch_factor, 2)
    test_loader = DataLoader(**test_loader_kwargs)
    
    return train_loader, val_loader, test_loader


def test_dataloader():
    """Test dataloader functionality with GCS"""
    print("Creating GCS dataloader...")
    train_loader, val_loader, test_loader = create_dataloader(
        gcp_bucket_name="styleme-data-bucket",
        gcp_project_id="styleme-475201",
        batch_size=4, 
        num_workers=0
    )
    
    print(f"Train dataset size: {len(train_loader.dataset)}")
    print(f"Validation dataset size: {len(val_loader.dataset)}")
    print(f"Test dataset size: {len(test_loader.dataset)}")
    print(f"Number of train batches: {len(train_loader)}")
    
    # Test one batch
    for batch in train_loader:
        print(f"Batch shapes:")
        print(f"  Anchor: {batch[0].shape}")
        print(f"  Positive: {batch[1].shape}")
        print(f"  Negative: {batch[2].shape}")
        break


if __name__ == "__main__":
    test_dataloader()
