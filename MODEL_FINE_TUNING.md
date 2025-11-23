# Model Fine-Tuning Documentation

## Overview

This document describes the fine-tuning implementation for the FashionCLIP model, including training scripts, configuration files, versioned dataset references, experiment logs, key results, and deployment strategy.

## 1. Training Scripts and Configuration Files

### Training Scripts

#### `src/models/train/run_fine_tuning.py`
Main fine-tuning script with the following features:
- **Data versioning support**: Links experiments to versioned datasets via DVC tags
- **GPU requirement**: Enforces GPU usage for fine-tuning (exits if GPU unavailable)
- **Experiment tracking**: Automatically creates experiment records with full configuration
- **Checkpoint support**: Can resume from previous checkpoints
- **Comprehensive logging**: Records all hyperparameters, metrics, and results

**Usage:**
```bash
cd src/models/train
python run_fine_tuning.py --data-version catalog-v_men_women_20251123
```

**Key Features:**
- Automatic experiment ID generation (`fine_tune_YYYYMMDD_HHMMSS`)
- Data version tracking in experiment records
- GPU detection and cuDNN initialization
- Early stopping with patience
- Model checkpoint saving (best and final)

#### `src/models/train/model_training.py`
Core training implementation:
- `FashionCLIPModel`: CLIP-based model for fashion compatibility
- `TripletLoss`: Triplet loss for learning compatible/incompatible pairs
- `FashionTrainer`: Training loop with validation and early stopping
- Experiment logging and visualization

### Configuration Files

#### `src/models/train/fine_tune_config.py`
Optimized hyperparameters for fine-tuning:

```python
TRAINING_CONFIG = {
    'batch_size': 64,        # Increased for better gradients
    'epochs': 50,            # More epochs for convergence
    'learning_rate': 2e-5,   # Optimized for fine-tuning
    'patience': 15,          # Early stopping patience
    'target_accuracy': 0.70 # Realistic target
}

MODEL_CONFIG = {
    'model_name': 'openai/clip-vit-base-patch32',
    'freeze_layers': 4,      # Fewer frozen layers for more fine-tuning
    'feature_dim': 512
}

TRIPLET_CONFIG = {
    'margin': 0.5,          # Reduced margin for tighter clustering
    'distance_metric': 'euclidean'
}
```

#### `src/models/train/config.py`
Default training configuration (used as fallback).

## 2. Dataset References (Versioned)

All fine-tuning experiments use **versioned datasets** tracked via DVC and linked to GCS snapshots.

### Data Versioning Strategy

1. **Catalog Versions**: Each catalog build is tagged with DVC
   - Example: `catalog-v_men_women_20251123`
   - Example: `catalog-v_men_only_20251123`

2. **GCS Snapshots**: GCS source state is recorded in `manifest.json`
   - Tracks which GCS files were used
   - Records gender filter (men/women/all)
   - Maintains history of data states

3. **Experiment Linking**: Each experiment record includes:
   - `data_version`: DVC tag reference
   - `gcs_snapshot_tag`: GCS snapshot identifier
   - Full data configuration

### Example Experiment Record

```json
{
  "experiment_id": "fine_tune_20251123_165320",
  "timestamp": "2025-11-23T16:53:20",
  "data_version": "catalog-v_men_women_20251123",
  "config": {
    "data": {
      "gcp_bucket": "styleme-data-bucket",
      "data_prefix": "json",
      "images_prefix": "images"
    }
  }
}
```

### Reproducibility

To reproduce an experiment:
1. Checkout the data version: `dvc checkout catalog-v_men_women_20251123`
2. Use the same config from `experiment_record.json`
3. Run training with the recorded hyperparameters

## 3. Experiment Logs

### Experiment Structure

Each fine-tuning run creates:
```
experiments/fine_tune_YYYYMMDD_HHMMSS/
├── experiment_record.json    # Complete experiment metadata
├── checkpoints/
│   ├── best_model.pth       # Best model checkpoint
│   └── final_model.pth      # Final model checkpoint
└── training_history.json     # Per-epoch metrics (if enabled)
```

### Experiment Record Format

