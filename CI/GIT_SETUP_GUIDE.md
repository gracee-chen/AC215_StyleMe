# Git Setup Guide: New Branch & Token

## Step 1: Get a New GitHub Personal Access Token

### Option A: Classic Token (Recommended for now)

1. Go to: **https://github.com/settings/tokens**
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `StyleMe CI Token`
4. Select expiration: **90 days** (or your preference)
5. Select scopes (check these):
   - ✅ **repo** (Full control of private repositories)
     - This includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
6. Click **"Generate token"**
7. **⚠️ COPY THE TOKEN IMMEDIATELY** - You won't see it again!
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Option B: Fine-Grained Token (More Secure)

1. Go to: **https://github.com/settings/tokens?type=beta**
2. Click **"Generate new token"**
3. Token name: `StyleMe CI Token`
4. Expiration: Choose your preference
5. Repository access: Select **"Only select repositories"** → Choose `AC215_StyleMe`
6. Permissions:
   - **Repository permissions**:
     - Contents: Read and write
     - Metadata: Read-only
     - Pull requests: Read and write
     - Actions: Read and write (for CI)
7. Click **"Generate token"**
8. **⚠️ COPY THE TOKEN IMMEDIATELY**

---

## Step 2: Update Git Remote with New Token

```bash
cd /home/chufeip/styleme10.0

# Replace YOUR_NEW_TOKEN with the token you just copied
git remote set-url origin https://YOUR_NEW_TOKEN@github.com/gracee-chen/AC215_StyleMe.git

# Verify it's updated
git remote -v
```

**Example:**
```bash
git remote set-url origin https://ghp_abc123xyz789@github.com/gracee-chen/AC215_StyleMe.git
```

---

## Step 3: Create a New Branch (or use current one)

### Option A: Create a new branch from current state

```bash
# Create and switch to new branch
git checkout -b ci-pipeline-setup

# Or if you want a different name:
git checkout -b feature/ci-integration
```

### Option B: Create branch from main/master

```bash
# Fetch latest from remote
git fetch origin

# Create new branch from main
git checkout -b ci-pipeline-setup origin/main

# Or from master:
git checkout -b ci-pipeline-setup origin/master
```

### Option C: Use current branch (styleme10.0)

```bash
# Just stay on current branch
git checkout styleme10.0
```

---

## Step 4: Commit Your Changes

```bash
# Add all CI-related files
git add .github/
git add CI/
git add .gitignore

# Add inference changes (if you want)
git add containers/inference/

# Check what will be committed
git status

# Commit
git commit -m "Add CI/CD pipeline with automated testing and 50%+ coverage

- Add GitHub Actions workflow for CI
- Add comprehensive test suite (unit, integration, E2E)
- Add Flake8 linting configuration
- Add coverage reporting (57.89% coverage)
- Integrate bg_removal into inference pipeline
- Add CI documentation and helper scripts"
```

---

## Step 5: Push to GitHub

```bash
# Push to your branch (replace branch-name with your actual branch)
git push origin ci-pipeline-setup

# Or if using current branch:
git push origin styleme10.0

# If branch doesn't exist on remote yet, use:
git push -u origin ci-pipeline-setup
```

---

## Step 6: Verify on GitHub

1. Go to: **https://github.com/gracee-chen/AC215_StyleMe**
2. Check your branch appears in the branch dropdown
3. Verify your commits are there
4. CI should automatically run if you pushed to `main`, `master`, or `develop`

---

## Troubleshooting

### Token Still Not Working?

```bash
# Test connection
git fetch origin

# If it fails, try using SSH instead (requires SSH key setup):
git remote set-url origin git@github.com:gracee-chen/AC215_StyleMe.git
```

### Permission Denied?

- Make sure token has **repo** scope
- Check token hasn't expired
- Verify you have write access to the repository

### Branch Already Exists?

```bash
# Delete local branch
git branch -D branch-name

# Delete remote branch
git push origin --delete branch-name

# Then create new one
```

---

## Quick Command Summary

```bash
# 1. Update token
git remote set-url origin https://YOUR_NEW_TOKEN@github.com/gracee-chen/AC215_StyleMe.git

# 2. Create branch
git checkout -b ci-pipeline-setup

# 3. Add and commit
git add .github/ CI/ .gitignore containers/inference/
git commit -m "Add CI/CD pipeline"

# 4. Push
git push -u origin ci-pipeline-setup
```

