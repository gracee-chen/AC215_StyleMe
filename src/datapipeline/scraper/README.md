# Image Extraction from Farfetch Dataset

Extract product images (index 1 and 2) from Farfetch dataset files with multi-threading and progress bars.

## Quick Start

```bash
# Install dependencies
pip3 install requests tqdm

# Navigate to scraper directory
cd scraper

# Run the extractor (processes data/men_data/)
python3 extract_images.py
```

## What It Does

- Scans `data/men_data/` for all dataset JSON files
- Extracts images with index 1 and 2 from all files
- Downloads images in parallel with 15 worker threads
- Shows real-time progress bar
- Saves to `data/images/` folder

## Features

✅ **Multi-file Processing** - Processes all JSON files in directory  
✅ **Multi-threaded Download** - 15 parallel workers for fast downloads  
✅ **Progress Bar** - Real-time download progress with tqdm  
✅ **Smart Resume** - Skips already downloaded images  
✅ **Error Logging** - Logs failed downloads to `failed_downloads.txt`

## Output Example

```
============================================================
Farfetch Image Extractor
Multi-threaded with Progress Bars
============================================================

Scanning directory: ../data/men_data
✓ Found 2 dataset file(s):
  - dataset_farfetch_2025-10-12_22-49-15-151.json
  - dataset_farfetch_2025-10-13_00-02-20-351.json

============================================================
Loading datasets...
============================================================
  Loading dataset_farfetch_2025-10-12_22-49-15-151.json...
  ✓ Loaded 244 products from dataset_farfetch_2025-10-12_22-49-15-151.json
  ✓ Found 488 images from dataset_farfetch_2025-10-12_22-49-15-151.json
  Loading dataset_farfetch_2025-10-13_00-02-20-351.json...
  ✓ Loaded 521 products from dataset_farfetch_2025-10-13_00-02-20-351.json
  ✓ Found 1042 images from dataset_farfetch_2025-10-13_00-02-20-351.json

============================================================
Total Summary:
  - Total products: 765
  - Total images (index 1 & 2): 1530
============================================================

============================================================
Starting parallel download:
  - Total images: 1530
  - Worker threads: 15
  - Output directory: ../data/images
============================================================

Downloading images: 100%|████████████| 1530/1530 [02:15<00:00, 11.32img/s]

============================================================
Download Summary:
  ✓ Successfully downloaded: 1485
  ✓ Already existed: 0
  ✗ Failed: 45
============================================================

✅ Processing complete!
Images saved to: ../data/images/
```

## File Structure

```
project 215/
├── scraper/
│   ├── extract_images.py          # Extraction script
│   └── README.md                  # This file
└── data/
    ├── men_data/                  # Input datasets
    │   ├── dataset_farfetch_2025-10-12_22-49-15-151.json
    │   └── dataset_farfetch_2025-10-13_00-02-20-351.json
    └── images/                    # Downloaded images (output)
        ├── 30586307_index1.jpg
        ├── 30586307_index2.jpg
        └── ...
```

## Configuration

Edit `extract_images.py` to customize:

```python
DATA_DIR = '../data/men_data'      # Input directory with JSON files
OUTPUT_DIR = '../data/images'      # Output directory for images
MAX_WORKERS = 15                   # Number of parallel download threads
```

## Implementation Details

### Process Multiple Files

```python
from pathlib import Path

# Find all dataset files
json_files = list(Path(data_dir).glob("dataset_farfetch_*.json"))

for json_file in json_files:
    with open(json_file, 'r') as f:
        dataset = json.load(f)
    # Process each file...
```

### Extract Image URLs

```python
for item in dataset:
    product_id = item['source']['id']
    medias = item.get('medias', [])
    
    for media in medias:
        if media.get('type') == 'Image' and media.get('index') in [1, 2]:
            url = media['url']
            index = media['index']
            # Add to download queue
```

### Multi-threaded Download with Progress Bar

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

with ThreadPoolExecutor(max_workers=15) as executor:
    futures = [executor.submit(download_image, task) for task in tasks]
    
    with tqdm(total=len(futures), desc="Downloading", unit="img") as pbar:
        for future in as_completed(futures):
            result = future.result()
            pbar.update(1)
```

## Requirements

```bash
pip3 install requests tqdm
```

- `requests` - HTTP downloads
- `tqdm` - Progress bars
