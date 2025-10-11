"""
Background Removal Module for StyleMe App
Uses state-of-the-art Hugging Face models for removing backgrounds from fashion images.
"""

import torch
from PIL import Image
import numpy as np
from transformers import AutoModelForImageSegmentation, AutoProcessor
from typing import Optional, Union, Tuple
import os
from pathlib import Path


class BackgroundRemover:
    """
    Background removal using pre-trained models from Hugging Face.
    Supports multiple models: RMBG-v1.4, BiRefNet, and U2Net variants.
    """
    
    def __init__(
        self, 
        model_name: str = "briaai/RMBG-1.4",
        device: Optional[str] = None
    ):
        """
        Initialize the background remover.
        
        Args:
            model_name: HuggingFace model identifier. Options:
                - "briaai/RMBG-1.4" (recommended, fast and accurate)
                - "ZhengPeng7/BiRefNet" (high quality)
                - "skytnt/anime-seg" (for anime/illustrated clothing)
            device: Computing device ('cuda', 'cpu', or None for auto-detect)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Loading model {model_name} on {self.device}...")
        
        try:
            self.model = AutoModelForImageSegmentation.from_pretrained(
                model_name,
                trust_remote_code=True
            ).to(self.device)
            self.model.eval()
            
            # Try to load processor if available
            try:
                self.processor = AutoProcessor.from_pretrained(
                    model_name,
                    trust_remote_code=True
                )
            except:
                self.processor = None
                
            self.model_name = model_name
            print(f"Model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            print("Falling back to rembg library...")
            self.model = None
            self.processor = None
            self.model_name = "rembg"
    
    def remove_background(
        self,
        image: Union[str, Path, Image.Image],
        return_mask: bool = False,
        alpha_matting: bool = True
    ) -> Union[Image.Image, Tuple[Image.Image, Image.Image]]:
        """
        Remove background from an image.
        
        Args:
            image: Input image (file path or PIL Image)
            return_mask: If True, also return the segmentation mask
            alpha_matting: If True, refine edges with alpha matting
            
        Returns:
            PIL Image with transparent background (and optionally the mask)
        """
        # Load image if path provided
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise ValueError("Image must be a file path or PIL Image")
        
        # Use rembg as fallback
        if self.model is None:
            return self._remove_background_rembg(image, return_mask)
        
        # Preprocess image
        if self.processor:
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        else:
            # Manual preprocessing for models without processor
            image_array = np.array(image)
            image_tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0).float() / 255.0
            inputs = image_tensor.to(self.device)
        
        # Generate mask
        with torch.no_grad():
            # Call model - handle different calling conventions
            if isinstance(inputs, dict):
                outputs = self.model(**inputs)
            else:
                # For models like RMBG that expect tensor directly
                outputs = self.model(inputs)
            
            # Handle different output formats
            if hasattr(outputs, 'logits'):
                mask = outputs.logits
            elif isinstance(outputs, torch.Tensor):
                mask = outputs
            else:
                mask = outputs[0]
        
        # Process mask
        mask = mask.squeeze().cpu()
        
        # Apply sigmoid if needed
        if mask.max() > 1.0:
            mask = torch.sigmoid(mask)
        
        # Resize mask to match original image size
        mask = mask.numpy()
        mask = Image.fromarray((mask * 255).astype(np.uint8)).resize(
            image.size, 
            Image.Resampling.BILINEAR
        )
        
        # Optional: alpha matting for edge refinement
        if alpha_matting:
            mask = self._refine_mask(mask)
        
        # Create RGBA image
        result = image.copy().convert('RGBA')
        result.putalpha(mask)
        
        if return_mask:
            return result, mask
        return result
    
    def _refine_mask(self, mask: Image.Image) -> Image.Image:
        """Apply edge refinement to the mask."""
        import cv2
        
        mask_array = np.array(mask)
        
        # Apply morphological operations to smooth edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_array = cv2.morphologyEx(mask_array, cv2.MORPH_CLOSE, kernel)
        mask_array = cv2.GaussianBlur(mask_array, (5, 5), 0)
        
        return Image.fromarray(mask_array)
    
    def _remove_background_rembg(
        self, 
        image: Image.Image, 
        return_mask: bool = False
    ) -> Union[Image.Image, Tuple[Image.Image, Image.Image]]:
        """Fallback method using rembg library."""
        from rembg import remove
        
        result = remove(image, alpha_matting=True)
        
        if return_mask:
            # Extract alpha channel as mask
            mask = result.split()[-1]
            return result, mask
        return result
    
    def process_batch(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        supported_formats: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.webp')
    ) -> int:
        """
        Process all images in a directory.
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save processed images
            supported_formats: Tuple of supported file extensions
            
        Returns:
            Number of images processed
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        image_files = [
            f for f in input_path.iterdir() 
            if f.suffix.lower() in supported_formats
        ]
        
        print(f"Processing {len(image_files)} images...")
        
        for i, image_file in enumerate(image_files, 1):
            try:
                print(f"[{i}/{len(image_files)}] Processing {image_file.name}...")
                result = self.remove_background(image_file)
                
                # Save with PNG format to preserve transparency
                output_file = output_path / f"{image_file.stem}_nobg.png"
                result.save(output_file, 'PNG')
                
            except Exception as e:
                print(f"Error processing {image_file.name}: {e}")
                continue
        
        print(f"Completed! Processed images saved to {output_path}")
        return len(image_files)


def main():
    """Example usage of the BackgroundRemover class."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove backgrounds from fashion images')
    parser.add_argument('--input', type=str, required=True, help='Input image or directory')
    parser.add_argument('--output', type=str, required=True, help='Output image or directory')
    parser.add_argument('--model', type=str, default='briaai/RMBG-1.4', 
                       help='Model name from HuggingFace')
    parser.add_argument('--batch', action='store_true', help='Process directory in batch mode')
    
    args = parser.parse_args()
    
    # Initialize remover
    remover = BackgroundRemover(model_name=args.model)
    
    if args.batch:
        # Batch processing
        remover.process_batch(args.input, args.output)
    else:
        # Single image processing
        result = remover.remove_background(args.input)
        result.save(args.output, 'PNG')
        print(f"Background removed! Saved to {args.output}")


if __name__ == '__main__':
    main()
