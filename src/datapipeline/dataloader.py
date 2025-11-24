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
                 transform=None, max_samples_per_file: int = None):
        """
        Args:
            gcp_bucket_name: GCS bucket name
            gcp_project_id: GCP project ID
            data_prefix: prefix for JSON data files in GCS
            images_prefix: prefix for image files in GCS
            transform: image transformations
            max_samples_per_file: maximum samples per file (None = use all data)
        """
        self.gcp_bucket_name = gcp_bucket_name or "styleme-data-bucket"
        self.gcp_project_id = gcp_project_id or "styleme-475201"
        self.data_prefix = data_prefix
        self.images_prefix = images_prefix
        self.transform = transform or self._get_default_transform()
        self.max_samples_per_file = max_samples_per_file
        
        # Initialize GCS client
        self.gcs_client = storage.Client(project=self.gcp_project_id)
        self.bucket = self.gcs_client.bucket(self.gcp_bucket_name)
        
        # Load all data
        self.items = self._load_all_data()
        self.item_ids = list(self.items.keys())
        
        # Build compatibility graph
        self.compatibility_graph = self._build_compatibility_graph()
        
        # Image cache to avoid re-downloading from GCS (limited size to prevent OOM)
        self._image_cache = {}
        self._max_cache_size = 500  # Limit cache to 500 images to save memory
        
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
            
            # 1. Gender consistency check - 性别一致性检查
            item_gender = item.get('gender', 'unknown')
            if anchor_gender != 'unknown' and item_gender != 'unknown' and anchor_gender != item_gender:
                continue
            
            # Check if product description matches
            description = item.get('description', '').lower()
            categories = [cat.lower() for cat in item.get('categories', [])]
            
            # 2. Category consistency check - 类别一致性检查（更严格）
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
    
    def _get_image_from_gcs(self, item_id: str) -> Optional[Image.Image]:
        """Get product image from GCS with caching"""
        # Check cache first
        if item_id in self._image_cache:
            return self._image_cache[item_id]
        
        # Try different image naming formats
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
                    # Cache the image
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
                     prefetch_factor: int = 2) -> Tuple[DataLoader, DataLoader, DataLoader]:
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
    # Create dataset using GCS
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
