"""
Fine-tuning Script for Background Removal Models
Adapt pre-trained models to fashion-specific images with custom datasets.
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import AutoModelForImageSegmentation, AutoProcessor
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from tqdm import tqdm
import json


class FashionSegmentationDataset(Dataset):
    """
    Dataset for fashion image segmentation.
    Expects images and corresponding masks.
    """
    
    def __init__(
        self,
        image_dir: str,
        mask_dir: str,
        processor: Optional[object] = None,
        image_size: Tuple[int, int] = (1024, 1024)
    ):
        """
        Args:
            image_dir: Directory containing fashion images
            mask_dir: Directory containing binary masks (same filenames)
            processor: HuggingFace processor for the model
            image_size: Target size for images
        """
        self.image_dir = Path(image_dir)
        self.mask_dir = Path(mask_dir)
        self.processor = processor
        self.image_size = image_size
        
        # Get list of images
        self.image_files = sorted([
            f for f in self.image_dir.iterdir()
            if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']
        ])
        
        print(f"Found {len(self.image_files)} images for training")
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        # Load image
        image_path = self.image_files[idx]
        image = Image.open(image_path).convert('RGB')
        
        # Load corresponding mask
        mask_path = self.mask_dir / f"{image_path.stem}.png"
        if not mask_path.exists():
            # Try alternative naming
            mask_path = self.mask_dir / f"{image_path.stem}_mask.png"
        
        if mask_path.exists():
            mask = Image.open(mask_path).convert('L')
        else:
            raise FileNotFoundError(f"Mask not found for {image_path.name}")
        
        # Resize
        image = image.resize(self.image_size, Image.Resampling.BILINEAR)
        mask = mask.resize(self.image_size, Image.Resampling.NEAREST)
        
        # Convert to tensors
        if self.processor:
            # Use processor if available
            inputs = self.processor(images=image, return_tensors="pt")
            pixel_values = inputs['pixel_values'].squeeze(0)
        else:
            # Manual preprocessing
            image_array = np.array(image).astype(np.float32) / 255.0
            pixel_values = torch.from_numpy(image_array).permute(2, 0, 1)
        
        # Process mask
        mask_array = np.array(mask).astype(np.float32) / 255.0
        mask_tensor = torch.from_numpy(mask_array)
        
        return {
            'pixel_values': pixel_values,
            'labels': mask_tensor
        }


class FashionBackgroundRemovalTrainer:
    """
    Trainer for fine-tuning background removal models on fashion images.
    """
    
    def __init__(
        self,
        model_name: str = "briaai/RMBG-1.4",
        output_dir: str = "./models/finetuned_bg_removal",
        device: Optional[str] = None
    ):
        """
        Args:
            model_name: Base model from HuggingFace
            output_dir: Directory to save fine-tuned model
            device: Computing device
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading base model {model_name}...")
        self.model = AutoModelForImageSegmentation.from_pretrained(
            model_name,
            trust_remote_code=True
        ).to(self.device)
        
        try:
            self.processor = AutoProcessor.from_pretrained(
                model_name,
                trust_remote_code=True
            )
        except:
            self.processor = None
            print("No processor found, using manual preprocessing")
        
        self.model_name = model_name
    
    def train(
        self,
        train_image_dir: str,
        train_mask_dir: str,
        val_image_dir: Optional[str] = None,
        val_mask_dir: Optional[str] = None,
        num_epochs: int = 10,
        batch_size: int = 4,
        learning_rate: float = 1e-5,
        save_steps: int = 500
    ):
        """
        Fine-tune the model on fashion images.
        
        Args:
            train_image_dir: Training images directory
            train_mask_dir: Training masks directory
            val_image_dir: Validation images directory
            val_mask_dir: Validation masks directory
            num_epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            save_steps: Save checkpoint every N steps
        """
        # Create datasets
        train_dataset = FashionSegmentationDataset(
            train_image_dir,
            train_mask_dir,
            self.processor
        )
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )
        
        # Create validation loader if provided
        val_loader = None
        if val_image_dir and val_mask_dir:
            val_dataset = FashionSegmentationDataset(
                val_image_dir,
                val_mask_dir,
                self.processor
            )
            val_loader = DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=4
            )
        
        # Setup optimizer
        optimizer = AdamW(self.model.parameters(), lr=learning_rate)
        
        # Loss function
        criterion = nn.BCEWithLogitsLoss()
        
        # Training loop
        print(f"\nStarting training for {num_epochs} epochs...")
        global_step = 0
        best_val_loss = float('inf')
        
        training_history = {
            'train_losses': [],
            'val_losses': []
        }
        
        for epoch in range(num_epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs}")
            
            for batch in progress_bar:
                pixel_values = batch['pixel_values'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = self.model(pixel_values=pixel_values)
                
                # Get logits
                if hasattr(outputs, 'logits'):
                    logits = outputs.logits
                else:
                    logits = outputs[0] if isinstance(outputs, tuple) else outputs
                
                # Ensure logits match label size
                if logits.shape[-2:] != labels.shape[-2:]:
                    logits = nn.functional.interpolate(
                        logits,
                        size=labels.shape[-2:],
                        mode='bilinear',
                        align_corners=False
                    )
                
                # Handle channel dimension
                if len(logits.shape) == 4 and logits.shape[1] > 1:
                    logits = logits[:, 0, :, :]  # Take first channel
                elif len(logits.shape) == 4:
                    logits = logits.squeeze(1)
                
                # Calculate loss
                loss = criterion(logits, labels)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                global_step += 1
                
                # Update progress bar
                progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
                
                # Save checkpoint
                if global_step % save_steps == 0:
                    checkpoint_path = self.output_dir / f"checkpoint-{global_step}"
                    self._save_model(checkpoint_path)
                    print(f"\nCheckpoint saved at step {global_step}")
            
            avg_train_loss = train_loss / len(train_loader)
            training_history['train_losses'].append(avg_train_loss)
            print(f"Epoch {epoch+1} - Average train loss: {avg_train_loss:.4f}")
            
            # Validation phase
            if val_loader:
                val_loss = self._validate(val_loader, criterion)
                training_history['val_losses'].append(val_loss)
                print(f"Epoch {epoch+1} - Validation loss: {val_loss:.4f}")
                
                # Save best model
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_model_path = self.output_dir / "best_model"
                    self._save_model(best_model_path)
                    print(f"Best model saved with val_loss: {val_loss:.4f}")
        
        # Save final model
        final_model_path = self.output_dir / "final_model"
        self._save_model(final_model_path)
        
        # Save training history
        with open(self.output_dir / "training_history.json", 'w') as f:
            json.dump(training_history, f, indent=2)
        
        print(f"\nTraining completed! Models saved to {self.output_dir}")
        return training_history
    
    def _validate(self, val_loader, criterion):
        """Run validation."""
        self.model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                pixel_values = batch['pixel_values'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(pixel_values=pixel_values)
                
                if hasattr(outputs, 'logits'):
                    logits = outputs.logits
                else:
                    logits = outputs[0] if isinstance(outputs, tuple) else outputs
                
                if logits.shape[-2:] != labels.shape[-2:]:
                    logits = nn.functional.interpolate(
                        logits,
                        size=labels.shape[-2:],
                        mode='bilinear',
                        align_corners=False
                    )
                
                if len(logits.shape) == 4 and logits.shape[1] > 1:
                    logits = logits[:, 0, :, :]
                elif len(logits.shape) == 4:
                    logits = logits.squeeze(1)
                
                loss = criterion(logits, labels)
                val_loss += loss.item()
        
        return val_loss / len(val_loader)
    
    def _save_model(self, path: Path):
        """Save model and processor."""
        path.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(path)
        if self.processor:
            self.processor.save_pretrained(path)


def main():
    """Example usage of the fine-tuning script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fine-tune background removal model')
    parser.add_argument('--train-images', type=str, required=True,
                       help='Training images directory')
    parser.add_argument('--train-masks', type=str, required=True,
                       help='Training masks directory')
    parser.add_argument('--val-images', type=str,
                       help='Validation images directory')
    parser.add_argument('--val-masks', type=str,
                       help='Validation masks directory')
    parser.add_argument('--model', type=str, default='briaai/RMBG-1.4',
                       help='Base model name')
    parser.add_argument('--output-dir', type=str, default='./models/finetuned_bg_removal',
                       help='Output directory for fine-tuned model')
    parser.add_argument('--epochs', type=int, default=10,
                       help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=4,
                       help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-5,
                       help='Learning rate')
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = FashionBackgroundRemovalTrainer(
        model_name=args.model,
        output_dir=args.output_dir
    )
    
    # Train
    trainer.train(
        train_image_dir=args.train_images,
        train_mask_dir=args.train_masks,
        val_image_dir=args.val_images,
        val_mask_dir=args.val_masks,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )


if __name__ == '__main__':
    main()
