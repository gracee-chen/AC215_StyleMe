"""
Personal Wardrobe AI Stylist - Inference Module
For outfit recommendations and product suggestions
"""

import torch
import torch.nn.functional as F
from PIL import Image
import torchvision.transforms as transforms
import numpy as np
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from .model_training import FashionCLIPModel
import warnings
warnings.filterwarnings('ignore')


class FashionStylist:
    """
    Personal Wardrobe AI Stylist
    """
    
    def __init__(self, model_path: str, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initialize stylist
        
        Args:
            model_path: path to trained model
            device: running device
        """
        self.device = device
        self.model = self._load_model(model_path)
        self.transform = self._get_transform()
        
        # User wardrobe data
        self.user_wardrobe = {}
        self.farfetch_database = {}
        
        print(f"🎨 Fashion Stylist initialized on {device}")
    
    def _load_model(self, model_path: str) -> FashionCLIPModel:
        """Load trained model"""
        model = FashionCLIPModel()
        
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint['model_state_dict'])
            print(f"✅ Model loaded from {model_path}")
        else:
            print(f"⚠️ Model file not found: {model_path}, using pretrained weights")
        
        model.to(self.device)
        model.eval()
        return model
    
    def _get_transform(self):
        """Get image transformations"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def load_user_wardrobe(self, wardrobe_dir: str):
        """
        Load user wardrobe
        
        Args:
            wardrobe_dir: user wardrobe image directory
        """
        wardrobe_path = Path(wardrobe_dir)
        if not wardrobe_path.exists():
            print(f"❌ Wardrobe directory not found: {wardrobe_dir}")
            return
        
        # Scan user wardrobe images
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        for img_path in wardrobe_path.rglob('*'):
            if img_path.suffix.lower() in image_extensions:
                item_id = img_path.stem
                self.user_wardrobe[item_id] = {
                    'path': str(img_path),
                    'category': self._infer_category(img_path.name),
                    'features': None  # Will be computed when needed
                }
        
        print(f"👔 Loaded {len(self.user_wardrobe)} items from user wardrobe")
    
    def load_farfetch_database(self, data_dir: str):
        """
        Load Farfetch product database
        
        Args:
            data_dir: Farfetch data directory
        """
        data_path = Path(data_dir)
        
        # Load JSON data
        json_files = []
        json_files.extend((data_path / "Data caption" / "men_data").glob("*.json"))
        json_files.extend((data_path / "Data caption" / "women_data").glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    item_id = item.get('source', {}).get('id')
                    if item_id:
                        self.farfetch_database[item_id] = {
                            'data': item,
                            'features': None,
                            'image_path': self._find_image_path(item_id, data_path / "images")
                        }
                        
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        print(f"🛍️ Loaded {len(self.farfetch_database)} items from Farfetch database")
    
    def _find_image_path(self, item_id: str, image_dir: Path) -> Optional[str]:
        """Find product image path"""
        possible_paths = [
            image_dir / f"{item_id}_index1.jpg",
            image_dir / f"{item_id}_index2.jpg",
            image_dir / f"{item_id}.jpg"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        return None
    
    def _infer_category(self, filename: str) -> str:
        """Infer product category from filename"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['shirt', 'blouse', 'top', 'tee']):
            return 'tops'
        elif any(word in filename_lower for word in ['pant', 'jean', 'trouser']):
            return 'bottoms'
        elif any(word in filename_lower for word in ['shoe', 'sneaker', 'boot']):
            return 'shoes'
        elif any(word in filename_lower for word in ['jacket', 'coat', 'blazer']):
            return 'outerwear'
        elif any(word in filename_lower for word in ['dress', 'skirt']):
            return 'dresses'
        else:
            return 'accessories'
    
    def _extract_features(self, image_path: str) -> torch.Tensor:
        """Extract image features"""
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                features = self.model(image_tensor)
            
            return features.squeeze(0)
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return torch.zeros(512).to(self.device)  # Return zero vector as fallback
    
    def recommend_from_wardrobe(self, selected_item_id: str, num_recommendations: int = 3) -> List[Dict]:
        """
        Recommend from user wardrobe
        
        Args:
            selected_item_id: user selected item ID
            num_recommendations: number of recommendations
            
        Returns:
            list of recommended items
        """
        if selected_item_id not in self.user_wardrobe:
            print(f"❌ Item {selected_item_id} not found in wardrobe")
            return []
        
        # Get selected item features
        selected_item = self.user_wardrobe[selected_item_id]
        if selected_item['features'] is None:
            selected_item['features'] = self._extract_features(selected_item['path'])
        
        selected_features = selected_item['features']
        recommendations = []
        
        # Calculate similarity with other items
        for item_id, item in self.user_wardrobe.items():
            if item_id == selected_item_id:
                continue
            
            # Extract features
            if item['features'] is None:
                item['features'] = self._extract_features(item['path'])
            
            # Calculate similarity
            similarity = F.cosine_similarity(
                selected_features.unsqueeze(0), 
                item['features'].unsqueeze(0)
            ).item()
            
            recommendations.append({
                'item_id': item_id,
                'path': item['path'],
                'category': item['category'],
                'similarity': similarity
            })
        
        # Sort by similarity and return top-k
        recommendations.sort(key=lambda x: x['similarity'], reverse=True)
        return recommendations[:num_recommendations]
    
    def recommend_from_farfetch(self, selected_item_id: str, num_recommendations: int = 3) -> List[Dict]:
        """
        Recommend from Farfetch database
        
        Args:
            selected_item_id: user selected item ID
            num_recommendations: number of recommendations
            
        Returns:
            list of recommended items
        """
        if selected_item_id not in self.user_wardrobe:
            print(f"❌ Item {selected_item_id} not found in wardrobe")
            return []
        
        # Get selected item features
        selected_item = self.user_wardrobe[selected_item_id]
        if selected_item['features'] is None:
            selected_item['features'] = self._extract_features(selected_item['path'])
        
        selected_features = selected_item['features']
        recommendations = []
        
        # Calculate similarity with Farfetch items
        for item_id, item in self.farfetch_database.items():
            if item['image_path'] is None:
                continue
            
            # Extract features
            if item['features'] is None:
                item['features'] = self._extract_features(item['image_path'])
            
            # Calculate similarity
            similarity = F.cosine_similarity(
                selected_features.unsqueeze(0), 
                item['features'].unsqueeze(0)
            ).item()
            
            # Get item information
            item_data = item['data']
            recommendations.append({
                'item_id': item_id,
                'brand': item_data.get('brand', 'Unknown'),
                'description': item_data.get('description', ''),
                'price': item_data.get('price', {}).get('value', 'N/A'),
                'currency': item_data.get('price', {}).get('currency', 'USD'),
                'image_path': item['image_path'],
                'similarity': similarity
            })
        
        # Sort by similarity and return top-k
        recommendations.sort(key=lambda x: x['similarity'], reverse=True)
        return recommendations[:num_recommendations]
    
    def get_complete_outfit(self, selected_item_id: str, 
                          wardrobe_recommendations: int = 2,
                          farfetch_recommendations: int = 1) -> Dict:
        """
        Get complete outfit recommendations
        
        Args:
            selected_item_id: user selected item ID
            wardrobe_recommendations: number of wardrobe recommendations
            farfetch_recommendations: number of Farfetch recommendations
            
        Returns:
            complete outfit recommendations
        """
        print(f"🎯 Creating outfit for item: {selected_item_id}")
        
        # Recommend from wardrobe
        wardrobe_recs = self.recommend_from_wardrobe(selected_item_id, wardrobe_recommendations)
        
        # Recommend from Farfetch
        farfetch_recs = self.recommend_from_farfetch(selected_item_id, farfetch_recommendations)
        
        return {
            'selected_item': {
                'id': selected_item_id,
                'path': self.user_wardrobe[selected_item_id]['path'],
                'category': self.user_wardrobe[selected_item_id]['category']
            },
            'wardrobe_recommendations': wardrobe_recs,
            'farfetch_recommendations': farfetch_recs,
            'styling_notes': self._generate_styling_notes(selected_item_id, wardrobe_recs, farfetch_recs)
        }
    
    def _generate_styling_notes(self, selected_item_id: str, 
                              wardrobe_recs: List[Dict], 
                              farfetch_recs: List[Dict]) -> str:
        """Generate styling suggestions"""
        selected_category = self.user_wardrobe[selected_item_id]['category']
        
        notes = f"Based on your {selected_category}, I recommend the following outfit:\n\n"
        
        if wardrobe_recs:
            notes += "👔 From your wardrobe:\n"
            for rec in wardrobe_recs:
                notes += f"• {rec['category']} (similarity: {rec['similarity']:.2f})\n"
        
        if farfetch_recs:
            notes += "\n🛍️ Recommended purchases:\n"
            for rec in farfetch_recs:
                notes += f"• {rec['brand']} - {rec['description']} (${rec['price']})\n"
        
        return notes


def demo_inference():
    """Demo inference functionality"""
    print("🎨 Fashion Stylist Demo")
    print("=" * 50)
    
    # Initialize stylist
    model_path = "fashion_clip_checkpoints/best_model.pth"
    stylist = FashionStylist(model_path)
    
    # Load data
    stylist.load_user_wardrobe("../data/images")  # Use existing images as user wardrobe
    stylist.load_farfetch_database("../data")
    
    # Get first item from user wardrobe as example
    if stylist.user_wardrobe:
        selected_item = list(stylist.user_wardrobe.keys())[0]
        print(f"\n🎯 User selected item: {selected_item}")
        
        # Get complete outfit recommendations
        outfit = stylist.get_complete_outfit(selected_item)
        
        print("\n📋 Outfit recommendations:")
        print(outfit['styling_notes'])
        
        print("\n👔 Wardrobe recommendations:")
        for rec in outfit['wardrobe_recommendations']:
            print(f"  - {rec['item_id']} ({rec['category']}) - similarity: {rec['similarity']:.3f}")
        
        print("\n🛍️ Farfetch recommendations:")
        for rec in outfit['farfetch_recommendations']:
            print(f"  - {rec['brand']}: {rec['description']} - ${rec['price']}")
    else:
        print("❌ No user wardrobe items found")


if __name__ == "__main__":
    demo_inference()
