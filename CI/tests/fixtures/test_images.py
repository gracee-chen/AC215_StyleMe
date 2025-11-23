"""
Test image fixtures for background removal testing
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw


def create_test_image_with_background(output_path: Path, size=(224, 224), 
                                     main_color='red', bg_color='white'):
    """
    Create a test image with a distinct background for testing bg removal
    
    Args:
        output_path: Path to save the image
        size: Image size (width, height)
        main_color: Color of the main object
        bg_color: Color of the background
    """
    img = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a rectangle in the center (simulating an object)
    margin = 20
    draw.rectangle(
        [margin, margin, size[0] - margin, size[1] - margin],
        fill=main_color,
        outline='black',
        width=2
    )
    
    # Add some text to make it more realistic
    try:
        draw.text((size[0] // 2 - 20, size[1] // 2 - 10), "TEST", fill='white')
    except:
        pass  # Font might not be available
    
    img.save(output_path)
    return output_path


def create_test_image_without_background(output_path: Path, size=(224, 224), 
                                        color='red'):
    """
    Create a test image without background (already processed)
    
    Args:
        output_path: Path to save the image
        size: Image size (width, height)
        color: Color of the object
    """
    # Create RGBA image with transparent background
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a rectangle (simulating an object)
    margin = 20
    draw.rectangle(
        [margin, margin, size[0] - margin, size[1] - margin],
        fill=(*Image.new('RGB', (1, 1), color=color).getpixel((0, 0)), 255),
        outline='black',
        width=2
    )
    
    img.save(output_path, 'PNG')
    return output_path


def setup_test_images(tmp_path):
    """
    Setup test images for bg removal testing
    
    Returns:
        dict with paths to test images
    """
    images_dir = tmp_path / "test_images"
    images_dir.mkdir(exist_ok=True)
    
    # Create image with background
    img_with_bg = images_dir / "query_with_bg.jpg"
    create_test_image_with_background(img_with_bg)
    
    # Create image without background (already processed)
    img_no_bg = images_dir / "query_no_bg.png"
    create_test_image_without_background(img_no_bg)
    
    return {
        'with_background': img_with_bg,
        'without_background': img_no_bg,
        'images_dir': images_dir
    }

