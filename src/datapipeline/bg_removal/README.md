# README.md

## StyleMe — Background Removal

Fast, reliable background removal for wardrobe photos. Works on CPU or GPU.

### 1) Install

```bash
pip install -r requirements.txt
```

### 2) Quick sanity check

```bash
python test_simple.py
```

This will download the model (first run only) and save results into `test_output/`.

### 3) Use it

**Single image (fast path):**

```bash
python background_removal_fast.py <input_image> <output_png>
# example
python background_removal_fast.py test_pics/ebay.jpg test_output/ebay_result.png
```

**Single image (flag-based script):**

```bash
python background_removal.py --input <input_image> --output <output_png>
```

**Folder of images:**

```bash
python batch_processor.py --input ./photos --output ./results --workers 4
```

**Switch model (optional):**

```bash
python background_removal.py --input img.jpg --output out.png --model briaai/RMBG-1.4   # default, fast/good
# or
python background_removal.py --input img.jpg --output out.png --model ZhengPeng7/BiRefNet # slower, higher quality
```

### Notes

* Outputs are PNG with transparent background.
* GPU auto-detected if available; otherwise runs on CPU (slower).
* First run downloads ~2GB of weights.

### Troubleshooting (quick)

* **ModuleNotFoundError** → `pip install -r requirements.txt`
* **CUDA out of memory** → close other GPU apps, or force CPU by setting `CUDA_VISIBLE_DEVICES=""`.
* **Slow first inference** → model download/caching is normal on first run.

---