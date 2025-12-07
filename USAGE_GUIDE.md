# StyleMe Application - Summary & Usage Guide

## 📋 Application Summary

**StyleMe** is an AI-powered personal wardrobe stylist that helps users create cohesive outfits from their existing wardrobes. The system uses a fine-tuned FashionCLIP model (based on OpenAI CLIP ViT-B/32) to learn fashion compatibility relationships from curated product data.

### Key Features
- **Image-to-Image Recommendations**: Query with a photo, get back product photos
- **Dual Index System**: Personal wardrobe + global catalog (6,700+ Farfetch products)
- **Smart Fallback Logic**: Searches user's wardrobe first, falls back to catalog if no good matches
- **FAISS-based Similarity Search**: Fast approximate nearest neighbor search with 512-D embeddings
- **Containerized Microservices**: Four services (ingestion, preprocessing, training, inference)
- **Cloud-Ready**: Supports Vertex AI for training and Cloud Run for inference

### Architecture
- **4 Microservices**: Ingestion → Preprocessing → Training → Inference
- **Data Storage**: Google Cloud Storage (GCS) for source data, DVC for versioning
- **Model**: FashionCLIP fine-tuned with triplet loss for fashion compatibility
- **Frontend**: React-based mobile-first SPA (TypeScript, Vite, Tailwind CSS)

---

## 🚀 How to Use the Application

### Prerequisites
- Docker and Docker Compose
- Python 3.9+ (for local development)
- GCP credentials configured (for cloud operations)
- GPU support (for training, optional for inference)

### Local Development

#### 1. Initial Setup
```bash
# Clone and navigate to project
cd AC215_StyleMe

# Create required directories
make setup
# Or manually: mkdir -p data logs catalog wardrobes queries results
```

#### 2. Run Complete Pipeline (Local)
```bash
# Run all services: ingestion → preprocessing → training → inference
make run
```

#### 3. Run Individual Services
```bash
make run-ingestion      # Data collection only
make run-preprocessing  # Data processing only
make run-training       # Model training only (requires GPU)
make run-inference      # Inference only (requires trained model)
```

#### 4. Run Inference for Specific Query
```bash
# Format: make infer USER=<user> QUERY=<query> THRESHOLD=<threshold> GENDER=<men/women>
make infer USER=grace QUERY=grace_query_01 THRESHOLD=0.3 GENDER=women
```

---

## ☁️ Cloud Training (Vertex AI)

### Overview
Training jobs run on Google Cloud Vertex AI with GPU support. Models are saved to GCS and can be used for inference.

### Quick Start

#### 1. Submit Training Job (Default Configuration)
```bash
cd /Users/chufeipeng/AC215_StyleMe
./scripts/submit_vertex_ai_training.sh
```

**Default Settings:**
- Machine Type: `n1-highmem-8` (8 vCPUs, 52GB RAM)
- GPU: `NVIDIA_TESLA_V100` (1 GPU)
- Output: `gs://styleme-production/experiments/`

#### 2. Submit with Custom Parameters
```bash
# Format: ./scripts/submit_vertex_ai_training.sh [machine] [gpu_type] [gpu_count]
./scripts/submit_vertex_ai_training.sh n1-highmem-16 NVIDIA_TESLA_V100 1
```

**Available Machine Types:**
- `n1-standard-8`: 8 vCPUs, 30GB RAM
- `n1-highmem-8`: 8 vCPUs, 52GB RAM (default)
- `n1-highmem-16`: 16 vCPUs, 104GB RAM (for large models)

**Available GPU Types:**
- `NVIDIA_TESLA_V100`: V100 GPU (default)
- `NVIDIA_TESLA_T4`: T4 GPU (cheaper alternative)

#### 3. Monitor Training Job
```bash
# After submitting, note the job name from output, then:
gcloud ai custom-jobs stream-logs <JOB_NAME> --region=us-central1

# Or check status:
gcloud ai custom-jobs describe <JOB_NAME> --region=us-central1

# List all jobs:
gcloud ai custom-jobs list --region=us-central1
```

#### 4. View Training Results
```bash
# Check experiments in GCS:
gsutil ls gs://styleme-production/experiments/

# Download specific experiment:
gsutil -m cp -r gs://styleme-production/experiments/<experiment_id> ./

# View training history:
gsutil cat gs://styleme-production/experiments/<experiment_id>/training_history.json
```

