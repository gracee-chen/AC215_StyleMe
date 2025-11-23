# Step-by-Step: Test CI Pipeline on GitHub

## Current Status
- ✅ Branch `ci-pipeline-setup` is pushed to GitHub
- ✅ CI workflow is configured (`.github/workflows/ci.yml`)
- ✅ CI triggers on PRs to `main`, `master`, or `develop`

---

## Step 1: Go to Your Repository

1. Open your browser
2. Go to: **https://github.com/gracee-chen/AC215_StyleMe**
3. You should see your repository

---

## Step 2: Create a Pull Request

### Option A: Using the GitHub Web Interface

1. On the repository page, click the **"Pull requests"** tab (top menu)
2. Click the green **"New pull request"** button
3. In the "Compare changes" page:
   - **Base branch**: Select `main` (or `master`/`develop` - whichever is your main branch)
   - **Compare branch**: Select `ci-pipeline-setup`
4. Review the changes (you should see 29 files changed)
5. Click **"Create pull request"**
6. Fill in:
   - **Title**: `Add CI/CD Pipeline with Automated Testing`
   - **Description**: 
     ```
     This PR adds a comprehensive CI/CD pipeline with:
     - GitHub Actions workflow
     - Automated testing (unit, integration, E2E)
     - Code coverage reporting (57.89% coverage)
     - Flake8 linting
     - Background removal integration
     ```
7. Click **"Create pull request"** (green button)

### Option B: Using the Direct Link

1. Click this link: **https://github.com/gracee-chen/AC215_StyleMe/pull/new/ci-pipeline-setup**
2. Select base branch: `main` (or `master`/`develop`)
3. Fill in title and description
4. Click **"Create pull request"**

---

## Step 3: Watch CI Pipeline Run

Once the PR is created, CI will **automatically start** (no need to do anything):

### On the PR Page:

1. **Scroll down** to the **"Checks"** section
2. You'll see 4 jobs queued/running:
   - 🔄 **build-and-lint** - Code quality checks
   - 🔄 **test** - Run all test suites
   - 🔄 **coverage** - Generate coverage report
   - 🔄 **ci-summary** - Summary of all checks

3. **Wait for jobs to complete** (takes ~15-25 minutes)

### What You'll See:

- **🟡 Yellow circle** = Job is running
- **✅ Green checkmark** = Job passed
- **❌ Red X** = Job failed
- **⏸️ Gray circle** = Job is queued/waiting

---

## Step 4: Check Individual Job Status

### To see detailed logs:

1. Click on any job name (e.g., "build-and-lint")
2. You'll see:
   - **Job status** (running/passed/failed)
   - **Step-by-step logs**
   - **Artifacts** (for coverage job)

### Or go to Actions tab:

1. Click **"Actions"** tab (top menu)
2. Click on the latest workflow run (should show "Add CI/CD Pipeline...")
3. See all 4 jobs and their status

---

## Step 5: View Coverage Report

1. Go to the **"coverage"** job (in Actions or PR Checks)
2. Scroll down to **"Artifacts"** section
3. Download **"coverage-report"** artifact
4. Extract the ZIP file
5. Open `CI/coverage_html/index.html` in your browser
6. You'll see:
   - Overall coverage percentage (should be ≥50%)
   - File-by-file coverage
   - Line-by-line coverage details

---

## Step 6: Verify All Checks Pass

### Success Indicators:

✅ All 4 jobs show **green checkmarks**
✅ Coverage shows **≥50%** (currently 57.89%)
✅ All tests pass (52 tests)
✅ Linting passes
✅ PR shows **"All checks have passed"**

### If Something Fails:

1. Click on the failed job
2. Check the error logs
3. Fix the issue locally
4. Push another commit to the same branch
5. CI will automatically re-run

---

## Step 7: Merge the PR (Optional)

Once all checks pass:

1. On the PR page, click **"Merge pull request"**
2. Confirm merge
3. CI will run again on the merged commit to `main`

---

## Expected Timeline

- **build-and-lint**: ~2-3 minutes
- **test**: ~5-10 minutes  
- **coverage**: ~5-10 minutes
- **ci-summary**: ~1 minute
- **Total**: ~15-25 minutes

---

## Quick Reference Links

- **Repository**: https://github.com/gracee-chen/AC215_StyleMe
- **Create PR**: https://github.com/gracee-chen/AC215_StyleMe/pull/new/ci-pipeline-setup
- **Actions**: https://github.com/gracee-chen/AC215_StyleMe/actions
- **Branch**: https://github.com/gracee-chen/AC215_StyleMe/tree/ci-pipeline-setup

---

## Troubleshooting

### CI Not Running?

- ✅ Check if PR is targeting `main`, `master`, or `develop`
- ✅ Verify `.github/workflows/ci.yml` exists in your branch
- ✅ Check Actions tab for any errors

### Tests Failing?

- Run tests locally first: `./CI/scripts/run_tests.sh all`
- Check error logs in the failed job
- Fix issues and push again

### Coverage Below 50%?

- Check coverage report in artifacts
- Review `CI/config/.coveragerc` for exclusions
- Add more tests if needed

---

## What Happens Next?

After CI passes:
- ✅ Your code is validated
- ✅ All tests pass
- ✅ Coverage meets requirements
- ✅ Code quality checks pass
- ✅ Ready to merge!

