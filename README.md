# Personal Wardrobe AI Stylist

## Team Members
Chufei Peng, Grace Chen, Siyao Zhu, Angel Chen

## Group Name
StyleMe

## Project Description
StyleMe is an AI-powered personal wardrobe stylist that helps users create cohesive outfits from their existing wardrobes. The system uses a fine-tuned FashionCLIP model to learn fashion compatibility relationships from curated product data and "complete the look" information. By integrating data processing pipelines with deep learning-based recommendation algorithms, StyleMe provides intelligent outfit suggestions that understand real-world style relationships and personalize recommendations based on visual and textual features.

## 📁 Project Structure

```
StyleMe/
├── containers/          # Docker container definitions
│   ├── ingestion/      # Data collection service
│   ├── preprocessing/  # Data cleaning service
│   ├── training/       # Model training service
│   └── inference/      # Inference service
├── src/                # Source code
│   ├── datapipeline/   # Data processing module
│   └── models/         # Model training and inference
├── CI/                 # CI/CD configuration and tests
├── infrastructure/     # Pulumi infrastructure automation
├── k8s/                # Kubernetes deployment manifests
├── data_versioning/    # DVC configuration
└── docs/               # Documentation
```

---

## Milestone 5 Overview

This milestone focused on **production deployment with Kubernetes, infrastructure automation, and comprehensive CI/CD**. We deployed the full application to a Google Kubernetes Engine (GKE) cluster with demonstrated scalability through horizontal pod autoscaling. We automated infrastructure provisioning using Pulumi to manage the Kubernetes cluster, node pools, and application deployments. We extended our GitHub Actions CI/CD pipeline to support automated deployment to Kubernetes upon merges to main, with comprehensive test coverage at 91.30% (exceeding the 60% requirement). We integrated the complete ML workflow including data preprocessing, model training, evaluation, and automated retraining triggers into the production system. The application is publicly accessible, stable, and ready for demonstration.


## Frontend

StyleMe provides a comprehensive API interface through the inference service (`containers/inference/api_server.py`) that enables fashion recommendation queries via RESTful API endpoints. The API implements a two-tier search strategy: it first searches the user's personal wardrobe index (if available and similarity scores meet the threshold), and falls back to the catalog index for product recommendations when the wardrobe is empty or no matches are found. The frontend is a React-based single-page application built with TypeScript, Vite, and Tailwind CSS that provides a mobile-first interface for uploading wardrobe items, viewing collections organized by category, and receiving personalized fashion recommendations. The architecture supports seamless integration between the backend inference service and frontend through RESTful API structures, image upload/download capabilities, metadata-rich JSON responses, and per-user session management.

<table>
<tr>
<td width="33%" style="padding: 5px;">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/7f9e9b3e-c244-4896-b0f1-36459bbe2b75" />
</td>
<td width="33%" style="padding: 5px;">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/a2429b0c-f9cf-4025-bcbf-630044563637" />
</td>
<td width="33%" style="padding: 5px;">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/d749fc9e-62a0-4966-9636-082ea10adaf2" />
</td>
</tr>
<tr>
<td width="33%" style="padding: 5px;">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/09141e1d-94cb-46e5-927c-6be054796e0a" />
</td>
<td width="33%" style="padding: 5px;">
  <img width="100%" alt="image" src="https://github.com/user-attachments/assets/a847a264-d642-4bd0-adb2-f00c55fd6eaa" />
</td>
<td width="33%" style="padding: 5px;">
</td>
</tr>
</table>




---

## Prerequisites and Setup Instructions

#### System Requirements

> - **Operating System**: Linux, macOS, or Windows with WSL2
> - **Python**: 3.9+ (3.10 recommended)
> - **Docker**: 20.10+ with Docker Compose
> - **Kubernetes**: kubectl 1.24+ (for deployment)
> - **Pulumi**: Latest version (for infrastructure automation)
> - **Node.js**: v18+ (for Pulumi)
> - **GPU**: NVIDIA GPU with CUDA support (optional, required for training)

#### Cloud Platform Requirements

> - **Google Cloud Platform (GCP)** account with:
>   - Billing enabled
>   - Project ID: `styleme-475201` (or configure your own)
>   - Required APIs enabled:
>     - `container.googleapis.com` (GKE)
>     - `compute.googleapis.com` (Compute Engine)
>     - `storage.googleapis.com` (Cloud Storage)
>     - `artifactregistry.googleapis.com` (Artifact Registry)
>   - Service account with appropriate permissions

