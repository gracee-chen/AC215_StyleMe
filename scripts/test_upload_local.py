#!/usr/bin/env python3
"""
Test wardrobe upload endpoint locally
Tests the async wardrobe rebuild functionality
"""

import sys
import json
import base64
import argparse
import requests
from pathlib import Path
import time

def test_upload(api_url, user_id, image_path):
    """Test upload endpoint and watch for async rebuild"""
    print(f"🧪 Testing wardrobe upload with async rebuild")
    print("=" * 60)
    print(f"API URL: {api_url}")
    print(f"User ID: {user_id}")
    print(f"Image: {image_path}")
    print()
    
    # Check if image exists
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return False
    
    # Read and encode image
    print("📤 Encoding image to base64...")
    with open(image_path, 'rb') as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Prepare request
    payload = {
        "user_id": user_id,
        "image": f"data:image/jpeg;base64,{image_base64}",
        "metadata": {
            "category": "Tops",
            "color": "Blue",
            "style": "Casual"
        }
    }
    
    print("📤 Uploading image (this should return immediately)...")
    print("   Watch the API server logs for async rebuild messages")
    print()
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{api_url}/api/upload",
            json=payload,
            timeout=30
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Upload response time: {elapsed:.2f}s")
        print(f"📊 HTTP Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(json.dumps(result, indent=2))
            print()
            print("🔍 Next steps:")
            print("   1. Check API server logs for async rebuild messages:")
            print("      - Look for '🚀 Triggered async wardrobe index rebuild'")
            print("      - Look for '🔨 Starting async wardrobe index rebuild'")
            print("      - Look for '🎉 Wardrobe index rebuild completed'")
            print()
            print("   2. Wait 30-60 seconds for rebuild to complete")
            print()
            print("   3. Verify index files in GCS:")
            print(f"      gsutil ls gs://styleme-production/wardrobes/{user_id}/")
            print()
            print("   4. Test recommendations (should be fast now):")
            print(f"      python3 scripts/test_inference_api.py \\")
            print(f"        --url {api_url} \\")
            print(f"        --user-id {user_id} \\")
            print(f"        --image {image_path}")
            return True
        else:
            print(f"❌ Upload failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 30s")
        print("   This might indicate the service is not running")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {api_url}")
        print("   Make sure the API server is running:")
        print("   docker-compose --profile api up inference")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Test wardrobe upload with async rebuild')
    parser.add_argument('--url', default='http://localhost:5001',
                       help='API server URL (default: http://localhost:5001)')
    parser.add_argument('--user-id', default='test_user_001',
                       help='User ID for testing')
    parser.add_argument('--image', required=True,
                       help='Path to image file to upload')
    
    args = parser.parse_args()
    
    success = test_upload(args.url, args.user_id, args.image)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

