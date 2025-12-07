# Quick Start: Training & Inference

## 🚀 Run Training (Vertex AI)

### Basic Usage
```bash
cd /home/chufeip/styleme12.0
./scripts/submit_vertex_ai_training.sh
```

### With Custom Parameters
```bash
# Format: ./scripts/submit_vertex_ai_training.sh [machine] [gpu_type] [gpu_count]
./scripts/submit_vertex_ai_training.sh n1-highmem-8 NVIDIA_TESLA_V100 1
```

### Monitor Training Job
```bash
# After submitting, note the job name from output, then:
gcloud ai custom-jobs stream-logs <JOB_NAME> --region=us-central1

# Or check status:
gcloud ai custom-jobs describe <JOB_NAME> --region=us-central1
```

### View Results
```bash
# Check experiments in GCS:
gsutil ls gs://styleme-production/experiments/

# Latest experiment will be auto-named (exp_005, exp_006, etc.)
```

---

## 🌐 Deploy/Update Inference (Cloud Run)

### Deploy or Update Service
```bash
cd /home/chufeip/styleme12.0
./scripts/deploy_cloud_run.sh
```

### With Custom Resources
```bash
# Format: ./scripts/deploy_cloud_run.sh [memory] [cpu] [timeout] [max] [min]
./scripts/deploy_cloud_run.sh 8Gi 4 600 20 2
```

### Test Inference Service
```bash
# Health check:
curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health

# Or use test script:
python3 scripts/test_inference_api.py
```

### View Logs
```bash
gcloud run services logs read styleme-inference --region us-central1 --limit 50
```

---

## 📊 Service Information

**Training:**
- Service: Vertex AI Custom Jobs
- Region: us-central1
- Output: gs://styleme-production/experiments/
- Auto-naming: exp_001, exp_002, etc.

**Inference:**
- Service: Cloud Run
- URL: https://styleme-inference-nty2g5pcpa-uc.a.run.app
- Region: us-central1
- Project: styleme-475201

---

## 🔧 Quick Commands

```bash
# Submit training job (default config)
./scripts/submit_vertex_ai_training.sh

# Deploy/update inference service
./scripts/deploy_cloud_run.sh

# Test inference API
curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health

# View Cloud Run logs
gcloud run services logs read styleme-inference --region us-central1

# List experiments
gsutil ls gs://styleme-production/experiments/
```

