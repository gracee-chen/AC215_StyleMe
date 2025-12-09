"""
Batch Processing Utilities for StyleMe Background Removal
Handles large-scale image processing with progress tracking and error handling.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import json
from datetime import datetime
from tqdm import tqdm
import hashlib

from background_removal import BackgroundRemover


class BatchProcessor:
    """
    Process multiple fashion images in parallel with progress tracking.
    """
    
    def __init__(
        self,
        model_name: str = "briaai/RMBG-1.4",
        max_workers: int = 4,
        output_format: str = "png"
    ):
        """
        Args:
            model_name: HuggingFace model to use
            max_workers: Number of parallel workers
            output_format: Output image format (png, webp)
        """
        self.remover = BackgroundRemover(model_name=model_name)
        self.max_workers = max_workers
        self.output_format = output_format.lower()
        self.processing_stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        recursive: bool = False,
        overwrite: bool = False,
        quality_threshold: Optional[float] = None,
        save_metadata: bool = True
    ) -> Dict:
        """
        Process all images in a directory.
        
        Args:
            input_dir: Source directory with images
            output_dir: Destination directory
            recursive: Process subdirectories
            overwrite: Overwrite existing files
            quality_threshold: Skip images below this quality score (0-1)
            save_metadata: Save processing metadata
            
        Returns:
            Dictionary with processing statistics
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all images
        if recursive:
            image_files = list(input_path.rglob('*'))
        else:
            image_files = list(input_path.iterdir())
        
        # Filter for image files
        image_files = [
            f for f in image_files
            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        ]
        
        self.processing_stats['total'] = len(image_files)
        print(f"Found {len(image_files)} images to process")
        
        # Process with progress bar
        with tqdm(total=len(image_files), desc="Processing images") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                
                for image_file in image_files:
                    # Calculate relative path for maintaining directory structure
                    rel_path = image_file.relative_to(input_path)
                    output_file = output_path / rel_path.parent / f"{rel_path.stem}_nobg.{self.output_format}"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Skip if exists and not overwriting
                    if output_file.exists() and not overwrite:
                        self.processing_stats['skipped'] += 1
                        pbar.update(1)
                        continue
                    
                    # Submit processing task
                    future = executor.submit(
                        self._process_single_image,
                        image_file,
                        output_file,
                        quality_threshold
                    )
                    futures[future] = (image_file, output_file)
                
                # Collect results
                for future in as_completed(futures):
                    image_file, output_file = futures[future]
                    try:
                        success, error = future.result()
                        if success:
                            self.processing_stats['success'] += 1
                        else:
                            self.processing_stats['failed'] += 1
                            self.processing_stats['errors'].append({
                                'file': str(image_file),
                                'error': error
                            })
                    except Exception as e:
                        self.processing_stats['failed'] += 1
                        self.processing_stats['errors'].append({
                            'file': str(image_file),
                            'error': str(e)
                        })
                    
                    pbar.update(1)
        
        # Save metadata
        if save_metadata:
            self._save_processing_report(output_path)
        
        return self.processing_stats
    
    def _process_single_image(
        self,
        input_file: Path,
        output_file: Path,
        quality_threshold: Optional[float] = None
    ) -> tuple:
        """
        Process a single image.
        
        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        try:
            # Quality check
            if quality_threshold:
                quality = self._assess_image_quality(input_file)
                if quality < quality_threshold:
                    return False, f"Quality too low: {quality:.2f}"
            
            # Remove background
            result = self.remover.remove_background(input_file)
            
            # Save result
            if self.output_format == 'png':
                result.save(output_file, 'PNG', optimize=True)
            elif self.output_format == 'webp':
                result.save(output_file, 'WEBP', quality=95)
            else:
                result.save(output_file)
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def _assess_image_quality(self, image_path: Path) -> float:
        """
        Assess image quality based on resolution, blur, etc.
        
        Returns:
            Quality score from 0 to 1
        """
        try:
            img = Image.open(image_path)
            
            # Resolution check
            width, height = img.size
            resolution_score = min(1.0, (width * height) / (1024 * 1024))
            
            # Simple quality heuristic
            # In production, you might use blur detection, etc.
            quality_score = resolution_score
            
            return quality_score
            
        except:
            return 0.0
    
    def _save_processing_report(self, output_dir: Path):
        """Save processing statistics to JSON."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.processing_stats,
            'configuration': {
                'model': self.remover.model_name,
                'max_workers': self.max_workers,
                'output_format': self.output_format
            }
        }
        
        report_file = output_dir / 'processing_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nProcessing report saved to {report_file}")
    
    def print_summary(self):
        """Print processing summary."""
        stats = self.processing_stats
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Total images: {stats['total']}")
        print(f"Successfully processed: {stats['success']}")
        print(f"Failed: {stats['failed']}")
        print(f"Skipped: {stats['skipped']}")
        
        if stats['errors']:
            print(f"\nErrors encountered: {len(stats['errors'])}")
            print("\nFirst 5 errors:")
            for error in stats['errors'][:5]:
                print(f"  - {Path(error['file']).name}: {error['error']}")
        
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        print("="*50)


def main():
    """Command-line interface for batch processing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch process fashion images for background removal'
    )
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory containing images')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for processed images')
    parser.add_argument('--model', type=str, default='briaai/RMBG-1.4',
                       help='HuggingFace model name')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers')
    parser.add_argument('--format', type=str, default='png',
                       choices=['png', 'webp'],
                       help='Output image format')
    parser.add_argument('--recursive', action='store_true',
                       help='Process subdirectories recursively')
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite existing files')
    parser.add_argument('--quality-threshold', type=float,
                       help='Minimum quality threshold (0-1)')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = BatchProcessor(
        model_name=args.model,
        max_workers=args.workers,
        output_format=args.format
    )
    
    # Process directory
    print(f"Starting batch processing...")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Model: {args.model}")
    print(f"Workers: {args.workers}\n")
    
    processor.process_directory(
        input_dir=args.input,
        output_dir=args.output,
        recursive=args.recursive,
        overwrite=args.overwrite,
        quality_threshold=args.quality_threshold
    )
    
    # Print summary
    processor.print_summary()


if __name__ == '__main__':
    main()
