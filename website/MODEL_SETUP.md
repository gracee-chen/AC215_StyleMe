# Model Setup Guide

## Problem
If you see the error: "No trained model found. Please train a model first."

This means the inference service cannot find a trained model file (`best_model.pth`) in the experiments directory.

## Solutions

### Option 1: Download Model from GCS (Recommended)

If you have GCP credentials configured:

```bash
# Install google-cloud-storage if needed
pip install google-cloud-storage

# Download model using the script
python3 scripts/download_model.py

# Or manually using gsutil
gsutil cp gs://styleme-production/experiments/exp_004/best_model.pth \
  src/models/train/experiments/exp_004/best_model.pth
```

### Option 2: Configure GCP Credentials

If running in Docker, you need to configure GCP credentials:

```bash
# Authenticate with GCP
gcloud auth application-default login

# Or set credentials file
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

Then restart the Docker container:

```bash
docker compose restart inference
```

### Option 3: Train a New Model

If you don't have access to GCS, you can train a new model:

```bash
# Start training service
docker compose --profile training up training
```

Note: Training requires GPU and can take several hours.

### Option 4: Use Local Model File

If you have a model file from another source, place it in:

```
src/models/train/experiments/exp_XXX/best_model.pth
```

Where `exp_XXX` is the experiment ID (e.g., `exp_001`, `exp_002`, etc.)

## Verify Model is Loaded

After setting up the model, check the API:

```bash
curl http://localhost:5001/health
```

The inference service should initialize successfully without the "No trained model" error.

