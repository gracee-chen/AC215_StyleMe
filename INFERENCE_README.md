# StyleMe 8.0 - Inference System

## 🎯 Overview

The inference system provides **image-to-image** fashion recommendations using the trained FashionCLIP model. Given a query image, it returns actual **product photos** of similar items, not just vector embeddings.

---

## 🏗️ Architecture

### **Components**

1. **Embeddings Service** - Loads trained FashionCLIP model and generates normalized vectors
2. **Catalog Index** - FAISS index of all Farfetch products with metadata
3. **Wardrobe Indexes** - Per-user FAISS indexes of their personal clothing
4. **Inference Service** - Orchestrates search with wardrobe → catalog fallback logic

### **Data Flow**

```
Query Image
    ↓
[Generate Embedding]
    ↓
[Search User Wardrobe FAISS Index]
    ↓
Score >= threshold?
    ↓ YES                    ↓ NO
[Return Wardrobe Items]  [Search Catalog FAISS Index]
                              ↓
                         [Return Top-3 Products]
```

---

## 📁 Directory Structure

Following the GCS-inspired structure:

```
styleme8.0/
├── catalog/
│   └── v_2025-10-24_model-b1/
│       ├── catalog_meta.parquet      # Metadata: id, title, brand, url, price
│       ├── catalog.vecs.npy          # [N, 512] L2-normalized embeddings
│       ├── catalog.index.faiss       # FAISS index for ANN search
│       ├── idmap.npy                 # row index → product_id mapping
│       └── manifest.json             # Version, build info
├── wardrobes/
│   └── {user_id}/
│       ├── images/                   # User's wardrobe photos
│       ├── wardrobe.parquet          # item_id, img_path metadata
│       ├── wardrobe.vecs.npy         # User item embeddings
│       ├── wardrobe.index.faiss      # User's FAISS index
│       ├── idmap.npy                 # row → item_id mapping
│       └── manifest.json             # Build metadata
├── queries/
│   └── {user_id}/
│       └── {request_id}/
│           └── query.jpg             # Query image
├── results/
│   └── {user_id}/
│       └── {request_id}.json         # Recommendations with scores
└── logs/
    └── inference/                    # Inference logs
```

---

## 🚀 Quick Start

### **1. Run Complete Pipeline**

```bash
make run
```

This runs all 4 stages:
- Ingestion → Preprocessing → Training → **Inference**

### **2. Run Only Inference** (requires trained model)

```bash
make run-inference
```

---

## 📊 Catalog Index Building

The catalog index is built automatically from your Farfetch data.

### **What Gets Built:**

```python
# From data/json/*.json files
{
  "id": "30586307",
  "title": "Polo Ralph Lauren gilet",
  "brand": "Polo Ralph Lauren",
  "price": "$336",
  "url": "https://www.farfetch.com/...",
  "category": "Men, Clothing, Jackets",
  "gender": "men",
  "image_path": "30586307_index1.jpg"
}

# Embeddings: [6700+, 512] float32 array
# FAISS Index: IndexFlatL2 for exact search
```

### **Manual Build:**

```bash
docker compose run inference python /app/build_catalog_index.py \
    --data-dir /app/data \
    --image-dir /app/data/images \
    --experiments-dir /app/experiments \
    --output-dir /app/catalog
```

---

## 👔 User Wardrobe Management

### **Add User Wardrobe**

1. Create user directory:
```bash
mkdir -p wardrobes/user_001/images
```

2. Add user's clothing images:
```bash
cp my_jacket.jpg wardrobes/user_001/images/
cp my_pants.jpg wardrobes/user_001/images/
```

3. Build user wardrobe index:
```bash
docker compose run inference python /app/build_user_wardrobe.py \
    --user-id user_001 \
    --wardrobe-dir /app/wardrobes/user_001 \
    --experiments-dir /app/experiments \
    --wardrobes-base-dir /app/wardrobes
```

---

## 🔍 Running Inference

### **Method 1: Command Line**

```bash
# Place query image
mkdir -p queries/user_001/req_001
cp query_jacket.jpg queries/user_001/req_001/query.jpg

# Run inference
docker compose run inference python /app/inference_service.py \
    --user-id user_001 \
    --query /app/queries/user_001/req_001/query.jpg \
    --output /app/results/user_001/req_001.json \
    --threshold 0.7 \
    --wardrobe-k 5 \
    --catalog-k 3

# View results
cat results/user_001/req_001.json
```

### **Method 2: Demo Script** (Automatic)

```bash
make run-inference
```

This runs the demo which:
- Automatically builds catalog if needed
- Tests with sample images from data
- Creates demo users and queries
- Saves results to `results/` directory

---

## 📋 Output Format

### **Result JSON Structure**

```json
{
  "user_id": "user_001",
  "query_image": "/app/queries/user_001/req_001/query.jpg",
  "timestamp": "2025-10-24T10:30:00",
  "used_wardrobe": true,
  "threshold": 0.7,
  "best_wardrobe_score": 0.89,
  "num_results": 5,
  "items": [
    {
      "rank": 1,
      "item_id": "jacket_001",
      "img_path": "user_001/images/jacket_001.jpg",
      "similarity": 0.89,
      "category": "jackets"
    },
    {
      "rank": 2,
      "title": "Polo Ralph Lauren gilet",
      "brand": "Polo Ralph Lauren",
      "price": "$336",
      "url": "https://www.farfetch.com/...",
      "similarity": 0.85,
      "image_path": "30586307_index1.jpg"
    }
  ]
}
```

### **Wardrobe Results** (used_wardrobe: true)
- Returns user's own clothing items
- Includes `item_id`, `img_path` (local path to image)
- High similarity scores (typically 0.8+)

