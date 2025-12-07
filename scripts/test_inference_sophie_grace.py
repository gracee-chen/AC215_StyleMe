#!/usr/bin/env python3
"""
Test Inference for sophie (with wardrobe) and grace (without wardrobe)
"""

import os
import sys
import json
import base64
import subprocess
from pathlib import Path
import requests

SERVICE_URL = os.getenv('SERVICE_URL', 'https://styleme-inference-nty2g5pcpa-uc.a.run.app')

def download_from_gcs(gcs_path, local_path):
    """Download file from GCS"""
    print(f"📥 Downloading {gcs_path}...")
    result = subprocess.run(
        ['gsutil', 'cp', gcs_path, str(local_path)],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"❌ Failed to download: {result.stderr}")
        return False
    print(f"✅ Downloaded to {local_path}")
    return True

def encode_image_to_base64(image_path):
    """Encode image to base64"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')

def test_inference(user_id, image_path, expected_wardrobe_use):
    """Test inference for a user"""
    print(f"\n{'='*70}")
    print(f"TEST: {user_id} ({'WITH' if expected_wardrobe_use else 'WITHOUT'} wardrobe)")
    print(f"{'='*70}\n")
    
    # Download query image
    temp_dir = Path('/tmp')
    local_image = temp_dir / f"{user_id}_query.jpg"
    
    if not download_from_gcs(image_path, local_image):
        print(f"❌ Failed to download query image for {user_id}")
        return False
    
    if not local_image.exists():
        print(f"❌ Image file not found: {local_image}")
        return False
    
    # Encode image
    print(f"📤 Encoding image to base64...")
    image_b64 = encode_image_to_base64(local_image)
    image_size_mb = len(image_b64) / (1024 * 1024)
    print(f"   Image size: {image_size_mb:.2f} MB (base64)")
    
    # Prepare request
    from datetime import datetime
    import uuid
    request_id = f"{user_id}_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    payload = {
        "user_id": user_id,
        "image": f"data:image/jpeg;base64,{image_b64}",
        "threshold": 0.3,
        "wardrobe_k": 5,
        "catalog_k": 3,
        "gender": "women",
        "request_id": request_id
    }
    
    # Send request
    print(f"📤 Sending inference request...")
    print(f"   Request ID: {request_id}")
    
    try:
        response = requests.post(
            f"{SERVICE_URL}/api/recommend",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout
        )
        
        response_time = response.elapsed.total_seconds()
        print(f"   ⏱️  Response time: {response_time:.2f}s")
        print(f"   HTTP Status: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"❌ Request failed:")
            print(json.dumps(response.json(), indent=2))
            return False
        
        result = response.json()
        
        # Print results
        print("✅ SUCCESS! Recommendations received:\n")
        print(json.dumps(result, indent=2))
        
        # Check results
        used_wardrobe = result.get('used_wardrobe', False)
        num_results = result.get('num_results', 0)
        
        print(f"\n📊 Summary:")
        print(f"   - Used wardrobe: {used_wardrobe}")
        print(f"   - Number of results: {num_results}")
        
        # Verify expected behavior
        if expected_wardrobe_use:
            if used_wardrobe:
                print(f"   ✅ CORRECT: {user_id}'s wardrobe was used!")
            else:
                print(f"   ⚠️  Expected wardrobe to be used for {user_id}")
        else:
            if not used_wardrobe:
                print(f"   ✅ CORRECT: catalog was used for {user_id} (no wardrobe)")
            else:
                print(f"   ⚠️  Expected catalog to be used for {user_id} (no wardrobe)")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if local_image.exists():
            local_image.unlink()

def main():
    print("🧪 Testing Inference for sophie and grace")
    print("=" * 70)
    print(f"Service URL: {SERVICE_URL}\n")
    
    # Test sophie (with wardrobe)
    sophie_success = test_inference(
        user_id="sophie",
        image_path="gs://styleme-production/queries/sophie/sophie_query_01/cloth_02555.jpg",
        expected_wardrobe_use=True
    )
    
    # Test grace (without wardrobe)
    grace_success = test_inference(
        user_id="grace",
        image_path="gs://styleme-production/queries/grace/grace_query_01/cloth_00150.jpg",
        expected_wardrobe_use=False
    )
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"sophie (with wardrobe): {'✅ PASS' if sophie_success else '❌ FAIL'}")
    print(f"grace (without wardrobe): {'✅ PASS' if grace_success else '❌ FAIL'}")
    print()
    
    print("📋 Check GCS for saved results:")
    print("  gsutil ls -r gs://styleme-production/results/")
    print("  gsutil ls -r gs://styleme-production/queries/")
    
    return 0 if (sophie_success and grace_success) else 1

if __name__ == '__main__':
    sys.exit(main())

