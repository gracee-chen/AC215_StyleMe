#!/usr/bin/env python3
"""
StyleMe Background Removal - Quick Start Script
Run this script to test the background removal system
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed."""
    print("Checking dependencies...")
    required_packages = [
        'torch',
        'transformers',
        'PIL',
        'numpy',
        'cv2'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'cv2':
                import cv2
            else:
                __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)
    
    if missing:
        print("\n⚠ Missing packages detected!")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies installed!")
    return True

def check_gpu():
    """Check GPU availability."""
    print("\nChecking GPU availability...")
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"  ✓ GPU available: {gpu_name}")
            print(f"  ✓ CUDA version: {torch.version.cuda}")
            return True
        else:
            print("  ⚠ No GPU detected, will use CPU (slower)")
            return False
    except:
        print("  ⚠ Cannot check GPU, will use CPU")
        return False

def download_test_model():
    """Download and test a model."""
    print("\nTesting model download and initialization...")
    try:
        from background_removal import BackgroundRemover
        
        print("  Loading RMBG-1.4 model...")
        remover = BackgroundRemover(model_name="briaai/RMBG-1.4")
        print("  ✓ Model loaded successfully!")
        
        return remover
    except Exception as e:
        print(f"  ✗ Error loading model: {e}")
        return None

def create_test_image():
    """Create a simple test image."""
    print("\nCreating test image...")
    try:
        from PIL import Image, ImageDraw
        import numpy as np
        
        # Create a simple image with a colored square
        img = Image.new('RGB', (512, 512), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a colored rectangle (simulating a piece of clothing)
        draw.rectangle([100, 100, 400, 400], fill='blue', outline='darkblue', width=3)
        
        # Save test image
        os.makedirs('test_data', exist_ok=True)
        img.save('test_data/test_image.png')
        print("  ✓ Test image created: test_data/test_image.png")
        
        return 'test_data/test_image.png'
    except Exception as e:
        print(f"  ✗ Error creating test image: {e}")
        return None

def test_background_removal(remover, image_path):
    """Test background removal on test image."""
    print("\nTesting background removal...")
    try:
        # Remove background
        result = remover.remove_background(image_path)
        
        # Save result
        output_path = 'test_data/test_output.png'
        result.save(output_path, 'PNG')
        print(f"  ✓ Background removed successfully!")
        print(f"  ✓ Output saved: {output_path}")
        
        # Also get mask
        result_with_mask, mask = remover.remove_background(image_path, return_mask=True)
        mask.save('test_data/test_mask.png')
        print(f"  ✓ Mask saved: test_data/test_mask.png")
        
        return True
    except Exception as e:
        print(f"  ✗ Error during background removal: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*60)
    print("SETUP COMPLETE! 🎉")
    print("="*60)
    print("\nNext steps:")
    print("\n1. Basic usage:")
    print("   python background_removal.py --input image.jpg --output result.png")
    
    print("\n2. Batch processing:")
    print("   python batch_processor.py --input ./images --output ./processed")
    
    print("\n3. View examples:")
    print("   python examples/example_basic_usage.py")
    print("   python examples/example_batch_processing.py")
    
    print("\n4. Read full documentation:")
    print("   See BACKGROUND_REMOVAL_GUIDE.md")
    
    print("\n5. For fine-tuning:")
    print("   python finetune_background_removal.py --help")
    
    print("\n" + "="*60)

def main():
    """Main quick start function."""
    print("="*60)
    print("StyleMe Background Removal - Quick Start")
    print("="*60)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Step 2: Check GPU
    has_gpu = check_gpu()
    
    # Step 3: Download and test model
    remover = download_test_model()
    if remover is None:
        print("\n⚠ Model loading failed. Check your internet connection.")
        print("   and ensure you have enough disk space (~2GB for models)")
        sys.exit(1)
    
    # Step 4: Create test image
    test_image = create_test_image()
    if test_image is None:
        sys.exit(1)
    
    # Step 5: Test background removal
    success = test_background_removal(remover, test_image)
    if not success:
        sys.exit(1)
    
    # Step 6: Print next steps
    print_next_steps()
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nQuick start interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n⚠ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
