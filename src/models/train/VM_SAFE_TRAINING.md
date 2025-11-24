# VM-Safe Training Configuration

## Problem
Training causes VM to crash due to:
- Memory/GPU memory exhaustion (OOM)
- CPU overload from too many workers
- I/O overload from data loading

## Solution: Optimized Configuration

### Changes Made

1. **Reduced Batch Size**: 64 → 16
   - Prevents GPU memory overflow
   - Reduces system memory pressure

2. **Disabled Multi-threading**: num_workers: 4 → 0
   - Prevents CPU overload
   - Prevents shared memory issues
   - Single-threaded data loading (safer for VM)

3. **Disabled Pin Memory**: pin_memory: True → False
   - Saves system memory
   - Reduces memory fragmentation

4. **Reduced Prefetch**: prefetch_factor: default → 2
   - Limits memory usage
   - Prevents buffer overflow

5. **Gradient Accumulation**: Added support (4 steps)
   - Simulates larger batch size (16 × 4 = 64 effective)
   - Maintains training quality with smaller batches

## Usage

### Before Training: Check Resources

```bash
# In a separate terminal, monitor resources
cd src/models/train
./monitor_resources.sh
```

Or manually check:
```bash
# Memory
free -h

# GPU
nvidia-smi

# CPU
htop
```

### Run Training

```bash
cd src/models/train
python run_fine_tuning.py \
    --data-version catalog-v_men_women_20251123 \
    --config fine_tune_config.py
```

The script will:
1. Check system resources before starting
2. Use VM-safe settings (batch_size=16, num_workers=0)
3. Monitor GPU memory during training
4. Save experiment logs automatically

## Configuration File

All settings are in `fine_tune_config.py`:

```python
TRAINING_CONFIG = {
    'batch_size': 16,              # Reduced from 64
    'num_workers': 0,              # Single-threaded (was 4)
    'pin_memory': False,           # Disabled to save memory
    'prefetch_factor': 2,          # Reduced prefetch
    'gradient_accumulation_steps': 4,  # Simulate larger batch
}
```

## If VM Still Crashes

1. **Further reduce batch_size**: Try 8 or 4
2. **Limit data**: Set `max_samples_per_file` in config
3. **Reduce epochs**: Start with fewer epochs to test
4. **Check other processes**: Close unnecessary applications
5. **Increase swap**: If possible, add more swap space

## Monitoring

Watch for:
- Memory usage > 80% → Reduce batch_size
- CPU usage > 80% → Already handled (num_workers=0)
- GPU memory > 90% → Reduce batch_size
- Disk I/O 100% → Reduce prefetch_factor

