"""
Flask API Server for StyleMe Inference Service
Provides REST API endpoints for frontend to interact with the inference service
"""

import os
import sys
import json
import base64
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io
from datetime import datetime

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, project_root)

from inference_service import InferenceService

app = Flask(__name__)
# Enable CORS for frontend with explicit configuration
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    },
    r"/health": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"]
    }
})

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
WARDROBES_DIR = Path(os.getenv('WARDROBES_DIR', '/gcs/styleme-production/wardrobes'))
CATALOG_DIR = Path(os.getenv('CATALOG_DIR', '/gcs/styleme-production/catalog'))
EXPERIMENTS_DIR = Path(os.getenv('EXPERIMENTS_DIR', '/gcs/styleme-production/experiments'))
RESULTS_DIR = Path(os.getenv('RESULTS_DIR', '/gcs/styleme-production/results'))
QUERIES_DIR = Path(os.getenv('QUERIES_DIR', '/gcs/styleme-production/queries'))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Image processing configuration
MAX_IMAGE_SIZE = (1024, 1024)  # Maximum width and height in pixels

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WARDROBES_DIR, exist_ok=True)

def resize_image(image: Image.Image, max_size: tuple = MAX_IMAGE_SIZE) -> Image.Image:
    """
    Resize image while maintaining aspect ratio.
    Ensures the entire image is visible without cropping.
    
    Args:
        image: PIL Image to resize
        max_size: Tuple of (max_width, max_height)
    
    Returns:
        Resized PIL Image with full content visible
    """
    width, height = image.size
    max_width, max_height = max_size
    
    # If image is already smaller than max size, return as is
    if width <= max_width and height <= max_height:
        return image
    
    # Calculate scaling factor to fit within max dimensions
    # Use min() to ensure both dimensions fit, maintaining aspect ratio
    scale = min(max_width / width, max_height / height)
    
    # Calculate new dimensions (must be integers)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Ensure dimensions are at least 1 pixel
    new_width = max(1, new_width)
    new_height = max(1, new_height)
    
    # Resize with high-quality resampling (LANCZOS for best quality)
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    print(f"📐 Resized image from {width}x{height} to {new_width}x{new_height} (scale: {scale:.3f})")
    
    return resized_image

# Initialize inference service (singleton)
inference_service = None
inference_service_error = None