### Training Configuration

**Environment Variables** (automatically set by script):
- `GCP_BUCKET_NAME=styleme-data-bucket` - Source data bucket
- `GCP_PROJECT_ID=styleme-475201` - GCP project
- `DATA_PREFIX=json` - JSON metadata prefix
- `IMAGES_PREFIX=images` - Images prefix
- `EXPERIMENTS_DIR=/gcs/styleme-production/experiments` - Output directory
- `LOG_LEVEL=INFO` - Logging level

**Training Parameters** (configured in `src/models/train/fine_tune_config.py`):
- Batch Size: 24
- Learning Rate: 2e-5
- Epochs: 12
- Frozen Layers: 4 (out of 12)
- Margin: 0.5 (triplet loss)
- Target Accuracy: >70%

### Important Notes
- ⚠️ **Outputs are saved to GCS**: All model checkpoints are saved to `gs://styleme-production/experiments/`
- ⚠️ **GPU Required**: Training requires CUDA-capable GPU (will exit if not available)
- ⚠️ **Job Naming**: Jobs are auto-named with timestamp: `styleme-training-YYYYMMDD-HHMMSS`
- ⚠️ **Cost**: Vertex AI jobs are billed per hour of GPU usage

---

## 🌐 Cloud Inference (Cloud Run)

### Overview
The inference service is deployed as a Cloud Run service, providing a REST API for fashion recommendations.

### Quick Start

#### 1. Deploy/Update Inference Service
```bash
cd /Users/chufeipeng/AC215_StyleMe
./scripts/deploy_cloud_run.sh
```

**Default Settings:**
- Memory: 4GB
- CPU: 2 vCPU
- Timeout: 300 seconds (5 minutes)
- Max Instances: 10
- Min Instances: 1 (reduces cold starts)

#### 2. Deploy with Custom Resources
```bash
# Format: ./scripts/deploy_cloud_run.sh [memory] [cpu] [timeout] [max] [min]
./scripts/deploy_cloud_run.sh 8Gi 4 600 20 2
```

#### 3. Test Inference Service
```bash
# Health check:
curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health

# Or use test script:
python3 scripts/test_inference_api.py

# Test with sample query:
curl -X POST https://styleme-inference-nty2g5pcpa-uc.a.run.app/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "query_image": "<base64_encoded_image>"
  }'
```

#### 4. View Service Logs
```bash
# View recent logs:
gcloud run services logs read styleme-inference --region us-central1 --limit 50

# Follow logs in real-time:
gcloud run services logs tail styleme-inference --region us-central1

# View service details:
gcloud run services describe styleme-inference --region us-central1
```

### API Endpoints

**Base URL**: `https://styleme-inference-nty2g5pcpa-uc.a.run.app`

1. **Health Check**
   ```bash
   GET /health
   ```

2. **Upload Wardrobe Item**
   ```bash
   POST /api/upload
   Content-Type: multipart/form-data
   Body: { user_id, image (file or base64) }
   ```

3. **Get Recommendations**
   ```bash
   POST /api/recommend
   Content-Type: application/json
   Body: {
     "user_id": "string",
     "query_image": "base64_string",
     "threshold": 0.7,
     "wardrobe_k": 5,
     "catalog_k": 3,
     "gender": "men" | "women"
   }
   ```

4. **Get User Wardrobe**
   ```bash
   GET /api/wardrobe/<user_id>
   ```

5. **Rebuild Wardrobe Index**
   ```bash
   POST /api/wardrobe/<user_id>/rebuild
   ```

### Service Configuration

**Environment Variables** (automatically set by script):
- `GCP_BUCKET_NAME=styleme-data-bucket`
- `GCP_PROJECT_ID=styleme-475201`
- `CATALOG_DIR=/gcs/styleme-production/catalog`
- `WARDROBES_DIR=/gcs/styleme-production/wardrobes`
- `EXPERIMENTS_DIR=/gcs/styleme-production/experiments`
- `RUN_API_SERVER=true`
- `PORT=8080` (Cloud Run default)

### Important Notes
- ⚠️ **Cold Starts**: First request may take 10-30 seconds (model loading)
- ⚠️ **Min Instances**: Set to 1 to reduce cold starts (incurs cost)
- ⚠️ **GCS Access**: Service uses GCS client library to access data
- ⚠️ **Service URL**: Get the actual URL from deployment output or `gcloud run services describe`

