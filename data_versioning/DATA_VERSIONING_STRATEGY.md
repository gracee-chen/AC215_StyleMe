# Data Versioning Strategy

## Overview

DVC (Data Version Control) is used for versioning locally generated data artifacts. Source training data in GCS is tracked via metadata snapshots.

## Why DVC?

- **Git-friendly**: Stores metadata in Git, data in remote storage
- **Efficient**: Content-addressable storage with deduplication
- **Reproducibility**: Tracks data dependencies
- **Remote support**: Works with GCS, S3, or local storage

## Data Architecture

```
GCS (Source Data)
    ↓
[build_catalog_index.py / build_user_wardrobe.py]
    ↓
Local Generated Data (catalog/, wardrobes/)
    ↓
[DVC Versioning]
```

## Data Artifacts

### 1. Catalog Data (`catalog/`)
- **Source**: Generated from GCS using `build_catalog_index.py`
- **Contents**: FAISS indices, embeddings, metadata
- **Versioning**: Tracked with DVC
- **GCS Linkage**: `manifest.json` records GCS source state

### 2. Training Datasets (GCS)
- **Location**: `gs://styleme-data-bucket/json/`, `images/`
- **Size**: ~13k images, too large for local versioning
- **Strategy**: Tracked via snapshots in `manifest.json`, not directly versioned

### 3. User Wardrobes (`wardrobes/`)
- **Contents**: User images, embeddings, FAISS indices
- **Versioning**: Tracked per-user with DVC

### 4. Training Experiments (`src/models/train/experiments/`)
- **Contents**: Configs, training history, plots
- **Versioning**: Tracked per-experiment

## Workflow

### Adding New Data

1. Generate data from GCS: `build_catalog_index.py`
2. Record GCS source state in `manifest.json`:
   ```bash
   python data_versioning/gcs_snapshot_tracker.py \
       catalog/v_VERSION/manifest.json
   ```
3. Add to DVC: `dvc add catalog/v_VERSION`
4. Create tag: `dvc tag create <tag_name>`

### Retrieving Data

- Pull latest: `dvc pull`
- Checkout version: `dvc checkout <tag>`

### Version History

Version history is maintained through three sources:

1. **DVC Tags**: Named versions of data artifacts
   ```bash
   python data_versioning/dvc_manager.py list-tags
   ```

2. **Git Commits**: `.dvc` files are committed to Git, tracking when data was added/modified
   ```bash
   git log --oneline --all -- "*.dvc"
   ```

3. **GCS Snapshots**: Recorded in `manifest.json`, showing which GCS files were used
   ```bash
   cat catalog/v_VERSION/manifest.json | grep -A 20 gcs_source
   ```

View complete history:
```bash
python data_versioning/dvc_manager.py history
python data_versioning/dvc_manager.py history catalog/v_VERSION
```

## GCS Source Tracking

Each catalog/wardrobe version records GCS state in `manifest.json`:

```json
{
  "version": "v_2025-10-24_model-b1",
  "gcs_source": {
    "bucket": "styleme-data-bucket",
    "snapshot_time": "2025-10-24T22:43:00Z",
    "file_list": {
      "men": ["json/men_data/file1.json", ...],
      "women": ["json/women_data/file1.json", ...]
    }
  }
}
```

This allows:
- Tracing which GCS files were used
- Reproducing catalog from same GCS state
- Comparing GCS data changes between versions

## Reproducibility Chain

```
Model Version → Training Config → Catalog Version → GCS Source State
```
