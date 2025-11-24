# Model Fine-Tuning Guide

## Current Model Performance

Based on experiment history:
- **Best Score**: 42.26% - 43.37% compatibility (EXP_002, exp_004)
- **Triplet Accuracy**: ~41% (needs improvement)
- **Inference Quality**: Poor - results not satisfactory

## Fine-Tuning Strategy

### 1. Data Versioning

All training uses versioned datasets:
- Reference specific data versions in training configs
- Link experiments to data versions for reproducibility

### 2. Hyperparameter Tuning

Key areas to improve:
- **Learning Rate**: Current 1e-5, try 5e-6, 2e-5
- **Batch Size**: Current 16-32, try 64 for better gradients
- **Margin**: Current 0.7, try 0.5, 1.0 for triplet loss
- **Frozen Layers**: Current 8, try 4, 6 for more fine-tuning

### 3. Training Improvements

- Increase training epochs (current: 20-30, try 50+)
- Use learning rate scheduling
- Add data augmentation
- Improve negative sampling strategy

## Fine-Tuning Workflow

### Step 1: Prepare Versioned Dataset

```bash
# Ensure data version is recorded
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_2025-10-24_model-b1/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201
```

### Step 2: Create Fine-Tuning Config

Create experiment-specific config with:
- Data version reference
- Hyperparameters
- Training settings

### Step 3: Run Training

```bash
cd src/models/train
python model_training.py --config fine_tune_config.py
```

### Step 4: Evaluate and Log

- Run evaluation after training
- Log results to experiments/
- Compare with previous experiments

## Experiment Tracking

Each fine-tuning experiment should record:
- Data version used
- Hyperparameters
- Training metrics
- Evaluation results
- Model checkpoint path

