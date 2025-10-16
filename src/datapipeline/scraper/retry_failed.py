#!/usr/bin/env python3
"""
Retry downloading failed images with longer timeout and more retries
"""

import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import re


def load_failed_list(failed_log_path):
    """Load list of failed downloads from log file"""
    failed_files = []
    
    with open(failed_log_path, 'r') as f:
        for line in f:
            # Extract filename from log entry
            # Format: "productID_indexN.jpg: error message"
            match = re.match(r'(\d+_index[12]\.jpg):', line.strip())
            if match:
                failed_files.append(match.group(1))
    
    return failed_files


def extract_product_info(filename):
    """Extract product ID and index from filename"""
    # Format: productID_indexN.jpg
    match = re.match(r'(\d+)_index([12])\.jpg', filename)
    if match:
        return {
            'product_id': match.group(1),
            'index': int(match.group(2)),
            'filename': filename
        }
    return None


def find_image_url(product_id, index, data_dir):
    """Find the URL for a specific product image from dataset files"""
    data_path = Path(data_dir)
    json_files = list(data_path.glob("dataset_farfetch_*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            for item in dataset:
                item_id = item.get('source', {}).get('id', '')
                if item_id == product_id:
                    medias = item.get('medias', [])
                    for media in medias:
                        if media.get('type') == 'Image' and media.get('index') == index:
                            return media.get('url')
        except Exception:
            continue
    
    return None


def download_image_with_retries(url, filepath, max_retries=5, timeout=60):
    """Download image with aggressive retry strategy"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return {'status': 'success'}
        
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3  # Progressive wait: 3s, 6s, 9s, 12s, 15s
                time.sleep(wait_time)
                continue
            return {'status': 'failed', 'error': f'Timeout after {max_retries} attempts'}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    return {'status': 'failed', 'error': 'Unknown error'}


def retry_failed_images(failed_log, data_dir, output_dir, max_workers=5):
    """Retry downloading failed images"""
    print("="*60)
    print("Retry Failed Images")
    print("Extended Timeout & More Retries")
    print("="*60)
    
    # Load failed list
    print(f"\nLoading failed downloads log: {failed_log}")
    failed_files = load_failed_list(failed_log)
    print(f"✓ Found {len(failed_files)} failed images")
    
    # Extract product info and find URLs
    print("\nSearching for image URLs in dataset files...")
    tasks = []
    not_found = []
    
    for filename in tqdm(failed_files, desc="Finding URLs", unit="img"):
        info = extract_product_info(filename)
        if not info:
            not_found.append(filename)
            continue
        
        url = find_image_url(info['product_id'], info['index'], data_dir)
        if url:
            tasks.append({
                'filename': filename,
                'url': url,
                'filepath': Path(output_dir) / filename
            })
        else:
            not_found.append(filename)
    
    print(f"\n✓ Found URLs for {len(tasks)} images")
    if not_found:
        print(f"✗ Could not find URLs for {len(not_found)} images")
    
    if not tasks:
        print("\n✗ No images to retry")
        return
    
    # Retry downloads
    print(f"\n{'='*60}")
    print(f"Retrying downloads with:")
    print(f"  - Timeout: 60 seconds (3x longer)")
    print(f"  - Max retries: 5 attempts")
    print(f"  - Progressive wait: 3s, 6s, 9s, 12s, 15s")
    print(f"  - Worker threads: {max_workers}")
    print(f"{'='*60}\n")
    
    results = {'success': 0, 'failed': 0}
    still_failed = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                download_image_with_retries, 
                task['url'], 
                task['filepath'],
                max_retries=5,
                timeout=60
            ): task for task in tasks
        }
        
        with tqdm(total=len(futures), desc="Retrying downloads", unit="img") as pbar:
            for future in as_completed(futures):
                task = futures[future]
                result = future.result()
                
                if result['status'] == 'success':
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    still_failed.append({
                        'filename': task['filename'],
                        'error': result.get('error', 'Unknown')
                    })
                
                pbar.update(1)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Retry Summary:")
    print(f"  ✓ Successfully recovered: {results['success']}")
    print(f"  ✗ Still failed: {results['failed']}")
    print(f"{'='*60}")
    
    # Update failed downloads log
    if still_failed:
        failed_path = Path(output_dir) / 'failed_downloads.txt'
        with open(failed_path, 'w') as f:
            for item in still_failed:
                f.write(f"{item['filename']}: {item['error']}\n")
        print(f"\nUpdated failed downloads log: {failed_path}")
        print(f"Remaining failures: {len(still_failed)}")
    else:
        # All recovered, delete the log
        failed_path = Path(output_dir) / 'failed_downloads.txt'
        if failed_path.exists():
            failed_path.unlink()
        print(f"\n🎉 All images recovered! Failed log removed.")
    
    if not_found:
        not_found_path = Path(output_dir) / 'urls_not_found.txt'
        with open(not_found_path, 'w') as f:
            f.write('\n'.join(not_found))
        print(f"\nImages with URLs not found: {not_found_path}")


def main():
    # Configuration
    DATA_DIR = '../data/men_data'
    OUTPUT_DIR = '../data/images'
    FAILED_LOG = '../data/images/failed_downloads.txt'
    MAX_WORKERS = 5  # Reduced workers for more stable connections
    
    # Retry failed images
    retry_failed_images(FAILED_LOG, DATA_DIR, OUTPUT_DIR, MAX_WORKERS)
    
    print(f"\n✅ Retry process complete!")


if __name__ == '__main__':
    main()

