#!/usr/bin/env python3
"""
Fast background removal using rembg (CPU-optimized)
Use this for testing on CPU - much faster!
"""

from rembg import remove
from PIL import Image
import sys

if len(sys.argv) < 3:
    print("Usage: python background_removal_fast.py input.jpg output.png")
    sys.exit(1)

input_path = sys.argv[1]
output_path = sys.argv[2]

print(f"Processing {input_path}...")
print("(This should take 10-30 seconds on CPU)")

# Load image
img = Image.open(input_path)

# Remove background
result = remove(img)

# Save
result.save(output_path, 'PNG')

print(f"✓ Done! Saved to {output_path}")
print(f"\nTo view: open {output_path}")
