# Data Versioning and Reproducibility

Data versioning strategy using DVC for the StyleMe project.

## Quick Start

### Step 1: Install DVC
```bash
pip install --user dvc
# Or if you have permissions:
pip install dvc
```

### Step 2: Configure Git (if not already configured)
```bash
git config user.email "your-email@example.com"
git config user.name "Your Name"
```

### Step 3: Initialize DVC
```bash
python data_versioning/dvc_manager.py init --remote-type local --remote-path ./dvc_storage
```

### Step 4: Remove Data from Git Tracking (if already tracked)
If your data is already tracked by Git, remove it first:
```bash
git rm -r --cached catalog/v_2025-10-24_model-b1
git commit -m "Stop tracking catalog in Git, will use DVC"
```

### Step 5: Add Data to DVC
```bash
# Add catalog
python data_versioning/dvc_manager.py add-catalog v_2025-10-24_model-b1

# Add wardrobe
python data_versioning/dvc_manager.py add-wardrobe sophie

# Add model checkpoints (after fine-tuning)
python data_versioning/dvc_manager.py add-model fine_tune_20251123_163849 --type both
```

### Step 6: Record GCS Source State (optional)
```bash
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_2025-10-24_model-b1/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201
```

### Step 7: Create Version Tags
```bash
python data_versioning/dvc_manager.py tag catalog-v_2025-10-24_model-b1 -m "Initial catalog version"
```

### Step 8: Commit DVC Files to Git
```bash
git add catalog/v_2025-10-24_model-b1.dvc .dvc/
git commit -m "Add catalog version to DVC"
```

### Step 9: View Version History
```bash
python data_versioning/dvc_manager.py history
python data_versioning/dvc_manager.py list-tags
```

### Step 10: Push to Remote (optional)
```bash
python data_versioning/dvc_manager.py push
```

## Data Retrieval

```bash
# Pull latest
python data_versioning/dvc_manager.py pull

# Checkout specific version
python data_versioning/dvc_manager.py checkout v1.0-catalog

# List tags
python data_versioning/dvc_manager.py list-tags

# View version history
python data_versioning/dvc_manager.py history
python data_versioning/dvc_manager.py history catalog/v_2025-10-24_model-b1
```

## GCS Integration

Source training data is stored in GCS (`styleme-data-bucket`), which is too large to version locally. Instead:

1. **GCS data** (~13k images) is tracked via snapshots in `manifest.json`
2. **Local generated data** (catalog indices, wardrobes) is versioned with DVC
3. Each catalog/wardrobe version links to GCS source state via `manifest.json`

### Record GCS Source State

```bash
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_2025-10-24_model-b1/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201
```

## DVC Manager Commands

```bash
# Initialize
python data_versioning/dvc_manager.py init --remote-type local --remote-path ./dvc_storage

# Add data
python data_versioning/dvc_manager.py add <path>
python data_versioning/dvc_manager.py add-catalog <version>
python data_versioning/dvc_manager.py add-wardrobe <user_id>
python data_versioning/dvc_manager.py add-model <experiment_id> [--type best|final|both] [--tag <tag>]

# Versioning
python data_versioning/dvc_manager.py tag <name> -m "<message>"
python data_versioning/dvc_manager.py list-tags

# Data operations
python data_versioning/dvc_manager.py push
python data_versioning/dvc_manager.py pull
python data_versioning/dvc_manager.py checkout <tag>
python data_versioning/dvc_manager.py status

# Version history
python data_versioning/dvc_manager.py history [path]
```

## Versioned Data

- **Catalog** (`catalog/v_*/`): FAISS indices, embeddings (generated from GCS)
- **Wardrobes** (`wardrobes/{user_id}/`): User wardrobe indices
- **Model Checkpoints** (`src/models/train/experiments/*/checkpoints/`): Trained model files
- **Experiments** (`src/models/train/experiments/`): Training results and metadata

## Version History

Version history is available through three sources:

1. **Git Tags**: Created with `python data_versioning/dvc_manager.py tag`
   ```bash
   python data_versioning/dvc_manager.py list-tags
   ```

2. **Git Commits**: Git commits for `.dvc` files track when data was added/modified
   ```bash
   git log --oneline --all -- "*.dvc"
   ```

3. **GCS Snapshots**: Recorded in `manifest.json` files, showing which GCS files were used
   ```bash
   cat catalog/v_2025-10-24_model-b1/manifest.json | grep -A 20 gcs_source
   ```

View complete history:
```bash
# View all version history
python data_versioning/dvc_manager.py history

# View history for specific data
python data_versioning/dvc_manager.py history catalog/v_2025-10-24_model-b1
```

**Note**: DVC 3.x uses Git tags instead of DVC tags. The `tag` command creates Git tags.

## Notes

- Existing data is not modified when adding version control
- Training code does not need changes
- GCS source data is tracked via metadata, not directly versioned

## Building Multiple Versions

To build different catalog versions (e.g., men only, men+women):

```bash
# Automated script
bash data_versioning/build_catalog_versions.sh

# Or manually
python containers/inference/build_catalog_index.py --gender men
python containers/inference/build_catalog_index.py --gender all
```

See [MULTI_VERSION_GUIDE.md](./MULTI_VERSION_GUIDE.md) for detailed instructions.

## Model Versioning

After fine-tuning, add model checkpoints to DVC:

```bash
# Add both best and final models (default)
python data_versioning/dvc_manager.py add-model fine_tune_20251123_163849

# Add only best model
python data_versioning/dvc_manager.py add-model fine_tune_20251123_163849 --type best

# Add only final model
python data_versioning/dvc_manager.py add-model fine_tune_20251123_163849 --type final

# With custom tag
python data_versioning/dvc_manager.py add-model fine_tune_20251123_163849 --tag model-v1.0
```

The command will:
1. Read `experiment_record.json` to get data version and training results
2. Add model checkpoints (`best_model.pth`, `final_model.pth`) to DVC
3. Create a Git tag linking model version to data version
4. Record metadata (best accuracy, data version used)

**Note**: Model versioning automatically links to the data version used during training, so you don't need to manually track which data version was used.

## Git Version Control

### How Git Tracks Versions

Every commit creates a new version in Git:

1. **Initial commit**: When you first add data to DVC
2. **Subsequent commits**: Each time you add/update data and commit `.dvc` files

### Viewing Git History

```bash
# View commit history
git log --oneline --all -- "*.dvc"

# View all commits
git log --oneline

# View specific commit
git show <commit-hash>
```

### Complete Version Tracking

You have three levels of versioning:

1. **Git Commits**: Every commit is a version (automatic)
2. **Git Tags**: Named milestones (created with `tag` command)
3. **GCS Snapshots**: Source data state (in `manifest.json`)

**Yes, every commit creates a new version in Git!** The more you commit, the more versions you have in your history.

## Documentation

- [DATA_VERSIONING_STRATEGY.md](./DATA_VERSIONING_STRATEGY.md) - Detailed strategy and rationale
- [MULTI_VERSION_GUIDE.md](./MULTI_VERSION_GUIDE.md) - Guide for building multiple catalog versions