def get_inference_service():
    """Lazy initialization of inference service"""
    global inference_service, inference_service_error
    if inference_service is None and inference_service_error is None:
        # Skip filesystem check in Cloud Run - will use GCS client library
        # The InferenceService will handle GCS access automatically
        
        # Model exists, try to initialize service
        # Background removal is disabled by default
        try:
            inference_service = InferenceService(
                catalog_dir=str(CATALOG_DIR),
                experiments_dir=str(EXPERIMENTS_DIR),
                wardrobes_dir=str(WARDROBES_DIR),
                bg_removal_enabled=False  # Background removal disabled
            )
        except FileNotFoundError as e:
            if "No trained model found" in str(e):
                inference_service_error = "No trained model found. Please train a model first."
            else:
                inference_service_error = str(e)
        except Exception as e:
            inference_service_error = f"Failed to initialize inference service: {str(e)}"
    
    if inference_service_error:
        return None, inference_service_error
    return inference_service, None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_clothing_tags(image_path: Path) -> dict:
    """
    Generate clothing tags using ChatGPT API.
    Each item is analyzed independently - tags don't affect each other.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with clothing tags (category, color, style only)
    """
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping automatic tagging")
        return {}
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        # Read image and convert to base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_mime_type = 'image/jpeg' if image_path.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png'
        image_data_url = f"data:{image_mime_type};base64,{image_base64}"
        
        # System prompt - only generate category, color, and style
        system_message = """You are a professional fashion expert analyzing clothing items from images. Your task is to accurately identify ONLY the category, color, and style of each item.

OUTPUT FORMAT (JSON only):
{
  "category": "ONE of these exact categories: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'",
  "color": "primary color name (e.g., 'black', 'white', 'blue', 'brown', 'green')",
  "style": "style description (e.g., 'casual', 'formal', 'sporty', 'elegant')"
}

ONLY return these three fields. Do not include any other fields.

═══════════════════════════════════════════════════════════════════
CATEGORY IDENTIFICATION - FOLLOW THESE RULES IN EXACT ORDER:
═══════════════════════════════════════════════════════════════════

STEP 1: Check for SHOES first (highest priority)
   ✓ Look at the BOTTOM of the image - are there feet, soles, heels, or footwear?
   ✓ Boots (ankle, knee-high, combat, UGG, leather, suede, etc.) → 'shoes'
   ✓ Sneakers, athletic shoes, running shoes → 'shoes'
   ✓ Sandals, flip-flops, slides → 'shoes'
   ✓ Heels, pumps, flats, loafers, oxfords → 'shoes'
   ✓ ANY item worn on the feet → 'shoes'
   ⚠️ CRITICAL: If you see footwear, it is ALWAYS 'shoes', NEVER 'shirt' or 'top'

STEP 2: Check for DRESS (second priority)
   ✓ Look for a ONE-PIECE garment that extends from shoulders/chest down to form a skirt
   ✓ A dress is a SINGLE garment combining top and bottom in one piece
   ✓ If the garment flows from upper body to lower body as one continuous piece → 'dress'
   ✓ Even if it's a short dress, mini dress, or maxi dress → 'dress'
   ⚠️ CRITICAL: If it's a dress, it is NEVER 'shirt' or 'top' - dresses are complete garments

STEP 3: Check for PANTS (CRITICAL - check this BEFORE shirt/top)
   ✓ Trousers, jeans, pants, leggings, shorts → 'pants'
   ✓ Any lower body garment that covers legs (fully or partially) → 'pants'
   ✓ Denim jeans, cargo pants, sweatpants, joggers → 'pants'
   ✓ If you see legs, thighs, or lower body garment → 'pants'
   ⚠️ CRITICAL: If it's pants/jeans/trousers, it is ALWAYS 'pants', NEVER 'shirt' or 'top'

STEP 4: Check for JACKET
   ✓ Outerwear: jackets, coats, blazers, cardigans, sweaters, hoodies → 'jacket'
   ✓ Items typically worn OVER other clothing → 'jacket'
   ✓ If it's a sweater or cardigan worn as outer layer → 'jacket'

STEP 5: Check for SHIRT
   ✓ Tops, shirts, blouses, t-shirts, tank tops, camisoles → 'shirt'
   ✓ Upper body garments that are NOT dresses and NOT outerwear → 'shirt'
   ✓ Only use 'shirt' if it's clearly a top and NOT a dress, NOT shoes, NOT pants

STEP 6: Check for ACCESSORIES
   ✓ Bags, handbags, backpacks, purses → 'accessories'
   ✓ Hats, caps, beanies → 'accessories'
   ✓ Scarves, belts, jewelry, watches → 'accessories'

═══════════════════════════════════════════════════════════════════
COLOR IDENTIFICATION - CRITICAL RULES:
═══════════════════════════════════════════════════════════════════

1. IGNORE these colors (they are NOT the main color):
   ✗ Background colors (white backgrounds, colored backgrounds)
   ✗ Inner layers (white collars, undershirts, inner garments)
   ✗ Small details (buttons, zippers, logos, labels)
   ✗ Accessories worn with the item (belts, jewelry, bags)

2. FOCUS ONLY on the OUTERMOST, DOMINANT color of the MAIN garment:
   ✓ Look at the largest visible area of the item
   ✓ If someone is wearing a green sweater over a white shirt → color is 'green'
   ✓ If someone is wearing a green dress → color is 'green' (NOT white from collar)
   ✓ If you see brown/tan/beige shoes → color is 'brown' or 'beige' (NOT white from background)

3. Color mapping rules:
   • Green shades: mint, olive, forest, sage, emerald, lime, teal, jade → 'green'
   • Brown shades: tan, camel, taupe, chocolate, coffee, caramel, suede, leather → 'brown'
   • Beige shades: nude, sand, cream (light brown tones) → 'beige'
   • Red shades: maroon, burgundy, crimson, wine, cherry, dark red → 'red'
   • Blue shades: navy, dark blue → 'navy'; light blue, sky blue → 'blue'
   • Gray shades: grey, silver → 'gray'
   • White shades: ivory, snow → 'white'

4. Valid color names (use EXACTLY these):
   'black', 'white', 'blue', 'brown', 'green', 'red', 'pink', 'purple', 'yellow', 'orange', 'gray', 'beige', 'navy', 'cream', 'khaki'

═══════════════════════════════════════════════════════════════════
STYLE IDENTIFICATION:
═══════════════════════════════════════════════════════════════════

Choose the most appropriate style from: 'casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'

═══════════════════════════════════════════════════════════════════
FINAL REQUIREMENTS:
═══════════════════════════════════════════════════════════════════

✓ ALL THREE fields (category, color, style) MUST be present
✓ Category MUST be exactly one of: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'
✓ Color MUST be one of the valid color names listed above
✓ Style MUST be one of: 'casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'
✓ NEVER use "miscellaneous", "unknown", "Unknown", "N/A", "n/a", "other", "Other", or any vague terms
✓ Do NOT omit any required fields
✓ If you cannot determine a value, use the most appropriate option from the valid lists above
✓ Analyze the image carefully and follow the priority order for category identification"""
        
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Analyze the clothing item in this image and return ONLY category, color, and style.