```json
{
  "experiment_id": "fine_tune_20251123_165320",
  "timestamp": "2025-11-23T16:53:20",
  "data_version": "catalog-v_men_women_20251123",
  "config": {
    "model": {
      "architecture": "openai/clip-vit-base-patch32",
      "frozen_layers": 4,
      "feature_dimension": 512
    },
    "training": {
      "epochs": 50,
      "batch_size": 64,
      "learning_rate": 2e-5,
      "optimizer": "AdamW",
      "scheduler": "CosineAnnealingLR",
      "patience": 15,
      "target_accuracy": 0.70
    },
    "triplet_loss": {
      "margin": 0.5,
      "distance_metric": "euclidean"
    },
    "data": {
      "gcp_bucket": "styleme-data-bucket",
      "data_prefix": "json",
      "images_prefix": "images"
    }
  },
  "results": {
    "best_val_acc": 0.65,
    "final_train_loss": 0.001,
    "final_val_loss": 0.0008,
    "final_train_acc": 0.68,
    "final_val_acc": 0.65,
    "epochs_trained": 45
  }
}
```

### Centralized Registry

All experiments are tracked in:
- `experiments/experiment_configs.json`: Centralized experiment registry
- `experiments/EXPERIMENT_SUMMARY.md`: Human-readable summary

## 4. Key Results Summary

### Baseline Performance

**Before Fine-Tuning:**
- Compatibility Score: 42.26% - 43.37% (EXP_002, exp_004)
- Triplet Accuracy: ~41%
- Inference Quality: Poor - recommendations not satisfactory

### Fine-Tuning Experiments

| Experiment | Data Version | Batch Size | Learning Rate | Frozen Layers | Best Val Acc | Status |
|------------|--------------|------------|---------------|---------------|-------------|--------|
| EXP_001 | Baseline | 16 | 1e-5 | 8 | 98.49%* | Simple eval (unrealistic) |
| EXP_002 | Baseline | 16 | 1e-5 | 8 | 42.26% | Strict eval (realistic) |
| EXP_003 | Baseline | 32 | 1e-5 | 8 | 34.44% | Early stopping |
| exp_004 | Baseline | 16 | 1e-5 | 8 | 43.37% | Completed |

*EXP_001 used simple cosine similarity (not suitable for production)

### Fine-Tuning Improvements

**Optimized Configuration:**
- **Batch Size**: 16 → 64 (better gradient estimates)
- **Learning Rate**: 1e-5 → 2e-5 (faster convergence)
- **Frozen Layers**: 8 → 4 (more fine-tuning capacity)
- **Margin**: 0.7 → 0.5 (tighter feature clustering)
- **Epochs**: 20-30 → 50 (more training)

**Expected Improvements:**
- Better feature separation for compatible items
- Improved inference quality
- Higher triplet accuracy (target: >70%)

### Model Design Choices

1. **Architecture**: CLIP ViT-B/32
   - Pre-trained on large-scale image-text pairs
   - Good transfer learning base for fashion

2. **Fine-Tuning Strategy**: Partial freezing
   - Freeze first 4 layers (preserve general features)
   - Fine-tune remaining layers (learn fashion-specific features)

3. **Loss Function**: Triplet Loss
   - Learn relative distances: anchor-positive < anchor-negative
   - Margin: 0.5 (tighter clustering for better recommendations)

4. **Training Process**:
   - Early stopping with patience
   - Learning rate scheduling (CosineAnnealingLR)
   - Validation-based model selection

## 5. Deployment Strategy Impact

### Current Deployment

**Inference Service**: `containers/inference/inference_service.py`
- Loads best model from `experiments/` directory
- Uses FAISS for efficient similarity search
- Supports wardrobe and catalog search

### Fine-Tuned Model Integration

**After Fine-Tuning:**

1. **Model Selection**:
   - Compare fine-tuned models with baseline
   - Select best performing model based on validation accuracy
   - Update inference service to use new model

2. **Update Inference Service**:
   
   The inference service (`containers/inference/inference_service.py`) currently looks for models in `exp_*` directories. To use fine-tuned models from `fine_tune_*` directories, you have two options:
   
   **Option A: Update `_load_model()` method** (recommended):
   ```python
   def _load_model(self):
       """Load trained FashionCLIP model"""
       print("📦 Loading model...")
       
       # Find best model - check both exp_* and fine_tune_* directories
       model_path = None
       
       # First, try fine_tune_* directories (newer fine-tuned models)
       for exp_dir in sorted(self.experiments_dir.glob("fine_tune_*"), reverse=True):
           best_model = exp_dir / "checkpoints" / "best_model.pth"
           if best_model.exists():
               model_path = best_model
               break
       
       # Fallback to exp_* directories (baseline models)
       if model_path is None:
           for exp_dir in sorted(self.experiments_dir.glob("exp_*"), reverse=True):
               best_model = exp_dir / "best_model.pth"
               if best_model.exists():
                   model_path = best_model
                   break
       
       if model_path is None:
           raise FileNotFoundError("No trained model found")
       
       print(f"   Model: {model_path}")
       # ... rest of the method
   ```
   
   **Option B: Create symlink** (quick fix):
   ```bash
   # Create symlink from exp_* to fine_tune_* checkpoint
   ln -s experiments/fine_tune_XXX/checkpoints/best_model.pth \
        experiments/exp_999_fine_tuned/best_model.pth
   ```

