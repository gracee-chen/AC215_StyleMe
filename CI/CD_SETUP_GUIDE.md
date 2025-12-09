# CI/CD Pipeline Setup Guide

This guide walks you through setting up the GitHub Actions CI/CD pipeline for StyleMe step by step.

## 📋 Prerequisites

Before setting up CI/CD, ensure you have:

1. ✅ A GitHub repository with your code
2. ✅ A GCP project with billing enabled
3. ✅ A GKE cluster (created via Pulumi or manually)
4. ✅ Artifact Registry repository for Docker images
5. ✅ GCP service account with required permissions

## 🔐 Step 1: Create GCP Service Account

The CI/CD pipeline needs a service account to:
- Push Docker images to Artifact Registry
- Deploy to GKE cluster

### 1.1 Create Service Account

```bash
# Set your project ID
export PROJECT_ID="styleme-475201"

# Create service account
gcloud iam service-accounts create github-actions-ci \
  --display-name="GitHub Actions CI/CD" \
  --project=$PROJECT_ID
```

### 1.2 Grant Required Permissions

```bash
# Grant Artifact Registry permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Grant GKE permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/container.developer"

# Grant GCS permissions (if needed for data access)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

### 1.3 Create and Download Key

```bash
# Create key file
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com \
  --project=$PROJECT_ID

# The key file will be saved as github-actions-key.json
```

## 🔑 Step 2: Configure GitHub Secrets

You need to add the service account key as a GitHub secret.

### 2.1 Go to GitHub Repository Settings

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### 2.2 Add GCP Service Account Key

1. **Name**: `GCP_SA_KEY`
2. **Value**: Copy the entire contents of `github-actions-key.json` file
   ```bash
   # To view the key content:
   cat github-actions-key.json
   ```
3. Click **Add secret**

### 2.3 Verify Secrets

You should now have:
- ✅ `GCP_SA_KEY` - GCP service account JSON key

## 🐳 Step 3: Verify Artifact Registry Setup

Ensure your Artifact Registry repository exists:

```bash
# Set variables
export PROJECT_ID="styleme-475201"
export REGION="us-central1"
export REPO_NAME="styleme-repo"

# Check if repository exists
gcloud artifacts repositories describe $REPO_NAME \
  --location=$REGION \
  --project=$PROJECT_ID

# If it doesn't exist, create it:
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID
```

## ☸️ Step 4: Verify GKE Cluster Setup

Ensure your GKE cluster exists and is accessible:

```bash
# Set variables
export PROJECT_ID="styleme-475201"
export CLUSTER_NAME="styleme-cluster"
export CLUSTER_ZONE="us-central1-b"

# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME \
  --zone=$CLUSTER_ZONE \
  --project=$PROJECT_ID

# Verify access
kubectl get nodes
```

## 📝 Step 5: Update Workflow Configuration (if needed)

The workflow file (`.github/workflows/ci-cd.yml`) has default values. Verify they match your setup:

```yaml
env:
  PROJECT_ID: styleme-475201        # Your GCP project ID
  REGION: us-central1               # Your GCP region
  REPO_NAME: styleme-repo           # Your Artifact Registry repo name
  CLUSTER_NAME: styleme-cluster    # Your GKE cluster name
  CLUSTER_ZONE: us-central1-b       # Your GKE cluster zone
```

If your values are different, edit `.github/workflows/ci-cd.yml` and update the `env` section.

## ✅ Step 6: Test the Pipeline

### 6.1 Push to GitHub

```bash
# Commit the workflow file
git add .github/workflows/ci-cd.yml
git commit -m "Add CI/CD pipeline"
git push origin main
```

### 6.2 Monitor Pipeline

1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see the workflow running
4. Click on the workflow run to see progress

### 6.3 Expected Workflow Jobs

The pipeline runs these jobs in order:

1. ✅ **Lint** - Code quality checks
2. ✅ **Unit Tests** - Unit test suite
3. ✅ **Integration Tests** - Integration test suite
4. ✅ **E2E Tests** - End-to-end tests
5. ✅ **Coverage** - Combined coverage report (must be ≥60%)
6. ✅ **Build Images** - Build Docker images (main branch only)
7. ✅ **Deploy K8s** - Deploy to Kubernetes (main branch only)

## 🐛 Troubleshooting

### Issue: "Permission denied" when pushing images

**Solution**: Verify the service account has `roles/artifactregistry.writer` permission.

```bash
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com"
```

### Issue: "Cluster not found" during deployment

**Solution**: Verify cluster name and zone in workflow file match your actual cluster.

```bash
# List your clusters
gcloud container clusters list --project=$PROJECT_ID
```

### Issue: "Coverage below 60%"

**Solution**: 
1. Check the coverage report in workflow artifacts
2. Review `CI/COVERAGE_DOCUMENTATION.md` for untested modules
3. Add more tests to increase coverage

### Issue: "kubectl connection failed"

**Solution**: Verify the service account has `roles/container.developer` permission and cluster exists.

## 📊 Monitoring

### View Coverage Reports

1. Go to GitHub Actions
2. Click on a completed workflow run
3. Download the `coverage-report` artifact
4. Extract and open `CI/coverage_html/index.html` in a browser

### View Deployment Status

After deployment, check Kubernetes:

```bash
# Get cluster credentials
gcloud container clusters get-credentials styleme-cluster \
  --zone=us-central1-b \
  --project=styleme-475201

# Check pods
kubectl get pods -l app=styleme

# Check services
kubectl get service styleme-inference-service

# View logs
kubectl logs -l component=inference --tail=50
```

## 🔄 Workflow Behavior

### On Pull Requests

- ✅ Runs lint, unit tests, integration tests, E2E tests
- ✅ Checks coverage (must be ≥60%)
- ❌ Does NOT build Docker images
- ❌ Does NOT deploy to Kubernetes

### On Push to Main

- ✅ Runs all tests (same as PR)
- ✅ Builds Docker images
- ✅ Pushes images to Artifact Registry
- ✅ Deploys to Kubernetes cluster
- ✅ Updates inference service with new images

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GCP Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [GKE Authentication](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)

## ✅ Checklist

Before your first deployment, verify:

- [ ] GCP service account created with correct permissions
- [ ] GitHub secret `GCP_SA_KEY` configured
- [ ] Artifact Registry repository exists
- [ ] GKE cluster exists and is accessible
- [ ] Workflow file has correct project/cluster names
- [ ] Tests pass locally: `./CI/scripts/run_tests.sh all`
- [ ] Coverage is ≥60%: Check `CI/coverage_html/index.html`

---

**Ready to deploy?** Push to `main` branch and watch the magic happen! 🚀

