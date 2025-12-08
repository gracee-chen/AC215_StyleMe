# 🚀 Next Steps - CI/CD Setup

> **⚠️ IMPORTANT:** You have 2 workflow files. GitHub will run BOTH. 
> **👉 Follow `CI/CD_QUICK_START.md` instead - it has clear instructions!**

## Current Status

✅ **Files Created:**
- `.github/workflows/ci-cd.yml` - New production CI/CD pipeline
- `CI/COVERAGE_DOCUMENTATION.md` - Coverage documentation
- `CI/CD_SETUP_GUIDE.md` - Setup instructions
- `CI/CD_IMPLEMENTATION_SUMMARY.md` - Implementation summary

⚠️ **Note:** You have two workflow files:
- `ci.yml` - Old CI pipeline (from previous milestone)
- `ci-cd.yml` - New production CI/CD pipeline (just created)

## Step-by-Step Action Plan

### Step 1: Update Old CI Workflow (Optional but Recommended)

The old `ci.yml` still has 50% coverage requirement. Update it to 60%:

```bash
# I can do this for you, or you can manually update:
# In .github/workflows/ci.yml, change:
# --cov-fail-under=50  →  --cov-fail-under=60
# (appears in two places)
```

**OR** you can keep both workflows:
- `ci.yml` - For development/testing
- `ci-cd.yml` - For production deployment

### Step 2: Set Up GCP Service Account (REQUIRED)

This is needed for the CI/CD pipeline to deploy to Kubernetes.

**Option A: Use the Setup Guide (Recommended)**
```bash
# Open and follow:
open CI/CD_SETUP_GUIDE.md
```

**Option B: Quick Commands**
```bash
# Set your project
export PROJECT_ID="styleme-475201"

# Create service account
gcloud iam service-accounts create github-actions-ci \
  --display-name="GitHub Actions CI/CD" \
  --project=$PROJECT_ID

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/container.developer"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com \
  --project=$PROJECT_ID

# View the key (you'll need to copy this)
cat github-actions-key.json
```

### Step 3: Add GitHub Secret (REQUIRED)

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. **Name**: `GCP_SA_KEY`
5. **Value**: Paste the entire contents of `github-actions-key.json`
6. Click **Add secret**

### Step 4: Verify Your Configuration

Check that these match your actual setup:

```bash
# Open the workflow file
open .github/workflows/ci-cd.yml

# Verify these values (around line 21-28):
# PROJECT_ID: styleme-475201        ← Your GCP project ID
# REGION: us-central1               ← Your GCP region
# REPO_NAME: styleme-repo           ← Your Artifact Registry repo
# CLUSTER_NAME: styleme-cluster     ← Your GKE cluster name
# CLUSTER_ZONE: us-central1-b        ← Your cluster zone
```

If any are different, edit the file and update them.

### Step 5: Verify Infrastructure Exists

```bash
# Check Artifact Registry
gcloud artifacts repositories describe styleme-repo \
  --location=us-central1 \
  --project=styleme-475201

# Check GKE cluster
gcloud container clusters describe styleme-cluster \
  --zone=us-central1-b \
  --project=styleme-475201
```

If either doesn't exist, create them or update the workflow file with correct names.

### Step 6: Test the Pipeline

**Option A: Test with a Pull Request (Recommended)**
```bash
# Create a new branch
git checkout -b test-ci-cd

# Add and commit the new files
git add .github/workflows/ci-cd.yml
git add CI/
git commit -m "Add production CI/CD pipeline"

# Push to GitHub
git push origin test-ci-cd

# Create a Pull Request on GitHub
# The pipeline will run and you can see if it works
```

**Option B: Test by Pushing to Main**
```bash
# Add and commit
git add .github/workflows/ci-cd.yml
git add CI/
git commit -m "Add production CI/CD pipeline"

# Push to main (will trigger deployment!)
git push origin main
```

### Step 7: Monitor the Pipeline

1. Go to your GitHub repository
2. Click the **Actions** tab
3. You should see:
   - **"CI/CD Pipeline"** - Your new workflow
   - **"Continuous Integration and Testing"** - Your old workflow (if you kept it)

4. Click on a workflow run to see:
   - ✅ Lint job
   - ✅ Unit Tests
   - ✅ Integration Tests
   - ✅ E2E Tests
   - ✅ Coverage Report (must be ≥60%)
   - ✅ Build Images (main branch only)
   - ✅ Deploy K8s (main branch only)

## Quick Checklist

Before your first deployment:

- [ ] GCP service account created (`github-actions-ci`)
- [ ] Service account has Artifact Registry and GKE permissions
- [ ] GitHub secret `GCP_SA_KEY` added
- [ ] Artifact Registry repository exists
- [ ] GKE cluster exists and accessible
- [ ] Workflow file has correct project/cluster names
- [ ] Tests pass locally: `./CI/scripts/run_tests.sh all`
- [ ] Coverage is ≥60% (check locally first)

## What Happens When You Push

### On Pull Request or Feature Branch:
- ✅ Runs lint
- ✅ Runs all tests
- ✅ Checks coverage (≥60%)
- ❌ Does NOT build images
- ❌ Does NOT deploy

### On Merge to Main:
- ✅ Runs all tests
- ✅ Checks coverage (≥60%)
- ✅ Builds Docker images
- ✅ Pushes to Artifact Registry
- ✅ Deploys to Kubernetes
- ✅ Updates inference service

## Troubleshooting

### If tests fail:
```bash
# Run tests locally first
./CI/scripts/run_tests.sh all
```

### If coverage is below 60%:
```bash
# Check coverage report
open CI/coverage_html/index.html

# Review what's not covered
open CI/COVERAGE_DOCUMENTATION.md
```

### If deployment fails:
- Check GCP service account permissions
- Verify cluster name/zone in workflow file
- Check Artifact Registry repository exists
- Review GitHub Actions logs for errors

## Need Help?

- **Setup Guide**: `CI/CD_SETUP_GUIDE.md` - Detailed setup instructions
- **Coverage Docs**: `CI/COVERAGE_DOCUMENTATION.md` - Coverage details
- **Summary**: `CI/CD_IMPLEMENTATION_SUMMARY.md` - What was implemented

---

**Ready?** Start with Step 2 (GCP Service Account setup)!