### **Catalog Results** (used_wardrobe: false)
- Returns Farfetch products
- Includes `title`, `brand`, `price`, `url` (buy link)
- `image_path` in `data/images/`
- `fallback_reason`: "empty_wardrobe" or "low_score"

---

## 🎯 Inference Logic

### **Threshold-Based Fallback**

```python
# Step 1: Search wardrobe
wardrobe_items, best_score = search_wardrobe(user_id, query_embedding, k=5)

# Step 2: Decide source
if wardrobe_items is None:
    # No wardrobe exists
    use_catalog()
elif best_score < threshold:  # default 0.7
    # Wardrobe items not similar enough
    use_catalog()
else:
    # Good wardrobe matches
    return wardrobe_items
```

### **Parameters**

- `threshold`: Minimum similarity score (default: 0.7)
  - Higher = stricter matching, more likely to use catalog
  - Lower = more lenient, prefers wardrobe
- `wardrobe_k`: Number of wardrobe items to return (default: 5)
- `catalog_k`: Number of catalog products to return (default: 3)

---

## 🔧 Advanced Usage

### **Custom Inference Script**

```python
from inference_service import InferenceService

# Initialize
service = InferenceService(
    catalog_dir='/app/catalog',
    experiments_dir='/app/experiments',
    wardrobes_dir='/app/wardrobes'
)

# Run inference
result = service.inference(
    user_id='user_001',
    query_image_path='queries/user_001/req_001/query.jpg',
    threshold=0.8,  # Custom threshold
    wardrobe_k=10,  # More wardrobe results
    catalog_k=5     # More catalog results
)

# Access results
for item in result['items']:
    print(f"{item['rank']}. {item.get('title', item.get('item_id'))}")
    print(f"   Similarity: {item['similarity']:.3f}")
    if 'url' in item:
        print(f"   Buy: {item['url']}")
```

### **Build Multiple Wardrobes**

```bash
# User 1
mkdir -p wardrobes/user_001/images
cp user1/*.jpg wardrobes/user_001/images/
docker compose run inference python /app/build_user_wardrobe.py --user-id user_001 --wardrobe-dir /app/wardrobes/user_001

# User 2
mkdir -p wardrobes/user_002/images
cp user2/*.jpg wardrobes/user_002/images/
docker compose run inference python /app/build_user_wardrobe.py --user-id user_002 --wardrobe-dir /app/wardrobes/user_002
```

---

## 📊 Performance

### **Catalog Index Build** (One-Time)
- **Input**: 6700+ Farfetch products
- **Time**: 10-30 minutes (GPU) / 1-2 hours (CPU)
- **Output**: ~3.4MB FAISS index, ~3MB metadata

### **Wardrobe Index Build** (Per User)
- **Input**: 10-100 user images
- **Time**: 1-5 minutes
- **Output**: ~50KB per user

### **Inference Query**
- **Time**: < 100ms per query
- **FAISS Search**: < 10ms (exact search with IndexFlatL2)
- **Model Inference**: ~50-80ms (generate query embedding)

---

## 🛠️ Troubleshooting

### **No catalog found**
```bash
# Manually build catalog
make run-inference
# Or
docker compose run inference python /app/build_catalog_index.py
```

### **User wardrobe not found**
```bash
# Check directory structure
ls -la wardrobes/user_001/
# Should have: images/, wardrobe.index.faiss, etc.

# Rebuild if missing
docker compose run inference python /app/build_user_wardrobe.py \
    --user-id user_001 \
    --wardrobe-dir /app/wardrobes/user_001
```

### **Low similarity scores**
- Adjust threshold: `--threshold 0.5` (lower = more lenient)
- Check image quality (blurry/occluded images perform worse)
- Verify wardrobe images are similar style to query

---

## 📚 Container Files

```
containers/inference/
├── Dockerfile                    # Python 3.9 + FAISS + PyTorch
├── requirements.txt              # Dependencies
├── build_catalog_index.py        # Builds global catalog FAISS index
├── build_user_wardrobe.py        # Builds per-user wardrobe index
├── inference_service.py          # Main inference service
└── entrypoint.sh                 # Orchestrates catalog build + demo
```

---

## ✅ Success Checklist

After running `make run-inference`, you should have:

- [ ] `catalog/v_*/catalog.index.faiss` - Catalog FAISS index
- [ ] `catalog/v_*/catalog_meta.parquet` - Product metadata
- [ ] `results/demo_user/demo_001.json` - Demo inference results
- [ ] `queries/demo_user/demo_001/query.jpg` - Demo query image

### **Verify:**

```bash
# Check catalog
ls -lh catalog/v_*/

# Check results
cat results/demo_user/demo_001.json | jq

# Check status
make status
```

---

## 🎓 Next Steps

1. **Add Your Wardrobe**: Create wardrobes with your own clothing images
2. **Test Different Queries**: Try various outfit queries
3. **Tune Threshold**: Experiment with different similarity thresholds
4. **Build API**: Wrap inference_service.py with FastAPI
5. **Scale Up**: Use IVF index for large catalogs (100K+ items)

---

## 💡 Key Features

✅ **Image-to-Image Search** - Query with photo, get back photos  
✅ **Dual Index System** - Personal wardrobe + global catalog  
✅ **FAISS Integration** - Fast approximate nearest neighbor search  
✅ **Smart Fallback** - Wardrobe → catalog with threshold logic  
✅ **Rich Metadata** - Product details, prices, buy URLs  
✅ **Versioned Catalog** - Track different model/data versions  
✅ **Per-User Isolation** - Each user has their own wardrobe index  

---

**Ready to recommend fashion! 🎨👔👗**

