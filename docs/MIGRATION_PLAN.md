# StyleMe Migration Plan: VM → Google Cloud Vertex AI / Cloud Run

**Status**: Planning Phase  
**Timeline**: 2-3 weeks  
**Approach**: Aggressive Incremental (3 phases)  
**Last Updated**: [Current Date]

---

## 📋 Executive Summary

This document outlines the step-by-step migration plan for moving StyleMe from a Virtual Machine deployment to Google Cloud Platform, specifically:
- **Training**: Vertex AI Training
- **Inference**: Cloud Run
- **Storage**: Google Cloud Storage (GCS)

**Migration Strategy**: Incremental but aggressive (2-3 weeks total)
- Phase 1: Training + Storage Migration (Week 1)
- Phase 2: Inference Deployment (Week 2)
- Phase 3: Frontend Cutover (Week 2-3)

---

## 🎯 Migration Goals

1. ✅ Migrate training jobs to Vertex AI Training (GPU support)
2. ✅ Deploy inference API to Cloud Run (serverless, auto-scaling)
3. ✅ Move all persistent data to GCS buckets
4. ✅ Maintain zero downtime during migration
5. ✅ Ensure sub-10 second inference latency
6. ✅ Preserve all existing functionality

---

## 📊 Current State Analysis

### Current Architecture
```
VM (Current)
├── Docker Compose Services
│   ├── ingestion/     → Reads from GCS
│   ├── preprocessing/ → Processes locally
│   ├── training/      → GPU training, saves to ./experiments/
│   └── inference/     → Flask API, reads from local volumes
│
├── Local Volumes (Current Locations)
│   ├── ./catalog/         → FAISS indices, embeddings
│   ├── ./wardrobes/       → User wardrobe indices
│   ├── ./experiments/     → Model checkpoints
│   ├── ./queries/         → User query images (temporary)
│   └── ./results/         → Inference results (temporary)
│
└── GCS (Already Using)
    └── gs://styleme-data-bucket/ → Source data (images, JSON)
```

### Current Environment Variables
- `GCP_BUCKET_NAME=styleme-data-bucket`
- `GCP_PROJECT_ID=styleme-475201`
- `EXPERIMENTS_DIR=/app/experiments`
- `CATALOG_DIR=/app/catalog`
- `WARDROBES_DIR=/app/wardrobes`
- `QUERIES_DIR=/app/queries`
- `RESULTS_DIR=/app/results`

### Current Data Locations (On VM)
- **Catalog**: `./catalog/v_2025-10-24_model-b1/` (FAISS index + metadata)
- **Wardrobes**: `./wardrobes/{user_id}/` (per-user FAISS indices)
- **Experiments**: `./src/models/train/experiments/` (model checkpoints)
- **Queries/Results**: Temporary, can be recreated

---

## 🏗️ Target Architecture

### Target State
```
Google Cloud Platform
├── Vertex AI Training
│   └── Training Jobs → Save to gs://styleme-production/experiments/
│
├── Cloud Run
│   └── Inference API → Read from GCS buckets
│
├── GCS Buckets (New Structure)
│   ├── gs://styleme-production/
│   │   ├── catalog/         → FAISS indices, embeddings
│   │   ├── wardrobes/       → User wardrobe indices
│   │   ├── experiments/     → Model checkpoints
│   │   ├── queries/         → Temporary query images
│   │   └── results/         → Temporary inference results
│   └── gs://styleme-data-bucket/ → Source data (unchanged)
│
└── Artifact Registry
    └── Docker images for training and inference
```

---

## 📝 Detailed Migration Plan

## PHASE 1: Infrastructure Setup & Data Migration (Week 1)

### Step 1.1: GCS Bucket Structure Setup
**Objective**: Create new GCS buckets for production data

**Actions**:
1. Create main production bucket: `gs://styleme-production`
2. Create subdirectories structure:
   ```
   gs://styleme-production/
   ├── catalog/
   ├── wardrobes/
   ├── experiments/
   ├── queries/
   └── results/
   ```
3. Set bucket permissions:
   - Enable versioning (optional, for safety)
   - Set lifecycle policies (delete queries/results after 30 days)
   - Configure uniform bucket-level access

