# Model Fine-Tuning

## Current Performance Issues

Based on experiment history:
- **Best Compatibility Score**: 42.26% - 43.37% (needs improvement)
- **Triplet Accuracy**: ~41% (target: >70%)
- **Inference Quality**: Poor - recommendations not satisfactory

## Fine-Tuning Strategy

### 1. Data Versioning

All training experiments reference versioned datasets:
- Link to specific catalog version via DVC tags
- Record GCS source state in experiment logs
- Ensure reproducibility

### 2. Hyperparameter Improvements

Key changes from current config:
- **Learning Rate**: 1e-5 → 2e-5 (faster learning)
- **Batch Size**: 16-32 → 64 (better gradients)
- **Frozen Layers**: 8 → 4 (more fine-tuning)
- **Margin**: 0.7 → 0.5 (tighter clustering)
- **Epochs**: 20-30 → 50 (more training)

### 3. Training Process

1. Use versioned dataset
2. Fine-tune with improved hyperparameters
3. Evaluate on validation set
4. Log experiment with data version reference
5. Compare with previous experiments

## Running Fine-Tuning

**Note: GPU is required for fine-tuning. The script will exit with an error if GPU is not available.**

### Check GPU Availability

```bash
# Check if CUDA is available
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Check GPU info
nvidia-smi
```

### Basic Fine-Tuning

```bash
cd src/models/train
python run_fine_tuning.py --data-version catalog-v_men_women_20251123
```

The script will automatically:
- Detect and use GPU if available
- Exit with error if GPU is not available (required for fine-tuning)

### With Custom Config

```bash
python run_fine_tuning.py \
    --config fine_tune_config.py \
    --data-version catalog-v_men_women_20251123
```

### Resume from Checkpoint

```bash
python run_fine_tuning.py \
    --resume experiments/exp_XXX/checkpoints/best_model.pth \
    --data-version catalog-v_men_women_20251123
```

## Experiment Tracking

Each fine-tuning run creates:
- `experiments/fine_tune_YYYYMMDD_HHMMSS/`
  - `experiment_record.json` - Full config and results
  - `checkpoints/best_model.pth` - Best model
  - `checkpoints/final_model.pth` - Final model
  - Training history and plots

## Expected Improvements

With fine-tuning:
- **Triplet Accuracy**: 41% → 60-70%
- **Compatibility Score**: 43% → 55-65%
- **Inference Quality**: Better recommendations

## Deployment Strategy

After fine-tuning:
1. Evaluate on test set
2. Compare with baseline
3. If improved, update inference service to use new model
4. Document performance improvements

