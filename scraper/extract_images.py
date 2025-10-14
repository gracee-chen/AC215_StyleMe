# place to change your file
# DATA_DIR = '../data/men_data'  # Relative to scraper directory
"""
Extract images (index 1 and 2) from Farfetch dataset
Supports processing multiple JSON files with multi-threading and progress bars
"""

import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time


def load_dataset(json_path):
    """Load dataset from JSON file"""
    print(f"  Loading {json_path.name}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  ✓ Loaded {len(data)} products from {json_path.name}")
    return data


def find_json_files(data_dir):
    """Find all JSON dataset files in directory"""
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Directory not found: {data_dir}")
    
    json_files = list(data_path.glob("*.json"))
    return sorted(json_files)


def extract_image_info(dataset, source_file):
    """Extract image URLs with index 1 and 2"""
    image_tasks = []
    
    for item in dataset:
        product_id = item.get('source', {}).get('id', '')
        if not product_id:
            continue
            
        medias = item.get('medias', [])
        
        for media in medias:
            if media.get('type') == 'Image' and media.get('index') in [1, 2]:
                image_tasks.append({
                    'product_id': product_id,
                    'url': media['url'],
                    'index': media['index'],
                    'source_file': source_file
                })
    
    return image_tasks


def download_image(task, output_dir, max_retries=2):
    """Download a single image with retry mechanism"""
    product_id = task['product_id']
    url = task['url']
    index = task['index']
    
    filename = f"{product_id}_index{index}.jpg"
    filepath = output_dir / filename
    
    # Skip if exists (fast check)
    if filepath.exists():
        return {'status': 'exists', 'filename': filename}
    
    # Try downloading with retries (reduced to 2 for speed)
    last_error = None
    for attempt in range(max_retries):
        try:
            # Reduced timeout to 20 seconds for faster failures
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return {'status': 'success', 'filename': filename}
        
        except requests.exceptions.Timeout:
            last_error = f"Timeout on attempt {attempt + 1}/{max_retries}"
            if attempt < max_retries - 1:
                time.sleep(1)  # Reduced wait time to 1 second
            continue
        
        except Exception as e:
            last_error = str(e)
            break  # Don't retry for other errors
    
    return {'status': 'failed', 'filename': filename, 'error': last_error}


def download_images_parallel(image_tasks, output_dir, max_workers=10):
    """Download images using parallel threads with progress bar"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Starting parallel download:")
    print(f"  - Total images: {len(image_tasks)}")
    print(f"  - Worker threads: {max_workers}")
    print(f"  - Output directory: {output_dir}")
    print(f"{'='*60}\n")
    
    results = {'success': 0, 'exists': 0, 'failed': 0}
    failed_images = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_image, task, output_path) for task in image_tasks]
        
        with tqdm(total=len(futures), desc="Downloading images", unit="img",
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
            for future in as_completed(futures):
                result = future.result()
                results[result['status']] += 1
                
                if result['status'] == 'failed':
                    failed_images.append({
                        'filename': result['filename'],
                        'error': result.get('error', 'Unknown error')
                    })
                
                pbar.update(1)
    
    print(f"\n{'='*60}")
    print(f"Download Summary:")
    print(f"  ✓ Successfully downloaded: {results['success']}")
    print(f"  ✓ Already existed: {results['exists']}")
    print(f"  ✗ Failed: {results['failed']}")
    print(f"{'='*60}")
    
    # Save failed downloads log
    if failed_images:
        log_file = output_path / 'failed_downloads.txt'
        with open(log_file, 'w') as f:
            for item in failed_images:
                f.write(f"{item['filename']}: {item['error']}\n")
        print(f"\nFailed downloads logged to: {log_file}")
    
    return results


def process_specific_files(data_dir, output_dir, specific_files, max_workers=10):
    """Process only specific JSON files"""
    print("=" * 60)
    print("Farfetch Image Extractor - Specific Files")
    print("=" * 60)
    
    data_path = Path(data_dir)
    json_files = [data_path / filename for filename in specific_files if (data_path / filename).exists()]
    
    if not json_files:
        print(f"✗ None of the specified files found in {data_dir}")
        return
    
    print(f"\nProcessing {len(json_files)} specific file(s):")
    for jf in json_files:
        print(f"  - {jf.name}")
    
    # Load datasets
    print(f"\n{'='*60}")
    print("Loading datasets...")
    print(f"{'='*60}")
    
    all_image_tasks = []
    total_products = 0
    
    for json_file in json_files:
        dataset = load_dataset(json_file)
        total_products += len(dataset)
        
        image_tasks = extract_image_info(dataset, json_file.name)
        all_image_tasks.extend(image_tasks)
        print(f"  ✓ Found {len(image_tasks)} images from {json_file.name}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  - Products: {total_products}")
    print(f"  - Images to process: {len(all_image_tasks)}")
    print(f"{'='*60}")
    
    if all_image_tasks:
        download_images_parallel(all_image_tasks, output_dir=output_dir, max_workers=max_workers)
        print(f"\n✅ Complete! Images saved to: {output_dir}/")
    else:
        print("\n✗ No images to download")


def process_data_directory(data_dir, output_dir='data/images', max_workers=15):
    """Process all JSON files in the data directory"""
    print("="*60)
    print("Farfetch Image Extractor")
    print("Multi-threaded with Progress Bars")
    print("="*60)
    
    # Find all JSON files
    print(f"\nScanning directory: {data_dir}")
    json_files = find_json_files(data_dir)
    print(json_files)
    
    if not json_files:
        print(f"✗ No dataset files found in {data_dir}")
        return
    
    print(f"✓ Found {len(json_files)} dataset file(s):")
    for jf in json_files:
        print(f"  - {jf.name}")
    
    # Load all datasets
    print(f"\n{'='*60}")
    print("Loading datasets...")
    print(f"{'='*60}")
    
    all_image_tasks = []
    total_products = 0
    
    for json_file in json_files:
        dataset = load_dataset(json_file)
        total_products += len(dataset)
        
        # Extract image info
        image_tasks = extract_image_info(dataset, json_file.name)
        all_image_tasks.extend(image_tasks)
        print(f"  ✓ Found {len(image_tasks)} images from {json_file.name}")
    
    print(f"\n{'='*60}")
    print(f"Total Summary:")
    print(f"  - Total products: {total_products}")
    print(f"  - Total images (index 1 & 2): {len(all_image_tasks)}")
    print(f"{'='*60}")
    
    # Download images
    if all_image_tasks:
        download_images_parallel(all_image_tasks, output_dir=output_dir, max_workers=max_workers)
        print(f"\n✅ Processing complete!")
        print(f"Images saved to: {output_dir}/")
    else:
        print("\n✗ No images to download")


def main():
    # Configuration
    DATA_DIR = '../data/women_data'  # Relative to scraper directory
    OUTPUT_DIR = '../data/images'  # Output to data/images
    MAX_WORKERS = 20  # Increased to 20 threads for faster downloads
    
    # Optional: Specify which files to process (leave empty to process all)
    # To process only specific files, uncomment and add their names here:
    # SPECIFIC_FILES = ['dataset_farfetch_2025-10-13_02-53-52-563.json']
    SPECIFIC_FILES = []  # Empty = process all files
    
    # Process the data directory
    if SPECIFIC_FILES:
        process_specific_files(DATA_DIR, OUTPUT_DIR, SPECIFIC_FILES, MAX_WORKERS)
    else:
        process_data_directory(DATA_DIR, OUTPUT_DIR, MAX_WORKERS)


if __name__ == '__main__':
    main()
