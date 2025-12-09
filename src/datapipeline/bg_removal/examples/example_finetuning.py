"""
Fine-tuning Examples for StyleMe Background Removal
Adapt models to your specific fashion image dataset
"""

from finetune_background_removal import FashionBackgroundRemovalTrainer
import os

print("="*60)
print("StyleMe Background Removal - Fine-tuning Examples")
print("="*60)

# Example 1: Basic fine-tuning
print("\n1. Basic Fine-tuning")
print("-" * 40)

# Initialize trainer
trainer = FashionBackgroundRemovalTrainer(
    model_name="briaai/RMBG-1.4",
    output_dir="./models/finetuned_fashion"
)

# Uncomment to run:
# history = trainer.train(
#     train_image_dir="./dataset/train/images",
#     train_mask_dir="./dataset/train/masks",
#     val_image_dir="./dataset/val/images",
#     val_mask_dir="./dataset/val/masks",
#     num_epochs=10,
#     batch_size=4,
#     learning_rate=1e-5
# )

# Example 2: Fine-tuning with custom parameters
print("\n2. Advanced Fine-tuning")
print("-" * 40)

trainer_advanced = FashionBackgroundRemovalTrainer(
    model_name="ZhengPeng7/BiRefNet",
    output_dir="./models/finetuned_birefnet"
)

# Uncomment to run:
# history = trainer_advanced.train(
#     train_image_dir="./dataset/train/images",
#     train_mask_dir="./dataset/train/masks",
#     val_image_dir="./dataset/val/images",
#     val_mask_dir="./dataset/val/masks",
#     num_epochs=20,  # More epochs
#     batch_size=2,   # Smaller batch for larger model
#     learning_rate=5e-6,  # Lower learning rate
#     save_steps=100  # Save more frequently
# )

# Example 3: Using fine-tuned model
print("\n3. Using Fine-tuned Model")
print("-" * 40)

from background_removal import BackgroundRemover

# Load fine-tuned model
# remover = BackgroundRemover(
#     model_name="./models/finetuned_fashion/best_model"
# )
# 
# # Use as normal
# result = remover.remove_background("test_image.jpg")
# result.save("output_finetuned.png")
# print("✓ Used fine-tuned model successfully")

# Example 4: Creating training masks from pre-trained model
print("\n4. Generate Training Masks")
print("-" * 40)

def generate_training_masks(image_dir, output_mask_dir):
    """
    Generate initial masks using pre-trained model.
    These can be refined manually and used for fine-tuning.
    """
    import os
    from pathlib import Path
    from background_removal import BackgroundRemover
    
    os.makedirs(output_mask_dir, exist_ok=True)
    
    remover = BackgroundRemover()
    image_path = Path(image_dir)
    
    for img_file in image_path.glob("*.jpg"):
        print(f"Processing {img_file.name}...")
        
        # Get mask
        _, mask = remover.remove_background(
            img_file,
            return_mask=True
        )
        
        # Save mask
        mask_file = Path(output_mask_dir) / f"{img_file.stem}.png"
        mask.save(mask_file)
    
    print(f"✓ Generated masks saved to {output_mask_dir}")
    print("  Tip: Refine these masks manually before fine-tuning")

# Uncomment to run:
# generate_training_masks(
#     image_dir="./raw_images",
#     output_mask_dir="./dataset/train/masks"
# )

# Example 5: Evaluating fine-tuned model
print("\n5. Evaluate Fine-tuned Model")
print("-" * 40)

def evaluate_model(model_path, test_image_dir, test_mask_dir):
    """
    Evaluate model performance on test set.
    """
    from background_removal import BackgroundRemover
    from pathlib import Path
    import numpy as np
    from PIL import Image
    
    remover = BackgroundRemover(model_name=model_path)
    
    test_images = list(Path(test_image_dir).glob("*.jpg"))
    scores = []
    
    for img_file in test_images:
        # Get prediction
        _, pred_mask = remover.remove_background(
            img_file,
            return_mask=True
        )
        
        # Load ground truth
        gt_mask_file = Path(test_mask_dir) / f"{img_file.stem}.png"
        if gt_mask_file.exists():
            gt_mask = Image.open(gt_mask_file).convert('L')
            
            # Calculate IoU (Intersection over Union)
            pred_array = np.array(pred_mask) > 128
            gt_array = np.array(gt_mask) > 128
            
            intersection = np.logical_and(pred_array, gt_array).sum()
            union = np.logical_or(pred_array, gt_array).sum()
            
            iou = intersection / union if union > 0 else 0
            scores.append(iou)
    
    mean_iou = np.mean(scores) if scores else 0
    print(f"Mean IoU: {mean_iou:.4f}")
    return mean_iou

# Uncomment to run:
# iou_score = evaluate_model(
#     model_path="./models/finetuned_fashion/best_model",
#     test_image_dir="./dataset/test/images",
#     test_mask_dir="./dataset/test/masks"
# )
# print(f"Model IoU Score: {iou_score:.4f}")

print("\n" + "="*60)
print("Fine-tuning examples complete!")
print("="*60)
print("\nDataset structure needed:")
print("  dataset/")
print("  ├── train/")
print("  │   ├── images/")
print("  │   └── masks/")
print("  ├── val/")
print("  │   ├── images/")
print("  │   └── masks/")
print("  └── test/")
print("      ├── images/")
print("      └── masks/")
