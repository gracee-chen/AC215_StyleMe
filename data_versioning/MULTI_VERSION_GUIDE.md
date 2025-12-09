# Building Multiple Catalog Versions

This guide explains how to build and version multiple catalog datasets with different data subsets.

## Building Two Versions: Men Only and Men+Women

### Option 1: Using the Automated Script

```bash
bash data_versioning/build_catalog_versions.sh
```

This script will:
1. Build version 1: Men only
2. Build version 2: Men + Women
3. Record GCS snapshots for both
4. Add both to DVC
5. Create tags for both versions

### Option 2: Manual Steps

#### Build Version 1: Men Only

```bash
# Build catalog with men only
python containers/inference/build_catalog_index.py \
    --gcp-bucket-name styleme-data-bucket \
    --gcp-project-id styleme-475201 \
    --data-prefix json \
    --images-prefix images \
    --experiments-dir src/models/train/experiments \
    --output-dir catalog \
    --gender men

# Rename to version name
mv catalog/v_* catalog/v_men_only_$(date +%Y%m%d)

# Record GCS snapshot
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_men_only_*/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201

# Add to DVC
python data_versioning/dvc_manager.py add-catalog v_men_only_*

# Create tag
python data_versioning/dvc_manager.py tag catalog-v_men_only_* -m "Catalog: Men only"
```

#### Build Version 2: Men + Women

```bash
# Build catalog with all data
python containers/inference/build_catalog_index.py \
    --gcp-bucket-name styleme-data-bucket \
    --gcp-project-id styleme-475201 \
    --data-prefix json \
    --images-prefix images \
    --experiments-dir src/models/train/experiments \
    --output-dir catalog \
    --gender all

# Rename to version name
mv catalog/v_* catalog/v_men_women_$(date +%Y%m%d)

# Record GCS snapshot
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_men_women_*/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201

# Add to DVC
python data_versioning/dvc_manager.py add-catalog v_men_women_*

# Create tag
python data_versioning/dvc_manager.py tag catalog-v_men_women_* -m "Catalog: Men + Women"
```

## Viewing Version History

```bash
# View all versions
python data_versioning/dvc_manager.py history

# List all tags
python data_versioning/dvc_manager.py list-tags

# View specific version
python data_versioning/dvc_manager.py history catalog/v_men_only_*
```

## Git Version Control

### How Git Tracks Versions

Every time you commit changes, Git creates a new version:

1. **Initial commit**: When you first add data to DVC and commit `.dvc` files
2. **Subsequent commits**: Each time you:
   - Add new catalog version
   - Update existing catalog
   - Modify `.dvc` files
   - Commit these changes

### Version History in Git

```bash
# View commit history for .dvc files
git log --oneline --all -- "*.dvc"

# View detailed history
git log --graph --oneline --all

# View changes in a specific commit
git show <commit-hash>
```

### Example Workflow

```bash
# 1. Build and add version 1
python data_versioning/dvc_manager.py add-catalog v_men_only_20251123
git add catalog/v_men_only_20251123.dvc
git commit -m "Add catalog version: Men only"

# 2. Build and add version 2
python data_versioning/dvc_manager.py add-catalog v_men_women_20251123
git add catalog/v_men_women_20251123.dvc
git commit -m "Add catalog version: Men + Women"

# 3. View history
git log --oneline
# Shows:
# abc123 Add catalog version: Men + Women
# def456 Add catalog version: Men only
```

### Complete Version Tracking

You have three levels of versioning:

1. **Git Commits**: Every commit is a version snapshot
   - Tracked automatically when you commit `.dvc` files
   - Full history with messages and timestamps

2. **Git Tags**: Named milestones
   - Created with `python data_versioning/dvc_manager.py tag`
   - Easy to reference specific versions

3. **GCS Snapshots**: Source data state
   - Recorded in `manifest.json`
   - Shows which GCS files were used

### Best Practices

1. **Commit after each version**: Always commit `.dvc` files after adding new data
2. **Use descriptive commit messages**: Include version name and description
3. **Create tags for releases**: Tag important versions for easy reference
4. **Record GCS snapshots**: Always record GCS state when building new versions

## Example: Complete Workflow

```bash
# Build version 1
python containers/inference/build_catalog_index.py --gender men
mv catalog/v_* catalog/v_men_only_20251123

# Record and version
python data_versioning/gcs_snapshot_tracker.py catalog/v_men_only_20251123/manifest.json
python data_versioning/dvc_manager.py add-catalog v_men_only_20251123
python data_versioning/dvc_manager.py tag catalog-v_men_only_20251123 -m "Men only"
git add catalog/v_men_only_20251123.dvc .dvc/
git commit -m "Add catalog version: Men only"

# Build version 2
python containers/inference/build_catalog_index.py --gender all
mv catalog/v_* catalog/v_men_women_20251123

# Record and version
python data_versioning/gcs_snapshot_tracker.py catalog/v_men_women_20251123/manifest.json
python data_versioning/dvc_manager.py add-catalog v_men_women_20251123
python data_versioning/dvc_manager.py tag catalog-v_men_women_20251123 -m "Men + Women"
git add catalog/v_men_women_20251123.dvc
git commit -m "Add catalog version: Men + Women"

# View history
python data_versioning/dvc_manager.py history
git log --oneline
```