**Validation Criteria**:
- ✅ Bucket created successfully
- ✅ Subdirectories accessible
- ✅ Permissions set correctly

**Rollback Plan**: Delete bucket if issues occur (data still on VM)

**Estimated Time**: 30 minutes

---

### Step 1.2: Inventory Current Data
**Objective**: Document what needs to be migrated

**Actions**:
1. List all catalog indices:
   ```bash
   ls -la ./catalog/
   du -sh ./catalog/*
   ```
2. List all user wardrobes:
   ```bash
   ls -la ./wardrobes/
   du -sh ./wardrobes/*
   ```
3. List all experiments:
   ```bash
   ls -la ./src/models/train/experiments/
   du -sh ./src/models/train/experiments/*
   ```
4. Document sizes and file counts

**Deliverables**:
- Spreadsheet/document with:
  - Catalog size: ___ GB
  - Wardrobes: ___ users, ___ GB total
  - Experiments: ___ experiments, ___ GB total

**Validation Criteria**:
- ✅ Complete inventory documented
- ✅ Data sizes verified

**Estimated Time**: 15 minutes

---

### Step 1.3: Upload Catalog Data to GCS
**Objective**: Migrate catalog indices to GCS

**Actions**:
1. Upload entire catalog directory:
   ```bash
   gsutil -m cp -r ./catalog/* gs://styleme-production/catalog/
   ```
2. Verify upload:
   ```bash
   gsutil ls -r gs://styleme-production/catalog/
   ```
3. Compare file counts:
   ```bash
   # Local
   find ./catalog -type f | wc -l
   # GCS
   gsutil ls -r gs://styleme-production/catalog/ | wc -l
   ```

**Validation Criteria**:
- ✅ All catalog files uploaded
- ✅ File counts match
- ✅ FAISS index files present (.faiss, .vecs.npy, .idmap.npy, .parquet)
- ✅ Manifest.json present

**Rollback Plan**: Data still exists on VM

**Estimated Time**: 30-60 minutes (depending on data size)

---

### Step 1.4: Upload Wardrobe Data to GCS
**Objective**: Migrate user wardrobes to GCS

**Actions**:
1. Upload wardrobes:
   ```bash
   gsutil -m cp -r ./wardrobes/* gs://styleme-production/wardrobes/
   ```
2. Verify upload:
   ```bash
   gsutil ls -r gs://styleme-production/wardrobes/
   ```

**Validation Criteria**:
- ✅ All user wardrobes uploaded
- ✅ File structure preserved
- ✅ FAISS indices present

**Estimated Time**: 15-30 minutes (depending on user count)

---

### Step 1.5: Upload Experiments to GCS
**Objective**: Migrate model checkpoints to GCS

**Actions**:
1. Upload experiments:
   ```bash
   gsutil -m cp -r ./src/models/train/experiments/* gs://styleme-production/experiments/
   ```
2. Identify latest/best model:
   ```bash
   # Find best model
   find ./src/models/train/experiments -name "best_model.pth" -type f
   ```

**Validation Criteria**:
- ✅ All experiments uploaded
- ✅ Model checkpoints (.pth files) present
- ✅ Training history JSONs present

**Estimated Time**: 30-60 minutes (depending on checkpoint sizes)

---

### Step 1.6: Test GCS Data Access
**Objective**: Verify data is accessible from code

**Actions**:
1. Test reading catalog from GCS:
   ```python
   from google.cloud import storage
   client = storage.Client(project='styleme-475201')
   bucket = client.bucket('styleme-production')
   blobs = list(bucket.list_blobs(prefix='catalog/'))
   print(f"Found {len(blobs)} files in catalog/")
   ```
2. Test downloading a small file
3. Test listing experiments

**Validation Criteria**:
- ✅ Can list GCS files
- ✅ Can download files
- ✅ No permission errors

**Estimated Time**: 15 minutes

---

## PHASE 2: Training Migration (Week 1, After Data Migration)

### Step 2.1: Set Up Artifact Registry
**Objective**: Create Docker registry for training containers

**Actions**:
1. Enable Artifact Registry API
2. Create repository:
   ```bash
   gcloud artifacts repositories create styleme-repo \
     --repository-format=docker \
     --location=us-central1 \
     --description="StyleMe Docker images"
   ```
