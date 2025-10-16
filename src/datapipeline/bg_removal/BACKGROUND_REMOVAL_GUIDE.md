# BACKGROUND_REMOVAL_GUIDE.md

## Need to know

* **Default model:** `briaai/RMBG-1.4` (fast + strong baseline)
* **Alternative:** `ZhengPeng7/BiRefNet` (slower, cleaner edges)
* **I/O:** PNG with alpha channel; JPG/WebP inputs supported.

## Common tasks

### 1) Single image (fastest)

```bash
python background_removal_fast.py <in> <out.png>
```

Use this for quick local testing or batch scripting.

### 2) Single image with flags / model switch

```bash
python background_removal.py --input <in> --output <out.png> [--model briaai/RMBG-1.4]
```

### 3) Batch a folder

```bash
python batch_processor.py --input ./wardrobe --output ./processed --workers 4
```

* Add `--recursive` to include subfolders.
* Add `--format webp` for smaller outputs.

## Quality tips

* Aim for ≥512px on the short side, decent lighting, centered subject.
* For tricky edges (hairy knits, sheer fabrics), try the BiRefNet model.
* If halos appear, re-save input as sRGB JPEG and retry; optionally downsize to ≤2048px long edge.

## Performance tips

* GPU is auto-used if available (PyTorch). Verify with:

```python
import torch; print(torch.cuda.is_available())
```

* CPU is fine; just slower. Keep `--workers` low (1–4) to avoid thrashing.

## Troubleshooting

* **Downloads are slow**: first run downloads weights; subsequent runs are cached.
* **OOM on GPU**: close other GPU apps or switch to CPU (`CUDA_VISIBLE_DEVICES=""`).
* **Poor cut-out**: try alternative model, or pre-sharpen image slightly before processing.

## Fine-tuning

```bash
python finetune_background_removal.py \
  --train-images ./dataset/train/images \
  --train-masks  ./dataset/train/masks \
  --val-images   ./dataset/val/images \
  --val-masks    ./dataset/val/masks \
  --model briaai/RMBG-1.4 --epochs 10 --batch-size 4 --lr 1e-5
```

---

# Housekeeping — what can be deleted?

**Keep (runtime):**

* `background_removal_fast.py` — your go-to, simple positional-args CLI.
* `background_removal.py` — flag-based CLI + options (model switch, etc.).
* `batch_processor.py` — folder processing; used for bulk runs.
* `requirements.txt` — dependency lock for runtime.

**Keep (tests/docs):**

* `test_simple.py` — sanity check + smoke test used by docs.
* `README.md`, `TEST.md`, `BACKGROUND_REMOVAL_GUIDE.md` — these cleaned versions.

**Optional (remove if you won’t use):**

* `finetune_background_removal.py` — only for training/fine-tuning.
* `examples/` — nice-to-have usage samples; safe to delete for a lean repo.
* `quick_start.py` — overlaps with `test_simple.py`; you can remove to avoid duplication.

**Folders you provide:**

* `test_pics/`, `test_output/` — user-created; keep as needed.

> If you’re keeping the project strictly to “run the model”, the truly minimal set is:
> `background_removal_fast.py`, `background_removal.py`, `batch_processor.py`, `requirements.txt`, `test_simple.py`, plus one README.
