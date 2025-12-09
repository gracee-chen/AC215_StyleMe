# Background Removal Integration Plan

## Current Status

✅ **Background removal code exists** in `src/datapipeline/bg_removal/background_removal.py`
✅ **Infrastructure is in place** - `InferenceService` and `api_server.py` have hooks for background removal
✅ **Dependencies installed** - `rembg>=2.0.50` is in `requirements.txt`
❌ **Currently disabled** - `bg_removal_enabled=False` by default

## Integration Steps

### 1. Enable Background Removal in Backend Configuration

**File:** `containers/inference/api_server.py`

**Current code (line ~146-153):**
```python
# Background removal is disabled by default
bg_removal_enabled=False  # Background removal disabled
```

**Action:** Enable via environment variable for flexibility:
- Add `BG_REMOVAL_ENABLED` environment variable (default: `false`)
- Allow enabling/disabling without code changes
- Support different models via `BG_REMOVAL_MODEL` environment variable

**Changes needed:**
1. Read `BG_REMOVAL_ENABLED` from environment (default: `False`)
2. Read `BG_REMOVAL_MODEL` from environment (default: `"briaai/RMBG-1.4"`)
3. Pass these to `InferenceService` initialization

### 2. Update InferenceService Initialization

**File:** `containers/inference/api_server.py` (around line 146)

**Current:**
```python
bg_removal_enabled=False  # Background removal disabled
```

**New:**
```python
# Background removal configuration
BG_REMOVAL_ENABLED = os.getenv('BG_REMOVAL_ENABLED', 'false').lower() == 'true'
BG_REMOVAL_MODEL = os.getenv('BG_REMOVAL_MODEL', 'briaai/RMBG-1.4')
```

**Then pass to InferenceService:**
```python
service = InferenceService(
    catalog_dir=CATALOG_DIR,
    experiments_dir=EXPERIMENTS_DIR,
    wardrobes_dir=WARDROBES_DIR,
    device=device,
    bg_removal_enabled=BG_REMOVAL_ENABLED,
    bg_removal_model=BG_REMOVAL_MODEL
)
```

### 3. Verify Upload Endpoint Integration

**File:** `containers/inference/api_server.py` (lines 903-926)

**Status:** ✅ Already implemented! The code is there but conditional:
- Lines 904-926 handle background removal
- Falls back gracefully if background removal fails
- Converts RGBA to RGB with white background

**Action:** No changes needed - it will work once enabled!

### 4. Update Docker Configuration

**File:** `docker-compose.yml`

**Add environment variables:**
```yaml
services:
  inference:
    environment:
      - BG_REMOVAL_ENABLED=true  # Enable background removal
      - BG_REMOVAL_MODEL=briaai/RMBG-1.4  # Optional: specify model
```

### 5. Update Cloud Run Deployment

**File:** `scripts/deploy_cloud_run.sh`

**Add to environment variables array:**
```bash
ENV_VARS+=(
    # ... existing vars ...
    "BG_REMOVAL_ENABLED=true"
    "BG_REMOVAL_MODEL=briaai/RMBG-1.4"  # Optional
)
```

### 6. Performance Considerations

**Memory:**
- Background removal models can be large (~500MB-1GB)
- May increase container memory usage
- Consider increasing Cloud Run memory allocation if needed

**Processing Time:**
- Background removal adds ~1-3 seconds per image
- Already runs asynchronously in upload endpoint
- Should not block user experience

**GPU vs CPU:**
- Works on CPU but slower (~3-5 seconds)
- Much faster on GPU (~0.5-1 second)
- Cloud Run doesn't support GPU, so CPU is fine for now

### 7. Testing Plan

**Local Testing:**
1. Enable in `docker-compose.yml`
2. Rebuild container: `docker-compose build inference`
3. Restart: `docker-compose up inference`
4. Upload an image and verify background is removed
5. Check logs for background removal messages

**Cloud Testing:**
1. Deploy with `BG_REMOVAL_ENABLED=true`
2. Upload test images
3. Verify processed images have white backgrounds
4. Check Cloud Run logs for any errors

### 8. Error Handling

**Current implementation already handles:**
- ✅ Falls back to original image if background removal fails
- ✅ Logs errors for debugging
- ✅ Doesn't break upload flow

**Considerations:**
- Model download on first use (may take time)
- Memory issues if model is too large
- Network issues downloading model from HuggingFace

### 9. Model Options

**Available models:**
1. **`briaai/RMBG-1.4`** (Recommended)
   - Fast and accurate
   - Good for fashion items
   - ~500MB model size

2. **`ZhengPeng7/BiRefNet`**
   - Higher quality
   - Slower processing
   - Better edge detection

3. **`rembg` (built-in)**
   - Fallback option
   - Already installed
   - Simpler but less accurate

### 10. Frontend Considerations

**Current status:** ✅ No changes needed!
- Frontend already uploads images as-is
- Backend handles all processing
- User sees processed result automatically

**Optional enhancements:**
- Show "Processing..." indicator during upload
- Preview before/after (if desired)
- Allow user to toggle background removal (future feature)

## Implementation Checklist

- [ ] Update `api_server.py` to read `BG_REMOVAL_ENABLED` from environment
- [ ] Update `api_server.py` to read `BG_REMOVAL_MODEL` from environment
- [ ] Pass environment variables to `InferenceService` initialization
- [ ] Update `docker-compose.yml` with environment variables
- [ ] Update `scripts/deploy_cloud_run.sh` with environment variables
- [ ] Test locally with Docker Compose
- [ ] Test on Cloud Run
- [ ] Monitor memory usage and processing time
- [ ] Update documentation

## Quick Start (Minimal Changes)

**To enable immediately with minimal changes:**

1. **Edit `containers/inference/api_server.py` line ~153:**
   ```python
   bg_removal_enabled=True  # Enable background removal
   ```

2. **Rebuild and redeploy:**
   ```bash
   ./scripts/deploy_cloud_run.sh
   ```

That's it! The rest of the infrastructure is already in place.

## Notes

- Background removal is **optional** - if it fails, original image is used
- Processing happens **server-side** - no frontend changes needed
- Images are saved with **white background** (converted from transparent)
- Works for both **wardrobe uploads** and **query images** (recommendations)

