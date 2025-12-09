"""
Quick evaluation module for FashionCLIP model
"""

import os
import sys
import torch
import numpy as np
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'train'))

from model_training import FashionCLIPModel, TripletLoss
from dataloader import create_dataloader
import config


def quick_triplet_evaluation(model_path: str, num_batches: int = 10) -> Dict:
    """
    Quick evaluation of Triplet Accuracy
    
    Args:
        model_path: Path to model
        num_batches: Number of batches to evaluate
        
    Returns:
        Evaluation results
    """
    print("🎯 Quick Triplet Accuracy Evaluation...")
    
    # Load model
    model = FashionCLIPModel()
    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
        print(f"✅ Model loaded from {model_path}")
    else:
        print(f"⚠️ Model file not found, using untrained model")
    
    model.eval()
    
    # Create data loader
    try:
        train_loader, val_loader, test_loader = create_dataloader(
            gcp_bucket_name=config.DATA_CONFIG['gcp_bucket_name'],
            gcp_project_id=config.DATA_CONFIG['gcp_project_id'],
            data_prefix=config.DATA_CONFIG['data_prefix'],
            images_prefix=config.DATA_CONFIG['images_prefix'],
            batch_size=config.TRAINING_CONFIG['batch_size'],
            num_workers=config.TRAINING_CONFIG['num_workers'],
            max_samples_per_file=100  # Limit for quick evaluation
        )
        
        print(f"📊 Dataset sizes - Train: {len(train_loader.dataset)}, Val: {len(val_loader.dataset)}, Test: {len(test_loader.dataset)}")
        
    except Exception as e:
        print(f"❌ Error creating data loader: {e}")
        return {'error': str(e)}
    
    # Evaluation
    total_correct = 0
    total_samples = 0
    
    with torch.no_grad():
        for i, batch in enumerate(test_loader):
            if i >= num_batches:
                break
                
            anchor, positive, negative = batch
            
            # Forward pass
            anchor_feat = model(anchor)
            positive_feat = model(positive)
            negative_feat = model(negative)
            
            # Calculate Triplet Loss
            loss_fn = TripletLoss(margin=0.5)
            loss = loss_fn(anchor_feat, positive_feat, negative_feat)
            
            # Calculate accuracy
            pos_dist = torch.norm(anchor_feat - positive_feat, dim=1)
            neg_dist = torch.norm(anchor_feat - negative_feat, dim=1)
            correct = (pos_dist < neg_dist).sum().item()
            
            total_correct += correct
            total_samples += anchor.size(0)
            
            print(f"Batch {i+1}/{num_batches}: Loss={loss:.4f}, Acc={correct/anchor.size(0):.3f}")
    
    # Calculate results
    accuracy = total_correct / total_samples if total_samples > 0 else 0
    
    results = {
        'triplet_accuracy': accuracy,
        'total_samples': total_samples,
        'num_batches': num_batches
    }
    
    print(f"📊 Quick Evaluation Results:")
    print(f"  Triplet Accuracy: {accuracy:.3f}")
    print(f"  Total Samples: {total_samples}")
    
    # Evaluation standards
    if accuracy > 0.85:
        print("🎉 Excellent performance! Model is ready for production.")
    elif accuracy > 0.7:
        print("✅ Good performance. Model shows promise.")
    elif accuracy > 0.5:
        print("⚠️ Moderate performance. Consider more training.")
    else:
        print("❌ Poor performance. Model needs significant improvement.")
    
    return results


def test_model_loading(model_path: str) -> bool:
    """Test model loading"""
    print("🧪 Testing model loading...")
    
    try:
        model = FashionCLIPModel()
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location='cpu')
            model.load_state_dict(checkpoint['model_state_dict'])
            print("✅ Model loaded successfully")
        else:
            print("⚠️ Model file not found, using untrained model")
        
        # Test forward pass
        dummy_input = torch.randn(1, 3, 224, 224)
        with torch.no_grad():
            output = model(dummy_input)
            print(f"✅ Forward pass successful, output shape: {output.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False


def test_data_loading() -> bool:
    """Test data loading"""
    print("🧪 Testing data loading...")
    
    try:
        train_loader, val_loader, test_loader = create_dataloader(
            gcp_bucket_name=config.DATA_CONFIG['gcp_bucket_name'],
            gcp_project_id=config.DATA_CONFIG['gcp_project_id'],
            data_prefix=config.DATA_CONFIG['data_prefix'],
            images_prefix=config.DATA_CONFIG['images_prefix'],
            batch_size=2,  # Small batch for testing
            num_workers=0,  # No multiprocessing for testing
            max_samples_per_file=10  # Limit for testing
        )
        
        print(f"✅ Data loaders created successfully")
        print(f"  Train: {len(train_loader.dataset)} samples")
        print(f"  Val: {len(val_loader.dataset)} samples")
        print(f"  Test: {len(test_loader.dataset)} samples")
        
        # Test one batch
        for batch in train_loader:
            anchor, positive, negative = batch
            print(f"✅ Batch shape - Anchor: {anchor.shape}, Positive: {positive.shape}, Negative: {negative.shape}")
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False


def main():
    """Main function"""
    
    print("🚀 Quick Evaluation Test")
    print("=" * 50)
    
    # 1. Test model loading
    model_path = "checkpoints/best_model.pth"
    if not test_model_loading(model_path):
        return
    
    # 2. Test data loading
    if not test_data_loading():
        return
    
    # 3. Quick evaluation
    print("=" * 50)
    print("🎯 Running Quick Evaluation...")
    print("=" * 50)
    
    try:
        results = quick_triplet_evaluation(model_path, num_batches=5)
        
        if 'error' not in results:
            print("\n📊 Final Results:")
            print(f"  Triplet Accuracy: {results['triplet_accuracy']:.3f}")
            print(f"  Samples Evaluated: {results['total_samples']}")
            
            # Save results
            import json
            with open('quick_eval_results.json', 'w') as f:
                json.dump(results, f, indent=2)
            print("💾 Results saved to quick_eval_results.json")
        
    except Exception as e:
        print(f"❌ Quick evaluation failed: {e}")


if __name__ == "__main__":
    main()
