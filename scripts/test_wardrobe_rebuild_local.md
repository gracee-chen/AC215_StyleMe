# Testing Async Wardrobe Rebuild Locally

This guide shows how to test the new async wardrobe rebuild functionality locally without deploying to Cloud Run.

## Prerequisites

1. Docker and Docker Compose installed
2. GCP credentials configured (`~/.config/gcloud` mounted)
3. At least one test image file

## Step 1: Start the Local API Server

```bash
# From project root
docker-compose --profile api up inference
```

The API will be available at `http://localhost:5001` (mapped from container port 5000).

## Step 2: Test the Upload Endpoint

In a **new terminal**, run the test script:

```bash
# Make sure you have a test image
python3 scripts/test_upload_local.py \
  --user-id test_user_001 \
  --image path/to/your/test/image.jpg
```

Or use curl:

```bash
# Encode image to base64
IMAGE_BASE64=$(base64 -i path/to/your/test/image.jpg)

# Upload image
curl -X POST http://localhost:5001/api/upload \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"test_user_001\",
    \"image\": \"data:image/jpeg;base64,$IMAGE_BASE64\"
  }"
```

## Step 3: Watch the Logs

In the terminal where the API server is running, you should see:

1. **Upload logs:**
   ```
   ✅ Saved wardrobe image to gs://...
   ✅ Saved wardrobe metadata to gs://...
   🚀 Triggered async wardrobe index rebuild for test_user_001 (running in background)
   ```

2. **Background rebuild logs (a few seconds later):**
   ```
   🔨 Starting async wardrobe index rebuild for test_user_001...
   📂 Found X images in GCS for test_user_001
   ✅ Downloaded X images and Y metadata files
   ✅ Wardrobe index built for test_user_001
   📤 Uploaded wardrobe.index.faiss to GCS
   📤 Uploaded wardrobe.parquet to GCS
   📤 Uploaded idmap.npy to GCS
   🎉 Wardrobe index rebuild completed for test_user_001 (3 files uploaded)
   ✅ Wardrobe rebuild process finished for test_user_001
   ```

## Step 4: Verify the Index Was Built

Check if the index files exist in GCS:

```bash
# List wardrobe files for the user
gsutil ls gs://styleme-production/wardrobes/test_user_001/
```

You should see:
- `wardrobe.index.faiss`
- `wardrobe.parquet`
- `idmap.npy`
- `images/` directory with uploaded images

## Step 5: Test Recommendations (Verify Index Works)

After the rebuild completes, test getting recommendations:

```bash
python3 scripts/test_inference_api.py \
  --url http://localhost:5001 \
  --user-id test_user_001 \
  --image path/to/query/image.jpg
```

The recommendation should be **fast** (no waiting for index build) because the index is already pre-built!

## Expected Behavior

### ✅ Success Indicators:
- Upload returns immediately (200 OK)
- Background thread starts rebuild (visible in logs)
- Index files appear in GCS within 30-60 seconds
- Recommendations work immediately without waiting

### ⚠️ Things to Watch For:
- If you see "Wardrobe rebuild already in progress", that's normal - it means a rebuild is already running
- If rebuild fails, check the error logs for details
- Make sure you have GCP credentials configured

## Troubleshooting

### Issue: "No wardrobe images found in GCS"
- Check that images were uploaded successfully
- Verify GCS bucket name is correct (`styleme-production`)
- Check GCP credentials are mounted

### Issue: Rebuild takes too long
- Normal for first rebuild (downloads images, builds index)
- Subsequent rebuilds should be faster
- Check logs for any errors

### Issue: Index not appearing in GCS
- Check the background thread logs for errors
- Verify GCS write permissions
- Check if rebuild completed successfully

## Testing Multiple Uploads

To test concurrent upload prevention:

1. Upload image 1 (triggers rebuild)
2. Immediately upload image 2 (should skip rebuild if first is still running)
3. Check logs - should see "Wardrobe rebuild already in progress" for image 2

## Local vs Cloud Run Behavior

**Local (with docker-compose):**
- Uses local filesystem paths (`./wardrobes/`)
- Rebuild happens on local filesystem
- Index files saved to `./wardrobes/{user_id}/`

**Cloud Run:**
- Uses GCS client library
- Downloads from GCS, builds in temp, uploads back
- Index files saved to `gs://styleme-production/wardrobes/{user_id}/`

The code automatically detects the environment and uses the appropriate method.

