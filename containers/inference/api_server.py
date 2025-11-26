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

# Add src to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, project_root)

from inference_service import InferenceService

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/app/uploads')
WARDROBES_DIR = Path(os.getenv('WARDROBES_DIR', '/app/wardrobes'))
CATALOG_DIR = Path(os.getenv('CATALOG_DIR', '/app/catalog'))
EXPERIMENTS_DIR = Path(os.getenv('EXPERIMENTS_DIR', '/app/experiments'))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WARDROBES_DIR, exist_ok=True)

# Initialize inference service (singleton)
inference_service = None
inference_service_error = None

def get_inference_service():
    """Lazy initialization of inference service"""
    global inference_service, inference_service_error
    if inference_service is None and inference_service_error is None:
        # Check if model exists before trying to initialize
        model_found = False
        for exp_dir in sorted(EXPERIMENTS_DIR.glob("exp_*"), reverse=True):
            best_model = exp_dir / "best_model.pth"
            if best_model.exists():
                model_found = True
                break
        
        if not model_found:
            inference_service_error = "No trained model found. Please train a model first."
            return None, inference_service_error
        
        # Model exists, try to initialize service
        # Disable background removal for faster startup (can be enabled later)
        try:
            inference_service = InferenceService(
                catalog_dir=str(CATALOG_DIR),
                experiments_dir=str(EXPERIMENTS_DIR),
                wardrobes_dir=str(WARDROBES_DIR),
                bg_removal_enabled=False  # Disabled for faster startup - can enable if needed
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

def save_image_from_base64(base64_string, output_path):
    """Save base64 encoded image to file"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        image.save(output_path)
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'StyleMe Inference API'})

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """
    Upload an image to user's wardrobe
    POST /api/upload
    Body: {
        "user_id": "string",
        "image": "base64_encoded_image" or multipart/form-data
    }
    """
    try:
        data = request.get_json() if request.is_json else {}
        user_id = data.get('user_id') or request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Create user wardrobe directory
        user_wardrobe_dir = WARDROBES_DIR / user_id / 'images'
        user_wardrobe_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle image upload
        image_path = None
        
        # Try base64 first
        if 'image' in data:
            image_filename = f"{user_id}_{len(list(user_wardrobe_dir.glob('*.jpg')))}.jpg"
            image_path = user_wardrobe_dir / image_filename
            if not save_image_from_base64(data['image'], image_path):
                return jsonify({'error': 'Failed to save image'}), 400
        
        # Try multipart form data
        elif 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_path = user_wardrobe_dir / filename
                file.save(image_path)
        
        if not image_path or not image_path.exists():
            return jsonify({'error': 'No valid image provided'}), 400
        
        # Return success with image info
        return jsonify({
            'success': True,
            'user_id': user_id,
            'image_path': str(image_path),
            'message': 'Image uploaded successfully. Wardrobe index will be rebuilt automatically on next recommendation.'
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
        
        # Run inference
        result = service.inference(
            user_id=user_id,
            query_image_path=str(query_image_path),
            threshold=threshold,
            wardrobe_k=wardrobe_k,
            catalog_k=catalog_k,
            gender=gender
        )
        
        # Clean up temp file
        try:
            query_image_path.unlink()
        except:
            pass
        
        # Format response for frontend
        formatted_items = []
        for item in result.get('items', []):
            # Handle image path - convert local paths to API URLs
            image_path = item.get('image_path') or item.get('image_url') or item.get('url', '')
            if image_path and not image_path.startswith('http'):
                # If it's a local path, check if it's a wardrobe image
                if 'wardrobes' in str(image_path):
                    # Extract filename from path
                    filename = Path(image_path).name
                    image_path = f"/api/wardrobe/{user_id}/image/{filename}"
                elif Path(image_path).exists():
                    # For catalog images, we might need to serve them differently
                    # For now, return the path and let frontend handle it
                    pass
            
            formatted_item = {
                'id': item.get('item_id') or item.get('id', ''),
                'image': image_path,
                'title': item.get('title') or item.get('name', 'Unknown'),
                'brand': item.get('brand', ''),
                'price': item.get('price', ''),
                'url': item.get('url') or item.get('product_url', ''),
                'category': item.get('category', ''),
                'similarity': item.get('similarity', 0.0),
                'rank': item.get('rank', 0)
            }
            formatted_items.append(formatted_item)
        
        return jsonify({
            'success': True,
            'user_id': result.get('user_id'),
            'used_wardrobe': result.get('used_wardrobe', False),
            'items': formatted_items,
            'num_results': len(formatted_items),
            'threshold': threshold
        }), 200
        
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
        
        # Get all images
        image_files = list(images_dir.glob('*.jpg')) + list(images_dir.glob('*.png'))
        
        items = []
        for idx, img_path in enumerate(image_files):
            items.append({
                'id': f"{user_id}_{idx}",
                'image': f"/api/wardrobe/{user_id}/image/{img_path.name}",
                'category': 'Unknown',
                'color': 'Unknown',
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

