# Cloud Run Deployment Configuration

**Created**: Step 3.2  
**Status**: Configuration Ready

---

## Service Configuration

### Basic Settings
- **Service Name**: `styleme-inference`
- **Region**: `us-central1`
- **Container Image**: `us-central1-docker.pkg.dev/styleme-475201/styleme-repo/inference:latest`
- **Platform**: Managed Cloud Run

### Resource Allocation
- **CPU**: 2-4 vCPU (default: 2)
- **Memory**: 4-8 GB (default: 4GB)
- **Timeout**: 300 seconds (5 minutes)
- **Max Instances**: 10 (auto-scaling)
- **Min Instances**: 1 (to reduce cold starts)

### Environment Variables
```bash
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
GCS_BUCKET=styleme-production
```

### Service Account
- **Service Account**: `871771559501-compute@developer.gserviceaccount.com`
- **Required Permissions**:
  - Storage Object Admin on `gs://styleme-production` (read/write)
  - Storage Object Admin on `gs://styleme-data-bucket` (read)

---

## Deployment

### Option 1: Use Deployment Script (Recommended)

**Location**: `scripts/deploy_cloud_run.sh`

```bash
# Default configuration (4GB memory, 2 CPU)
./scripts/deploy_cloud_run.sh

# Custom resource allocation
./scripts/deploy_cloud_run.sh 8Gi 4 600 20 1
# Arguments: memory, cpu, timeout, max-instances, min-instances
```

### Option 2: Manual gcloud Command

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
  --set-env-vars "GCP_BUCKET_NAME=styleme-data-bucket,GCP_PROJECT_ID=styleme-475201,CATALOG_DIR=/gcs/styleme-production/catalog,WARDROBES_DIR=/gcs/styleme-production/wardrobes,EXPERIMENTS_DIR=/gcs/styleme-production/experiments,QUERIES_DIR=/tmp/queries,RESULTS_DIR=/tmp/results,PORT=8080,RUN_API_SERVER=true,LOG_LEVEL=INFO,GCS_BUCKET=styleme-production" \
  --service-account 871771559501-compute@developer.gserviceaccount.com \
  --project styleme-475201
```

---

## Important Notes

### GCS Access
- Cloud Run doesn't support FUSE filesystems by default
- The entrypoint script attempts to mount GCS using gcsfuse
- If mounting fails, the service should use GCS client library (needs code updates)
- **Note**: For production, consider updating code to use GCS client library directly instead of FUSE

### Port Configuration
- Cloud Run uses port 8080 by default
- The API server reads `PORT` environment variable (defaults to 5000)
- We set `PORT=8080` for Cloud Run compatibility

### Cold Starts
- Min instances set to 1 to reduce cold start latency
- First request may still experience cold start (~10-30 seconds)
- Subsequent requests should be fast (< 10 seconds target)

### Cost Considerations
- Min instances = 1 means always running (incurring costs)
- Consider setting to 0 for development/testing to reduce costs
- Monitor Cloud Run usage and costs in GCP Console

---

## Post-Deployment

### 1. Verify Service URL
After deployment, note the service URL:
```bash
gcloud run services describe styleme-inference \
  --region us-central1 \
  --format="value(status.url)"
```

### 2. Test Health Endpoint
```bash
curl https://styleme-inference-xxx-uc.a.run.app/health
```

### 3. View Logs
```bash
gcloud run services logs read styleme-inference \
  --region us-central1 \
  --limit 50
```

### 4. Monitor Service
```bash
gcloud run services describe styleme-inference \
  --region us-central1
```

---

## Troubleshooting

### Common Issues

1. **GCS Mount Failure**
   - Check service account permissions
   - Verify GCS bucket exists
   - Review logs for mount errors

2. **Cold Start Timeout**
   - Increase timeout if needed
   - Reduce model loading time
   - Use min-instances=1

3. **Memory Issues**
   - Increase memory allocation
   - Check model size
   - Monitor memory usage in logs

4. **Port Conflicts**
   - Ensure PORT=8080 is set
   - Check API server configuration

---

**Next Steps**: Proceed to Step 3.3 (Deploy and Test)