3. Configure Docker authentication:
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

**Validation Criteria**:
- ✅ Repository created
- ✅ Docker auth configured
- ✅ Can push/pull images

**Estimated Time**: 15 minutes

---

### Step 2.2: Build and Push Training Container
**Objective**: Prepare training container for Vertex AI

**Actions**:
1. Build training Docker image:
   ```bash
   docker build -f containers/training/Dockerfile -t styleme-training:latest .
   ```
2. Tag for Artifact Registry:
   ```bash
   docker tag styleme-training:latest \
     us-central1-docker.pkg.dev/styleme-475201/styleme-repo/training:latest
   ```
3. Push to registry:
   ```bash
   docker push us-central1-docker.pkg.dev/styleme-475201/styleme-repo/training:latest
   ```

**Validation Criteria**:
- ✅ Image builds successfully
- ✅ Image pushed to registry
- ✅ Image visible in Artifact Registry console

**Rollback Plan**: Revert to VM training if needed

**Estimated Time**: 20-30 minutes

---

### Step 2.3: Create Vertex AI Training Job (Dry Run)
**Objective**: Set up Vertex AI Training job configuration

**Actions**:
1. Create training job specification file (without running yet)
2. Configure:
   - Machine type: `n1-standard-8` or GPU instance
   - GPU: `nvidia-tesla-v100` or `nvidia-tesla-t4`
   - Image URI: Artifact Registry image
   - Environment variables:
     - `GCP_BUCKET_NAME=styleme-data-bucket`
     - `GCP_PROJECT_ID=styleme-475201`
     - `EXPERIMENTS_DIR=/gcs/styleme-production/experiments`
     - `DATA_PREFIX=json`
     - `IMAGES_PREFIX=images`
   - Command: Entrypoint script

**Configuration File Location**: To be created in next step

**Validation Criteria**:
- ✅ Job specification documented
- ✅ All environment variables listed
- ✅ GPU requirements specified

**Estimated Time**: 30 minutes

---

### Step 2.3.5: Update Training Code for GCS Paths
**Objective**: Modify training code to save outputs to GCS instead of local filesystem

**Actions**:
1. Update `containers/training/entrypoint.sh`:
   - Change `save_dir` from `/app/experiments/temp_training_output` to `/gcs/styleme-production/experiments/temp_training_output`
   - Update `EXPERIMENTS_DIR` environment variable handling
2. Verify training code can write to `/gcs/` mounted paths
3. Test that directory creation works with GCS mounts

**Code Changes**:
- **File**: `containers/training/entrypoint.sh`
  - Line 78: Update `save_dir` to use `/gcs/styleme-production/experiments/`
  - Ensure `EXPERIMENTS_DIR` is set correctly for Vertex AI

**Validation Criteria**:
- ✅ Entrypoint script updated to use GCS paths
- ✅ Code can create directories in `/gcs/` mount
- ✅ No hardcoded local paths remain

**Note**: Vertex AI automatically mounts GCS buckets at `/gcs/{bucket-name}/`, so minimal code changes needed.

**Estimated Time**: 15-30 minutes

---

### Step 2.4: Test Vertex AI Training Job (Small Test)
**Objective**: Validate training works on Vertex AI

**Actions**:
1. Create a test training job with:
   - Small dataset subset
   - 1-2 epochs only
   - Minimal GPU time
2. Submit job via gcloud CLI or console
3. Monitor job logs
4. Verify output saved to GCS

**Validation Criteria**:
- ✅ Training job completes successfully
- ✅ Model checkpoints saved to `gs://styleme-production/experiments/`
- ✅ Training logs accessible
- ✅ No errors in execution

**Rollback Plan**: Continue using VM training if issues

**Estimated Time**: 1-2 hours (waiting for job to complete)

---

### Step 2.5: Run Full Training Job on Vertex AI
**Objective**: Complete full training on Vertex AI

**Actions**:
1. Submit full training job with complete dataset
2. Monitor training progress
3. Verify final model saved to GCS

**Validation Criteria**:
- ✅ Training completes successfully
- ✅ Best model checkpoint in GCS
- ✅ Training metrics comparable to VM training

