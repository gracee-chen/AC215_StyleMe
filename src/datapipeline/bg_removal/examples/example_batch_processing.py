"""
Batch Processing Examples for StyleMe
Process multiple fashion images efficiently
"""

from batch_processor import BatchProcessor
import os

print("="*60)
print("StyleMe Background Removal - Batch Processing Examples")
print("="*60)

# Example 1: Basic batch processing
print("\n1. Basic Batch Processing")
print("-" * 40)

processor = BatchProcessor(
    model_name="briaai/RMBG-1.4",
    max_workers=4,
    output_format="png"
)

# Uncomment to run:
# stats = processor.process_directory(
#     input_dir="./wardrobe_photos",
#     output_dir="./processed_wardrobe"
# )
# processor.print_summary()

# Example 2: Recursive processing with subdirectories
print("\n2. Recursive Processing")
print("-" * 40)

# Uncomment to run:
# stats = processor.process_directory(
#     input_dir="./all_fashion_images",
#     output_dir="./processed_all",
#     recursive=True,  # Process subdirectories
#     overwrite=False   # Skip existing files
# )

# Example 3: High-performance processing
print("\n3. High-Performance Processing")
print("-" * 40)

processor_fast = BatchProcessor(
    model_name="briaai/RMBG-1.4",
    max_workers=8,  # More workers
    output_format="webp"  # Smaller file size
)

# Uncomment to run:
# stats = processor_fast.process_directory(
#     input_dir="./large_dataset",
#     output_dir="./processed_large",
#     recursive=True,
#     quality_threshold=0.3  # Skip low-quality images
# )
# processor_fast.print_summary()

# Example 4: Custom processing with quality control
print("\n4. Quality-Controlled Processing")
print("-" * 40)

processor_quality = BatchProcessor(
    model_name="ZhengPeng7/BiRefNet",  # High-quality model
    max_workers=2,  # Fewer workers for GPU model
    output_format="png"
)

# Uncomment to run:
# stats = processor_quality.process_directory(
#     input_dir="./premium_catalog",
#     output_dir="./processed_premium",
#     quality_threshold=0.5,  # Only process high-quality images
#     save_metadata=True  # Save processing report
# )
# 
# print(f"\nProcessing statistics:")
# print(f"  Total: {stats['total']}")
# print(f"  Success: {stats['success']}")
# print(f"  Failed: {stats['failed']}")
# print(f"  Skipped: {stats['skipped']}")

# Example 5: Error handling and retry
print("\n5. Advanced Error Handling")
print("-" * 40)

def process_with_retry(input_dir, output_dir, max_retries=2):
    """Process with automatic retry on failures."""
    processor = BatchProcessor()
    
    for attempt in range(max_retries + 1):
        print(f"\nAttempt {attempt + 1}/{max_retries + 1}")
        
        stats = processor.process_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            overwrite=(attempt > 0)  # Overwrite on retries
        )
        
        if stats['failed'] == 0:
            print("✓ All images processed successfully!")
            break
        elif attempt < max_retries:
            print(f"⚠ {stats['failed']} images failed, retrying...")
        else:
            print(f"✗ {stats['failed']} images still failed after {max_retries} retries")
            print("\nFailed images:")
            for error in stats['errors']:
                print(f"  - {error['file']}: {error['error']}")
    
    return stats

# Uncomment to run:
# stats = process_with_retry(
#     input_dir="./difficult_images",
#     output_dir="./processed_difficult",
#     max_retries=2
# )

print("\n" + "="*60)
print("Batch processing examples complete!")
print("="*60)
print("\nNote: Uncomment the code blocks to run these examples")
print("      with your actual image directories.")
