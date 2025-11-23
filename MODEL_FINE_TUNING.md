# Model Fine-Tuning Implementation

## Summary

This document describes the fine-tuning implementation for improving model inference quality. The current model achieves 42-43% compatibility, which needs improvement.

## Implementation Components

### 1. Training Scripts and Config Files

**Files Created:**
- `src/models/train/run_fine_tuning.py` - Fine-tuning script with data versioning support
- `src/models/train/fine_tune_config.py` - Optimized hyperparameters for fine-tuning
- `src/models/train/model_training.py` - Updated to record data versions in experiments

**Key Features:**
- References versioned datasets via DVC tags
- Records data version in experiment logs
- Supports resuming from checkpoints
- Tracks all hyperparameters and results

### 2. Dataset References (Versioned)

All training experiments reference versioned datasets:
- Data version specified via `--data-version` argument
- Recorded in `experiment_record.json`
- Links to DVC tags (e.g., `catalog-v_men_women_20251123`)
- GCS source state tracked in manifest files

**Example:**
```python
DATA_CONFIG = {
    'data_version': 'v_men_women_20251123',
    'gcs_snapshot_tag': 'catalog-v_men_women_20251123',
}
```

### 3. Experiment Logs

Each fine-tuning run creates:
- `experiments/fine_tune_YYYYMMDD_HHMMSS/experiment_record.json`
  - Full configuration (model, training, data)
  - Data version reference
  - Training metrics (loss, accuracy)
  - Evaluation results
  - Model checkpoint paths

- `experiments/experiment_configs.json` - Centralized experiment registry

**Experiment Record Structure:**
```json
{
  "experiment_id": "fine_tune_20251123_120000",
  "timestamp": "2025-11-23T12:00:00",
  "data_version": "catalog-v_men_women_20251123",
  "config": {
    "model": {...},
    "training": {...},
    "data": {...}
  },
  "results": {
    "best_val_acc": 0.65,
    "final_train_loss": 0.001,
    "epochs_trained": 45
  }
}
```

## Fine-Tuning Strategy

### Hyperparameter Improvements

| Parameter | Current | Fine-Tuning | Reason |
|-----------|---------|-------------|--------|
| Learning Rate | 1e-5 | 2e-5 | Faster learning |
| Batch Size | 16-32 | 64 | Better gradients |
| Frozen Layers | 8 | 4 | More fine-tuning |
| Margin | 0.7 | 0.5 | Tighter clustering |
| Epochs | 20-30 | 50 | More training |

### Expected Results

- **Triplet Accuracy**: 41% → 60-70%
- **Compatibility Score**: 43% → 55-65%
- **Inference Quality**: Improved recommendations

## Usage

**⚠️ GPU Required**: Fine-tuning requires GPU. The script will exit if GPU is not available.

### Check GPU

```bash
# Verify CUDA is available
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
nvidia-smi
```

### Basic Fine-Tuning

```bash
cd src/models/train
python run_fine_tuning.py --data-version catalog-v_men_women_20251123
```

The script will:
- ✅ Automatically detect and use GPU
- ❌ Exit with error if GPU unavailable (GPU required for training)

### With Custom Config

```bash
python run_fine_tuning.py \
    --config fine_tune_config.py \
    --data-version catalog-v_men_women_20251123
```

### Resume from Checkpoint

```bash
python run_fine_tuning.py \
    --resume experiments/fine_tune_XXX/checkpoints/best_model.pth \
    --data-version catalog-v_men_women_20251123
```

## Key Results Summary

### Current Baseline
- Compatibility: 42-43%
- Triplet Accuracy: ~41%
- Status: Poor inference quality

### Fine-Tuning Goals
- Compatibility: 55-65%
- Triplet Accuracy: 60-70%
- Status: Production-ready

## Deployment Strategy

After fine-tuning:

1. **Evaluate on Test Set**
   ```bash
   python src/models/eval/evaluation.py \
       --model experiments/fine_tune_XXX/checkpoints/best_model.pth
   ```

2. **Compare with Baseline**
   - Review experiment records
   - Compare metrics in `experiment_configs.json`

3. **Update Inference Service**
   - If improved, update model path in `containers/inference/inference_service.py`
   - Deploy new model checkpoint

4. **Document Performance**
   - Update deployment docs
   - Record performance improvements

## Reproducibility

All experiments are reproducible through:
- **Data Versioning**: DVC tags reference specific data states
- **Config Files**: All hyperparameters recorded
- **Experiment Logs**: Complete training history saved
- **Model Checkpoints**: Best and final models saved

## Files Structure

```
src/models/train/
├── run_fine_tuning.py          # Fine-tuning script
├── fine_tune_config.py          # Fine-tuning config
├── model_training.py            # Core training (updated)
├── FINE_TUNING.md              # Quick guide
├── FINE_TUNING_GUIDE.md        # Detailed strategy
├── README_FINE_TUNING.md       # Documentation
└── experiments/
    ├── fine_tune_YYYYMMDD_HHMMSS/
    │   ├── experiment_record.json
    │   └── checkpoints/
    │       ├── best_model.pth
    │       └── final_model.pth
    └── experiment_configs.json
```