**Estimated Time**: Several hours (training time)

---

## PHASE 3: Inference Migration (Week 2)

### Step 3.1: Build and Push Inference Container
**Objective**: Prepare inference container for Cloud Run

**Actions**:
1. Build inference Docker image:
   ```bash
   docker build -f containers/inference/Dockerfile -t styleme-inference:latest .
   ```
2. Tag for Artifact Registry:
   ```bash
   docker tag styleme-inference:latest \
     us-central1-docker.pkg.dev/styleme-475201/styleme-repo/inference:latest
   ```
3. Push to registry:
   ```bash
   docker push us-central1-docker.pkg.dev/styleme-475201/styleme-repo/inference:latest
   ```

**Validation Criteria**:
- ✅ Image builds successfully
- ✅ Image pushed to registry
- ✅ Image is < 10GB (Cloud Run limit)

**Estimated Time**: 20-30 minutes

---

### Step 3.1.5: Update Inference Code for GCS Paths
**Objective**: Modify inference code to read/write from GCS instead of local filesystem

**Actions**:
1. **Install Cloud Storage FUSE** in inference Dockerfile:
   - Add `gcsfuse` installation
   - Configure mount point in entrypoint

2. **Update inference service** (`containers/inference/inference_service.py`):
   - Update catalog loading to read from GCS paths
   - Update wardrobe loading to read from GCS
   - Update experiments loading to read from GCS
   - Ensure file operations work with GCS mounts

3. **Update API server** (`containers/inference/api_server.py`):
   - Update image upload to save to GCS
   - Update image serving to read from GCS
   - Update wardrobe rebuild operations

4. **Update build scripts**:
   - `build_catalog_index.py`: Save to GCS
   - `build_user_wardrobe.py`: Save to GCS

5. **Update environment variables**:
   - Set paths to `/gcs/styleme-production/{catalog,wardrobes,experiments}/`

**Code Changes**:
- **Files to modify**: 
  - `containers/inference/Dockerfile` (add gcsfuse)
  - `containers/inference/entrypoint.sh` (mount GCS)
  - `containers/inference/inference_service.py` (read from GCS)
  - `containers/inference/api_server.py` (write to GCS)
  - `containers/inference/build_catalog_index.py` (save to GCS)
  - `containers/inference/build_user_wardrobe.py` (save to GCS)

**Validation Criteria**:
- ✅ GCS buckets can be mounted via gcsfuse
- ✅ All read operations work from GCS
- ✅ All write operations save to GCS
- ✅ File paths updated throughout codebase

**Estimated Time**: 1-2 hours

---

### Step 3.2: Configure Cloud Run Service (Preparation)
**Objective**: Set up Cloud Run configuration

**Key Configuration Points**:
1. **Service Name**: `styleme-inference`
2. **Region**: `us-central1` (or closest to users)
3. **Container Image**: Artifact Registry image
4. **Environment Variables**:
   ```
   GCP_BUCKET_NAME=styleme-data-bucket
   GCP_PROJECT_ID=styleme-475201
   CATALOG_DIR=/gcs/styleme-production/catalog
   WARDROBES_DIR=/gcs/styleme-production/wardrobes
   EXPERIMENTS_DIR=/gcs/styleme-production/experiments
   QUERIES_DIR=/tmp/queries
   RESULTS_DIR=/tmp/results
   PORT=8080
   RUN_API_SERVER=true
   LOG_LEVEL=INFO
   ```
5. **Resource Allocation**:
   - CPU: 2-4 vCPU
   - Memory: 4-8 GB
   - Timeout: 300 seconds (5 minutes)
   - Max instances: 10 (auto-scaling)
   - Min instances: 1 (to reduce cold starts)
6. **Volumes**: Use Cloud Storage FUSE to mount GCS buckets
   - Mount `gs://styleme-production/catalog` to `/gcs/styleme-production/catalog`
   - Mount `gs://styleme-production/wardrobes` to `/gcs/styleme-production/wardrobes`
   - Mount `gs://styleme-production/experiments` to `/gcs/styleme-production/experiments`

**Important Note**: Cloud Run uses port 8080 by default, but our code uses 5000. We'll need to update PORT env var.

