# Quick Test Guide - StyleMe Background Removal

## 🚀 Fastest Test (One Command)

```bash
pip install -r requirements.txt && python test_simple.py
```

**Done!** Check `test_output/` folder for results.

---

## OR: Test in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Quick Test
```bash
python quick_start.py
```

This will:
- ✓ Check all dependencies
- ✓ Download the model (~2GB, one-time)
- ✓ Create a test image
- ✓ Remove background
- ✓ Save results to `test_data/` folder

**Expected output:**
```
✓ All dependencies installed!
✓ Model loaded successfully!
✓ Test image created: test_data/test_image.png
✓ Background removed successfully!
✓ Output saved: test_data/test_output.png
```

### Step 3: Test with Your Own Image

```bash
python background_removal.py --input YOUR_IMAGE.jpg --output result.png
```

**That's it!** Check `result.png` - background should be transparent.

---

## Quick Commands Reference

```bash
# Single image
python background_removal.py --input image.jpg --output result.png

# Folder of images
python batch_processor.py --input ./input_folder --output ./output_folder

# Different model (higher quality, slower)
python background_removal.py --input image.jpg --output result.png --model ZhengPeng7/BiRefNet
```

---

## Troubleshooting

**"ModuleNotFoundError"**
→ Run: `pip install -r requirements.txt`

**"CUDA out of memory"**
→ System will automatically use CPU (slower but works)

**Model download is slow**
→ First time only, downloads ~2GB model

**Need help?**
→ See `BACKGROUND_REMOVAL_GUIDE.md` for detailed docs
