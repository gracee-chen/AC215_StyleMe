"""
FashionCLIP Fine-tuning with Triplet Loss
Core model for personal wardrobe AI stylist
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torch.nn.functional as F
from transformers import CLIPModel, CLIPProcessor
import numpy as np
from tqdm import tqdm
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import sys
import warnings
warnings.filterwarnings('ignore')

# Initialize cuDNN settings for GPU training
# Disable cuDNN if initialization fails (fallback to standard CUDA operations)
if torch.cuda.is_available():
    try:
        # Try to enable cuDNN
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = False
        # Test cuDNN initialization
        dummy = torch.zeros(1, 1, 1, 1).cuda()
        _ = torch.nn.functional.conv2d(dummy, torch.zeros(1, 1, 1, 1).cuda())
        del dummy
        torch.cuda.empty_cache()
    except Exception:
        # If cuDNN fails, disable it and use standard CUDA operations
        print("⚠️  cuDNN initialization failed, disabling cuDNN (using standard CUDA operations)")
        torch.backends.cudnn.enabled = False

# Set environment variable to bypass torch.load security check
os.environ['TRANSFORMERS_OFFLINE'] = '0'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from src.datapipeline.dataloader import create_dataloader
from typing import Tuple, List, Dict
import warnings
warnings.filterwarnings('ignore')
from .config import TRAINING_CONFIG, MODEL_CONFIG, TRIPLET_CONFIG, SAVE_CONFIG, DATA_CONFIG, OPTIMIZER_CONFIG


class FashionCLIPModel(nn.Module):
    """
    FashionCLIP model for fashion compatibility learning based on CLIP
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", freeze_layers: int = 8):
        super(FashionCLIPModel, self).__init__()
        
        # Load pre-trained CLIP model with multiple fallback options
        # Try local cache first, then download if needed
        try:
            # Try local cache first (fastest, no network)
            print(f"   Attempting to load CLIP from local cache...")
            self.clip_model = CLIPModel.from_pretrained(
                model_name,
                local_files_only=True,
                trust_remote_code=True,
                torch_dtype=torch.float32
            )
            print(f"   ✅ Loaded CLIP from local cache")
        except Exception as e1:
            print(f"   ⚠️  Local cache not available: {e1}")
            try:
                # Try with safetensors (may be cached)
                print(f"   Attempting to download CLIP from Hugging Face...")
                self.clip_model = CLIPModel.from_pretrained(
                    model_name, 
                    use_safetensors=True,
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                    resume_download=True  # Resume if download was interrupted
                )
                print(f"   ✅ Downloaded CLIP model")
            except Exception as e2:
                print(f"   ⚠️  Safetensors download failed: {e2}")
                try:
                    # Final fallback - regular loading
                    self.clip_model = CLIPModel.from_pretrained(
                        model_name,
                        local_files_only=False,
                        trust_remote_code=True,
                        resume_download=True
                    )
                    print(f"   ✅ Loaded CLIP model (fallback)")
                except Exception as e3:
                    print(f"   ❌ All CLIP loading methods failed")
                    print(f"      Last error: {e3}")
                    raise RuntimeError(f"Failed to load CLIP model. This is required for inference. Error: {e3}")
        
        # Load processor (usually cached)
        try:
            self.processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
        except:
            try:
                self.processor = CLIPProcessor.from_pretrained(model_name)
            except Exception as e:
                print(f"   ⚠️  Failed to load processor: {e}")
                raise
        
        # Freeze first 8 layers
        self._freeze_layers(freeze_layers)
        
        # Get feature dimension
        self.feature_dim = self.clip_model.config.projection_dim
        
        print(f"FashionCLIP initialized with {model_name}")
        print(f"Feature dimension: {self.feature_dim}")
        print(f"Frozen layers: {freeze_layers}")
    
    def _freeze_layers(self, num_frozen_layers: int):
        """Freeze first N transformer layers"""
        if hasattr(self.clip_model.vision_model, 'encoder'):
            # Freeze first N layers of vision encoder
            for i, layer in enumerate(self.clip_model.vision_model.encoder.layers):
                if i < num_frozen_layers:
                    for param in layer.parameters():
                        param.requires_grad = False
                    print(f"Frozen vision layer {i}")
        
        if hasattr(self.clip_model.text_model, 'encoder'):
            # Freeze first N layers of text encoder
            for i, layer in enumerate(self.clip_model.text_model.encoder.layers):
                if i < num_frozen_layers:
                    for param in layer.parameters():
                        param.requires_grad = False
                    print(f"Frozen text layer {i}")
    
    def encode_image(self, images):
        """Encode images"""
        return self.clip_model.get_image_features(images)
    
    def encode_text(self, texts):
        """Encode text"""
        return self.clip_model.get_text_features(texts)
    
    def forward(self, images):
        """Forward pass, return image features"""
        return self.encode_image(images)