**Validation Criteria**:
- ✅ Configuration documented
- ✅ All env vars listed
- ✅ Resource requirements specified

**Estimated Time**: 30 minutes

---

### Step 3.3: Deploy to Cloud Run (Test Deployment)
**Objective**: Deploy inference service to Cloud Run

**Actions**:
1. Deploy service (using gcloud CLI or console):
   ```bash
   gcloud run deploy styleme-inference \
     --image us-central1-docker.pkg.dev/styleme-475201/styleme-repo/inference:latest \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --memory 4Gi \
     --cpu 2 \
     --timeout 300 \
     --max-instances 10 \
     --min-instances 1 \
     --set-env-vars "GCP_BUCKET_NAME=styleme-data-bucket,GCP_PROJECT_ID=styleme-475201,..."
   ```
2. Note the service URL (e.g., `https://styleme-inference-xxx-uc.a.run.app`)
3. Test health endpoint:
   ```bash
   curl https://styleme-inference-xxx-uc.a.run.app/health
   ```

**Validation Criteria**:
- ✅ Service deploys successfully
- ✅ Health endpoint returns 200 OK
- ✅ Service URL accessible

**Rollback Plan**: Delete Cloud Run service if issues, continue using VM

**Estimated Time**: 15-20 minutes

---

### Step 3.4: Test API Endpoints on Cloud Run
**Objective**: Verify all API endpoints work

**Actions**:
1. Test `/health` endpoint
2. Test `/api/wardrobe/<user_id>` endpoint
3. Test `/api/recommend` with sample image
4. Test `/api/upload` with sample image
5. Check response times (should be < 10 seconds)

**Test Script**:
```bash
# Health check
curl https://styleme-inference-xxx-uc.a.run.app/health

# Get wardrobe
curl https://styleme-inference-xxx-uc.a.run.app/api/wardrobe/sophie

# Upload test (adjust path)
curl -X POST -F "file=@test_image.jpg" -F "user_id=test_user" \
  https://styleme-inference-xxx-uc.a.run.app/api/upload

# Recommendation test (adjust path)
curl -X POST -F "file=@query_image.jpg" -F "user_id=test_user" \
  https://styleme-inference-xxx-uc.a.run.app/api/recommend
```

**Validation Criteria**:
- ✅ All endpoints respond correctly
- ✅ Inference latency < 10 seconds
- ✅ Upload works and saves to GCS
- ✅ Recommendations are generated correctly

**Estimated Time**: 30 minutes

---

### Step 3.5: Load Testing
**Objective**: Verify Cloud Run handles traffic

**Actions**:
1. Run concurrent request test:
   ```bash
   # Install hey or use similar tool
   hey -n 100 -c 10 https://styleme-inference-xxx-uc.a.run.app/health
   ```
2. Monitor:
   - Response times
   - Error rates
   - Auto-scaling behavior
   - Cold start times

**Validation Criteria**:
- ✅ Handles 10+ concurrent requests
- ✅ Response times acceptable
- ✅ Auto-scaling works
- ✅ Cold starts < 5 seconds

**Estimated Time**: 30 minutes

---

## PHASE 4: Frontend Integration & Cutover (Week 2-3)

### Step 4.1: Update Frontend Environment Variable
**Objective**: Point frontend to Cloud Run (staging)

**Actions**:
1. Create staging environment variable:
   - `VITE_API_URL=https://styleme-inference-xxx-uc.a.run.app`
2. Test frontend with Cloud Run backend
3. Verify all features work:
   - Upload images
   - View wardrobe
   - Get recommendations
   - Complete the look

**Note**: Keep VM running as backup

**Validation Criteria**:
- ✅ Frontend connects to Cloud Run
- ✅ All features functional
- ✅ No errors in browser console

**Estimated Time**: 30 minutes

---

### Step 4.2: Production Cutover
**Objective**: Switch production traffic to Cloud Run

**Actions**:
1. Update production frontend `.env` file:
   ```
   VITE_API_URL=https://styleme-inference-xxx-uc.a.run.app
   ```
2. Redeploy frontend (or update environment)
3. Monitor:
   - Error rates
   - Response times
   - User reports

**Validation Criteria**:
- ✅ Traffic flowing to Cloud Run
- ✅ No increase in error rates
- ✅ Response times acceptable
- ✅ Users can use app successfully

