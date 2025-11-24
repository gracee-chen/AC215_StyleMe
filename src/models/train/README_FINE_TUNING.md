# Model Fine-Tuning Documentation

## Overview

This directory contains scripts and configurations for fine-tuning the FashionCLIP model to improve inference quality.

## Current Performance

- **Best Compatibility Score**: 42.26% - 43.37%
- **Triplet Accuracy**: ~41%
- **Status**: Needs improvement

## Files

- `FINE_TUNING.md` - Quick start guide
- `FINE_TUNING_GUIDE.md` - Detailed strategy
- `fine_tune_config.py` - Fine-tuning configuration
- `run_fine_tuning.py` - Fine-tuning script
- `model_training.py` - Core training code (updated with data versioning)

## Quick Start

### 1. Ensure Data Version is Recorded

```bash
# Record current data version
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_2025-10-24_model-b1/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201 \
    --gender all
```

### 2. Run Fine-Tuning

```bash
cd src/models/train
python run_fine_tuning.py --data-version catalog-v_men_women_20251123
```

### 3. Check Results

Results are saved to `experiments/fine_tune_YYYYMMDD_HHMMSS/`:
- `experiment_record.json` - Full experiment details
- `checkpoints/best_model.pth` - Best model
- Training history and plots

## Experiment Tracking

Each experiment records:
- Data version reference
- Hyperparameters
- Training metrics
- Evaluation results
- Model checkpoint path

All experiments are logged in `experiments/experiment_configs.json`.

## Deployment

After fine-tuning:
1. Evaluate on test set
2. Compare with baseline
3. If improved, update inference service
4. Document performance improvements

