# Vertex AI Training Job Configuration

**Created**: Step 2.3  
**Status**: Configuration Ready (Not yet executed)

---

## Job Configuration

### Container Image
- **Image URI**: `us-central1-docker.pkg.dev/styleme-475201/styleme-repo/training:latest`
- **Image Size**: ~4.2GB

### Machine Type & GPU
- **Machine Type**: `n1-highmem-16` (16 vCPUs, 104GB RAM) - Required for large model training
- **GPU Type**: `nvidia-tesla-v100`
- **GPU Count**: 1
- **Accelerator Type**: `NVIDIA_TESLA_V100`

### Environment Variables
```bash
# GCS Configuration
GCP_BUCKET_NAME=styleme-data-bucket
GCP_PROJECT_ID=styleme-475201
DATA_PREFIX=json
IMAGES_PREFIX=images

# Data directories (Vertex AI will mount GCS)
EXPERIMENTS_DIR=/gcs/styleme-production/experiments
DATA_DIR=/gcs/temp_training_data  # Temporary staging area for data

# Training configuration
LOG_LEVEL=INFO
CUDA_VISIBLE_DEVICES=0

# Note: Vertex AI uses /gcs/ prefix to mount GCS buckets
```

### Command (Entrypoint)
The container entrypoint is `/app/entrypoint.sh`, which will:
1. Check GPU availability
2. Load data from GCS (using GCS paths)
3. Run training
4. Save outputs to `/gcs/styleme-production/experiments/`

**Note**: The training script already supports GCS data loading via `gcp_bucket_name` in DATA_CONFIG.

### Input/Output Paths

**Input Data** (from GCS):
- Source data: `gs://styleme-data-bucket/json/` and `gs://styleme-data-bucket/images/`
- Training will access this directly via `google-cloud-storage` client

**Output Data** (to GCS):
- Experiments: `gs://styleme-production/experiments/`
- Model checkpoints: `gs://styleme-production/experiments/{experiment_id}/`
- Training history: `gs://styleme-production/experiments/{experiment_id}/training_history.json`

### Service Account
- **Service Account**: Default compute service account
- **Required Permissions**:
  - Storage Object Admin on `gs://styleme-data-bucket` (read training data)
  - Storage Object Admin on `gs://styleme-production` (write experiments)

### Job Configuration Summary

| Setting | Value |
|---------|-------|
| **Region** | `us-central1` |
| **Machine Type** | `n1-highmem-16` (104GB RAM) |
| **GPU Type** | `NVIDIA_TESLA_V100` |
| **GPU Count** | 1 |
| **Container Image** | `us-central1-docker.pkg.dev/styleme-475201/styleme-repo/training:latest` |
| **Max Runtime** | 7200 seconds (2 hours) |
| **Replica Count** | 1 |

---

## Submitting Training Jobs

### Option 1: Use Helper Script (Recommended)

**Location**: `scripts/submit_vertex_ai_training.sh`

This script automatically sets all required environment variables, including `EXPERIMENTS_DIR`:

```bash
# Basic usage (uses n1-highmem-8 with 1x V100 GPU)
./scripts/submit_vertex_ai_training.sh

# Specify machine type, GPU type, and GPU count
./scripts/submit_vertex_ai_training.sh n1-highmem-8 NVIDIA_TESLA_V100 1

# CPU-only test job
./scripts/submit_vertex_ai_training.sh n1-highmem-8 "" 0
```

**Important**: The script automatically sets `EXPERIMENTS_DIR=/gcs/styleme-production/experiments` in the `--env-vars` parameter, ensuring all outputs are saved to GCS.

### Option 2: Manual gcloud Command

```bash
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=styleme-training-$(date +%Y%m%d-%H%M%S) \
  --worker-pool-spec=machine-type=n1-highmem-8,replica-count=1,container-image-uri=us-central1-docker.pkg.dev/styleme-475201/styleme-repo/training:latest,accelerator-type=NVIDIA_TESLA_V100,accelerator-count=1 \
  --env-vars=GCP_BUCKET_NAME=styleme-data-bucket,GCP_PROJECT_ID=styleme-475201,DATA_PREFIX=json,IMAGES_PREFIX=images,EXPERIMENTS_DIR=/gcs/styleme-production/experiments,LOG_LEVEL=INFO \
  --service-account=871771559501-compute@developer.gserviceaccount.com
```

**⚠️ CRITICAL**: Make sure `EXPERIMENTS_DIR=/gcs/styleme-production/experiments` is included in the `--env-vars` parameter. Without it, outputs will be saved locally in the container and lost when the job completes!

---

## Important Notes

### GCS Mounting
Vertex AI automatically mounts GCS buckets using the `/gcs/` prefix:
- `gs://styleme-production/experiments/` → `/gcs/styleme-production/experiments/`
- The training code needs to save outputs to `/gcs/styleme-production/experiments/`

### Data Access
The training code uses `google-cloud-storage` to read from GCS:
- Source data: `gs://styleme-data-bucket/json/` and `gs://styleme-data-bucket/images/`
- This is handled by the `FashionTripletDataset` class which supports GCS

### Output Paths
Model checkpoints and training history will be saved to:
- `gs://styleme-production/experiments/{experiment_id}/best_model.pth`
- `gs://styleme-production/experiments/{experiment_id}/final_model.pth`
- `gs://styleme-production/experiments/{experiment_id}/training_history.json`

### Next Steps
1. ✅ Configuration created
2. ⏭️ Test with small training job (Step 2.4)
3. ⏭️ Run full training job (Step 2.5)

---

## Code Changes Required (Future)

**Note**: The current training entrypoint assumes local filesystem paths. For Vertex AI, we may need to:
1. Update entrypoint to handle GCS paths correctly
2. Ensure training code saves to `/gcs/` mounted paths
3. Verify data loading from GCS works in Vertex AI environment

This will be tested in Step 2.4 (Test Training Job).