---

## 📊 Service Information

### Training (Vertex AI)
- **Service**: Vertex AI Custom Jobs
- **Region**: `us-central1`
- **Output**: `gs://styleme-production/experiments/`
- **Container**: `us-central1-docker.pkg.dev/styleme-475201/styleme-repo/training:latest`
- **Project**: `styleme-475201`

### Inference (Cloud Run)
- **Service**: Cloud Run
- **URL**: `https://styleme-inference-nty2g5pcpa-uc.a.run.app`
- **Region**: `us-central1`
- **Container**: `us-central1-docker.pkg.dev/styleme-475201/styleme-repo/inference:latest`
- **Project**: `styleme-475201`

---

## 🔧 Quick Reference Commands

### Training
```bash
# Submit training job (default)
./scripts/submit_vertex_ai_training.sh

# Submit with custom config
./scripts/submit_vertex_ai_training.sh n1-highmem-16 NVIDIA_TESLA_V100 1

# Monitor job
gcloud ai custom-jobs stream-logs <JOB_NAME> --region=us-central1

# List experiments
gsutil ls gs://styleme-production/experiments/
```

### Inference
```bash
# Deploy/update service
./scripts/deploy_cloud_run.sh

# Test health
curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health

# View logs
gcloud run services logs read styleme-inference --region us-central1
```

### Local Development
```bash
# Setup
make setup

# Run full pipeline
make run

# Run inference only
make run-inference

# Run specific query
make infer USER=grace QUERY=grace_query_01 THRESHOLD=0.3 GENDER=women
```

---

## 📁 Key Directories

- `catalog/` - FAISS catalog indices (versioned)
- `wardrobes/` - User wardrobe indices and images
- `queries/` - User query images
- `results/` - Inference output results
- `src/models/train/experiments/` - Local training experiments
- `containers/` - Docker container definitions
- `scripts/` - Utility scripts (training, deployment, testing)

---

## 🎯 Workflow Examples

### Complete Training → Inference Workflow

1. **Train Model on Vertex AI**
   ```bash
   ./scripts/submit_vertex_ai_training.sh
   # Wait for job to complete (check logs)
   ```

2. **Verify Model in GCS**
   ```bash
   gsutil ls gs://styleme-production/experiments/
   # Note the experiment ID
   ```

3. **Deploy Inference Service**
   ```bash
   ./scripts/deploy_cloud_run.sh
   # Service will automatically load latest model from GCS
   ```

4. **Test Inference**
   ```bash
   curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health
   python3 scripts/test_inference_api.py
   ```

### Local Development Workflow

1. **Setup Environment**
   ```bash
   make setup
   ```

2. **Run Training (if needed)**
   ```bash
   make run-training  # Requires GPU
   ```

3. **Run Inference**
   ```bash
   make run-inference
   # Or for specific query:
   make infer USER=grace QUERY=grace_query_01 THRESHOLD=0.3
   ```

4. **View Results**
   ```bash
   cat results/grace/grace_query_01.json | jq
   ```

---

## 🐛 Troubleshooting

### Training Issues
- **No GPU available**: Training requires GPU. Check Vertex AI job has GPU configured.
- **Job fails**: Check logs with `gcloud ai custom-jobs stream-logs`
- **Outputs not saved**: Verify `EXPERIMENTS_DIR=/gcs/styleme-production/experiments` is set

### Inference Issues
- **Service not responding**: Check logs with `gcloud run services logs read`
- **Cold start timeout**: Increase timeout or set min-instances=1
- **Model not found**: Verify model exists in `gs://styleme-production/experiments/`
- **GCS access errors**: Check service account permissions

### Local Issues
- **Docker errors**: Ensure Docker is running and has sufficient resources
- **Permission errors**: Check file permissions in `data/`, `catalog/`, etc.
- **GPU not detected**: Verify NVIDIA drivers and Docker GPU support

---

## 📚 Additional Documentation

- **Application Design**: `docs/Application design doc.md`
- **Model Training**: `docs/model_training.md`
- **API Integration**: `docs/api_integration.md`
- **Data Versioning**: `docs/data_versioning.md`
- **Vertex AI Config**: `docs/vertex_ai_training_config.md`
- **Cloud Run Config**: `docs/cloud_run_config.md`
- **Inference README**: `containers/inference/INFERENCE_README.md`

---

**Ready to train and deploy! 🚀**