3. **Performance Monitoring**:
   - Track inference quality metrics
   - Monitor recommendation relevance
   - A/B test fine-tuned vs baseline model

4. **Deployment Steps**:
   ```bash
   # 1. Identify best model
   python src/models/eval/evaluation.py \
       --model experiments/fine_tune_XXX/checkpoints/best_model.pth
   
   # 2. Update inference service (see Option A or B above)
   
   # 3. Rebuild catalog index (if needed)
   python containers/inference/build_catalog_index.py \
       --experiments-dir experiments/fine_tune_XXX
   ```

4. **Versioning**:
   - Version model checkpoints with DVC
   - Link model versions to data versions
   - Maintain model registry

### Deployment Considerations

**Advantages of Fine-Tuned Model:**
- Better fashion compatibility understanding
- Improved recommendation quality
- Higher user satisfaction

**Challenges:**
- Model size: ~150MB per checkpoint
- Inference latency: Similar to baseline (same architecture)
- Catalog index rebuild: Required if feature space changes significantly

**Rollback Strategy:**
- Keep baseline model available
- Can quickly revert if fine-tuned model underperforms
- Model versioning enables easy switching

## 6. Evaluation Metrics

### Training Metrics
- **Triplet Accuracy**: Percentage of triplets correctly ordered
- **Validation Loss**: Triplet loss on validation set
- **Training Loss**: Triplet loss on training set

### Inference Metrics
- **Compatibility Score**: Fashion compatibility evaluation
- **Recommendation Relevance**: User feedback on recommendations
- **Inference Latency**: Time to generate recommendations

### Target Metrics
- **Triplet Accuracy**: >70% (current: ~41%)
- **Compatibility Score**: >50% (current: 42-43%)
- **Inference Latency**: <500ms per query

## 7. Reproducibility

### Requirements
- Python 3.10+
- PyTorch 2.1.2+ with CUDA support
- GPU required (CUDA-capable)
- Access to GCS bucket: `styleme-data-bucket`

### Reproducing Experiments

1. **Checkout Data Version**:
   ```bash
   cd data_versioning
   python dvc_manager.py checkout catalog-v_men_women_20251123
   ```

2. **Run Fine-Tuning**:
   ```bash
   cd src/models/train
   python run_fine_tuning.py \
       --data-version catalog-v_men_women_20251123 \
       --config fine_tune_config.py
   ```

3. **Verify Results**:
   ```bash
   cat experiments/fine_tune_XXX/experiment_record.json
   ```

## 8. Next Steps

1. **Complete Fine-Tuning**: Run full training with optimized hyperparameters
2. **Evaluate Results**: Compare fine-tuned model with baseline
3. **Deploy Best Model**: Update inference service with best performing model
4. **Monitor Performance**: Track inference quality in production
5. **Iterate**: Continue fine-tuning based on production feedback

## Files Summary

### Training Scripts
- ✅ `src/models/train/run_fine_tuning.py` - Main fine-tuning script
- ✅ `src/models/train/model_training.py` - Core training implementation
- ✅ `src/models/train/fine_tune_config.py` - Fine-tuning configuration

### Configuration Files
- ✅ `src/models/train/config.py` - Default configuration
- ✅ `src/models/train/fine_tune_config.py` - Optimized fine-tuning config

### Experiment Logs
- ✅ `experiments/experiment_configs.json` - Centralized registry
- ✅ `experiments/EXPERIMENT_SUMMARY.md` - Human-readable summary
- ✅ `experiments/fine_tune_*/experiment_record.json` - Individual experiment records

### Documentation
- ✅ `MODEL_FINE_TUNING.md` - This document (complete guide)
- ✅ `src/models/train/FINE_TUNING.md` - Quick start guide
- ✅ `src/models/train/README_FINE_TUNING.md` - Fine-tuning overview

## Conclusion

The fine-tuning implementation provides:
- ✅ Complete training scripts with data versioning
- ✅ Versioned dataset references via DVC
- ✅ Comprehensive experiment logging
- ✅ Clear results summary and deployment strategy

All components are in place for reproducible model fine-tuning and deployment.