IMPORTANT INSTRUCTIONS:
1. Look carefully at the image - identify what type of clothing item this is
2. Follow the category identification rules in EXACT order (shoes → dress → pants → jacket → shirt → accessories)
3. Identify the PRIMARY/MAIN color of the OUTERMOST garment (ignore background, inner layers, small details)
4. Determine the style based on the item's appearance

Return ONLY a JSON object with these three fields: category, color, style."""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                }
            ]
        }
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                user_message
            ],
            max_tokens=500,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)
        
        # Ensure required fields exist (only category, color, style)
        result = {
            'category': analysis.get('category', 'shirt'),
            'color': analysis.get('color', 'white'),
            'style': analysis.get('style', 'casual')
        }
        
        return result
        
    except ImportError:
        print("⚠️  OpenAI library not installed, skipping automatic tagging")
        return {}
    except Exception as e:
        print(f"⚠️  Failed to generate tags with ChatGPT API: {e}")
        return {}

def save_image_from_base64(base64_string, output_path):
    """Save base64 encoded image to file"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        
        # Load image and verify it's complete
        image = Image.open(io.BytesIO(image_data))
        # Verify image is complete by loading it fully
        image.load()
        
        # Save with explicit format and quality to prevent truncation
        if output_path.suffix.lower() in ['.jpg', '.jpeg']:
            image = image.convert('RGB')  # Ensure RGB mode for JPEG
            image.save(output_path, 'JPEG', quality=95, optimize=False)
        elif output_path.suffix.lower() == '.png':
            image.save(output_path, 'PNG', optimize=False)
        else:
            # Default to JPEG
            image = image.convert('RGB')
            image.save(output_path, 'JPEG', quality=95, optimize=False)
        
        # Verify file was saved correctly
        if not output_path.exists() or output_path.stat().st_size == 0:
            print(f"⚠️  Warning: Saved image file is empty or doesn't exist")
            return False
        
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_query_to_gcs(user_id: str, request_id: str, query_image_path: Path) -> str:
    """Save query image to GCS queries/{user_id}/{request_id}/query.jpg"""
    from google.cloud import storage
    
    gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
    gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
    
    # GCS path
    gcs_path = f"queries/{user_id}/{request_id}/query.jpg"
    
    try:
        client = storage.Client(project=gcp_project_id)
        bucket = client.bucket(gcp_bucket_name)
        blob = bucket.blob(gcs_path)
        
        # Upload query image
        blob.upload_from_filename(str(query_image_path))
        print(f"✅ Saved query image to gs://{gcp_bucket_name}/{gcs_path}")
        return gcs_path
    except Exception as e:
        print(f"⚠️  Failed to save query to GCS: {e}")
        # Return local path as fallback
        return str(query_image_path)

