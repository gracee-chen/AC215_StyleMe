#!/usr/bin/env python3
"""
Test script for StyleMe API
Tests all endpoints to verify the API is working correctly
"""

import requests
import json
import base64
import sys
from pathlib import Path

import os
API_BASE_URL = os.getenv("API_URL", "http://localhost:5000")
TEST_USER_ID = "test_user"

def test_health():
    """Test health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the server running?")
        print(f"   Try: docker-compose --profile api up inference")
        print(f"   Or check if port 5000 is available (macOS AirPlay may use it)")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def create_test_image_base64():
    """Create a test image as base64 - use real image if available"""
    # Try to use a real test image first
    test_image_path = Path("queries/sophie/sophie_query_01/cloth_02555.jpg")
    if test_image_path.exists():
        with open(test_image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    # Fallback: Create a minimal valid JPEG
    # This is a valid 1x1 pixel JPEG
    jpeg_data = base64.b64decode(
        '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA/8A'
    )
    return base64.b64encode(jpeg_data).decode('utf-8')

def test_upload_image():
    """Test image upload endpoint"""
    print("\n🔍 Testing image upload endpoint...")
    try:
        # Create a test image
        test_image_base64 = create_test_image_base64()
        
        payload = {
            "user_id": TEST_USER_ID,
            "image": f"data:image/jpeg;base64,{test_image_base64}"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/upload",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_get_wardrobe():
    """Test get wardrobe endpoint"""
    print("\n🔍 Testing get wardrobe endpoint...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/wardrobe/{TEST_USER_ID}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Wardrobe retrieved: {data.get('num_items', 0)} items")
            if data.get('items'):
                print(f"   First item: {data['items'][0]}")
            return True
        else:
            print(f"❌ Get wardrobe failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get wardrobe error: {e}")
        return False

def test_get_recommendations():
    """Test recommendations endpoint"""
    print("\n🔍 Testing recommendations endpoint...")
    
    # First, check if we have a query image
    query_path = Path("queries/sophie/sophie_query_01/cloth_02555.jpg")
    if not query_path.exists():
        print("⚠️  No test query image found. Skipping recommendation test.")
        print(f"   Expected: {query_path}")
        return None
    
    try:
        # Read image and convert to base64
        with open(query_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            "user_id": TEST_USER_ID,
            "image": f"data:image/jpeg;base64,{image_base64}",
            "threshold": 0.7,
            "wardrobe_k": 5,
            "catalog_k": 3
        }
        
        print("   Sending recommendation request (this may take a while)...")
        response = requests.post(
            f"{API_BASE_URL}/api/recommend",
            json=payload,
            timeout=120  # Recommendations can take time
        )
        
        if response.status_code == 200:
            data = response.json()
            num_items = data.get('num_results', 0)
            used_wardrobe = data.get('used_wardrobe', False)
            print(f"✅ Recommendations retrieved: {num_items} items")
            print(f"   Used wardrobe: {used_wardrobe}")
            if data.get('items'):
                print(f"   First recommendation: {data['items'][0].get('title', 'N/A')}")
            return True
        elif response.status_code == 503:
            # Service Unavailable - model not found (expected in test environment)
            data = response.json()
            error_msg = data.get('error', 'Service unavailable')
            if 'No trained model found' in error_msg:
                print(f"⚠️  Recommendations unavailable: {error_msg}")
                print(f"   This is expected if no model has been trained yet.")
                print(f"   Hint: {data.get('hint', 'Train a model to enable recommendations')}")
                return None  # Skip, not a failure
            else:
                print(f"❌ Recommendations failed: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
        else:
            print(f"❌ Recommendations failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")  # First 500 chars
            return False
    except Exception as e:
        print(f"❌ Recommendations error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_wardrobe_image():
    """Test wardrobe image serving"""
    print("\n🔍 Testing wardrobe image endpoint...")
    try:
        # First get wardrobe to see if there are images
        response = requests.get(
            f"{API_BASE_URL}/api/wardrobe/{TEST_USER_ID}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if not items:
                print("⚠️  No wardrobe items found. Skipping image test.")
                return None
            
            # Try to get the first image
            image_url = items[0].get('image', '')
            if not image_url or not image_url.startswith('/api/'):
                print("⚠️  No valid image URL found. Skipping image test.")
                return None
            
            # Extract filename from URL
            filename = image_url.split('/')[-1]
            response = requests.get(
                f"{API_BASE_URL}{image_url}",
                timeout=10
            )
            
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
                print(f"✅ Image served successfully: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Image serving failed: {response.status_code}")
                return False
        else:
            print("⚠️  Could not get wardrobe. Skipping image test.")
            return None
    except Exception as e:
        print(f"❌ Image serving error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 StyleMe API Test Suite")
    print("=" * 60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print()
    
    results = {}
    
    # Test 1: Health check
    results['health'] = test_health()
    if not results['health']:
        print("\n❌ API server is not running or not accessible.")
        print("   Please start it with: docker-compose --profile api up inference")
        sys.exit(1)
    
    # Test 2: Upload image
    results['upload'] = test_upload_image()
    
    # Test 3: Get wardrobe
    results['wardrobe'] = test_get_wardrobe()
    
    # Test 4: Get recommendations (optional - requires model)
    results['recommendations'] = test_get_recommendations()
    
    # Test 5: Serve wardrobe image
    results['image'] = test_wardrobe_image()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"⚠️  {test_name}: SKIPPED")
    
    print()
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()

