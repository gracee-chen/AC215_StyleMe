"""
Basic Usage Examples for StyleMe Background Removal
"""

from background_removal import BackgroundRemover
from PIL import Image
import os

# Create output directory
os.makedirs("output", exist_ok=True)

print("="*60)
print("StyleMe Background Removal - Basic Examples")
print("="*60)

# Example 1: Simple background removal
print("\n1. Simple Background Removal")
print("-" * 40)
remover = BackgroundRemover(model_name="briaai/RMBG-1.4")

# Note: Replace with actual image path
# result = remover.remove_background("path/to/your/image.jpg")
# result.save("output/result_simple.png", "PNG")
# print("✓ Saved to output/result_simple.png")

# Example 2: Get both image and mask
print("\n2. Get Image and Mask")
print("-" * 40)
# result, mask = remover.remove_background(
#     "path/to/your/image.jpg",
#     return_mask=True
# )
# result.save("output/result_with_mask.png", "PNG")
# mask.save("output/mask.png", "PNG")
# print("✓ Saved image and mask to output/")

# Example 3: Process PIL Image directly
print("\n3. Process PIL Image")
print("-" * 40)
# img = Image.open("path/to/your/image.jpg")
# img = img.resize((1024, 1024))  # Resize if needed
# result = remover.remove_background(img)
# result.save("output/result_pil.png", "PNG")
# print("✓ Processed PIL image")

# Example 4: Disable alpha matting for speed
print("\n4. Fast Processing (no alpha matting)")
print("-" * 40)
# result = remover.remove_background(
#     "path/to/your/image.jpg",
#     alpha_matting=False
# )
# result.save("output/result_fast.png", "PNG")
# print("✓ Fast processing complete")

# Example 5: Try different models
print("\n5. Using Different Models")
print("-" * 40)

# High quality model
# remover_hq = BackgroundRemover(model_name="ZhengPeng7/BiRefNet")
# result_hq = remover_hq.remove_background("path/to/your/image.jpg")
# result_hq.save("output/result_hq.png", "PNG")
# print("✓ High quality result saved")

# For anime/illustrated images
# remover_anime = BackgroundRemover(model_name="skytnt/anime-seg")
# result_anime = remover_anime.remove_background("path/to/anime_clothing.jpg")
# result_anime.save("output/result_anime.png", "PNG")
# print("✓ Anime result saved")

print("\n" + "="*60)
print("Examples complete!")
print("="*60)
print("\nNote: Uncomment the code and replace 'path/to/your/image.jpg'")
print("      with actual image paths to run these examples.")
