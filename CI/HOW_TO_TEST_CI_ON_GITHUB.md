# How to Test CI Pipeline on GitHub

## Quick Steps

### Step 1: Commit Your Changes

```bash
cd /home/chufeip/styleme10.0

# Add all CI files
git add .github/ CI/ .gitignore
git add containers/inference/  # If you modified inference files

# Commit
git commit -m "Add CI/CD pipeline with 50%+ coverage"

# Push to your branch
git push origin styleme10.0
```

### Step 2: Create Pull Request

1. Go to: **https://github.com/gracee-chen/AC215_StyleMe**
2. Click **"Pull Requests"** tab
3. Click **"New Pull Request"**
4. Select:
   - **Base**: `main` (or `master`/`develop` - whichever is your main branch)
   - **Compare**: `styleme10.0`
5. Click **"Create Pull Request"**
6. Fill in PR title and description
7. Click **"Create Pull Request"**

### Step 3: Watch CI Run

Once PR is created, CI will **automatically start**:

1. Go to your PR page
2. Scroll down to **"Checks"** section
3. You'll see 4 jobs running:
   - ✅ **build-and-lint** - Linting check
   - ✅ **test** - Run all tests
   - ✅ **coverage** - Generate coverage report
   - ✅ **ci-summary** - Summary of all checks

### Step 4: Check CI Status

**On PR Page:**
- Look for checkmarks (✅) or X marks (❌) next to each job
- Click on a job to see detailed logs

**Or go directly to Actions:**
- Go to: **https://github.com/gracee-chen/AC215_StyleMe/actions**
- Click on the latest workflow run
- See all jobs and their status

---

## Method 2: Push Directly to Main Branch

⚠️ **Note**: Only do this if you have permission to push to main/master/develop

```bash
# Switch to main branch
git checkout main  # or master/develop

# Merge your changes
git merge styleme10.0

# Push
git push origin main
```

CI will automatically run on push.

---

## What to Look For

### ✅ Success Indicators:
- All jobs show green checkmarks (✅)
- Coverage shows **≥50%**
- All tests pass
- Linting passes

### ❌ Failure Indicators:
- Red X marks (❌)
- Click on failed job to see error logs
- Common issues:
  - Tests failing
  - Coverage below 50%
  - Linting errors

---

## Viewing Coverage Report

1. Go to the **coverage** job in Actions
2. Scroll to **"Artifacts"** section
3. Download **"coverage-report"** artifact
4. Extract and open `CI/coverage_html/index.html` in browser

---

## Expected Duration

- **build-and-lint**: ~2-3 minutes
- **test**: ~5-10 minutes
- **coverage**: ~5-10 minutes
- **Total**: ~15-25 minutes

---

## Troubleshooting

### CI Not Running?
- Check if branch name matches: `main`, `master`, or `develop`
- Verify `.github/workflows/ci.yml` exists
- Check Actions tab for any errors

### Tests Failing?
- Click on failed test job
- Check error logs
- Run tests locally first: `./CI/scripts/run_tests.sh`

### Coverage Below 50%?
- Check coverage report in artifacts
- Add more tests to increase coverage
- Review `CI/config/.coveragerc` for exclusions

---

## Quick Commands

```bash
# Test locally before pushing
./CI/scripts/run_lint.sh
./CI/scripts/run_tests.sh all

# Commit and push
git add .github/ CI/ .gitignore
git commit -m "Add CI/CD pipeline"
git push origin styleme10.0
```

Then create PR on GitHub!