**Rollback Plan**: Revert `VITE_API_URL` to VM endpoint if issues

**Estimated Time**: 15 minutes

---

### Step 4.3: Monitor Production (48 hours)
**Objective**: Ensure stability

**Actions**:
1. Monitor Cloud Run metrics:
   - Request count
   - Latency (p50, p95, p99)
   - Error rate
   - Instance count
2. Monitor GCS access:
   - Read/write operations
   - Storage costs
3. Check application logs
4. Gather user feedback

**Validation Criteria**:
- ✅ Error rate < 1%
- ✅ Latency p95 < 10 seconds
- ✅ No critical issues
- ✅ User satisfaction maintained

**Estimated Time**: Ongoing monitoring

---

### Step 4.4: Decommission VM (After Validation)
**Objective**: Complete migration

**Actions**:
1. After 1-2 weeks of stable operation:
   - Stop VM inference service
   - Keep VM as backup for 1 more week
   - Archive VM data to GCS
   - Decommission VM

**Validation Criteria**:
- ✅ All traffic on Cloud Run
- ✅ No dependency on VM
- ✅ VM data backed up

**Estimated Time**: 1 hour

---

## 🔧 Code Changes Summary

**Note**: Code changes are now integrated into the migration plan as explicit steps:
- **Step 2.3.5**: Update Training Code for GCS Paths (Phase 2)
- **Step 3.1.5**: Update Inference Code for GCS Paths (Phase 3)

See the respective steps above for detailed code change requirements.

### Summary of Changes:

**Training (Step 2.3.5)**:
- Update `containers/training/entrypoint.sh` to use `/gcs/` paths
- Minimal changes needed (Vertex AI auto-mounts GCS)

**Inference (Step 3.1.5)**:
- Install and configure `gcsfuse` for Cloud Run
- Update all file I/O operations to use GCS paths
- Update 5-6 files with path changes

### Estimated Code Changes:
- **Files to modify**: ~6-7 files total
- **Lines of code**: ~200-300 lines
- **Complexity**: Medium (mostly path changes and GCS mounting)

---

## 📊 Success Metrics

### Performance Targets:
- ✅ Inference latency: < 10 seconds (p95)
- ✅ Upload latency: < 5 seconds
- ✅ Training job success rate: > 95%
- ✅ API uptime: > 99.5%

### Cost Targets:
- ✅ Cloud Run costs: Monitor and optimize
- ✅ GCS storage costs: Within budget
- ✅ Training costs: Per-job basis

### Quality Targets:
- ✅ Zero data loss during migration
- ✅ Model accuracy maintained
- ✅ User experience unchanged

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Cold start latency | High | Medium | Set min-instances=1 |
| GCS access latency | Medium | Low | Use Cloud Storage FUSE, cache locally |
| Training job failures | High | Low | Test with small job first |
| Data migration errors | High | Low | Verify file counts, checksums |
| Budget overrun | Medium | Medium | Set quotas, monitor costs |
| Code compatibility issues | High | Medium | Thorough testing before cutover |

---

## 📅 Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: Infrastructure & Data | 2-3 days | GCS buckets, data migrated |
| Phase 2: Training Migration | 2-3 days | Vertex AI training working |
| Phase 3: Inference Migration | 2-3 days | Cloud Run deployed and tested |
| Phase 4: Cutover | 1-2 days | Production on Cloud Run |
| **Total** | **2-3 weeks** | **Complete migration** |

---

## 📝 Next Steps

**IMMEDIATE ACTION**: Review this plan and approve Phase 1, Step 1.1

Once approved, we will proceed step-by-step:
1. ✅ You review and approve each step
2. ✅ Execute approved step
3. ✅ Validate results
4. ✅ Move to next step only after your approval

**No code will be modified until you explicitly request it.**

---

## 📚 Reference Links

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Training Documentation](https://cloud.google.com/vertex-ai/docs/training/overview)
- [Cloud Storage FUSE Documentation](https://cloud.google.com/storage/docs/gcs-fuse)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)

---

**Status**: ✅ Plan Ready for Review  
**Next Action**: Awaiting approval to proceed with Phase 1, Step 1.1