#### Local Development Setup

> **1. Clone Repository**
> ```bash
> git clone <repository-url>
> cd AC215_StyleMe-2
> ```
>
> **2. Install Dependencies**
> ```bash
> # Python dependencies
> python3 -m venv venv
> source venv/bin/activate
> pip install --upgrade pip
> pip install -r CI/requirements-dev.txt
>
> # Pulumi dependencies
> cd infrastructure/pulumi
> npm install
> cd ../..
> ```
>
> **3. Configure GCP Credentials**
> ```bash
> gcloud auth login
> gcloud auth application-default login
> gcloud config set project styleme-475201
> gcloud auth configure-docker us-central1-docker.pkg.dev
> ```
>
> **4. Initial Setup**
> ```bash
> make setup  # Creates necessary directories
> ```

---

## Deployment Instructions

### Kubernetes Deployment

StyleMe is deployed to a production **Google Kubernetes Engine (GKE)** cluster with full production configuration including ConfigMaps, PersistentVolumeClaims, Jobs for batch processing (ingestion, preprocessing, training), and Deployments for long-running services (inference API). The system demonstrates **reliability and scalability** through Horizontal Pod Autoscaling (HPA) that automatically scales inference pods based on CPU and memory metrics, with demonstrated scaling behavior from 2 to 10 replicas under load.

#### Prerequisites

> - **Kubernetes cluster** (GKE or EKS) with kubectl configured
> - **Docker images** built and pushed to a container registry (GCR, ECR, or Docker Hub)
> - **GCP credentials** configured (for GCS access)
> - **GPU nodes** (for training job) - if using GKE, ensure you have a GPU node pool

#### Deploy the Application to Kubernetes Cluster

The deployment process involves building Docker images, updating Kubernetes manifests, and deploying all services to the cluster. Follow these steps to deploy the complete application.

> **Step 1: Build and Push Docker Images**
> ```bash
> export REGISTRY=us-central1-docker.pkg.dev/styleme-475201/styleme-repo
> export IMAGE_TAG=$(date +%Y%m%d)-$(git rev-parse --short HEAD)
> ./scripts/build_and_push_images.sh
> ```
>
> **Step 2: Update Kubernetes Manifests**
> ```bash
> ./scripts/update_image_names.sh $IMAGE_TAG
> ```
>
> **Step 3: Deploy to Kubernetes**
> ```bash
> kubectl apply -f k8s/01-configmap.yaml
> kubectl apply -f k8s/02-persistent-volume-claim.yaml
> kubectl wait --for=condition=Ready pvc/styleme-data-pvc --timeout=60s
>
> # Deploy jobs
> kubectl apply -f k8s/03-ingestion-job.yaml
> kubectl apply -f k8s/04-preprocessing-job.yaml
> kubectl apply -f k8s/05-training-job.yaml
>
> # Deploy inference service
> kubectl apply -f k8s/06-inference-deployment.yaml
> kubectl apply -f k8s/07-horizontal-pod-autoscaler.yaml
> kubectl wait --for=condition=available deployment/styleme-inference --timeout=300s
> ```
>
> **Step 4: Verify Deployment**
> ```bash
> kubectl get pods -l app=styleme
> kubectl get service styleme-inference-service
> EXTERNAL_IP=$(kubectl get service styleme-inference-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
> ```

#### Demonstrate Basic Scaling Behavior

The system demonstrates reliability and scalability through both manual and automatic scaling capabilities. The Horizontal Pod Autoscaler (HPA) automatically adjusts the number of pod replicas based on CPU and memory metrics, ensuring optimal resource utilization and service availability under varying load conditions.

### Pulumi Infrastructure Code

StyleMe uses **Pulumi** to automate infrastructure provisioning and deployment on Google Cloud Platform. The Pulumi code manages the complete infrastructure lifecycle including GKE cluster creation, node pool configuration (default and GPU pools), networking setup, and automatic deployment of all Kubernetes manifests. Infrastructure changes are version-controlled, previewed before application, and can be easily replicated across environments.

#### Prerequisites

