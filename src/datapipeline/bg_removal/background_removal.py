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
    Background and person removal for fashion images.
    
    Removes background and all human body parts (skin, face, hands, arms, legs, etc.),
    keeping only the clothing items. This ensures that processed images contain only
    clothing without any background or person elements.
    
    Uses pre-trained models from Hugging Face for background removal and rembg's
    human segmentation model for person removal.
    
    Supports multiple models: RMBG-v1.4, BiRefNet, and U2Net variants.
    """
    
    def __init__(
        self, 
        model_name: str = "briaai/RMBG-1.4",
        device: Optional[str] = None,
        remove_person: bool = True
    ):
        """
        Initialize the background remover.
        
        Args:
            model_name: HuggingFace model identifier. Options:
                - "briaai/RMBG-1.4" (recommended, fast and accurate)
                - "ZhengPeng7/BiRefNet" (high quality)
                - "skytnt/anime-seg" (for anime/illustrated clothing)
            device: Computing device ('cuda', 'cpu', or None for auto-detect)
            remove_person: If True, remove person/human body parts and keep only clothing (default: True)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.remove_person = remove_person
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
            # Try to import rembg as fallback
            try:
                from rembg import remove as rembg_remove
                self.rembg_available = True
                print("   ✅ rembg library available as fallback")
            except ImportError:
                print("   ⚠️  rembg library not available. Background removal may not work.")
                self.rembg_available = False
            self.model = None
            self.processor = None
            self.model_name = "rembg"
        
        # Initialize person removal model if needed (after main model is loaded)
        if self.remove_person:
            self._init_person_removal()
    
    def _init_person_removal(self):
        """Initialize person/human body removal model to keep only clothing."""
        try:
            # Try to use rembg's human segmentation model
            try:
                from rembg import remove, new_session
                # Use u2net_human_seg model for human body segmentation
                self.person_session = new_session('u2net_human_seg')
                self.person_removal_available = True
                print("   ✅ Person removal model (u2net_human_seg) loaded")
            except Exception as e:
                print(f"   ⚠️  Could not load person removal model: {e}")
                self.person_removal_available = False
                self.person_session = None
        except ImportError:
            print("   ⚠️  rembg not available for person removal")
            self.person_removal_available = False
            self.person_session = None
    
    def remove_background(
        self,
        image: Union[str, Path, Image.Image],
        return_mask: bool = False,
        alpha_matting: bool = True
    ) -> Union[Image.Image, Tuple[Image.Image, Image.Image]]:
        """
        Remove background and person from an image, keeping only clothing.
        
        This method performs two steps:
        1. Removes the background
        2. Removes all human body parts (skin, face, hands, arms, legs, etc.)
        3. Keeps only the clothing items
        
        Args:
            image: Input image (file path or PIL Image)
            return_mask: If True, also return the segmentation mask
            alpha_matting: If True, refine edges with alpha matting
            
        Returns:
            PIL Image with transparent background, person removed, only clothing kept (and optionally the mask)
        """
        # Load image if path provided
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise ValueError("Image must be a file path or PIL Image")
        
        # Use rembg as fallback if model not available
        if self.model is None:
            if hasattr(self, 'rembg_available') and self.rembg_available:
                return self._remove_background_rembg(image, return_mask)
            else:
                # If rembg is not available either, raise an error
                raise RuntimeError("Background removal model failed to load and rembg fallback is not available. Please install rembg: pip install rembg")
        
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
        
        # Handle multi-channel masks (take first channel if needed)
        if len(mask.shape) > 2:
            mask = mask[0] if mask.shape[0] == 1 else mask.mean(dim=0)
        
        # Apply sigmoid if needed (normalize to 0-1 range)
        if mask.max() > 1.0 or mask.min() < 0.0:
            mask = torch.sigmoid(mask)
        
        # Ensure mask is in 0-1 range
        if mask.max() > 1.0:
            mask = mask / mask.max()
        if mask.min() < 0.0:
            mask = (mask - mask.min()) / (mask.max() - mask.min())
        
        # Convert to numpy and resize to match original image size
        mask_np = mask.numpy()
        
        # Ensure mask is 2D
        if len(mask_np.shape) > 2:
            mask_np = mask_np[0] if mask_np.shape[0] == 1 else mask_np.mean(axis=0)
        
        # Resize mask to match original image size BEFORE converting to uint8
        # This preserves more detail
        mask_pil = Image.fromarray((mask_np * 255).astype(np.uint8), mode='L')
        mask_pil = mask_pil.resize(image.size, Image.Resampling.BILINEAR)
        
        # Convert back to numpy for processing
        mask_np = np.array(mask_pil, dtype=np.float32) / 255.0
        
        # Ensure mask is properly normalized (0 = background, 1 = foreground)
        # Some models might output inverted masks, so check and fix if needed
        # RMBG models typically output: 1 = foreground (keep), 0 = background (remove)
        # If most of the mask is dark (low values), it might be inverted
        mask_mean = mask_np.mean()
        mask_std = mask_np.std()
        
        # Heuristic: if mean is very low (< 0.2) and std is low, likely inverted
        # Or if mean is very high (> 0.8), likely correct
        if mask_mean < 0.2 and mask_std < 0.3:
            # Likely inverted - most pixels are background
            print(f"   ⚠️  Mask appears inverted (mean={mask_mean:.3f}), inverting...")
            mask_np = 1.0 - mask_np
        elif mask_mean > 0.8:
            # Likely correct - most pixels are foreground
            pass
        # If mean is around 0.5, check edge distribution
        elif 0.3 < mask_mean < 0.7:
            # Check if edges are bright (foreground) or dark (background)
            # Sample center region (likely foreground) vs edges (likely background)
            h, w = mask_np.shape
            center_region = mask_np[h//4:3*h//4, w//4:3*w//4]
            edge_region = np.concatenate([
                mask_np[:h//8, :].flatten(),
                mask_np[-h//8:, :].flatten(),
                mask_np[:, :w//8].flatten(),
                mask_np[:, -w//8:].flatten()
            ])
            center_mean = center_region.mean()
            edge_mean = edge_region.mean()
            
            # If center is darker than edges, likely inverted
            if center_mean < edge_mean - 0.1:
                print(f"   ⚠️  Mask appears inverted (center={center_mean:.3f} < edge={edge_mean:.3f}), inverting...")
                mask_np = 1.0 - mask_np
        
        # Apply threshold to clean up the mask (remove noise)
        # Values below threshold become 0, above become 1
        threshold = 0.5
        mask_np = np.where(mask_np > threshold, 1.0, 0.0).astype(np.float32)
        
        # Convert to 0-255 range and ensure uint8
        mask_np = (mask_np * 255).astype(np.uint8)
        mask = Image.fromarray(mask_np, mode='L')
        
        # Optional: alpha matting for edge refinement
        if alpha_matting:
            mask = self._refine_mask(mask)
        
        # Ensure mask is in 'L' mode (grayscale) for proper alpha channel
        if mask.mode != 'L':
            mask = mask.convert('L')
        
        # Create RGBA image with proper alpha channel
        # Ensure original image is RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Verify mask is valid (not all black or all white)
        mask_array = np.array(mask)
        mask_mean = mask_array.mean()
        if mask_mean < 10:  # Almost all black - mask failed
            print(f"   ⚠️  Warning: Mask is almost entirely black (mean={mask_mean:.1f}). Background removal may not work correctly.")
        elif mask_mean > 245:  # Almost all white - no background removed
            print(f"   ⚠️  Warning: Mask is almost entirely white (mean={mask_mean:.1f}). No background detected to remove.")
        
        result = image.copy().convert('RGBA')
        
        # Apply mask as alpha channel
        # The mask should be 0 (transparent) for background, 255 (opaque) for foreground
        result.putalpha(mask)
        
        # Verify the result has proper alpha channel
        if result.mode != 'RGBA':
            result = result.convert('RGBA')
        
        # Remove person/human body parts if enabled (keep only clothing)
        if self.remove_person and self.person_removal_available:
            result = self._remove_person_from_result(result, image)
        
        if return_mask:
            return result, mask
        return result
    
    def _remove_person_from_result(self, result_image: Image.Image, original_image: Image.Image) -> Image.Image:
        """
        Remove person/human body parts from the result, keeping only clothing.
        This removes all human body parts (skin, face, hands, arms, legs, etc.) and keeps only the clothing.
        
        Args:
            result_image: RGBA image with background removed
            original_image: Original RGB image for person detection
        
        Returns:
            RGBA image with person removed, only clothing kept
        """
        try:
            from rembg import remove
            
            # Get person/human segmentation mask from original image
            # This will identify ALL human body parts (skin, face, hands, arms, torso, legs, etc.)
            person_mask_result = remove(original_image, session=self.person_session)
            
            # Extract person mask (alpha channel or convert to grayscale)
            if person_mask_result.mode == 'RGBA':
                person_mask = person_mask_result.split()[3]  # Alpha channel
            else:
                person_mask = person_mask_result.convert('L')
            
            # Convert to numpy array for processing
            person_mask_array = np.array(person_mask, dtype=np.float32)
            
            # Normalize to 0-1 range
            if person_mask_array.max() > 1.0:
                person_mask_array = person_mask_array / 255.0
            
            # Use a lower threshold to be more aggressive in removing person parts
            # Values above threshold are person parts (skin, body) to remove
            # We want to keep only clothing, which should not be detected as person
            threshold = 0.3  # Lower threshold = more aggressive person removal
            
            # Identify person regions (skin, body parts)
            person_regions = person_mask_array > threshold
            
            # Create clothing mask: 0 where person is (remove), 255 where clothing is (keep)
            # Invert: person regions become 0 (transparent), non-person regions become 255 (opaque)
            clothing_mask_array = np.where(person_regions, 0.0, 1.0).astype(np.float32)
            
            # Apply morphological operations to clean up the mask
            # This helps remove small noise and smooth edges
            try:
                import cv2
                # Convert to uint8 for morphological operations
                clothing_mask_uint8 = (clothing_mask_array * 255).astype(np.uint8)
                
                # Apply closing to fill small holes
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                clothing_mask_uint8 = cv2.morphologyEx(clothing_mask_uint8, cv2.MORPH_CLOSE, kernel)
                
                # Apply opening to remove small noise
                clothing_mask_uint8 = cv2.morphologyEx(clothing_mask_uint8, cv2.MORPH_OPEN, kernel)
                
                # Convert back to float
                clothing_mask_array = (clothing_mask_uint8 / 255.0).astype(np.float32)
            except ImportError:
                # If cv2 not available, skip morphological operations
                pass
            
            # Convert to uint8 for PIL
            clothing_mask = Image.fromarray((clothing_mask_array * 255).astype(np.uint8), mode='L')
            
            # Get existing alpha channel from background removal result
            existing_alpha = np.array(result_image.split()[3], dtype=np.float32) / 255.0
            
            # Combine masks: keep pixels where BOTH background removal AND person removal agree
            # This ensures we only keep clothing (not background, not person)
            combined_alpha = np.minimum(existing_alpha, clothing_mask_array)
            
            # Apply additional threshold to ensure clean edges
            # Remove very low alpha values (likely noise or partial pixels)
            combined_alpha = np.where(combined_alpha < 0.1, 0.0, combined_alpha)
            
            # Convert back to 0-255 range
            combined_alpha = (combined_alpha * 255).astype(np.uint8)
            
            # Apply combined mask to result
            result_rgb = result_image.convert('RGB')
            result_final = result_rgb.copy().convert('RGBA')
            result_final.putalpha(Image.fromarray(combined_alpha, mode='L'))
            
            # Verify result has meaningful content (not all transparent)
            alpha_check = np.array(combined_alpha)
            if alpha_check.max() < 10:
                print(f"   ⚠️  Warning: Person removal may have removed too much. Result is mostly transparent.")
            
            return result_final
            
        except Exception as e:
            print(f"   ⚠️  Person removal failed: {e}, keeping original result")
            return result_image
    
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
        
        # Ensure image is in RGB mode for rembg
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Remove background - rembg returns RGBA image with transparent background
        result = remove(image, alpha_matting=True)
        
        # Ensure result is RGBA
        if result.mode != 'RGBA':
            result = result.convert('RGBA')
        
        # Remove person/human body parts if enabled (keep only clothing)
        if self.remove_person and self.person_removal_available:
            result = self._remove_person_from_result(result, image)
        
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
