# Model Training & Fine-Tuning Summary

## Training Process

### Architecture

- **Model**: FashionCLIP (based on OpenAI CLIP ViT-B/32 `openai/clip-vit-base-patch32`)
- **Fine-Tuning Strategy**: Partial freezing (baseline: 8 layers frozen, fine-tuning: 4 layers frozen)
- **Loss Function**: Triplet Loss (baseline: margin 0.7, fine-tuning: margin 0.5)
- **Optimizer**: AdamW (baseline: lr 5e-6, fine-tuning: lr 2e-5)
- **Scheduler**: CosineAnnealingLR

### Training Configuration

**Baseline Configuration** (`config.py`):
- Batch Size: 32
- Learning Rate: 5e-6
- Epochs: 20
- Frozen Layers: 8
- Margin: 0.7
- Early Stopping: Patience of 10 epochs

**Fine-Tuning Configuration** (`fine_tune_config.py`):
- Batch Size: 24 (optimized for VM safety)
- Learning Rate: 2e-5 (increased from baseline)
- Epochs: 12 (reduced for faster training)
- Frozen Layers: 4 (reduced from 8 for more fine-tuning)
- Margin: 0.5 (reduced from 0.7 for tighter clustering)
- Early Stopping: Patience of 8 epochs
- Target Accuracy: 70%

### Training Workflow

1. **Data Versioning**: All experiments reference versioned datasets via DVC tags
2. **GPU Requirement**: Training requires CUDA-capable GPU
3. **Experiment Tracking**: Automatic experiment ID generation (`fine_tune_YYYYMMDD_HHMMSS`)
4. **Checkpointing**: Saves best and final model checkpoints
5. **Validation**: Early stopping based on validation accuracy

### Running Training

```bash
cd src/models/train
python run_fine_tuning.py \
    --data-version catalog-v_men_women_20251123 \
    --config fine_tune_config.py
```

## Results

### Baseline Performance (Before Fine-Tuning)

- **Compatibility Score**: 42.26% (EXP_002)
- **Triplet Accuracy**: ~41%
- **Inference Quality**: Poor - recommendations not satisfactory

### Training Experiments

| Experiment | Batch Size | Learning Rate | Frozen Layers | Best Score | Status |
|------------|------------|---------------|---------------|-----------|--------|
| EXP_001 | 16 | 1e-5 | 8 | 98.49%* | Simple eval (unrealistic) |
| EXP_002 | 16 | 1e-5 | 8 | 42.26% | Strict eval (realistic) |
| EXP_003 | 32 | 1e-5 | 8 | 34.44% | Early stopping (16 epochs) |

*EXP_001 used simple cosine similarity (not suitable for production)

**Note**: Only EXP_001, EXP_002, and EXP_003 have corresponding experiment directories. Fine-tuning experiments use the `fine_tune_*` naming convention.

### Fine-Tuning Goals

The fine-tuning configuration aims to improve upon baseline performance through:
- Reduced frozen layers (8 → 4) for more model adaptation
- Higher learning rate (5e-6 → 2e-5) for faster convergence
- Tighter margin (0.7 → 0.5) for better feature clustering
- Target: >70% triplet accuracy (current baseline: ~41%)

## Deployment Implications

### Model Integration

**Inference Service**: `containers/inference/inference_service.py`
- Currently loads models from `experiments/exp_*` directories
- Requires update to support `fine_tune_*` directories
- Uses FAISS for efficient similarity search

### Deployment Steps

1. **Select Best Model**: Compare fine-tuned models with baseline
2. **Update Inference Service**: Modify `_load_model()` to check `fine_tune_*` directories
3. **Rebuild Catalog Index**: Required if feature space changes significantly
4. **Version Model**: Add model checkpoint to DVC with data version reference

### Deployment Considerations

**Advantages:**
- Better fashion compatibility understanding
- Improved recommendation quality
- Higher user satisfaction

**Challenges:**
- Model size: ~150MB per checkpoint
- Catalog index rebuild required if feature space changes
- Need rollback strategy if performance degrades

**Rollback Strategy:**
- Keep baseline model available
- Model versioning enables easy switching between versions
- Can quickly revert if fine-tuned model underperforms

### Performance Targets

- **Triplet Accuracy**: >70% (current: ~41%)
- **Compatibility Score**: >50% (current: 42.26%)
- **Inference Latency**: <500ms per query