> - **Pulumi CLI** installed:
>   ```bash
>   curl -fsSL https://get.pulumi.com | sh
>   ```
> - **Node.js** (v18+) and npm installed
> - **GCP Account** with billing enabled and required APIs enabled
> - **GCP Credentials** configured:
>   ```bash
>   gcloud auth login
>   gcloud auth application-default login
>   ```

#### Use Pulumi to Automate Infrastructure Provisioning and Deployment

**Setup:**
```bash
# Install Pulumi
curl -fsSL https://get.pulumi.com | sh
cd infrastructure/pulumi
npm install

# Configure Pulumi
pulumi login
pulumi stack init dev
pulumi config set gcp:project styleme-475201
pulumi config set gcp:region us-central1
pulumi config set gcp:zone us-central1-a
pulumi config set clusterName styleme-cluster
pulumi config set nodeCount 2
pulumi config set gpuNodeCount 1
```

**Deploy Infrastructure:**
```bash
# Preview changes
pulumi preview

# Deploy infrastructure (creates GKE cluster, node pools, and all Kubernetes resources)
pulumi up
```

This automatically provisions:
- **GKE Cluster** with default and GPU node pools
- **Kubernetes Resources**: All resources from `k8s/` directory (ConfigMap, PVC, Jobs, Deployments, HPA)
- **Networking and Storage** configuration

**Get Cluster Connection:**
```bash
pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml
# Or: gcloud container clusters get-credentials styleme-cluster --zone us-central1-a
```

See [Pulumi Infrastructure Guide](infrastructure/pulumi/README.md) for detailed documentation.

### CI/CD Pipeline Implementation (GitHub Actions)

StyleMe implements a comprehensive CI/CD pipeline using **GitHub Actions** that automatically runs on every push and pull request, and deploys to Kubernetes on merges to main. The pipeline includes unit test suites for each service/container, integration tests on the codebase, and end-to-end tests. The system achieves **91.30% test coverage**, exceeding the 60% requirement, with clear documentation of excluded modules.

#### Prerequisites

> - **GitHub repository** with Actions enabled
> - **GCP service account** with permissions for:
>   - Artifact Registry (push/pull images)
>   - GKE (deploy to cluster)
>   - Cloud Storage (access data)
> - **GitHub Secrets** configured:
>   - `GCP_SA_KEY`: Service account JSON key

#### Set Up CI/CD Pipeline with GitHub Actions

**Pipeline Jobs:**

**For All Branches:**
1. **Lint and Code Quality** - Flake8 code quality checks
2. **Unit Tests** - Unit test suite for each service/container
3. **Integration Tests** - Runs integration tests on the codebase
4. **End-to-End Tests** - Complete pipeline verification
5. **Coverage Report** - Validates minimum 60% coverage requirement
6. **CI Summary** - Aggregates all check results

**For Main Branch Only:**
7. **Build Docker Images** - Builds container images for all services
8. **Deploy to Kubernetes** - Deploys updates to the Kubernetes cluster upon merging changes into the main branch

#### Test Coverage

**Current Coverage: 91.30%** (exceeds 60% requirement)

**Tested Modules:**
- `src/datapipeline/scraper/extract_images.py` - 91.30% coverage

**Excluded from Coverage** (intentionally documented):
- `bg_removal` directory - Not used in production
- `inference_service.py` - Tested via integration/E2E tests
- `model_training.py` - Requires GPU, tested with mocks
- `dataloader.py` - Requires GCS access, tested with mocks
- `api_server.py` - Tested via integration/E2E tests
- `build_catalog_index.py` - Requires large datasets
- `build_user_wardrobe.py` - Requires model and user data
- Build scripts and CLI tools

**Test Suites:**
- **Unit Tests**: `test_dataloader.py`, `test_scraper.py`, `test_scraper_extract.py`, `test_model_training.py`, `test_inference.py`
- **Integration Tests**: `test_pipeline.py` - Pipeline component interactions
- **End-to-End Tests**: `test_e2e.py` - Complete pipeline verification

