# TEST.md

## Quick Test (1–2 minutes)

```bash
pip install -r requirements.txt
python test_simple.py
```

Check `test_output/` for `test_output.png` (transparent background).

## Manual test with your photo

```bash
# Fast positional-args script
python background_removal_fast.py your.jpg out.png

# Alt: flag-based script
python background_removal.py --input your.jpg --output out.png
```

## Expected

* Log shows the model loads, then a file appears at the output path.
* Opening the PNG should show your garment with transparency.

## If something breaks

* Re-run install: `pip install -r requirements.txt`
* Try CPU: `CUDA_VISIBLE_DEVICES="" python background_removal_fast.py your.jpg out.png`
* Try different image / smaller resolution (≤2048 on the long side).

---