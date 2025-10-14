# Project 215 - Farfetch Dataset Image Extraction

Extract product images from Farfetch dataset JSON files with multi-threading and progress bars.

## 📁 Project Structure

```
project 215/
├── scraper/                    # Image extraction tool
│   ├── extract_images.py      # Multi-threaded extraction script
│   └── README.md              # Implementation guide
└── data/
    ├── men_data/              # Input datasets
    │   ├── dataset_farfetch_2025-10-12_22-49-15-151.json
    │   └── dataset_farfetch_2025-10-13_00-02-20-351.json
    └── images/                # Downloaded images (output)
        ├── 30586307_index1.jpg
        ├── 30586307_index2.jpg
        └── ... (1139+ images)
```

## 🚀 Quick Start

```bash
# Install dependencies
pip3 install requests tqdm

# Navigate to scraper directory
cd scraper

# Run the image extractor
python3 extract_images.py
```

## ✨ Features

✅ **Multi-file Processing** - Automatically processes all JSON files in `data/men_data/`  
✅ **Multi-threaded Download** - 15 parallel workers for fast downloads  
✅ **Real-time Progress Bar** - Beautiful progress tracking with tqdm  
✅ **Smart Resume** - Skips already downloaded images  
✅ **Error Logging** - Failed downloads saved to log file  
✅ **Index Filtering** - Extracts only index 1 and 2 images  

## 🎯 Usage Example

### Run the Extractor

```bash
cd scraper
python3 extract_images.py
```

### Output Example

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
  ✓ Loaded 244 products
  ✓ Found 488 images
  Loading dataset_farfetch_2025-10-13_00-02-20-351.json...
  ✓ Loaded 496 products
  ✓ Found 992 images

============================================================
Total Summary:
  - Total products: 740
  - Total images (index 1 & 2): 1480
============================================================

============================================================
Starting parallel download:
  - Total images: 1480
  - Worker threads: 15
  - Output directory: ../data/images
============================================================

Downloading images: 100%|████████████| 1480/1480 [14:55<00:00, 1.65img/s]

============================================================
Download Summary:
  ✓ Successfully downloaded: 881
  ✓ Already existed: 258
  ✗ Failed: 341
============================================================

✅ Processing complete!
Images saved to: ../data/images/
```

## 📊 Dataset Info

- **Total Products**: 740 fashion items
- **Total Images**: 1480 images (index 1 and 2)
- **Successfully Downloaded**: 1139+ images
- **Source Files**: 2 dataset JSON files
- **Brands**: Various luxury and designer brands
- **Source**: Farfetch e-commerce platform

## 📦 Dataset Structure

### Input JSON Format
```json
{
  "brand": "Polo Ralph Lauren",
  "title": "logo-embroidered corduroy-padded gilet",
  "description": "...",
  "categories": ["Men", "Clothing", "Jackets"],
  "medias": [
    {
      "type": "Image",
      "url": "https://cdn-images.farfetch-contents.com/.../image.jpg",
      "alt": "Product image",
      "index": 1
    },
    {
      "type": "Image",
      "url": "https://cdn-images.farfetch-contents.com/.../image.jpg",
      "alt": "Product image",
      "index": 2
    }
  ],
  "price": {
    "current": 33600,
    "currentFormatted": "$336"
  },
  "source": {
    "id": "30586307"
  }
}
```

### Output Images
```
data/images/
├── 30586307_index1.jpg  (Product ID + index)
├── 30586307_index2.jpg
├── 16683802_index1.jpg
├── 16683802_index2.jpg
└── ... (1139+ images)
```

## 🛠️ Dependencies

- `requests` - HTTP requests and image downloads
- `tqdm` - Progress bars

Install with:
```bash
pip3 install requests tqdm
```

## ⚙️ Configuration

Edit `scraper/extract_images.py` to customize:

```python
DATA_DIR = '../data/men_data'   # Input directory with JSON files
OUTPUT_DIR = '../data/images'   # Output directory for images
MAX_WORKERS = 15                # Number of parallel download threads
```

## 📋 Implementation

For implementation details and code examples, see:
- [scraper/README.md](scraper/README.md) - Complete implementation guide

## ⚠️ Important Notes

- ✅ For educational and personal use only
- ✅ Please respect Farfetch's terms of service
- ✅ Use appropriate request delays
- ✅ Do not abuse or over-scrape

## 🤝 Contributing

Issues and improvement suggestions are welcome!

## 📄 License

This project is for educational purposes only.

---

**Get Started**: `cd scraper && python3 extract_images.py`