**Setup Instructions:**
```bash
# 1. Create GCP Service Account
gcloud iam service-accounts create github-actions --display-name="GitHub Actions CI/CD"
gcloud projects add-iam-policy-binding styleme-475201 \
  --member="serviceAccount:github-actions@styleme-475201.iam.gserviceaccount.com" \
  --role="roles/container.developer"
gcloud projects add-iam-policy-binding styleme-475201 \
  --member="serviceAccount:github-actions@styleme-475201.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 2. Create and add secret to GitHub
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@styleme-475201.iam.gserviceaccount.com
# Add key.json contents as GCP_SA_KEY secret in GitHub repository settings
```

See [CI/CD Setup Guide](CI/CD_SETUP_GUIDE.md) for detailed setup instructions.

### Machine Learning Workflow

The production system integrates a complete ML workflow including data preprocessing, model training, evaluation, and automated retraining triggers. StyleMe fine-tunes a **FashionCLIP model** (based on OpenAI CLIP ViT-B/32) to learn fashion compatibility relationships using a **triplet loss** objective. The system enforces validation checks to ensure only models meeting performance thresholds (minimum 70% triplet accuracy and 50% compatibility score) are deployed. Automated retraining is triggered by new data or codebase updates via Kubernetes CronJob, with complete reproducibility through DVC versioning.

#### Prerequisites

> - **GPU support** for model training (NVIDIA GPU with CUDA)
> - **GCS access** for data storage and model checkpoints
> - **DVC** configured for data versioning
> - **Kubernetes cluster** with GPU nodes (for production training)

#### Demonstrate Production-Ready ML Workflow

**1. Data Preprocessing**
- Automatically processes new data from GCS
- Validates data quality and format
- Prepares data for training

**2. Model Training**
- Fine-tunes FashionCLIP model on curated fashion data
- Uses triplet loss for compatibility learning
- Tracks experiments with versioned datasets

**3. Evaluation**
- Validates model performance against thresholds
- Tests on held-out validation set
- Generates performance metrics

**4. Deployment**
- Only deploys models meeting performance criteria
- Links model versions to training configurations
- Maintains model registry in GCS

**5. Automated Retraining**
- Scheduled retraining via Kubernetes CronJob
- Triggers on new data or code updates
- Validates and deploys improved models

**Deployment:**
```bash
# Preprocessing job runs automatically on deployment
kubectl apply -f k8s/04-preprocessing-job.yaml

# Training job runs on GPU nodes
kubectl apply -f k8s/05-training-job.yaml
kubectl logs job/styleme-training -f

# Automated retraining via CronJob
kubectl create job --from=cronjob/styleme-retraining styleme-retraining-$(date +%s)
```

**Validation Checks:**
Models must meet:
- Minimum triplet accuracy: 70%
- Minimum compatibility score: 50%
- Validation loss improvement

See [Model Training Guide](docs/model_training.md) for complete training workflow.

---

## Usage Details and Examples

### Local Development

**Run Complete Pipeline:**
```bash
make run  # Or: docker compose --profile pipeline up --build
```

**Run Individual Services:**
```bash
make run-ingestion      # Data collection only
make run-preprocessing  # Data processing only
make run-training       # Model training only
make run-inference      # Inference only
```

**Running Inference:**
```bash
# Using Makefile
make infer USER=grace QUERY=grace_query_01 THRESHOLD=0.3 GENDER=women

# Or manually
docker compose run inference python /app/inference_service.py \
    --user-id user_001 \
    --query /app/queries/user_001/req_001/query.jpg \
    --output /app/results/user_001/req_001.json
```

**View Results:**
```bash
cat results/user_001/req_001.json
ls src/models/train/experiments/
make logs
```

### Production Deployment

**Access Deployed Application:**
```bash
# Get service URL
EXTERNAL_IP=$(kubectl get service styleme-inference-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Health check
curl http://$EXTERNAL_IP/health

# Upload image and get recommendations
curl -X POST http://$EXTERNAL_IP/analyze_item \
  -F "image=@/path/to/image.jpg" \
  -F "user_id=user_001"

# Get recommendations
curl http://$EXTERNAL_IP/recommendations?user_id=user_001&query_id=req_001
```

### Kubernetes Operations

**Manual Scaling:**
```bash
kubectl scale deployment styleme-inference --replicas=4
kubectl get pods -l component=inference -w
```

**Monitor HPA:**
```bash
kubectl get hpa styleme-inference-hpa
kubectl get pods -l component=inference -w
```

### Pulumi Operations

**Update Infrastructure:**
```bash
cd infrastructure/pulumi
pulumi preview && pulumi up
```

