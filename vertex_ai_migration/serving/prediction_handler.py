"""
Vertex AI Prediction Handler
Handles prediction requests from Vertex AI Endpoints
"""

import os
import json
import base64
import tempfile
from typing import Any, Dict, List
from pathlib import Path

# Import inference service
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "containers" / "inference"))

from inference_service import InferenceService


class PredictionHandler:
    """
    Handler for Vertex AI prediction requests
    """
    
    def __init__(self):
        """Initialize the prediction handler"""
        # Get paths from environment variables (set by Vertex AI)
        catalog_dir = os.environ.get('CATALOG_DIR', '/gcs/catalog')
        experiments_dir = os.environ.get('EXPERIMENTS_DIR', '/gcs/models')
        wardrobes_dir = os.environ.get('WARDROBES_DIR', '/gcs/wardrobes')
        
        print(f"Initializing PredictionHandler...")
        print(f"  Catalog Dir: {catalog_dir}")
        print(f"  Experiments Dir: {experiments_dir}")
        print(f"  Wardrobes Dir: {wardrobes_dir}")
        
        # Initialize inference service
        self.service = InferenceService(
            catalog_dir=catalog_dir,
            experiments_dir=experiments_dir,
            wardrobes_dir=wardrobes_dir
        )
        
        print("✅ PredictionHandler initialized")
    
    def predict(self, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Handle prediction requests from Vertex AI
        
        Expected input format:
        {
            "user_id": "user_001",
            "image_bytes": "<base64_encoded_image>",  # OR
            "image_path": "gs://bucket/path/to/image.jpg",
            "threshold": 0.7,
            "wardrobe_k": 5,
            "catalog_k": 3,
            "gender": "men"  # optional
        }
        
        Returns:
            List of prediction results
        """
        predictions = []
        
        for instance in instances:
            try:
                # Handle image input
                image_path = None
                
                if 'image_bytes' in instance:
                    # Decode base64 image
                    image_data = base64.b64decode(instance['image_bytes'])
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(image_data)
                        image_path = tmp_file.name
                
                elif 'image_path' in instance:
                    image_path = instance['image_path']
                    
                    # If GCS path, download to temp file
                    if image_path.startswith('gs://'):
                        from google.cloud import storage
                        
                        # Parse GCS path
                        bucket_name = image_path.split('/')[2]
                        blob_path = '/'.join(image_path.split('/')[3:])
                        
                        # Download to temp file
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(bucket_name)
                        blob = bucket.blob(blob_path)
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                            blob.download_to_file(tmp_file)
                            image_path = tmp_file.name
                
                else:
                    raise ValueError("Either 'image_bytes' or 'image_path' required in instance")
                
                # Extract parameters
                user_id = instance.get('user_id', 'default')
                threshold = instance.get('threshold', 0.7)
                wardrobe_k = instance.get('wardrobe_k', 5)
                catalog_k = instance.get('catalog_k', 3)
                gender = instance.get('gender')
                
                # Run inference
                result = self.service.inference(
                    user_id=user_id,
                    query_image_path=image_path,
                    threshold=threshold,
                    wardrobe_k=wardrobe_k,
                    catalog_k=catalog_k,
                    gender=gender
                )
                
                predictions.append(result)
                
            except Exception as e:
                # Return error in prediction result
                predictions.append({
                    "error": str(e),
                    "user_id": instance.get('user_id', 'unknown')
                })
        
        return predictions


def handler(request):
    """
    Cloud Function / Vertex AI Endpoint handler
    
    Args:
        request: HTTP request object or dict
        
    Returns:
        Prediction results
    """
    # Handle different request formats
    if hasattr(request, 'get_json'):
        # Flask request
        data = request.get_json()
    elif isinstance(request, dict):
        # Direct dict
        data = request
    else:
        data = request
    
    # Extract instances
    instances = data.get('instances', [])
    if not instances:
        # Single instance format
        instances = [data]
    
    # Initialize handler (singleton pattern could be used here)
    handler = PredictionHandler()
    
    # Get predictions
    predictions = handler.predict(instances)
    
    return {"predictions": predictions}


# For Vertex AI custom prediction
if __name__ == "__main__":
    # Read from stdin (Vertex AI format)
    import sys
    
    input_data = json.load(sys.stdin)
    instances = input_data.get('instances', [])
    
    handler = PredictionHandler()
    predictions = handler.predict(instances)
    
    output = {"predictions": predictions}
    print(json.dumps(output))

