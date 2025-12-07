# GCS Model Download Guide

## Method 1: Using gcloud CLI (Recommended)

### Step 1: Install Google Cloud SDK

**macOS:**
```bash
brew install --cask google-cloud-sdk
```

**Or install manually:**
Visit https://cloud.google.com/sdk/docs/install

### Step 2: Set Up Authentication

```bash
# Run authentication script (will automatically open browser)
./scripts/setup_gcp_auth.sh

# Or run manually
gcloud auth application-default login
```

### Step 3: Download Model

```bash
# Using script (automatically selects fastest method)
./scripts/download_model_gcs.sh

# Or use Python script directly
python3 scripts/download_model.py

# Or use gsutil
gsutil cp gs://styleme-production/experiments/exp_004/best_model.pth \
  src/models/train/experiments/exp_004/best_model.pth
```

## Method 2: Using Service Account Key File

If you have a service account JSON key file:

```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"

# Download model
python3 scripts/download_model.py
```

## Method 3: Download in Docker Container

If you want to download in a Docker container (container already has authentication configured):

```bash
# Enter container
docker exec -it styleme-inference bash

# Run download inside container
python3 -c "
from google.cloud import storage
from pathlib import Path
import os

client = storage.Client(project='styleme-475201')
bucket = client.bucket('styleme-production')

# Find available experiments
prefix = 'experiments/'
experiments = set()
for blob in bucket.list_blobs(prefix=prefix):
    if 'best_model.pth' in blob.name:
        exp = blob.name.replace(prefix, '').split('/')[0]
        experiments.add(exp)

if experiments:
    latest_exp = sorted(experiments)[-1]
    print(f'Downloading {latest_exp}...')
    
    model_path = f'experiments/{latest_exp}/best_model.pth'
    local_path = f'/app/experiments/{latest_exp}/best_model.pth'
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    
    bucket.blob(model_path).download_to_filename(local_path)
    print(f'✅ Downloaded to {local_path}')
else:
    print('❌ No models found')
"
```

## Verify Download

After download completes, check the file:

```bash
ls -lh src/models/train/experiments/exp_*/best_model.pth
```

File size should be around 100-500 MB.

## Restart Service

After downloading the model, restart the Docker container for changes to take effect:

```bash
docker compose restart inference
```

## Common Issues

### Issue: "Your default credentials were not found"

**Solution:**
```bash
gcloud auth application-default login
```

### Issue: "Permission denied" or "Access denied"

**Solution:**
Ensure your GCP account has access to `gs://styleme-production`. Contact project administrator to add permissions.

### Issue: Cannot find exp_004

The script will automatically find the latest experiment. You can also specify other experiment IDs:

```bash
python3 scripts/download_model.py --experiment-id exp_003
```