class TripletLoss(nn.Module):
    """
    Triplet Loss for fashion compatibility learning
    """
    
    def __init__(self, margin: float = 0.5):
        super(TripletLoss, self).__init__()
        self.margin = margin
    
    def forward(self, anchor, positive, negative):
        """
        Calculate triplet loss
        
        Args:
            anchor: anchor features [batch_size, feature_dim]
            positive: positive features [batch_size, feature_dim]
            negative: negative features [batch_size, feature_dim]
        """
        # Calculate distances
        pos_dist = F.pairwise_distance(anchor, positive, p=2)
        neg_dist = F.pairwise_distance(anchor, negative, p=2)
        
        # Triplet loss
        loss = F.relu(pos_dist - neg_dist + self.margin)
        return loss.mean()


class FashionTrainer:
    """
    FashionCLIP trainer
    """
    
    def __init__(self, model: FashionCLIPModel, loss_fn: TripletLoss, device=None, require_gpu: bool = False):
        # Explicitly check and set device
        if device is None:
            if torch.cuda.is_available():
                device_str = "cuda"
                print(f"🚀 CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}")
                print(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            else:
                if require_gpu:
                    raise RuntimeError("❌ GPU required but not available! Please ensure CUDA is installed and GPU is accessible.")
                device_str = "cpu"
                print("⚠️ CUDA not available, using CPU")
            self.device = torch.device(device_str)
        elif isinstance(device, torch.device):
            # If device is already a torch.device, use it directly
            self.device = device
        else:
            # Convert string to device
            self.device = torch.device(device)
        
        # Final check: if require_gpu, ensure we're using CUDA
        if require_gpu and self.device.type != "cuda":
            raise RuntimeError("❌ GPU required but not using CUDA device!")
        self.model = model.to(self.device)
        self.triplet_loss = loss_fn.to(self.device)
        
        # Training history
        self.train_losses = []
        self.train_accuracies = []
        self.val_losses = []
        self.val_accuracies = []
        
        print(f"🎯 Training on device: {self.device}")
        print(f"🔧 Model device: {next(self.model.parameters()).device}")
        print(f"🔧 Loss function: {type(self.triplet_loss).__name__} (no parameters)")
        
        # Print GPU memory info if available
        if torch.cuda.is_available():
            self._print_gpu_info()
    
    def _clear_memory(self, clear_cache: bool = True, clear_gpu: bool = True):
        """
        Clear unused memory to prevent OOM
        
        Args:
            clear_cache: Clear Python garbage collection
            clear_gpu: Clear PyTorch CUDA cache
        """
        import gc
        
        if clear_cache:
            # Force Python garbage collection
            collected = gc.collect()
            if collected > 0:
                print(f"   🧹 Cleared {collected} Python objects")
        
        if clear_gpu and torch.cuda.is_available():
            # Clear PyTorch CUDA cache
            allocated_before = torch.cuda.memory_allocated() / 1024**3
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            allocated_after = torch.cuda.memory_allocated() / 1024**3
            if allocated_before > allocated_after:
                freed = allocated_before - allocated_after
                print(f"   🧹 Freed {freed:.2f}GB GPU memory")
    
    def _print_gpu_info(self):
        """Print GPU information"""
        if torch.cuda.is_available():
            print(f"🎮 GPU Information:")
            print(f"   Device: {torch.cuda.get_device_name(0)}")
            print(f"   Total Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            print(f"   Allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
            print(f"   Reserved: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
            print(f"   CUDA Version: {torch.version.cuda}")
            print(f"   PyTorch Version: {torch.__version__}")
    
    def train_epoch(self, dataloader: DataLoader, optimizer: optim.Optimizer) -> Tuple[float, float]:
        """Train one epoch"""
        self.model.train()
        total_loss = 0.0
        total_accuracy = 0.0
        num_batches = 0
        
        progress_bar = tqdm(dataloader, desc="🔥 Training", 
                           bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
        
        for batch_idx, batch in enumerate(progress_bar):
            # Move data to device (batch is a tuple: (anchor, positive, negative))
            anchor, positive, negative = batch
            anchor = anchor.to(self.device, non_blocking=True)
            positive = positive.to(self.device, non_blocking=True)
            negative = negative.to(self.device, non_blocking=True)
            
            # Debug: Print device info for first batch
            if batch_idx == 0:
                print(f"🔍 Debug - Batch {batch_idx}:")
                print(f"   Anchor device: {anchor.device}, shape: {anchor.shape}")
                print(f"   Positive device: {positive.device}, shape: {positive.shape}")
                print(f"   Negative device: {negative.device}, shape: {negative.shape}")
                if torch.cuda.is_available():
                    print(f"   GPU Memory: {torch.cuda.memory_allocated()/1024**3:.2f}GB / {torch.cuda.memory_reserved()/1024**3:.2f}GB")
            
            # Forward pass
            anchor_features = self.model(anchor)
            positive_features = self.model(positive)
            negative_features = self.model(negative)
            
            # Calculate loss
            loss = self.triplet_loss(anchor_features, positive_features, negative_features)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # Calculate improved fashion compatibility score
            accuracy = self._compute_fashion_specific_score(anchor_features, positive_features, negative_features)
            recommendation_score = self._compute_fashion_recommendation_score(anchor_features, positive_features, negative_features)
            
            # Combined score for training monitoring
            combined_score = (accuracy + recommendation_score) / 2
            
            loss_value = loss.item()
            total_loss += loss_value
            total_accuracy += combined_score
            num_batches += 1
            
            # Update progress bar before clearing
            progress_bar.set_postfix({
                'Loss': f'{loss_value:.4f}',
                'Fashion': f'{accuracy:.4f}',
                'Recommendation': f'{recommendation_score:.4f}',
                'Combined': f'{combined_score:.4f}'
            })
            
            # Clear intermediate tensors to save memory
            del anchor_features, positive_features, negative_features, loss
            
            # Periodic memory cleanup (every 10 batches to avoid overhead)
            if batch_idx % 10 == 0 and torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # Final cleanup after epoch
        self._clear_memory(clear_cache=True, clear_gpu=True)
        
        avg_loss = total_loss / num_batches
        avg_accuracy = total_accuracy / num_batches
        
        return avg_loss, avg_accuracy
    
    def validate(self, dataloader: DataLoader) -> Tuple[float, float]:
        """Validate model"""
        self.model.eval()
        total_loss = 0.0
        total_accuracy = 0.0
        num_batches = 0
        
        with torch.no_grad():
            progress_bar = tqdm(dataloader, desc="📊 Validation", 
                               bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
            
            for batch_idx, batch in enumerate(progress_bar):
                # Move data to device (batch is a tuple: (anchor, positive, negative))
                anchor, positive, negative = batch
                anchor = anchor.to(self.device, non_blocking=True)
                positive = positive.to(self.device, non_blocking=True)
                negative = negative.to(self.device, non_blocking=True)
                
                # Forward pass
                anchor_features = self.model(anchor)
                positive_features = self.model(positive)
                negative_features = self.model(negative)
                
                # Calculate loss
                loss = self.triplet_loss(anchor_features, positive_features, negative_features)
                
                # Calculate improved fashion compatibility score
                accuracy = self._compute_fashion_specific_score(anchor_features, positive_features, negative_features)
                recommendation_score = self._compute_fashion_recommendation_score(anchor_features, positive_features, negative_features)
                
                # Combined score for validation monitoring
                combined_score = (accuracy + recommendation_score) / 2
                
                loss_value = loss.item()
                total_loss += loss_value
                total_accuracy += combined_score
                num_batches += 1
                
                # Clear intermediate tensors to save memory
                del anchor_features, positive_features, negative_features, loss
                
                # Periodic memory cleanup
                if batch_idx % 10 == 0 and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Update progress bar before clearing
                progress_bar.set_postfix({
                    'Loss': f'{loss_value:.4f}',
                    'Fashion': f'{accuracy:.4f}',
                    'Recommendation': f'{recommendation_score:.4f}',
                    'Combined': f'{combined_score:.4f}'
                })
        
        avg_loss = total_loss / num_batches
        avg_accuracy = total_accuracy / num_batches
        
        return avg_loss, avg_accuracy
    
    def _compute_triplet_accuracy(self, anchor, positive, negative) -> float:
        """
        Calculate triplet accuracy
        accuracy = ratio of (pos_dist < neg_dist)
        """
        pos_dist = F.pairwise_distance(anchor, positive, p=2)
        neg_dist = F.pairwise_distance(anchor, negative, p=2)
        
        # If positive distance is smaller than negative distance, prediction is correct
        correct = (pos_dist < neg_dist).float()
        accuracy = correct.mean().item()
        
        return accuracy
    
    def _compute_compatibility_score(self, anchor, positive, negative) -> float:
        """Compute strict fashion compatibility score with multiple criteria"""
        # Normalize features
        anchor_norm = torch.nn.functional.normalize(anchor, p=2, dim=1)
        positive_norm = torch.nn.functional.normalize(positive, p=2, dim=1)
        negative_norm = torch.nn.functional.normalize(negative, p=2, dim=1)
        
        # 1. Cosine similarity (current method)
        pos_cos_sim = torch.sum(anchor_norm * positive_norm, dim=1)
        neg_cos_sim = torch.sum(anchor_norm * negative_norm, dim=1)
        
        # 2. Euclidean distance (stricter)
        pos_eucl_dist = torch.norm(anchor - positive, dim=1)
        neg_eucl_dist = torch.norm(anchor - negative, dim=1)
        
        # 3. Manhattan distance (even stricter)
        pos_manh_dist = torch.sum(torch.abs(anchor - positive), dim=1)
        neg_manh_dist = torch.sum(torch.abs(anchor - negative), dim=1)
        
        # Combined strict criteria:
        # - Cosine similarity: positive should be more similar
        cos_criteria = (pos_cos_sim > neg_cos_sim).float()
        
        # - Euclidean distance: positive should be closer
        eucl_criteria = (pos_eucl_dist < neg_eucl_dist).float()
        
        # - Manhattan distance: positive should be closer
        manh_criteria = (pos_manh_dist < neg_manh_dist).float()
        
        # - Strict margin: positive should be significantly better
        cos_margin = (pos_cos_sim - neg_cos_sim > 0.1).float()  # 10% margin
        eucl_margin = (neg_eucl_dist - pos_eucl_dist > 0.1).float()  # 10% margin
        
        # Weighted combination (all criteria must be met for high score)
        strict_compatibility = (
            cos_criteria * 0.3 +      # 30% weight for cosine
            eucl_criteria * 0.3 +     # 30% weight for euclidean
            manh_criteria * 0.2 +     # 20% weight for manhattan
            cos_margin * 0.1 +        # 10% weight for cosine margin
            eucl_margin * 0.1         # 10% weight for euclidean margin
        ).mean().item()
        
        return strict_compatibility
    
    def _compute_fashion_specific_score(self, anchor, positive, negative) -> float:
        """
        Compute improved fashion compatibility score
        Focuses on learning effectiveness, not just ranking metrics
        """
        # Use Euclidean distance (better for triplet loss optimization)
        pos_dist = F.pairwise_distance(anchor, positive, p=2)
        neg_dist = F.pairwise_distance(anchor, negative, p=2)
        
        # 1. Triplet accuracy - direct measure of training effectiveness
        triplet_acc = (pos_dist < neg_dist).float().mean().item()
        
        # 2. Margin-based score - how well separated positive vs negative are
        margin = pos_dist - neg_dist
        margin_score = torch.sigmoid(margin).mean().item()
        
        # 3. Distance ratio - measures relative distance quality
        avg_pos_dist = pos_dist.mean().item()
        avg_neg_dist = neg_dist.mean().item()
        distance_ratio = avg_neg_dist / (avg_pos_dist + 1e-6)
        # Higher is better (negative should be farther than positive)
        distance_ratio_score = min(1.0, distance_ratio / 2.0)  # Cap at 1.0
        
        # 4. Separation quality - absolute separation
        separation = (neg_dist - pos_dist).mean().item()
        separation_score = torch.sigmoid(torch.tensor(separation / 2.0)).item()
        
        # Combined score (weighted toward triplet accuracy and separation)
        modern_score = (
            triplet_acc * 0.50 +          # 50% - direct triplet accuracy
            margin_score * 0.25 +          # 25% - margin quality
            separation_score * 0.15 +     # 15% - absolute separation
            distance_ratio_score * 0.10  # 10% - distance ratio
        )
        
        return modern_score
    
    def _compute_fashion_recommendation_score(self, anchor, positive, negative) -> float:
        """
        Compute simplified fashion recommendation quality score
        Focuses on triplet learning quality
        """
        # Use the same triplet accuracy as main score
        pos_dist = F.pairwise_distance(anchor, positive, p=2)
        neg_dist = F.pairwise_distance(anchor, negative, p=2)
        
        # Simple triplet accuracy
        triplet_acc = (pos_dist < neg_dist).float().mean().item()
        
        # Margin quality
        margin = pos_dist - neg_dist
        margin_quality = torch.sigmoid(margin).mean().item()
        
        # Combined score (simplified)
        recommendation_score = (triplet_acc * 0.6 + margin_quality * 0.4)
        
        return recommendation_score
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader, 
              epochs: int = 20, learning_rate: float = 5e-6, 
              save_dir: str = "checkpoints"):
        """
        Train model from scratch
        
        Args:
            train_loader: training data loader
            val_loader: validation data loader
            epochs: number of training epochs
            learning_rate: learning rate
            save_dir: model save directory
        """
        # Create save directory
        os.makedirs(save_dir, exist_ok=True)
        
        # Always start fresh training
        print("🆕 Starting fresh training from scratch...")
        
        # Optimizer
        optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=learning_rate,
            weight_decay=0.01
        )
        
        # Learning rate scheduler
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        
        best_accuracy = 0.0
        patience_counter = 0
        patience = TRAINING_CONFIG['patience']
        
        # Start from epoch 0
        start_epoch = 0
        total_epochs = epochs
        
        print(f"\n🚀 Starting training for {total_epochs} epochs...")
        print(f"📈 Learning rate: {learning_rate}")
        print(f"🎯 Target accuracy: >{TRAINING_CONFIG['target_accuracy']*100:.0f}%")
        print(f"⏰ Early stopping patience: {patience} epochs")
        print("="*60)
        
        # Print GPU status before training
        if torch.cuda.is_available():
            print(f"🎮 Pre-training GPU Status:")
            self._print_gpu_info()
            print("="*60)
        
        for epoch in range(start_epoch, total_epochs):
            print(f"\n🔄 Epoch {epoch+1}/{total_epochs}")
            print("-" * 50)
            
            # Clear image cache at start of each epoch (if dataset has cache)
            if hasattr(train_loader.dataset, 'dataset') and hasattr(train_loader.dataset.dataset, '_image_cache'):
                cache_size = len(train_loader.dataset.dataset._image_cache)
                if cache_size > 0:
                    # Clear 50% of cache to free memory
                    keys_to_clear = list(train_loader.dataset.dataset._image_cache.keys())[:cache_size // 2]
                    for key in keys_to_clear:
                        del train_loader.dataset.dataset._image_cache[key]
                    print(f"   🧹 Cleared {len(keys_to_clear)} images from cache")
            
            # Training
            train_loss, train_acc = self.train_epoch(train_loader, optimizer)
            
            # Validation
            val_loss, val_acc = self.validate(val_loader)
            
            # Clear memory after validation
            self._clear_memory(clear_cache=True, clear_gpu=True)
            
            # Update learning rate
            scheduler.step()
            
            # Record history
            self.train_losses.append(train_loss)
            self.train_accuracies.append(train_acc)
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)
            
            # Print results with better formatting
            print(f"\n📊 Epoch {epoch+1}/{total_epochs} Results:")
            print(f"🔥 Train - Loss: {train_loss:.4f} | Fashion Score: {train_acc:.4f}")
            print(f"📊 Val   - Loss: {val_loss:.4f} | Fashion Score: {val_acc:.4f}")
            print(f"📈 LR: {scheduler.get_last_lr()[0]:.2e}")
            
            # Save best model
            if val_acc > best_accuracy:
                best_accuracy = val_acc
                patience_counter = 0  # Reset patience counter
                self.save_model(os.path.join(save_dir, "best_model.pth"), best_accuracy, optimizer, scheduler, epoch, patience_counter)
                print(f"🎉 New best fashion score: {best_accuracy:.4f} - Model saved!")
            else:
                patience_counter += 1
            
            # Check if target is reached
            if val_acc > TRAINING_CONFIG['target_accuracy']:
                print(f"🎉 Target accuracy achieved! ({val_acc:.4f} > {TRAINING_CONFIG['target_accuracy']})")
                print(f"🏁 Training completed after {epoch+1} epochs")
                break
            
            # Early stopping check
            if patience_counter >= patience:
                print(f"🛑 Early stopping triggered after {patience} epochs without improvement")
                print(f"📊 Best accuracy achieved: {best_accuracy:.4f}")
                print(f"🏁 Training completed after {epoch+1} epochs")
                break
            
            # Show patience counter
            if patience_counter > 0:
                print(f"⏳ No improvement for {patience_counter}/{patience} epochs")
        
        # Save final model
        self.save_model(os.path.join(save_dir, "final_model.pth"), patience_counter=patience_counter)
        
        # Save training history
        self.save_training_history(save_dir)
        
        # Plot training curves
        self.plot_training_curves(save_dir)
        
        # Auto-generate experiment logs
        self.generate_experiment_logs(save_dir, best_accuracy)
        
        print(f"\n🎉 Training completed!")
        print(f"📊 Best validation compatibility: {best_accuracy:.4f}")
        print(f"📁 Model saved to: {save_dir}/")
        print(f"📈 Training curves saved to: {save_dir}/training_curves.png")
        print(f"📋 Training history saved to: {save_dir}/training_history.json")
        print(f"📝 Experiment logs generated in experiments/ folder")
    
    def save_model(self, path: str, best_accuracy: float = None, optimizer=None, scheduler=None, epoch=None, patience_counter=None):
        """Save model with optimizer and scheduler state"""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'model_config': {
                'model_name': 'openai/clip-vit-base-patch32',
                'freeze_layers': 8
            }
        }
        
        if best_accuracy is not None:
            checkpoint['best_accuracy'] = best_accuracy
        if optimizer is not None:
            checkpoint['optimizer_state_dict'] = optimizer.state_dict()
        if scheduler is not None:
            checkpoint['scheduler_state_dict'] = scheduler.state_dict()
        if epoch is not None:
            checkpoint['epoch'] = epoch
        if patience_counter is not None:
            checkpoint['patience_counter'] = patience_counter
            
        torch.save(checkpoint, path)
        print(f"Model saved to {path}")
    
    def save_training_history(self, save_dir: str):
        """Save training history"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        history = {
            'timestamp': timestamp,
            'train_losses': self.train_losses,
            'train_accuracies': self.train_accuracies,
            'val_losses': self.val_losses,
            'val_accuracies': self.val_accuracies,
            'final_train_loss': self.train_losses[-1] if self.train_losses else None,
            'final_val_loss': self.val_losses[-1] if self.val_losses else None,
            'final_train_acc': self.train_accuracies[-1] if self.train_accuracies else None,
            'final_val_acc': self.val_accuracies[-1] if self.val_accuracies else None,
            'best_val_acc': max(self.val_accuracies) if self.val_accuracies else None
        }
        
        filename = f"training_history_{timestamp}.json"
        with open(os.path.join(save_dir, filename), 'w') as f:
            json.dump(history, f, indent=2)
        
        # Also save a latest version
        with open(os.path.join(save_dir, "training_history_latest.json"), 'w') as f:
            json.dump(history, f, indent=2)
    
    def plot_training_curves(self, save_dir: str):
        """Plot training curves"""
        print(f"📊 Plotting training curves...")
        print(f"   Train losses: {len(self.train_losses)} points")
        print(f"   Val losses: {len(self.val_losses)} points")
        print(f"   Train accuracies: {len(self.train_accuracies)} points")
        print(f"   Val accuracies: {len(self.val_accuracies)} points")
        
        if len(self.train_losses) == 0:
            print("⚠️ No training data to plot!")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss curves
        epochs = range(1, len(self.train_losses) + 1)
        ax1.plot(epochs, self.train_losses, label='Train Loss', marker='o')
        ax1.plot(epochs, self.val_losses, label='Val Loss', marker='s')
        ax1.set_title('Training and Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Compatibility curves
        ax2.plot(epochs, self.train_accuracies, label='Train Compatibility', marker='o')
        ax2.plot(epochs, self.val_accuracies, label='Val Compatibility', marker='s')
        ax2.axhline(y=TRAINING_CONFIG['target_accuracy'], color='r', linestyle='--', 
                   label=f'Target ({TRAINING_CONFIG["target_accuracy"]*100:.0f}%)')
        ax2.set_title('Training and Validation Compatibility')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Compatibility Score')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        
        # Generate timestamped filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_curves_{timestamp}.png"
        
        plt.savefig(os.path.join(save_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Training curves saved to {save_dir}/{filename}")
    
    def generate_experiment_logs(self, save_dir: str, best_accuracy: float):
        """Auto-generate experiment logs and organize files"""
        from datetime import datetime
        import json
        import shutil
        
        # Determine experiments directory - use SAVE_CONFIG or default
        # If save_dir is in GCS path, use that; otherwise use local experiments/
        if save_dir.startswith('/gcs/') or 'styleme-production' in save_dir:
            # Extract base experiments directory from save_dir
            # e.g., /gcs/styleme-production/experiments/temp_training_output -> /gcs/styleme-production/experiments
            experiments_dir = os.path.dirname(save_dir.rstrip('/'))
        else:
            experiments_dir = "experiments"
        
        os.makedirs(experiments_dir, exist_ok=True)
        
        # Generate experiment ID - check both local and GCS for existing experiments
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        existing_numbers = []
        
        # Check local filesystem
        if os.path.exists(experiments_dir):
            try:
                existing_experiments = [d for d in os.listdir(experiments_dir) if d.startswith('exp_') and os.path.isdir(os.path.join(experiments_dir, d))]
                for exp_dir in existing_experiments:
                    try:
                        # Extract number from exp_XXX or exp_XXX_* format
                        parts = exp_dir.split('_')
                        if len(parts) >= 2 and parts[0] == 'exp':
                            num = int(parts[1])
                            existing_numbers.append(num)
                    except (ValueError, IndexError):
                        continue
            except (OSError, PermissionError):
                pass
        
        # Check GCS if using GCS paths
        if experiments_dir.startswith('/gcs/') or 'styleme-production' in experiments_dir:
            try:
                from google.cloud import storage
                gcp_bucket_name = DATA_CONFIG.get('gcp_bucket_name', 'styleme-production')
                gcp_project_id = DATA_CONFIG.get('gcp_project_id', 'styleme-475201')
                
                # Extract bucket name and prefix from path
                # e.g., /gcs/styleme-production/experiments -> bucket=styleme-production, prefix=experiments/
                if experiments_dir.startswith('/gcs/'):
                    path_parts = experiments_dir.replace('/gcs/', '').split('/', 1)
                    bucket_name = path_parts[0]
                    prefix = f"{path_parts[1]}/" if len(path_parts) > 1 else ""
                else:
                    # Fallback parsing
                    bucket_name = gcp_bucket_name
                    prefix = "experiments/"
                
                client = storage.Client(project=gcp_project_id)
                bucket = client.bucket(bucket_name)
                
                # List all blobs with prefix
                blobs = bucket.list_blobs(prefix=prefix)
                
                # Extract experiment directories from blob paths
                seen_dirs = set()
                for blob in blobs:
                    # Extract directory name from blob path
                    # e.g., experiments/exp_001/best_model.pth -> exp_001
                    path_parts = blob.name.replace(prefix, '').split('/')
                    if path_parts and path_parts[0].startswith('exp_'):
                        exp_dir_name = path_parts[0]
                        if exp_dir_name not in seen_dirs:
                            seen_dirs.add(exp_dir_name)
                            try:
                                parts = exp_dir_name.split('_')
                                if len(parts) >= 2 and parts[0] == 'exp':
                                    num = int(parts[1])
                                    existing_numbers.append(num)
                            except (ValueError, IndexError):
                                continue
                
                print(f"📊 Checked GCS bucket {bucket_name} for existing experiments")
            except Exception as e:
                print(f"⚠️  Could not check GCS for existing experiments: {e}")
                print(f"   Will use local filesystem check only")
        
        # Find the next available experiment number
        if existing_numbers:
            next_exp_num = max(existing_numbers) + 1
            print(f"📋 Found existing experiments: {sorted(set(existing_numbers))}")
        else:
            next_exp_num = 1
            print(f"📋 No existing experiments found, starting with exp_001")
        
        exp_id = f"exp_{next_exp_num:03d}"
        print(f"✅ Next experiment ID: {exp_id}")
        
        # Determine experiment type based on target accuracy (for documentation only)
        target_acc = TRAINING_CONFIG['target_accuracy']
        if target_acc >= 0.9:
            exp_type = "simple_evaluation"
            exp_name = "Simple Cosine Similarity Evaluation"
        else:
            exp_type = "strict_evaluation"
            exp_name = "Strict Fashion Compatibility Evaluation"
        
        # Create experiment folder - use just exp_XXX format (no suffix) for inference compatibility
        exp_folder = os.path.join(experiments_dir, exp_id)
        
        # Check if experiment folder already exists and warn user
        if os.path.exists(exp_folder):
            print(f"⚠️  Warning: Experiment folder {exp_folder} already exists!")
            print(f"   This might indicate a previous training run. Skipping folder creation.")
            return
        
        os.makedirs(exp_folder, exist_ok=True)
        
        # Copy files to experiment folder
        files_to_copy = [
            ("training_curves.png", "training_curves.png"),
            ("training_history.json", "training_history.json"),
            ("best_model.pth", "best_model.pth"),
            ("final_model.pth", "final_model.pth")
        ]
        
        for src_file, dst_file in files_to_copy:
            src_path = os.path.join(save_dir, src_file)
            dst_path = os.path.join(exp_folder, dst_file)
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
        
        # Generate experiment README
        readme_content = f"""# Experiment {exp_id}: {exp_name}

## Overview
- **Experiment ID**: {exp_id}
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Evaluation Method**: {exp_name}
- **Status**: Completed

## Configuration
- **Model**: CLIP ViT-B/32
- **Frozen Layers**: 8
- **Target Accuracy**: {target_acc*100:.0f}%
- **Epochs**: {TRAINING_CONFIG['epochs']}
- **Batch Size**: {TRAINING_CONFIG['batch_size']}
- **Learning Rate**: {TRAINING_CONFIG['learning_rate']}

## Results
- **Best Score**: {best_accuracy:.4f} ({best_accuracy*100:.2f}%)
- **Epochs Trained**: {len(self.train_losses)}
- **Final Train Loss**: {self.train_losses[-1] if self.train_losses else 'N/A'}
- **Final Val Loss**: {self.val_losses[-1] if self.val_losses else 'N/A'}

## Files
- `best_model.pth`: Best performing model
- `final_model.pth`: Final epoch model
- `training_curves.png`: Training visualization
- `training_history.json`: Detailed training metrics

## Conclusion
This experiment used {exp_name.lower()} and achieved {best_accuracy*100:.2f}% compatibility score.
"""
        
        with open(os.path.join(exp_folder, "README.md"), 'w') as f:
            f.write(readme_content)
        
        # Update experiment configs (save to same experiments directory)
        data_version = DATA_CONFIG.get('data_version', None)
        configs_file = os.path.join(experiments_dir, "experiment_configs.json")
        self.update_experiment_configs(exp_id, exp_type, exp_name, best_accuracy, timestamp, data_version, configs_file)
        
        print(f"📝 Experiment {exp_id} logs generated in {exp_folder}/")
    
    def update_experiment_configs(self, exp_id: str, exp_type: str, exp_name: str, best_accuracy: float, timestamp: str, data_version: str = None, configs_file: str = None):
        """Update experiment_configs.json with new experiment"""
        if configs_file is None:
            configs_file = "experiments/experiment_configs.json"
        
        # Load existing configs or create new
        if os.path.exists(configs_file):
            with open(configs_file, 'r') as f:
                configs = json.load(f)
        else:
            configs = {"experiments": {}, "summary": {"total_experiments": 0}}
        
        # Get data version from config or use default
        data_ver = data_version or DATA_CONFIG.get('data_version', 'unknown')
        
        # Add new experiment
        configs["experiments"][exp_id] = {
            "date": timestamp,
            "description": exp_name,
            "data_version": data_ver,  # Reference to versioned dataset
            "config": {
                "model": {
                    "architecture": MODEL_CONFIG['model_name'],
                    "frozen_layers": MODEL_CONFIG['freeze_layers'],
                    "feature_dimension": MODEL_CONFIG['feature_dim']
                },
                "training": {
                    "epochs": TRAINING_CONFIG['epochs'],
                    "batch_size": TRAINING_CONFIG['batch_size'],
                    "learning_rate": TRAINING_CONFIG['learning_rate'],
                    "optimizer": OPTIMIZER_CONFIG['optimizer'],
                    "scheduler": OPTIMIZER_CONFIG['scheduler'],
                    "patience": TRAINING_CONFIG['patience'],
                    "target_accuracy": TRAINING_CONFIG['target_accuracy']
                },
                "triplet_loss": {
                    "margin": TRIPLET_CONFIG['margin'],
                    "distance_metric": TRIPLET_CONFIG['distance_metric']
                },
                "evaluation": {
                    "method": exp_type,
                    "description": exp_name
                },
                "dataset": {
                    "gcp_bucket": DATA_CONFIG['gcp_bucket_name'],
                    "data_prefix": DATA_CONFIG['data_prefix'],
                    "images_prefix": DATA_CONFIG['images_prefix']
                }
            },
            "results": {
                "best_score": best_accuracy,
                "epochs_trained": len(self.train_losses),
                "final_train_loss": self.train_losses[-1] if self.train_losses else None,
                "final_val_loss": self.val_losses[-1] if self.val_losses else None,
                "convergence": "completed" if len(self.train_losses) == TRAINING_CONFIG['epochs'] else "early_stopping"
            }
        }
        
        # Update summary
        configs["summary"]["total_experiments"] = len(configs["experiments"])
        configs["summary"]["latest_experiment"] = exp_id
        
        # Save updated configs
        with open(configs_file, 'w') as f:
            json.dump(configs, f, indent=2)
        
        print(f"📋 Updated experiment_configs.json with {exp_id}")


def main():
    """Main training function"""
    # Load parameters from config file
    gcp_bucket_name = DATA_CONFIG['gcp_bucket_name']
    gcp_project_id = DATA_CONFIG['gcp_project_id']
    data_prefix = DATA_CONFIG['data_prefix']
    images_prefix = DATA_CONFIG['images_prefix']
    batch_size = TRAINING_CONFIG['batch_size']
    epochs = TRAINING_CONFIG['epochs']
    learning_rate = TRAINING_CONFIG['learning_rate']
    num_workers = TRAINING_CONFIG['num_workers']
    patience = TRAINING_CONFIG['patience']
    target_accuracy = TRAINING_CONFIG['target_accuracy']
    
    print("🚀 Starting Optimized FashionCLIP Training")
    print("🎯 Target: 75% Fashion Compatibility Score")
    print("=" * 50)
    print("📊 Optimized Configuration:")
    print(f"   - Batch Size: {batch_size} (reduced for better gradients)")
    print(f"   - Epochs: {epochs} (increased from 20)")
    print(f"   - Learning Rate: {learning_rate}")
    print(f"   - Patience: {patience} (increased for more training)")
    print(f"   - Target Accuracy: {target_accuracy}")
    print(f"   - GCS Bucket: {gcp_bucket_name}")
    print(f"   - GCP Project: {gcp_project_id}")
    print(f"   - Data Prefix: {data_prefix}")
    print(f"   - Images Prefix: {images_prefix}")
    print("=" * 50)
    
    # Create data loaders
    print("Creating data loaders...")
    train_loader, val_loader, test_loader = create_dataloader(
        gcp_bucket_name=gcp_bucket_name,
        gcp_project_id=gcp_project_id,
        data_prefix=data_prefix,
        images_prefix=images_prefix,
        batch_size=batch_size,
        num_workers=num_workers,
        max_samples_per_file=DATA_CONFIG['max_samples_per_file']
    )
    
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print(f"Test batches: {len(test_loader)}")
    
    # Create model
    print("\nCreating FashionCLIP model...")
    model = FashionCLIPModel(freeze_layers=MODEL_CONFIG['freeze_layers'])
    
    # Create loss function
    loss_fn = TripletLoss(margin=TRIPLET_CONFIG['margin'])
    
    # Create trainer
    trainer = FashionTrainer(model, loss_fn)
    
    # Start training
    print("\nStarting training...")
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=epochs,
        learning_rate=learning_rate,
        save_dir=SAVE_CONFIG['save_dir']
    )


if __name__ == "__main__":
    main()