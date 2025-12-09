# 🚀 CI/CD Quick Start - Follow This Guide

## ⚠️ Important: Two Workflow Files

You currently have **2 workflow files**:
1. `ci.yml` - Old CI (testing only, no deployment)
2. `ci-cd.yml` - New CI/CD (testing + deployment)

**GitHub Actions runs BOTH workflows** - they will both execute on every push/PR.

## ✅ Solution: Keep Only One

**RECOMMENDED:** Use the new `ci-cd.yml` and disable/delete the old `ci.yml`

### Option 1: Delete the Old One (Recommended)

```bash
# Delete the old workflow
rm .github/workflows/ci.yml

# Commit the change
git add .github/workflows/
git commit -m "Remove old CI workflow, use new CI/CD pipeline"
```

### Option 2: Disable the Old One (Keep for Reference)

Rename it so GitHub doesn't run it:
```bash
# Rename to disable it
mv .github/workflows/ci.yml .github/workflows/ci.yml.disabled

# Or move to a backup folder
mkdir -p .github/workflows/backup
mv .github/workflows/ci.yml .github/workflows/backup/
```

## 📋 Setup Instructions (Follow These Steps)

### Step 1: Set Up GCP Service Account

**Open your terminal and run:**

```bash
# Set your project ID
export PROJECT_ID="styleme-475201"

# Create service account
gcloud iam service-accounts create github-actions-ci \
  --display-name="GitHub Actions CI/CD" \
  --project=$PROJECT_ID

# Grant Artifact Registry permission
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Grant GKE permission
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/container.developer"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-ci@${PROJECT_ID}.iam.gserviceaccount.com \
  --project=$PROJECT_ID

# View the key (copy this entire output)
cat github-actions-key.json
```

### Step 2: Add GitHub Secret

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret** (green button)
5. **Name**: `GCP_SA_KEY`
6. **Secret**: Paste the ENTIRE contents from `github-actions-key.json`
7. Click **Add secret**

### Step 3: Verify Configuration

Check that your workflow file has the correct values:

```bash
# Open the workflow file
open .github/workflows/ci-cd.yml
```

**Verify these values (around lines 21-28):**
- `PROJECT_ID: styleme-475201` ← Your GCP project
- `CLUSTER_NAME: styleme-cluster` ← Your GKE cluster name
- `CLUSTER_ZONE: us-central1-b` ← Your cluster zone

**If different, edit the file and update them.**

### Step 4: Test It

```bash
# Add all new files
git add .github/workflows/ci-cd.yml
git add CI/
git add NEXT_STEPS.md

# Commit
git commit -m "Add production CI/CD pipeline"

# Push to a test branch first (recommended)
git checkout -b test-ci-cd
git push origin test-ci-cd

# Then create a Pull Request on GitHub
# OR push directly to main:
# git push origin main
```

### Step 5: Monitor

1. Go to GitHub → **Actions** tab
2. You should see **"CI/CD Pipeline"** running
3. Click on it to see progress

## ✅ Checklist

Before pushing:

- [ ] GCP service account created
- [ ] GitHub secret `GCP_SA_KEY` added
- [ ] Workflow file has correct project/cluster names
- [ ] Old `ci.yml` deleted or disabled (to avoid running twice)
- [ ] Ready to push!

## 🎯 What Happens

### On Pull Request:
- ✅ Runs tests
- ✅ Checks coverage (≥60%)
- ❌ Does NOT deploy

### On Merge to Main:
- ✅ Runs tests
- ✅ Checks coverage (≥60%)
- ✅ Builds Docker images
- ✅ Deploys to Kubernetes

## 🐛 Troubleshooting

**If you see errors:**
- Check GitHub Actions logs
- Verify GCP service account has correct permissions
- Verify cluster name/zone in workflow file

**If tests fail:**
```bash
# Run tests locally first
./CI/scripts/run_tests.sh all
```

---

**That's it!** Follow these steps in order. Start with Step 1.

