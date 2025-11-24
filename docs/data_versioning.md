# Data Versioning Documentation

## Overview

StyleMe uses **DVC (Data Version Control)** to version locally generated data artifacts, ensuring reproducibility and tracking data lineage throughout the project lifecycle.

## Methodology

### Why DVC?

- **Git-friendly**: Stores metadata in Git, data in remote storage (doesn't bloat repository)
- **Efficient**: Content-addressable storage with automatic deduplication
- **Reproducibility**: Links code versions to data versions
- **GCS Integration**: Tracks source data state in Google Cloud Storage
- **Flexibility**: Supports local and remote storage backends

### Data Architecture

```
GCS (Source Data: ~13k images)
    ↓
[build_catalog_index.py / build_user_wardrobe.py]
    ↓
Local Generated Data (catalog/, wardrobes/)
    ↓
[DVC Versioning]
```

### Versioned Artifacts

1. **Catalog Data** (`catalog/`)
   - FAISS indices, embeddings, metadata
   - Generated from GCS using `build_catalog_index.py`
   - Each version tagged: `catalog-v_YYYYMMDD_description`

2. **User Wardrobes** (`wardrobes/`)
   - User images, embeddings, FAISS indices
   - Versioned per-user

3. **Model Checkpoints** (`experiments/`)
   - Trained model weights
   - Automatically linked to data versions used during training

### GCS Source Tracking

Source data in GCS (`gs://styleme-data-bucket/`) is tracked via metadata snapshots in `manifest.json`:
- Records which GCS files were used
- Tracks gender filter (men/women/all)
- Maintains history of data states

## Usage Instructions

### Adding New Data Version

```bash
# 1. Build catalog from GCS
python containers/inference/build_catalog_index.py \
    --gcp-bucket-name styleme-data-bucket \
    --gcp-project-id styleme-475201 \
    --output-dir catalog

# 2. Record GCS source state
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_VERSION/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201

# 3. Add to DVC
python data_versioning/dvc_manager.py add-catalog v_VERSION

# 4. Create version tag
python data_versioning/dvc_manager.py tag catalog-v_VERSION -m "Description"

# 5. Commit to Git
git add catalog/v_VERSION.dvc .dvc/
git commit -m "Add catalog version v_VERSION"
```

### Retrieving Data Versions

```bash
# Pull latest version
python data_versioning/dvc_manager.py pull

# Checkout specific version
python data_versioning/dvc_manager.py checkout catalog-v_VERSION

# List all tags
python data_versioning/dvc_manager.py list-tags
```

### Viewing Version History

```bash
# View complete history
python data_versioning/dvc_manager.py history

# View history for specific artifact
python data_versioning/dvc_manager.py history catalog/v_VERSION
```

## Reproducibility Chain

```
Model Version → Training Config → Catalog Version → GCS Source State
```

Each model checkpoint automatically links to the data version used during training, ensuring full traceability.

