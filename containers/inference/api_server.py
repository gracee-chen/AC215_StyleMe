"""
Flask API Server for StyleMe Inference Service
Provides REST API endpoints for frontend to interact with the inference service
"""

import os
import sys
import json
import base64
import time
import random
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io
from datetime import datetime

# Force unbuffered output for logging
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

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
    },
    r"/api/catalog/image/*": {
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
_inference_service_lock = threading.Lock()

def get_inference_service():
    """Lazy initialization of inference service with thread safety"""
    global inference_service, inference_service_error
    
    # Double-check locking pattern to prevent race conditions
    if inference_service is not None:
        return inference_service, None
    
    if inference_service_error is not None:
        return None, inference_service_error
    
    # Acquire lock to prevent concurrent initialization
    with _inference_service_lock:
        # Check again after acquiring lock (another thread might have initialized it)
        if inference_service is not None:
            return inference_service, None
        
        if inference_service_error is not None:
            return None, inference_service_error
        
        # Skip filesystem check in Cloud Run - will use GCS client library
        # The InferenceService will handle GCS access automatically
        
        # Model exists, try to initialize service
        # Background removal is disabled by default
        try:
            print("🔮 Initializing inference service...", flush=True)
            inference_service = InferenceService(
                catalog_dir=str(CATALOG_DIR),
                experiments_dir=str(EXPERIMENTS_DIR),
                wardrobes_dir=str(WARDROBES_DIR),
                bg_removal_enabled=False  # Background removal disabled
            )
            print("✅ Inference service initialized successfully", flush=True)
        except FileNotFoundError as e:
            if "No trained model found" in str(e):
                inference_service_error = "No trained model found. Please train a model first."
            else:
                inference_service_error = str(e)
            print(f"❌ Inference service initialization failed: {inference_service_error}", flush=True)
        except Exception as e:
            inference_service_error = f"Failed to initialize inference service: {str(e)}"
            print(f"❌ Inference service initialization failed: {inference_service_error}", flush=True)
            import traceback
            traceback.print_exc()
    
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
        system_message = """You are a professional fashion expert analyzing clothing items from images. Your task is to accurately identify ONLY the category, color, and style of each item by CAREFULLY EXAMINING THE ACTUAL IMAGE.

OUTPUT FORMAT (JSON only):
{
  "category": "ONE of these exact categories: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'",
  "color": "primary color name (e.g., 'black', 'white', 'blue', 'brown', 'green')",
  "style": "style description (e.g., 'casual', 'formal', 'sporty', 'elegant')"
}

ONLY return these three fields. Do not include any other fields.

═══════════════════════════════════════════════════════════════════
⚠️ CRITICAL: YOU MUST ACTUALLY LOOK AT THE IMAGE ⚠️
═══════════════════════════════════════════════════════════════════

DO NOT DEFAULT TO "white" OR "casual" WITHOUT EXAMINING THE IMAGE!
You MUST identify the ACTUAL color and style visible in the image.

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
COLOR IDENTIFICATION - CRITICAL RULES (READ CAREFULLY):
═══════════════════════════════════════════════════════════════════

⚠️ YOU MUST IDENTIFY THE ACTUAL COLOR IN THE IMAGE - DO NOT DEFAULT TO "white" ⚠️

1. EXAMINE THE IMAGE CAREFULLY:
   ✓ Look at the MAIN GARMENT - what is its dominant color?
   ✓ Is it green? → 'green'
   ✓ Is it brown/tan/beige? → 'brown' or 'beige'
   ✓ Is it red/burgundy/maroon? → 'red'
   ✓ Is it blue/navy? → 'blue' or 'navy'
   ✓ Is it black? → 'black'
   ✓ Is it actually white/cream? → 'white' or 'cream'
   ✓ Is it pink, purple, yellow, orange, gray, khaki? → use that color

2. IGNORE these (they are NOT the main color):
   ✗ Background colors (white backgrounds, colored backgrounds, walls, floors)
   ✗ Inner layers visible through outerwear (white collars, undershirts showing)
   ✗ Small details (buttons, zippers, logos, labels, stitching)
   ✗ Accessories worn with the item (belts, jewelry, bags, shoes)
   ✗ The person's skin color
   ✗ Other clothing items in the image

3. FOCUS ONLY on the OUTERMOST, DOMINANT color of the MAIN garment:
   ✓ Look at the LARGEST VISIBLE AREA of the clothing item
   ✓ If someone is wearing a DARK GREEN sweater → color is 'green' (NOT white!)
   ✓ If someone is wearing a BURGUNDY/RED top → color is 'red' (NOT white!)
   ✓ If someone is wearing a CREAM/BEIGE dress → color is 'beige' or 'cream' (NOT white!)
   ✓ If someone is wearing OLIVE GREEN clothing → color is 'green' (NOT white!)
   ✓ If the item is actually white/ivory → then use 'white' or 'cream'

4. Color mapping rules (be specific):
   • Green shades: olive, forest, sage, emerald, mint, lime, teal, jade, army green → 'green'
   • Brown shades: tan, camel, taupe, chocolate, coffee, caramel, suede, leather, rust → 'brown'
   • Beige shades: nude, sand, cream (light brown/beige tones), tan-beige → 'beige'
   • Red shades: maroon, burgundy, crimson, wine, cherry, dark red, brick red → 'red'
   • Blue shades: navy, dark blue, royal blue → 'navy'; light blue, sky blue, baby blue → 'blue'
   • Gray shades: grey, silver, charcoal → 'gray'
   • White shades: pure white, ivory, snow → 'white'
   • Cream shades: off-white with yellow/beige tint → 'cream'

5. Valid color names (use EXACTLY these - choose the BEST match):
   'black', 'white', 'blue', 'brown', 'green', 'red', 'pink', 'purple', 'yellow', 'orange', 'gray', 'beige', 'navy', 'cream', 'khaki'

6. EXAMPLES OF CORRECT COLOR IDENTIFICATION:
   • Dark olive green top → 'green' (NOT white!)
   • Burgundy/maroon shirt → 'red' (NOT white!)
   • Cream/beige dress → 'beige' or 'cream' (NOT white!)
   • Brown leather jacket → 'brown' (NOT white!)
   • Navy blue blazer → 'navy' (NOT white!)
   • Actually white shirt on white background → 'white' (only if truly white!)

═══════════════════════════════════════════════════════════════════
STYLE IDENTIFICATION - ANALYZE THE ACTUAL STYLE:
═══════════════════════════════════════════════════════════════════

⚠️ YOU MUST IDENTIFY THE ACTUAL STYLE - DO NOT DEFAULT TO "casual" ⚠️

Look at the item and determine its style based on:
✓ Formality: Is it formal (suit, blazer, dress shirt) or casual (t-shirt, jeans)?
✓ Design: Is it elegant (flowing, refined), sporty (athletic, functional), or edgy (bold, unconventional)?
✓ Aesthetic: Is it vintage (retro, classic), modern (contemporary, trendy), or classic (timeless)?
✓ Gender expression: Is it feminine (delicate, soft) or masculine (structured, bold)?
✓ Overall vibe: Is it minimalist (simple, clean), bohemian (free-spirited), or chic (stylish, sophisticated)?

Valid styles: 'casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic'

EXAMPLES:
• T-shirt and jeans → 'casual'
• Business suit → 'formal'
• Athletic wear → 'sporty'
• Flowing evening dress → 'elegant'
• Vintage 70s style → 'vintage'
• Simple, clean lines → 'minimalist'
• Bold, unconventional → 'edgy'
• Delicate, soft fabrics → 'feminine'
• Structured, tailored → 'masculine'
• Stylish, sophisticated → 'chic'

═══════════════════════════════════════════════════════════════════
FINAL REQUIREMENTS:
═══════════════════════════════════════════════════════════════════

✓ ALL THREE fields (category, color, style) MUST be present
✓ Category MUST be exactly one of: 'shirt', 'pants', 'dress', 'jacket', 'shoes', 'accessories'
✓ Color MUST be one of the valid color names listed above - IDENTIFY THE ACTUAL COLOR IN THE IMAGE
✓ Style MUST be one of: 'casual', 'formal', 'sporty', 'elegant', 'bohemian', 'minimalist', 'vintage', 'modern', 'classic', 'edgy', 'feminine', 'masculine', 'chic' - IDENTIFY THE ACTUAL STYLE
✓ NEVER use "miscellaneous", "unknown", "Unknown", "N/A", "n/a", "other", "Other", or any vague terms
✓ Do NOT default to "white" or "casual" - you MUST examine the image and identify the actual color and style
✓ If the item is green, say 'green' - NOT 'white'
✓ If the item is red/burgundy, say 'red' - NOT 'white'
✓ If the item is brown/beige, say 'brown' or 'beige' - NOT 'white'
✓ Analyze the image carefully and follow the priority order for category identification"""
        
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Analyze the clothing item in this image and return ONLY category, color, and style.

⚠️ CRITICAL INSTRUCTIONS - READ CAREFULLY:

1. EXAMINE THE IMAGE: Look carefully at the actual clothing item visible in the image
   - What is the DOMINANT COLOR of the main garment? (NOT the background, NOT inner layers)
   - Is it green, red, brown, beige, blue, black, or actually white?
   - DO NOT default to "white" - identify the ACTUAL color you see

2. CATEGORY: Follow the identification rules in EXACT order:
   - shoes → dress → pants → jacket → shirt → accessories
   - Look at what part of the body the garment covers

3. COLOR: Identify the PRIMARY/MAIN color of the OUTERMOST garment:
   - Ignore: background colors, white backgrounds, inner layers (collars, undershirts), small details
   - Focus: The largest visible area of the main clothing item
   - If you see GREEN → return 'green' (NOT 'white'!)
   - If you see RED/BURGUNDY → return 'red' (NOT 'white'!)
   - If you see BROWN/BEIGE → return 'brown' or 'beige' (NOT 'white'!)
   - Only use 'white' if the item is ACTUALLY white/ivory

4. STYLE: Determine the style based on the item's ACTUAL appearance:
   - Is it formal (suit, blazer)? → 'formal'
   - Is it casual (t-shirt, jeans)? → 'casual'
   - Is it elegant (flowing, refined)? → 'elegant'
   - Is it sporty (athletic wear)? → 'sporty'
   - Look at the design, formality, and aesthetic - DO NOT default to "casual"

5. EXAMINE THE IMAGE CAREFULLY - Do not guess or default. Look at what is actually visible.

Return ONLY a JSON object with these three fields: category, color, style. Make sure the color and style match what you ACTUALLY see in the image."""
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
        # IMPORTANT: Do NOT use 'white' or 'casual' as defaults - these are often wrong!
        # If ChatGPT doesn't return a value, try to infer from the analysis text or use a safer default
        category = analysis.get('category', '')
        color = analysis.get('color', '')
        style = analysis.get('style', '')
        
        # Only use defaults if absolutely necessary, and log a warning
        if not category or category.lower() in ['unknown', 'n/a', '']:
            print(f"⚠️  Warning: ChatGPT didn't return category, using 'shirt' as fallback")
            category = 'shirt'
        if not color or color.lower() in ['unknown', 'n/a', '']:
            print(f"⚠️  Warning: ChatGPT didn't return color, using 'black' as safer fallback (NOT white!)")
            color = 'black'  # Use 'black' instead of 'white' as it's less likely to be wrong
        if not style or style.lower() in ['unknown', 'n/a', '']:
            print(f"⚠️  Warning: ChatGPT didn't return style, using 'modern' as safer fallback (NOT casual!)")
            style = 'modern'  # Use 'modern' instead of 'casual' as it's less likely to be wrong
        
        result = {
            'category': category,
            'color': color,
            'style': style
        }
        
        print(f"📊 Generated tags: category={category}, color={color}, style={style}")
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

def save_wardrobe_image_to_gcs(user_id: str, image_path: Path, metadata_path: Path = None):
    """Save wardrobe image and metadata to GCS wardrobes/{user_id}/images/"""
    from google.cloud import storage
    
    gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
    gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
    
    try:
        client = storage.Client(project=gcp_project_id)
        bucket = client.bucket(gcp_bucket_name)
        
        # Upload image
        image_filename = image_path.name
        image_gcs_path = f"wardrobes/{user_id}/images/{image_filename}"
        image_blob = bucket.blob(image_gcs_path)
        image_blob.upload_from_filename(str(image_path))
        print(f"✅ Saved wardrobe image to gs://{gcp_bucket_name}/{image_gcs_path}")
        
        # Upload metadata if provided
        if metadata_path and metadata_path.exists():
            metadata_filename = metadata_path.name
            metadata_gcs_path = f"wardrobes/{user_id}/{metadata_filename}"
            metadata_blob = bucket.blob(metadata_gcs_path)
            metadata_blob.upload_from_filename(str(metadata_path))
            print(f"✅ Saved wardrobe metadata to gs://{gcp_bucket_name}/{metadata_gcs_path}")
        
        return True
    except Exception as e:
        print(f"⚠️  Failed to save wardrobe image to GCS: {e}")
        # Don't raise - allow local save to continue
        return False

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
        
        # Get metadata if provided - check BOTH JSON body and form data
        metadata = {}
        
        # First, try to get from JSON body (if request is JSON)
        if request.is_json and data.get('metadata'):
            metadata = data.get('metadata', {})
            print(f"📥 Received metadata from JSON body: {metadata}")
        
        # Then, try to get from form data (if request is multipart/form-data)
        # This is the PRIMARY way frontend sends metadata (via FormData)
        print(f"🔍 Checking request.form: {request.form}", flush=True)
        print(f"🔍 Checking request.files: {list(request.files.keys()) if request.files else 'None'}", flush=True)
        print(f"🔍 Content-Type: {request.content_type}", flush=True)
        
        if request.form:
            metadata_str = request.form.get('metadata')
            print(f"🔍 metadata_str from form: {metadata_str}", flush=True)
            print(f"🔍 metadata_str type: {type(metadata_str)}", flush=True)
            if metadata_str:
                try:
                    parsed_metadata = json.loads(metadata_str)
                    # Merge form metadata (takes precedence if both exist)
                    metadata.update(parsed_metadata)
                    print(f"📥 Received metadata from form data: {parsed_metadata}", flush=True)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse metadata JSON from form: {e}")
                    print(f"   Raw metadata string (first 500 chars): {metadata_str[:500] if metadata_str else 'None'}")
                    # Try to extract manually if JSON parsing fails
                    try:
                        # Sometimes the string might have extra quotes or escaping
                        if metadata_str.startswith('"') and metadata_str.endswith('"'):
                            metadata_str = metadata_str[1:-1].replace('\\"', '"')
                        parsed_metadata = json.loads(metadata_str)
                        metadata.update(parsed_metadata)
                        print(f"📥 Successfully parsed after cleanup: {parsed_metadata}")
                    except:
                        print(f"❌ Could not parse metadata even after cleanup")
                except Exception as e:
                    print(f"⚠️  Unexpected error parsing metadata: {e}")
                    print(f"   Raw metadata string (first 500 chars): {metadata_str[:500] if metadata_str else 'None'}")
        
        # Log what metadata we have - DEBUG INFO
        print(f"🔍 DEBUG: Checking metadata...", flush=True)
        print(f"   request.is_json: {request.is_json}", flush=True)
        print(f"   request.form keys: {list(request.form.keys()) if request.form else 'None'}", flush=True)
        print(f"   data keys: {list(data.keys()) if data else 'None'}", flush=True)
        print(f"   metadata dict: {metadata}", flush=True)
        print(f"   metadata type: {type(metadata)}", flush=True)
        print(f"   metadata.get('category'): {metadata.get('category')}", flush=True)
        print(f"   metadata.get('color'): {metadata.get('color')}", flush=True)
        print(f"   metadata.get('style'): {metadata.get('style')}", flush=True)
        
        if metadata and any(metadata.get(k) for k in ['category', 'color', 'style']):
            print(f"📋 Final metadata to use: category={metadata.get('category')}, color={metadata.get('color')}, style={metadata.get('style')}", flush=True)
        else:
            print("⚠️  No valid metadata provided by frontend - will generate with ChatGPT", flush=True)
            print(f"   This means frontend metadata was NOT received properly!", flush=True)
            print(f"   ⚠️  WARNING: This will cause incorrect 'white'/'casual' defaults!", flush=True)
        
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
            
            # Generate final image filename with timestamp to ensure uniqueness
            # Use timestamp + random suffix to prevent overwrites
            timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
            random_suffix = random.randint(1000, 9999)  # 4-digit random number
            image_filename = f"{user_id}_{timestamp}_{random_suffix}.jpg"
            final_image_path = user_wardrobe_dir / image_filename
            
            # Ensure filename doesn't already exist (very unlikely but check anyway)
            counter = 0
            while final_image_path.exists() and counter < 10:
                random_suffix = random.randint(1000, 9999)
                image_filename = f"{user_id}_{timestamp}_{random_suffix}.jpg"
                final_image_path = user_wardrobe_dir / image_filename
                counter += 1
            
            print(f"📁 Generated unique filename: {image_filename}")
            
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
            # Check if we have valid metadata from frontend (frontend already called ChatGPT)
            # Be more lenient - if ANY of the three fields exist and are not empty/Unknown, use it
            has_category = metadata.get('category') and str(metadata.get('category')).strip() not in ['', 'Unknown', 'unknown']
            has_color = metadata.get('color') and str(metadata.get('color')).strip() not in ['', 'Unknown', 'unknown']
            has_style = metadata.get('style') and str(metadata.get('style')).strip() not in ['', 'Unknown', 'unknown']
            
            has_valid_metadata = metadata and (has_category or has_color or has_style)
            
            if has_valid_metadata:
                # User provided metadata - use it (frontend already analyzed with ChatGPT)
                print(f"✅ Using user-provided metadata for {final_image_path.name}")
                print(f"   Category: {metadata.get('category')}, Color: {metadata.get('color')}, Style: {metadata.get('style')}")
                # Use provided values, with safe fallbacks only if completely missing
                metadata_to_save = {
                    'filename': final_image_path.name,
                    'category': metadata.get('category') if has_category else 'shirt',
                    'color': metadata.get('color') if has_color else 'black',  # Use 'black' not 'white' as safer default
                    'style': metadata.get('style') if has_style else 'modern',  # Use 'modern' not 'casual' as safer default
                    'timestamp': datetime.now().isoformat(),
                    'tagged_at': datetime.now().isoformat(),
                    'source': 'user_provided'
                }
                print(f"✅ Saved metadata with source: user_provided")
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
        
        # Upload to GCS if local save succeeded
        try:
            save_wardrobe_image_to_gcs(user_id, final_image_path, metadata_path)
        except Exception as gcs_error:
            print(f"⚠️  Warning: Failed to upload to GCS, but local save succeeded: {gcs_error}")
            # Continue - local save is still valid
        
        # Invalidate wardrobe index so it gets rebuilt on next search
        # This ensures new items are included in recommendations
        try:
            wardrobe_index_path = WARDROBES_DIR / user_id / "wardrobe.index.faiss"
            if wardrobe_index_path.exists():
                print(f"🗑️  Removing stale wardrobe index to trigger rebuild on next search")
                # Remove index files so they get rebuilt
                for index_file in ['wardrobe.index.faiss', 'wardrobe.parquet', 'idmap.npy', 'wardrobe.vecs.npy']:
                    index_path = WARDROBES_DIR / user_id / index_file
                    if index_path.exists():
                        index_path.unlink()
        except Exception as index_error:
            print(f"⚠️  Warning: Failed to invalidate wardrobe index: {index_error}")
            # Continue - index will be rebuilt on next search anyway
        
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
        query_category = data.get('query_category') or request.form.get('query_category')  # Category of query item (e.g., "Tops", "Pants")
        
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
            gender=gender,
            query_category=query_category  # Pass query category to filter out same-category items
        )
        
        # Add metadata to result
        result['request_id'] = request_id
        result['query_image_path'] = str(query_saved_path) if query_saved_path else str(query_image_path)
        result['timestamp'] = datetime.now().isoformat()
        
        # Helper function to format items
        def format_item(item, is_wardrobe=False):
            # Handle image path - convert local paths to API URLs
            # Catalog items have image_path like "{product_id}_index1.jpg"
            # Wardrobe items have img_path (from parquet) or image_path
            image_path = item.get('image_path') or item.get('img_path') or item.get('image_url') or item.get('url', '')
            
            # Convert to API URL if needed
            if image_path and not image_path.startswith('http') and not image_path.startswith('/api/'):
                # Check if it's a wardrobe image (has full path with 'wardrobes' or '/wardrobe/' or is_wardrobe flag)
                if 'wardrobes' in str(image_path) or '/wardrobe/' in str(image_path) or is_wardrobe:
                    # Extract filename from path
                    # img_path might be like "wardrobes/user/images/file.jpg" or just "file.jpg"
                    filename = Path(image_path).name
                    image_path = f"/api/wardrobe/{user_id}/image/{filename}"
                elif image_path.endswith('.jpg') or image_path.endswith('.png') or image_path.endswith('.jpeg'):
                    # Catalog image - format: "{product_id}_index1.jpg"
                    # These are stored in gs://styleme-data-bucket/images/
                    # Serve via API endpoint
                    filename = Path(image_path).name
                    image_path = f"/api/catalog/image/{filename}"
            elif is_wardrobe and not image_path:
                # Fallback: try to get filename from item_id or filename field
                filename = item.get('filename') or f"{item.get('item_id', 'unknown')}.jpg"
                image_path = f"/api/wardrobe/{user_id}/image/{filename}"
            
            # Extract category from category string if needed
            category_str = item.get('category', '')
            if isinstance(category_str, str) and ',' in category_str:
                # Category format: "Men, Shoes, Sneakers" - extract main category
                category_parts = [p.strip() for p in category_str.split(',')]
                category = category_parts[1] if len(category_parts) > 1 else category_parts[0]
            else:
                category = category_str or 'Unknown'
            
            # Format price - normalize inconsistent formats
            price_raw = item.get('price', '')
            price_formatted = ''
            if price_raw:
                price_str = str(price_raw).strip()
                # Handle different price formats:
                # - "R$ 3.916" -> "R$ 3,916" (Brazilian Real: period = thousand separator)
                # - "$230" -> "$230" (US Dollar)
                # - "£150" -> "£150" (British Pound)
                # - "3.916" -> "3,916" (number with period as thousand separator)
                
                # Extract currency symbol if present
                currency_symbol = ''
                number_part = price_str
                for symbol in ['R$', '$', '£', '€', '¥', '₹']:
                    if price_str.startswith(symbol):
                        currency_symbol = symbol
                        number_part = price_str[len(symbol):].strip()
                        break
                
                # Check if number part has period as thousand separator
                if '.' in number_part:
                    parts = number_part.split('.')
                    if len(parts) == 2:
                        decimal_part = parts[1].strip()
                        # If decimal part is exactly 3 digits, it's likely a thousand separator
                        # (e.g., "3.916" = 3916, not "3.91" = 3.91)
                        if len(decimal_part) == 3 and decimal_part.isdigit():
                            # Convert period to comma for thousand separator
                            number_part = number_part.replace('.', ',')
                        # Otherwise keep as decimal (e.g., "3.50")
                
                # Reconstruct price with currency symbol
                if currency_symbol:
                    price_formatted = f"{currency_symbol} {number_part}".strip()
                else:
                    price_formatted = number_part
            
            return {
                'id': item.get('item_id') or item.get('id', ''),
                'image': image_path or '',
                'title': item.get('title') or item.get('name', 'Unknown'),
                'brand': item.get('brand', ''),
                'price': '',  # Remove price display - no longer shown in UI
                'url': item.get('url') or item.get('product_url', ''),
                'category': category,
                'color': item.get('color', 'Unknown'),
                'dateAdded': item.get('dateAdded', datetime.now().timestamp()),
                'similarity': item.get('similarity', 0.0),
                'rank': item.get('rank', 0)
            }
        
        # Format wardrobe items
        formatted_wardrobe_items = []
        for item in result.get('wardrobe_items', []):
            formatted_wardrobe_items.append(format_item(item, is_wardrobe=True))
        
        # Format catalog items
        formatted_catalog_items = []
        for item in result.get('catalog_items', []):
            formatted_catalog_items.append(format_item(item, is_wardrobe=False))
        
        # Prepare response with BOTH arrays
        response_data = {
            'success': True,
            'user_id': result.get('user_id'),
            'request_id': request_id,
            'threshold': threshold,
            'wardrobe_items': formatted_wardrobe_items,
            'catalog_items': formatted_catalog_items,
            'wardrobe_count': len(formatted_wardrobe_items),
            'catalog_count': len(formatted_catalog_items),
            'wardrobe_reason': result.get('wardrobe_reason'),
            'catalog_reason': result.get('catalog_reason'),
            # For backward compatibility
            'used_wardrobe': result.get('used_wardrobe', False),
            'items': formatted_wardrobe_items if len(formatted_wardrobe_items) > 0 else formatted_catalog_items,
            'num_results': len(formatted_wardrobe_items) + len(formatted_catalog_items)
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
    Reads from local filesystem first, falls back to GCS if local files don't exist
    """
    try:
        user_wardrobe_dir = WARDROBES_DIR / user_id
        images_dir = user_wardrobe_dir / 'images'
        
        items = []
        
        # Try local filesystem first
        if images_dir.exists():
            # Get all images (only files that actually exist)
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                image_files.extend(images_dir.glob(ext))
            
            # Filter to only existing files
            image_files = [f for f in image_files if f.exists() and f.is_file()]
            
            if image_files:
                # Sort by modification time (newest first) to ensure consistent ordering
                image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                print(f"📂 Found {len(image_files)} images locally for user {user_id}")
                
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
        
        # Always check GCS to merge with local items (local might be incomplete after container restart)
        # This ensures we get ALL items from GCS, not just local ones
        print(f"📂 Checking GCS for user {user_id} to merge with local items...")
        try:
            from google.cloud import storage
            
            gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
            gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
            
            client = storage.Client(project=gcp_project_id)
            bucket = client.bucket(gcp_bucket_name)
            
            # List images in GCS
            prefix = f"wardrobes/{user_id}/images/"
            image_blobs = list(bucket.list_blobs(prefix=prefix))
            
            # Filter to image files only
            image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
            image_blobs = [b for b in image_blobs if any(b.name.lower().endswith(ext) for ext in image_extensions)]
            
            # Track filenames we already have from local filesystem
            local_filenames = {item.get('filename', '') for item in items}
            
            if image_blobs:
                print(f"📂 Found {len(image_blobs)} images in GCS for user {user_id}")
                
                # Sort by time created (newest first)
                image_blobs.sort(key=lambda b: b.time_created, reverse=True)
                
                gcs_items_added = 0
                for blob in image_blobs:
                    filename = blob.name.split('/')[-1]
                    
                    # Skip if we already have this file from local filesystem
                    if filename in local_filenames:
                        continue
                    
                    # Try to load metadata from GCS
                    metadata_filename = Path(filename).stem + '_metadata.json'
                    metadata_blob_path = f"wardrobes/{user_id}/{metadata_filename}"
                    metadata_blob = bucket.blob(metadata_blob_path)
                    
                    category = 'Unknown'
                    color = 'Unknown'
                    style = 'Casual'
                    
                    if metadata_blob.exists():
                        try:
                            metadata_json = metadata_blob.download_as_text()
                            metadata = json.loads(metadata_json)
                            category = metadata.get('category', 'Unknown')
                            color = metadata.get('color', 'Unknown')
                            style = metadata.get('style', 'Casual')
                        except Exception as e:
                            print(f"⚠️  Failed to load metadata from GCS for {filename}: {e}")
                    
                    # Use blob time_created as dateAdded (convert to timestamp)
                    date_added = blob.time_created.timestamp() if blob.time_created else 0
                    
                    items.append({
                        'id': f"{user_id}_{len(items)}",  # Use current length as index
                        'image': f"/api/wardrobe/{user_id}/image/{filename}",
                        'filename': filename,
                        'category': category,
                        'color': color,
                        'style': style,
                        'dateAdded': date_added
                    })
                    gcs_items_added += 1
                
                if gcs_items_added > 0:
                    print(f"✅ Added {gcs_items_added} items from GCS (total: {len(items)} items)")
            else:
                print(f"📂 No images found in GCS for user {user_id}")
        except Exception as gcs_error:
            print(f"⚠️  Failed to load wardrobe from GCS: {gcs_error}")
            # Continue with local items if GCS fails
        
        # Sort all items by dateAdded (newest first) after merging local and GCS
        items.sort(key=lambda x: x.get('dateAdded', 0), reverse=True)
        
        # Reassign IDs after sorting to ensure consistent ordering
        for idx, item in enumerate(items):
            item['id'] = f"{user_id}_{idx}"
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'items': items,
            'num_items': len(items)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/image/<filename>', methods=['GET'])
def get_catalog_image(filename):
    """Serve catalog image from GCS bucket styleme-data-bucket/images/"""
    try:
        # Secure filename to prevent path traversal
        filename = secure_filename(filename)
        
        # Images are stored in gs://styleme-data-bucket/images/{filename}
        gcp_bucket_name = os.getenv('GCP_BUCKET_NAME', 'styleme-data-bucket')
        gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
        
        try:
            from google.cloud import storage
            client = storage.Client(project=gcp_project_id)
            bucket = client.bucket(gcp_bucket_name)
            
            # Try index1 first, then index2, then without index
            possible_filenames = [filename]
            if '_index1.' in filename:
                possible_filenames.append(filename.replace('_index1.', '_index2.'))
                possible_filenames.append(filename.replace('_index1.', '.'))
            elif '_index2.' in filename:
                possible_filenames.append(filename.replace('_index2.', '_index1.'))
                possible_filenames.append(filename.replace('_index2.', '.'))
            
            image_blob = None
            for possible_filename in possible_filenames:
                blob_path = f"images/{possible_filename}"
                blob = bucket.blob(blob_path)
                if blob.exists():
                    image_blob = blob
                    break
            
            if image_blob:
                # Download image to memory
                image_data = image_blob.download_as_bytes()
                
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
                
                return send_file(io.BytesIO(image_data), mimetype=mimetype)
            else:
                return jsonify({'error': f'Image not found in GCS: {filename}'}), 404
        except Exception as gcs_error:
            print(f"⚠️  Error loading image from GCS: {gcs_error}")
            return jsonify({'error': f'Failed to load image from GCS: {str(gcs_error)}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wardrobe/<user_id>/image/<filename>', methods=['GET'])
def get_wardrobe_image(user_id, filename):
    """Serve wardrobe image - tries local first, then GCS"""
    try:
        # Secure filename to prevent path traversal
        filename = secure_filename(filename)
        image_path = WARDROBES_DIR / user_id / 'images' / filename
        
        # Try local filesystem first
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
        
        # If not found locally, try GCS
        print(f"📂 Image not found locally, checking GCS for {filename}...")
        try:
            from google.cloud import storage
            import tempfile
            
            gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
            gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
            
            client = storage.Client(project=gcp_project_id)
            bucket = client.bucket(gcp_bucket_name)
            
            # Try to get image from GCS
            blob_path = f"wardrobes/{user_id}/images/{filename}"
            blob = bucket.blob(blob_path)
            
            if blob.exists():
                # Download to temp file and serve
                temp_dir = Path(tempfile.gettempdir()) / "styleme_wardrobe_images"
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / filename
                
                blob.download_to_filename(str(temp_path))
                
                # Determine mimetype
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                mimetype_map = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'webp': 'image/webp'
                }
                mimetype = mimetype_map.get(ext, 'image/jpeg')
                
                return send_file(str(temp_path), mimetype=mimetype)
            else:
                return jsonify({'error': 'Image not found in GCS'}), 404
        except Exception as gcs_error:
            print(f"⚠️  Failed to load image from GCS: {gcs_error}")
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
        
        # Note: Local directory might not exist if using GCS-only storage
        # We'll still try to delete from local if it exists, and always try GCS
        
        # Image file path
        image_path = images_dir / filename
        
        # Also try with different extensions if original doesn't exist
        possible_paths = [image_path]
        if not image_path.exists():
            # Try common extensions
            base_name = Path(filename).stem
            for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                possible_paths.append(images_dir / f"{base_name}{ext}")
        
        # Find the actual file (only if local directory exists)
        actual_image_path = None
        if images_dir.exists():
            for path in possible_paths:
                if path.exists() and path.is_file():
                    actual_image_path = path
                    break
        
        # Metadata file path
        metadata_filename = Path(filename).stem + '_metadata.json'
        metadata_path = user_wardrobe_dir / metadata_filename
        
        deleted_files = []
        
        # Delete image file from local storage (if exists)
        if actual_image_path:
            try:
                actual_image_path.unlink()
                deleted_files.append(f"local image: {actual_image_path.name}")
                print(f"✅ Deleted local image: {actual_image_path}")
            except Exception as e:
                print(f"⚠️  Failed to delete local image {actual_image_path}: {e}")
                # Continue - will try GCS deletion
        elif images_dir.exists():
            print(f"⚠️  Local image file not found: {image_path}")
            # List available files for debugging
            available_files = list(images_dir.glob('*'))
            print(f"   Available files in directory: {[f.name for f in available_files[:10]]}")
        else:
            print(f"ℹ️  Local wardrobe directory does not exist (using GCS-only storage)")
        
        # Delete metadata file from local storage (if exists)
        if metadata_path.exists() and metadata_path.is_file():
            try:
                metadata_path.unlink()
                deleted_files.append(f"local metadata: {metadata_filename}")
                print(f"✅ Deleted local metadata: {metadata_path}")
            except Exception as e:
                print(f"⚠️  Warning: Failed to delete local metadata {metadata_path}: {e}")
                # Don't fail if metadata deletion fails
        
        # Also delete from GCS
        try:
            from google.cloud import storage
            
            gcp_bucket_name = os.getenv('GCS_BUCKET', 'styleme-production')
            gcp_project_id = os.getenv('GCP_PROJECT_ID', 'styleme-475201')
            
            client = storage.Client(project=gcp_project_id)
            bucket = client.bucket(gcp_bucket_name)
            
            # Delete image from GCS
            image_gcs_path = f"wardrobes/{user_id}/images/{filename}"
            image_blob = bucket.blob(image_gcs_path)
            if image_blob.exists():
                image_blob.delete()
                deleted_files.append(f"GCS image: {image_gcs_path}")
                print(f"✅ Deleted image from GCS: {image_gcs_path}")
            else:
                print(f"⚠️  Image not found in GCS: {image_gcs_path}")
            
            # Delete metadata from GCS
            metadata_gcs_path = f"wardrobes/{user_id}/{metadata_filename}"
            metadata_blob = bucket.blob(metadata_gcs_path)
            if metadata_blob.exists():
                metadata_blob.delete()
                deleted_files.append(f"GCS metadata: {metadata_gcs_path}")
                print(f"✅ Deleted metadata from GCS: {metadata_gcs_path}")
            
            # Invalidate wardrobe index so it gets rebuilt on next search
            # This ensures deleted items are removed from recommendations
            try:
                index_files = ['wardrobe.index.faiss', 'wardrobe.parquet', 'idmap.npy', 'wardrobe.vecs.npy']
                for index_file in index_files:
                    index_gcs_path = f"wardrobes/{user_id}/{index_file}"
                    index_blob = bucket.blob(index_gcs_path)
                    if index_blob.exists():
                        index_blob.delete()
                        print(f"🗑️  Deleted wardrobe index file from GCS: {index_file} (will be rebuilt on next search)")
            except Exception as index_error:
                print(f"⚠️  Warning: Failed to invalidate wardrobe index in GCS: {index_error}")
                # Continue - index will be rebuilt on next search anyway
                
        except Exception as gcs_error:
            print(f"⚠️  Warning: Failed to delete from GCS: {gcs_error}")
            # Don't fail the request if GCS deletion fails - local deletion succeeded
            # But log it so we know there's a sync issue
        
        # If nothing was deleted (neither local nor GCS), return 404
        if not deleted_files:
            return jsonify({
                'error': 'Item not found',
                'details': {
                    'requested_filename': filename,
                    'searched_path': str(image_path) if images_dir.exists() else 'N/A (GCS-only)',
                    'images_dir': str(images_dir) if images_dir.exists() else 'N/A (GCS-only)'
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

