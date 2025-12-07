#!/usr/bin/env python3
"""
Test Inference API on Cloud Run
More detailed Python version with better error handling
"""

import sys
import json
import base64
import argparse
import requests
from pathlib import Path
from google.cloud import storage
import time

def download_test_image(bucket_name="styleme-data-bucket", prefix="images/"):
    """Download a random test image from GCS"""
    print(f"📥 Downloading test image from gs://{bucket_name}/{prefix}...")
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # List images (filter for .jpg files only)
    blobs = [b for b in bucket.list_blobs(prefix=prefix, max_results=20) 
             if b.name.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not blobs:
        return None
    
    # Get first image
    blob = blobs[0]
    local_path = Path("/tmp") / blob.name.split("/")[-1]
    
    print(f"   Downloading: {blob.name}")
    blob.download_to_filename(local_path)
    print(f"   ✅ Saved to: {local_path}")
    
    return local_path

def test_health(service_url):
    """Test health endpoint"""
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{service_url}/health", timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_inference(service_url, user_id, image_path, threshold=0.3, gender=None):
    """Test inference endpoint"""
    print(f"\n2. Testing inference endpoint...")
    print(f"   Image: {image_path}")
    print(f"   User ID: {user_id}")
    print(f"   Threshold: {threshold}")
    
    # Read and encode image
    print("   Encoding image to base64...")
    with open(image_path, 'rb') as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Prepare request
    payload = {
        "user_id": user_id,
        "image": f"data:image/jpeg;base64,{image_base64}",
        "threshold": threshold,
        "wardrobe_k": 5,
        "catalog_k": 3
    }
    
    if gender:
        payload["gender"] = gender
    
    print("   Sending request (this may take 30-60s on first request)...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{service_url}/api/recommend",
            json=payload,
            timeout=120  # Allow time for model/catalog loading
        )
        
        elapsed = time.time() - start_time
        print(f"   ⏱️  Response time: {elapsed:.2f}s")
        print(f"   HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! Recommendations received:\n")
            print(json.dumps(result, indent=2))
            
            # Summary
            print("\n📊 Summary:")
            print(f"   - Number of results: {result.get('num_results', 0)}")
            print(f"   - Used wardrobe: {result.get('used_wardrobe', False)}")
            print(f"   - Items returned: {len(result.get('items', []))}")
            
            # Show first few items
            items = result.get('items', [])
            if items:
                print("\n📦 Top Recommendations:")
                for i, item in enumerate(items[:3], 1):
                    print(f"\n   {i}. {item.get('title', 'Unknown')}")
                    print(f"      Similarity: {item.get('similarity', 0):.3f}")
                    if item.get('brand'):
                        print(f"      Brand: {item.get('brand')}")
                    if item.get('price'):
                        print(f"      Price: {item.get('price')}")
            
            return True
            
        elif response.status_code == 503:
            print("\n⚠️  Service Unavailable")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                print(f"   Message: {error_data.get('message', '')}")
                print(f"   Hint: {error_data.get('hint', '')}")
            except:
                print(f"   Response: {response.text}")
            print("\n💡 The service may still be loading the model/catalog.")
            print("   First request can take 30-60 seconds. Try again in a moment.")
            return False
            
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 120s")
        print("   This might indicate the service is loading model/catalog.")
        print("   Try again in a moment.")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Test StyleMe Inference API')
    parser.add_argument('--url', default='https://styleme-inference-nty2g5pcpa-uc.a.run.app',
                       help='Service URL')
    parser.add_argument('--user-id', default='test_user_001',
                       help='User ID for testing')
    parser.add_argument('--image', type=str,
                       help='Path to query image (optional, will download from GCS if not provided)')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='Similarity threshold')
    parser.add_argument('--gender', choices=['men', 'women'],
                       help='Gender filter')
    
    args = parser.parse_args()
    
    print("🧪 Testing StyleMe Inference API")
    print("=" * 50)
    print(f"Service URL: {args.url}")
    print()
    
    # Test health
    if not test_health(args.url):
        print("\n❌ Health check failed. Service may not be available.")
        sys.exit(1)
    
    # Get test image
    image_path = args.image
    if not image_path:
        image_path = download_test_image()
        if not image_path:
            print("\n❌ Could not download test image. Please provide one with --image")
            sys.exit(1)
    elif not Path(image_path).exists():
        print(f"\n❌ Image not found: {image_path}")
        sys.exit(1)
    
    # Test inference
    success = test_inference(
        args.url,
        args.user_id,
        image_path,
        args.threshold,
        args.gender
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

