"""
FashionCLIP Dataloader for Triplet Loss Training
Process Farfetch data and build triplet pairs for fashion compatibility learning
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


class FashionTripletDataset(Dataset):
    """
    Fashion Triplet Dataset for learning clothing combinations
    
    Each sample contains:
    - anchor: main product image
    - positive: compatible product image (from complete_the_look)
    - negative: incompatible product image (randomly selected)
    """
    
    def __init__(self, data_dir: str, image_dir: str, transform=None, max_samples_per_file: int = None):
        """
        Args:
            data_dir: JSON data files directory
            image_dir: image files directory
            transform: image transformations
            max_samples_per_file: maximum samples per file (None = use all data) (None = use all data)
        """
        self.data_dir = Path(data_dir).expanduser()
        self.image_dir = Path(image_dir).expanduser()
        self.transform = transform or self._get_default_transform()
        self.max_samples_per_file = max_samples_per_file  # None means use all data
        
        # Load all data
        self.items = self._load_all_data()
        self.item_ids = list(self.items.keys())
        
        # Build compatibility graph
        self.compatibility_graph = self._build_compatibility_graph()
        
        print(f"\n🎉 Dataset initialization complete!")
        print(f"📦 Total items: {len(self.items):,}")
        print(f"🔗 Compatibility relationships: {len(self.compatibility_graph):,}")
    
    def _get_default_transform(self):
        """Default image transformations"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def _load_all_data(self) -> Dict:
        """Load all JSON data files"""
        items = {}
        
        print("🔄 Loading fashion data...")
        
        # Load men_data
        men_data_dir = self.data_dir / "json" / "men_data"
        if men_data_dir.exists():
            json_files = list(men_data_dir.glob("*.json"))
            print(f"📁 Found {len(json_files)} men's data files")
            
            for json_file in tqdm(json_files, desc="Loading men's data", unit="file"):
                file_items = self._load_json_file(json_file)
                items.update(file_items)
        
        # Load women_data
        women_data_dir = self.data_dir / "json" / "women_data"
        if women_data_dir.exists():
            json_files = list(women_data_dir.glob("*.json"))
            print(f"📁 Found {len(json_files)} women's data files")
            
            for json_file in tqdm(json_files, desc="Loading women's data", unit="file"):
                file_items = self._load_json_file(json_file)
                items.update(file_items)
        
        print(f"✅ Total items loaded: {len(items):,}")
        return items
    
    def _load_json_file(self, json_file: Path) -> Dict:
        """Load single JSON file"""
        items = {}
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Use all data if max_samples_per_file is None, otherwise limit
            items_to_process = data if self.max_samples_per_file is None else data[:self.max_samples_per_file]
            
            for item in items_to_process:
                item_id = item.get('source', {}).get('id')
                if item_id and 'complete_the_look' in item:
                    items[item_id] = item
                    
        except Exception as e:
            print(f"❌ Error loading {json_file}: {e}")
        
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
        """Find compatible items based on complete_the_look description"""
        compatible_ids = []
        target_item = look_item.get('item', '').lower()
        target_color = look_item.get('color', '').lower()
        target_texture = look_item.get('texture', '').lower()
        
        # Early exit if no meaningful target
        if not target_item:
            return compatible_ids
        
        # Get the category of the target item to avoid same-category matches
        target_category = self._get_item_category(target_item)
        
        # Use all items for better compatibility matching
        items_to_search = list(self.items.items())
        
        for item_id, item in items_to_search:
            if item_id == exclude_id:
                continue
                
            # Check if product description matches
            description = item.get('description', '').lower()
            categories = [cat.lower() for cat in item.get('categories', [])]
            
            # Skip items in the same category to avoid duplicates (e.g., shirt matching shirt)
            item_category = self._get_item_category(description)
            if target_category and item_category and target_category == item_category:
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
    
    def _get_image_path(self, item_id: str) -> Optional[Path]:
        """Get product image path"""
        # Try different image naming formats
        possible_paths = [
            self.image_dir / f"{item_id}_index1.jpg",
            self.image_dir / f"{item_id}_index2.jpg",
            self.image_dir / f"{item_id}.jpg"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
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
            
            # Get anchor image
            anchor_path = self._get_image_path(anchor_id)
            if anchor_path is not None:
                break
        else:
            # If no valid image found, create a dummy sample
            return self._create_dummy_sample()
        
        anchor_image = Image.open(anchor_path).convert('RGB')
        anchor_image = self.transform(anchor_image)
        
        # Get positive sample (compatible items)
        positive_ids = self.compatibility_graph[anchor_id]
        if not positive_ids:
            # If no compatible items, return next sample
            return self.__getitem__((idx + 1) % len(self))
        
        positive_id = random.choice(positive_ids)
        positive_path = self._get_image_path(positive_id)
        
        if positive_path is None:
            return self.__getitem__((idx + 1) % len(self))
        
        positive_image = Image.open(positive_path).convert('RGB')
        positive_image = self.transform(positive_image)
        
        # Get negative sample (incompatible items) - try multiple times for better diversity
        negative_image = None
        for _ in range(5):  # Try up to 5 times to find a good negative sample
            negative_id = self._get_negative_sample(anchor_id, positive_ids)
            negative_path = self._get_image_path(negative_id)
            
            if negative_path is not None:
                negative_image = Image.open(negative_path).convert('RGB')
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


def create_dataloader(data_dir: str, image_dir: str, batch_size: int = 32, 
                     num_workers: int = 4, shuffle: bool = True, 
                     max_samples_per_file: int = None,
                     use_gcp_storage: bool = False, gcp_config: dict = None) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Create DataLoader for training, validation and test
    
    Args:
        data_dir: data directory (ignored if use_gcp_storage=True)
        image_dir: image directory (ignored if use_gcp_storage=True)
        batch_size: batch size
        num_workers: number of worker processes
        shuffle: whether to shuffle data
        max_samples_per_file: maximum samples per file (None = use all data)
        use_gcp_storage: whether to use GCP Storage
        gcp_config: GCP configuration dictionary
    
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    if use_gcp_storage and gcp_config:
        # Use GCP Storage dataloader
        from gcp_dataloader import create_gcp_dataloader
        
        return create_gcp_dataloader(
            bucket_name=gcp_config['gcp_bucket_name'],
            project_id=gcp_config['gcp_project_id'],
            data_prefix=gcp_config['gcp_data_prefix'],
            images_prefix=gcp_config['gcp_images_prefix'],
            batch_size=batch_size,
            num_workers=num_workers,
            max_samples_per_file=max_samples_per_file,
            train_split=0.7,
            val_split=0.15
        )
    else:
        # Use local dataloader
        # Create dataset
        dataset = FashionTripletDataset(data_dir, image_dir, max_samples_per_file=max_samples_per_file)
        
        # Split dataset into train, validation and test (70/15/15)
        total_size = len(dataset)
        train_size = int(0.7 * total_size)
        val_size = int(0.15 * total_size)
        test_size = total_size - train_size - val_size
        
        train_dataset, val_dataset, test_dataset = torch.utils.data.random_split(
            dataset, [train_size, val_size, test_size]
        )
    
    # Create train dataloader
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )
    
    # Create validation dataloader
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,  # No shuffle for validation
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )
    
    # Create test dataloader
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,  # No shuffle for test
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )
    
    return train_loader, val_loader, test_loader


def test_dataloader():
    """Test dataloader functionality"""
    data_dir = "../data"
    image_dir = "../data/images"
    
    print("Creating dataloader...")
    dataloader = create_dataloader(data_dir, image_dir, batch_size=4, num_workers=0)
    
    print(f"Dataset size: {len(dataloader.dataset)}")
    print(f"Number of batches: {len(dataloader)}")
    
    # Test one batch
    for batch in dataloader:
        print(f"Batch shapes:")
        print(f"  Anchor: {batch['anchor'].shape}")
        print(f"  Positive: {batch['positive'].shape}")
        print(f"  Negative: {batch['negative'].shape}")
        print(f"  Anchor IDs: {batch['anchor_id']}")
        break


if __name__ == "__main__":
    test_dataloader()