def save_result_to_gcs(user_id: str, request_id: str, result_data: dict):
    """Save inference results to GCS results/{user_id}/{request_id}.json"""
    from google.cloud import storage
    import json
    
    gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
    gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
    
    # GCS path
    gcs_path = f"results/{user_id}/{request_id}.json"
    
    try:
        client = storage.Client(project=gcp_project_id)
        bucket = client.bucket(gcp_bucket_name)
        blob = bucket.blob(gcs_path)
        
        # Upload results as JSON
        blob.upload_from_string(
            json.dumps(result_data, indent=2),
            content_type='application/json'
        )
        print(f"✅ Saved results to gs://{gcp_bucket_name}/{gcs_path}")
    except Exception as e:
        print(f"⚠️  Failed to save results to GCS: {e}")
        raise

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'StyleMe Inference API'})

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """
    Upload an image to user's wardrobe with automatic tagging
    POST /api/upload
    Body: {
        "user_id": "string",
        "image": "base64_encoded_image" or multipart/form-data,
        "metadata": {
            "category": "string" (optional - will be auto-generated if not provided),
            "color": "string" (optional - will be auto-generated if not provided),
            "style": "string" (optional - will be auto-generated if not provided)
        } (optional)
    }
    
    If metadata is not provided, ChatGPT API will automatically generate category, color, and style tags.
    Each item is tagged independently - tags don't affect each other.
    Once tags are saved, they won't change (metadata file is checked first).
    """
    try:
        data = request.get_json() if request.is_json else {}
        user_id = data.get('user_id') or request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Get metadata if provided
        metadata = data.get('metadata') or {}
        if request.form:
            # Try to parse metadata from form data
            metadata_str = request.form.get('metadata')
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                except:
                    pass
        
        # Create user wardrobe directory
        user_wardrobe_dir = WARDROBES_DIR / user_id / 'images'
        user_wardrobe_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata directory
        metadata_dir = WARDROBES_DIR / user_id
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle image upload
        temp_image_path = None
        
        # Try base64 first
        if 'image' in data:
            temp_filename = f"temp_{user_id}_{os.getpid()}.jpg"
            temp_image_path = Path(UPLOAD_FOLDER) / temp_filename
            if not save_image_from_base64(data['image'], temp_image_path):
                return jsonify({'error': 'Failed to save image'}), 400
        
        # Try multipart form data
        elif 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                temp_filename = f"temp_{user_id}_{os.getpid()}.jpg"
                temp_image_path = Path(UPLOAD_FOLDER) / temp_filename
                file.save(temp_image_path)
        
        if not temp_image_path or not temp_image_path.exists():
            return jsonify({'error': 'No valid image provided'}), 400
        
        # Process image: resize and save (background removal is optional)
        final_image_path = None
        try:
            # Get inference service (optional, for background removal if enabled)
            service, error = get_inference_service()
            
            # Generate final image filename
            image_filename = f"{user_id}_{len(list(user_wardrobe_dir.glob('*.jpg')))}.jpg"
            final_image_path = user_wardrobe_dir / image_filename
            
            # Load original image
            processed_image = Image.open(temp_image_path).convert('RGB')
            
            # Optional: Apply background removal if enabled
            if service and service.bg_removal_enabled and service.bg_remover:
                try:
                    # Remove background - returns RGBA image with transparent background
                    processed_image = service.bg_remover.remove_background(processed_image)
                    
                    # Convert to RGB with white background
                    if processed_image.mode == 'RGBA':
                        # Create white background
                        background = Image.new('RGB', processed_image.size, (255, 255, 255))
                        # Get alpha channel as mask
                        alpha = processed_image.split()[3]
                        # Ensure mask is in 'L' mode (grayscale) for proper masking
                        if alpha.mode != 'L':
                            alpha = alpha.convert('L')
                        # Apply mask to paste only the foreground (clothing) onto white background
                        background.paste(processed_image, mask=alpha)
                        processed_image = background
                    elif processed_image.mode != 'RGB':
                        processed_image = processed_image.convert('RGB')
                    print(f"✅ Background removed from image")
                except Exception as bg_error:
                    print(f"⚠️  Background removal failed: {str(bg_error)}, using original image")
                    # Continue with original image if background removal fails
            
            # Resize image to appropriate size for wardrobe
            # This ensures the full item is visible, not cropped
            processed_image = resize_image(processed_image, MAX_IMAGE_SIZE)
            
            # Ensure image is in RGB mode for JPEG
            if processed_image.mode != 'RGB':
                processed_image = processed_image.convert('RGB')
            
            # Save processed image to wardrobe with explicit parameters to prevent truncation
            processed_image.save(final_image_path, 'JPEG', quality=95, optimize=False)
            
            # Verify file was saved correctly
            if not final_image_path.exists() or final_image_path.stat().st_size == 0:
                raise Exception("Saved image file is empty or doesn't exist")
            
            print(f"✅ Image processed and resized to {processed_image.size}, saved {final_image_path.stat().st_size} bytes")
        
        except Exception as e:
            error_msg = f"Image processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            return jsonify({'error': error_msg}), 500
        finally:
            # Clean up temp file
            if temp_image_path and temp_image_path.exists():
                temp_image_path.unlink()
        
        if not final_image_path or not final_image_path.exists():
            return jsonify({'error': 'Failed to process image'}), 500
        
        # Check if metadata file already exists (to prevent re-tagging)
        # Each item is tagged independently - tags don't affect each other
        metadata_filename = final_image_path.stem + '_metadata.json'
        metadata_path = metadata_dir / metadata_filename
        metadata_to_save = None  # Initialize to None
        
        # Priority: 1) Existing metadata file, 2) User-provided metadata, 3) Generate with ChatGPT
        if metadata_path.exists():
            # Metadata already exists - use it (don't re-tag)
            try:
                with open(metadata_path, 'r') as f:
                    existing_metadata = json.load(f)
                print(f"✅ Metadata already exists for {final_image_path.name}, using existing tags (won't change)")
                # Use existing metadata, but update timestamp
                metadata_to_save = existing_metadata.copy()
                metadata_to_save['timestamp'] = datetime.now().isoformat()
            except Exception as e:
                print(f"⚠️  Failed to load existing metadata: {e}, will use provided or generate new tags")
                # Fall through to generate new metadata below
                metadata_to_save = None
        
        # If metadata_to_save is None (failed to load existing), generate new
        if metadata_to_save is None:
            # No existing metadata file - use provided metadata or generate
            # Check only category, color, style (the three required tags)
            if metadata and any(metadata.get(k) and metadata.get(k) != 'Unknown' and metadata.get(k) != '' 
                               for k in ['category', 'color', 'style']):
                # User provided metadata - use it
                print(f"✅ Using user-provided metadata for {final_image_path.name}")
                metadata_to_save = {
                    'filename': final_image_path.name,
                    'category': metadata.get('category', 'Unknown'),
                    'color': metadata.get('color', 'Unknown'),
                    'style': metadata.get('style', 'Casual'),
                    'timestamp': datetime.now().isoformat(),
                    'tagged_at': datetime.now().isoformat(),
                    'source': 'user_provided'
                }
            else:
                # No metadata provided - generate with ChatGPT API
                print(f"🔄 No metadata provided, generating tags with ChatGPT API for {final_image_path.name}...")
                try:
                    generated_metadata = generate_clothing_tags(final_image_path)
                    if generated_metadata:
                        print(f"✅ Generated tags for {final_image_path.name}")
                        metadata_to_save = {
                            'filename': final_image_path.name,
                            'category': generated_metadata.get('category', 'Unknown'),
                            'color': generated_metadata.get('color', 'Unknown'),
                            'style': generated_metadata.get('style', 'Casual'),
                            'timestamp': datetime.now().isoformat(),
                            'tagged_at': datetime.now().isoformat(),
                            'source': 'chatgpt_auto'
                        }
                    else:
                        # Fallback to defaults if generation failed
                        print(f"⚠️  Tag generation failed, using default values")
                        metadata_to_save = {
                            'filename': final_image_path.name,
                            'category': 'Unknown',
                            'color': 'Unknown',
                            'style': 'Casual',
                            'timestamp': datetime.now().isoformat(),
                            'tagged_at': datetime.now().isoformat(),
                            'source': 'default'
                        }
                except Exception as tag_error:
                    print(f"⚠️  Failed to generate tags: {tag_error}, using default values")
                    metadata_to_save = {
                        'filename': final_image_path.name,
                        'category': 'Unknown',
                        'color': 'Unknown',
                        'style': 'Casual',
                        'timestamp': datetime.now().isoformat(),
                        'tagged_at': datetime.now().isoformat(),
                        'source': 'default'
                    }
        
        # Save metadata to JSON file (one file per image)
        # This ensures tags are persisted and won't change once saved
        if not metadata_to_save:
            # Fallback if metadata_to_save is None (shouldn't happen, but safety check)
            metadata_to_save = {
                'filename': final_image_path.name,
                'category': 'Unknown',
                'color': 'Unknown',
                'style': 'Casual',
                'timestamp': datetime.now().isoformat(),
                'source': 'default'
            }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata_to_save, f, indent=2)
        print(f"✅ Saved metadata for {final_image_path.name} (source: {metadata_to_save.get('source', 'unknown')})")
        
        # Return success with image info and metadata
        return jsonify({
            'success': True,
            'user_id': user_id,
            'image_path': str(final_image_path),
            'metadata': metadata_to_save,
            'message': 'Image uploaded and processed successfully. Tags generated and saved.'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """
    Get recommendations for a query image
    POST /api/recommend
    Body: {
        "user_id": "string",
        "image": "base64_encoded_image" or multipart/form-data,
        "threshold": 0.7 (optional),
        "wardrobe_k": 5 (optional),
        "catalog_k": 3 (optional),
        "gender": "men" or "women" (optional)
    }
    """
    try:
        data = request.get_json() if request.is_json else {}
        user_id = data.get('user_id') or request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Get parameters
        threshold = float(data.get('threshold', 0.7))
        wardrobe_k = int(data.get('wardrobe_k', 5))
        catalog_k = int(data.get('catalog_k', 3))
        gender = data.get('gender')
        
        # Handle image upload
        query_image_path = None
        
        # Try base64 first
        if 'image' in data:
            temp_filename = f"query_{user_id}_{os.getpid()}.jpg"
            query_image_path = Path(UPLOAD_FOLDER) / temp_filename
            if not save_image_from_base64(data['image'], query_image_path):
                return jsonify({'error': 'Failed to process image'}), 400
        
        # Try multipart form data
        elif 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                temp_filename = f"query_{user_id}_{os.getpid()}.jpg"
                query_image_path = Path(UPLOAD_FOLDER) / temp_filename
                file.save(query_image_path)
        
        if not query_image_path or not query_image_path.exists():
            return jsonify({'error': 'No valid query image provided'}), 400
        
        # Get inference service
        service, error = get_inference_service()
        
        if service is None:
            return jsonify({
                'error': error or 'Inference service not available',
                'message': 'The model needs to be trained before recommendations can be generated.',
                'hint': 'Run the training pipeline to create a model, or ensure best_model.pth exists in experiments directory.'
            }), 503  # Service Unavailable
        
        # Process query image: remove background (REQUIRED for recommendations)
        # Background removal is mandatory for all query images - only keep clothing
        processed_query_path = None
        try:
            # Load original query image
            processed_query_image = Image.open(query_image_path).convert('RGB')
            
            # Optional: Apply background removal if enabled
            if service and service.bg_removal_enabled and service.bg_remover:
                try:
                    # Remove background - returns RGBA image with transparent background
                    processed_query_image = service.bg_remover.remove_background(processed_query_image)
                    
                    # Convert to RGB with white background
                    if processed_query_image.mode == 'RGBA':
                        # Create white background
                        background = Image.new('RGB', processed_query_image.size, (255, 255, 255))
                        # Get alpha channel as mask
                        alpha = processed_query_image.split()[3]
                        # Ensure mask is in 'L' mode (grayscale) for proper masking
                        if alpha.mode != 'L':
                            alpha = alpha.convert('L')
                        # Apply mask to paste only the foreground (clothing) onto white background
                        background.paste(processed_query_image, mask=alpha)
                        processed_query_image = background
                    elif processed_query_image.mode != 'RGB':
                        processed_query_image = processed_query_image.convert('RGB')
                    print(f"✅ Background removed from query image")
                except Exception as bg_error:
                    print(f"⚠️  Background removal failed for query image: {str(bg_error)}, using original image")
                    # Continue with original image if background removal fails
            
            # Save processed query image (replace original temp file)
            processed_query_path = query_image_path
            
            # Ensure image is in RGB mode for JPEG
            if processed_query_image.mode != 'RGB':
                processed_query_image = processed_query_image.convert('RGB')
            
            # Save with explicit parameters to prevent truncation
            processed_query_image.save(processed_query_path, 'JPEG', quality=95, optimize=False)
            
            # Verify file was saved correctly
            if not processed_query_path.exists() or processed_query_path.stat().st_size == 0:
                print(f"⚠️  Warning: Saved query image file is empty or doesn't exist")
            else:
                print(f"✅ Query image processed, saved {processed_query_path.stat().st_size} bytes")
        
        except Exception as e:
            error_msg = f"Query image processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            # Clean up temp file before returning error
            try:
                if query_image_path and query_image_path.exists():
                    query_image_path.unlink()
            except:
                pass
            return jsonify({'error': error_msg}), 500
        
        # Generate request ID for organizing query and results
        from datetime import datetime
        import uuid
        request_id = data.get('request_id') or f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Save processed query image to GCS queries/{user_id}/{request_id}/
        query_saved_path = None
        try:
            # Save processed query image to GCS (with background removed)
            query_saved_path = save_query_to_gcs(user_id, request_id, processed_query_path)
        except Exception as e:
            print(f"⚠️  Warning: Failed to save query image to GCS: {e}")
        
        # Run inference with processed query image (background already removed)
        result = service.inference(
            user_id=user_id,
            query_image_path=str(processed_query_path),
            threshold=threshold,
            wardrobe_k=wardrobe_k,
            catalog_k=catalog_k,
            gender=gender
        )
        
        # Add metadata to result
        result['request_id'] = request_id
        result['query_image_path'] = str(query_saved_path) if query_saved_path else str(query_image_path)
        result['timestamp'] = datetime.now().isoformat()
        
        # Format response for frontend
        formatted_items = []
        for item in result.get('items', []):
            # Handle image path - convert local paths to API URLs
            # Catalog items have image_path like "{product_id}_index1.jpg"
            # Wardrobe items have full paths like "/path/to/wardrobes/user/images/file.jpg"
            image_path = item.get('image_path') or item.get('image_url') or item.get('url', '')
            
            # Convert to API URL if needed
            if image_path and not image_path.startswith('http') and not image_path.startswith('/api/'):
                # Check if it's a wardrobe image (has full path with 'wardrobes' or '/wardrobe/')
                if 'wardrobes' in str(image_path) or '/wardrobe/' in str(image_path):
                    # Extract filename from path
                    filename = Path(image_path).name
                    image_path = f"/api/wardrobe/{user_id}/image/{filename}"
                elif image_path.endswith('.jpg') or image_path.endswith('.png'):
                    # Catalog image - format: "{product_id}_index1.jpg"
                    # These are stored in GCS or local catalog directory
                    # For now, we'll try to construct a URL or use the product URL
                    # If we have a product URL, we could use that as fallback
                    product_url = item.get('url') or item.get('product_url', '')
                    if product_url and product_url.startswith('http'):
                        # Use product URL as image source (many e-commerce sites have image URLs in product pages)
                        # For now, keep image_path as-is and let frontend handle it
                        # Or we could try to extract image from product URL
                        pass
                    # Catalog images might need to be served via a catalog image endpoint
                    # For now, return the image_path and let frontend construct the URL if needed
            
            # Extract category from category string if needed
            category_str = item.get('category', '')
            if isinstance(category_str, str) and ',' in category_str:
                # Category format: "Men, Shoes, Sneakers" - extract main category
                category_parts = [p.strip() for p in category_str.split(',')]
                category = category_parts[1] if len(category_parts) > 1 else category_parts[0]
            else:
                category = category_str or 'Unknown'
            
            formatted_item = {
                'id': item.get('item_id') or item.get('id', ''),
                'image': image_path or '',
                'title': item.get('title') or item.get('name', 'Unknown'),
                'brand': item.get('brand', ''),
                'price': str(item.get('price', '')) if item.get('price') else '',
                'url': item.get('url') or item.get('product_url', ''),
                'category': category,
                'color': item.get('color', 'Unknown'),
                'dateAdded': item.get('dateAdded', datetime.now().timestamp()),
                'similarity': item.get('similarity', 0.0),
                'rank': item.get('rank', 0)
            }
            formatted_items.append(formatted_item)
        
        # Prepare response
        response_data = {
            'success': True,
            'user_id': result.get('user_id'),
            'request_id': request_id,
            'used_wardrobe': result.get('used_wardrobe', False),
            'items': formatted_items,
            'num_results': len(formatted_items),
            'threshold': threshold
        }
        
        # Save results to GCS
        try:
            save_result_to_gcs(user_id, request_id, response_data)
        except Exception as e:
            print(f"⚠️  Warning: Failed to save results to GCS: {e}")
        
        # Clean up temp file (after saving to GCS)
        try:
            if processed_query_path and processed_query_path.exists():
                processed_query_path.unlink()
        except:
            pass
        
        return jsonify(response_data), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/wardrobe/<user_id>', methods=['GET'])
def get_wardrobe(user_id):
    """
    Get user's wardrobe items
    GET /api/wardrobe/<user_id>
    """
    try:
        user_wardrobe_dir = WARDROBES_DIR / user_id
        images_dir = user_wardrobe_dir / 'images'
        
        if not images_dir.exists():
            return jsonify({'items': [], 'user_id': user_id}), 200
        
        # Get all images (only files that actually exist)
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(images_dir.glob(ext))
        
        # Filter to only existing files
        image_files = [f for f in image_files if f.exists() and f.is_file()]
        
        items = []
        for idx, img_path in enumerate(image_files):
            # Try to load metadata from JSON file
            metadata_filename = img_path.stem + '_metadata.json'
            metadata_path = user_wardrobe_dir / metadata_filename
            
            category = 'Unknown'
            color = 'Unknown'
            style = 'Casual'
            
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        category = metadata.get('category', 'Unknown')
                        color = metadata.get('color', 'Unknown')
                        style = metadata.get('style', 'Casual')
                except Exception as e:
                    print(f"⚠️  Failed to load metadata for {img_path.name}: {e}")
            
            items.append({
                'id': f"{user_id}_{idx}",
                'image': f"/api/wardrobe/{user_id}/image/{img_path.name}",
                'filename': img_path.name,  # Store filename for easy deletion
                'category': category,
                'color': color,
                'style': style,
                'dateAdded': img_path.stat().st_mtime
            })
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'items': items,
            'num_items': len(items)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wardrobe/<user_id>/image/<filename>', methods=['GET'])
def get_wardrobe_image(user_id, filename):
    """Serve wardrobe image"""
    try:
        # Secure filename to prevent path traversal
        filename = secure_filename(filename)
        image_path = WARDROBES_DIR / user_id / 'images' / filename
        
        if image_path.exists() and image_path.is_file():
            # Determine mimetype from extension
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            mimetype_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            mimetype = mimetype_map.get(ext, 'image/jpeg')
            return send_file(str(image_path), mimetype=mimetype)
        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wardrobe/<user_id>/item/<path:filename>', methods=['DELETE', 'OPTIONS'])
def delete_wardrobe_item(user_id, filename):
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    """
    Delete a wardrobe item (image and metadata)
    DELETE /api/wardrobe/<user_id>/item/<filename>
    Note: Using <path:filename> to handle filenames with special characters
    """
    try:
        # Decode URL-encoded filename if needed
        from urllib.parse import unquote
        filename = unquote(filename)
        
        # Secure filename to prevent path traversal
        filename = secure_filename(filename)
        
        print(f"🗑️  Attempting to delete item: user_id={user_id}, filename={filename}")
        
        user_wardrobe_dir = WARDROBES_DIR / user_id
        images_dir = user_wardrobe_dir / 'images'
        
        if not images_dir.exists():
            print(f"⚠️  Images directory does not exist: {images_dir}")
            return jsonify({'error': 'Wardrobe directory not found'}), 404
        
        # Image file path
        image_path = images_dir / filename
        
        # Also try with different extensions if original doesn't exist
        possible_paths = [image_path]
        if not image_path.exists():
            # Try common extensions
            base_name = Path(filename).stem
            for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                possible_paths.append(images_dir / f"{base_name}{ext}")
        
        # Find the actual file
        actual_image_path = None
        for path in possible_paths:
            if path.exists() and path.is_file():
                actual_image_path = path
                break
        
        # Metadata file path
        metadata_filename = Path(filename).stem + '_metadata.json'
        metadata_path = user_wardrobe_dir / metadata_filename
        
        deleted_files = []
        
        # Delete image file
        if actual_image_path:
            try:
                actual_image_path.unlink()
                deleted_files.append(f"image: {actual_image_path.name}")
                print(f"✅ Deleted image: {actual_image_path}")
            except Exception as e:
                print(f"⚠️  Failed to delete image {actual_image_path}: {e}")
                return jsonify({'error': f'Failed to delete image: {str(e)}'}), 500
        else:
            print(f"⚠️  Image file not found: {image_path}")
            # List available files for debugging
            available_files = list(images_dir.glob('*'))
            print(f"   Available files in directory: {[f.name for f in available_files[:10]]}")
        
        # Delete metadata file
        if metadata_path.exists() and metadata_path.is_file():
            try:
                metadata_path.unlink()
                deleted_files.append(f"metadata: {metadata_filename}")
                print(f"✅ Deleted metadata: {metadata_path}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to delete metadata {metadata_path}: {e}")
                # Don't fail if metadata deletion fails, image is already deleted
        
        if not deleted_files:
            return jsonify({
                'error': 'Item not found',
                'details': {
                    'requested_filename': filename,
                    'searched_path': str(image_path),
                    'images_dir': str(images_dir)
                }
            }), 404
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'filename': filename,
            'deleted_files': deleted_files,
            'message': 'Item deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Error deleting item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/wardrobe/<user_id>/rebuild', methods=['POST'])
def rebuild_wardrobe_index(user_id):
    """
    Rebuild wardrobe index for a user
    POST /api/wardrobe/<user_id>/rebuild
    """
    try:
        import subprocess
        service, error = get_inference_service()
        
        if service is None:
            return jsonify({
                'error': error or 'Inference service not available',
                'message': 'Cannot rebuild wardrobe index without inference service.'
            }), 503
        
        user_wardrobe_dir = WARDROBES_DIR / user_id
        images_dir = user_wardrobe_dir / 'images'
        
        if not images_dir.exists() or not list(images_dir.glob('*.jpg')):
            return jsonify({'error': 'No images found for user'}), 400
        
        # Build wardrobe index
        result = subprocess.run([
            sys.executable,
            "/app/build_user_wardrobe.py",
            "--user-id", user_id,
            "--wardrobe-dir", str(user_wardrobe_dir),
            "--experiments-dir", str(EXPERIMENTS_DIR),
            "--wardrobes-base-dir", str(WARDROBES_DIR)
        ], capture_output=True, text=True, check=True)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Wardrobe index rebuilt successfully'
        }), 200
        
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Failed to rebuild index: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting StyleMe API Server on port {port}")
    print(f"   Upload folder: {UPLOAD_FOLDER}")
    print(f"   Wardrobes dir: {WARDROBES_DIR}")
    print(f"   Catalog dir: {CATALOG_DIR}")
    print(f"   Experiments dir: {EXPERIMENTS_DIR}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