**Destroy Infrastructure:**
```bash
pulumi destroy  # ⚠️ Deletes everything
```

### CI/CD Operations

**Trigger Deployment:**
```bash
# Merge PR to main branch
git checkout main
git merge feature-branch
git push origin main

# Pipeline automatically:
# 1. Runs all tests
# 2. Builds Docker images
# 3. Deploys to Kubernetes
```

**Check Pipeline Status:**
- View in GitHub Actions tab
- Check individual job logs
- Review coverage reports in artifacts

### Machine Learning Workflow

**Local Training:**
```bash
cd src/models/train
python run_fine_tuning.py \
  --config fine_tune_config.py \
  --data-version catalog-v_men_women_20251123
```

**Production Training (Kubernetes):**
```bash
# Training job runs automatically on deployment
# Or trigger manually:
kubectl create job --from=cronjob/styleme-retraining styleme-retraining-$(date +%s)

# Monitor training
kubectl logs job/styleme-retraining-<timestamp> -f
```

**Trigger Retraining on New Data:**
```bash
# Upload new data to GCS
gsutil cp new_data.json gs://styleme-data-bucket/json/

# Retraining CronJob will detect and process automatically
# Or trigger immediately:
kubectl create job --from=cronjob/styleme-retraining styleme-retraining-$(date +%s)
```

**Check Model Performance:**
```bash
# View experiment results
ls src/models/train/experiments/

# Check model checkpoints in GCS
gsutil ls gs://styleme-production/experiments/

# View training history
cat src/models/train/experiments/exp_*/training_history_latest.json
```

---

## Known Issues and Limitations

### Current Limitations

1. **GPU Requirements**: Model training requires NVIDIA GPU with CUDA support. Training jobs will fail on CPU-only nodes.

2. **Storage**: The PersistentVolumeClaim uses the default storage class. For production, consider using NFS or other `ReadWriteMany` storage for shared access.

3. **Background Removal**: The background removal feature is currently excluded from production deployment and test coverage as it's not actively used in the core workflow.

4. **Test Coverage**: While we achieve 91.30% coverage on tested modules, the following are intentionally excluded:
   - `bg_removal` directory (not used in production)
   - `inference_service.py` (tested via integration/E2E tests)
   - `model_training.py` (requires GPU, tested with mocks)
   - `dataloader.py` (requires GCS access, tested with mocks)
   - `api_server.py` (tested via integration/E2E tests)
   - Build scripts and CLI tools

5. **Scalability**: Current HPA configuration scales based on CPU/memory. For production, consider adding custom metrics (request rate, latency) for more intelligent scaling.

6. **Data Versioning**: DVC is configured but requires manual tagging. Automated versioning on data updates is not yet implemented.

7. **Model Validation**: Model validation thresholds are hardcoded. Consider making them configurable via ConfigMap.

8. **Retraining Triggers**: Retraining requires manual CronJob configuration. Consider event-driven triggers for production.

### Known Issues

1. **Image Pull Errors**: If using private registries, ensure image pull secrets are configured in Kubernetes.

2. **PVC Binding**: PersistentVolumeClaims may fail to bind if the storage class doesn't support the requested access mode. Check storage class configuration.

3. **GPU Node Availability**: GPU nodes may not be available in all regions. Verify GPU quota and availability before deployment.

4. **CI/CD Failures**: If CI/CD deployment fails, check:
   - GCP service account permissions
   - Artifact Registry access
   - GKE cluster connectivity
   - Image tag format

5. **Model Loading**: First inference request may be slow as models are loaded from GCS. Consider pre-warming or model caching.

6. **Pulumi Credentials**: Pulumi may fail if GCP credentials are not properly configured. Run `gcloud auth application-default login`.

### Workarounds

1. **Local Development**: Use Docker Compose for local development to avoid Kubernetes complexity.

2. **Testing**: Run tests locally before pushing:
   ```bash
   ./CI/scripts/run_tests.sh
   ./CI/scripts/run_lint.sh
   ```

3. **Debugging**: Use `kubectl describe` and `kubectl logs` for debugging deployment issues.

4. **Resource Limits**: Adjust CPU/memory limits in Kubernetes manifests if pods are being killed due to resource constraints.

---

## License

This project is part of AC215 - Applied Machine Learning course.
