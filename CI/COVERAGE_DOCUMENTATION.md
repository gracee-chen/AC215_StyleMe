# Test Coverage Documentation

## Overview

This document details the test coverage status for the StyleMe codebase. The minimum coverage requirement is **60%** for production deployments.

## Current Coverage Status

Coverage is measured across:
- `src/` - Source code modules
- `containers/` - Container service code

## Excluded from Coverage

The following modules and files are **intentionally excluded** from coverage requirements:

### 1. Configuration and Setup Files
- `*/__init__.py` - Package initialization files (no executable code)
- `*/setup.py` - Package setup scripts
- `*/config.py` - Configuration files (tested via integration tests)
- `*/entrypoint.sh` - Shell scripts (not Python code)
- `*/Dockerfile` - Docker build files

### 2. Documentation and Examples
- `*/README.md` - Documentation files
- `*/TEST.md` - Test documentation
- `*/BACKGROUND_REMOVAL_GUIDE.md` - Guide documentation
- `*/CONTAINERIZATION.md` - Containerization docs
- `*/INFERENCE_*.md` - Inference documentation
- `*/examples/*` - Example code (not production code)

### 3. Data and Artifact Directories
- `*/experiments/*` - Experiment results (data, not code)
- `*/catalog/*` - Catalog data files
- `*/wardrobes/*` - User wardrobe data
- `*/data/*` - Data files
- `*/logs/*` - Log files
- `*/results/*` - Result files
- `*/queries/*` - Query data files

### 4. Build and Utility Scripts
- `*/build_*.py` - Build scripts (run during container build)
- `*/retry_failed.py` - Utility scripts for manual operations
- `*/run_training.sh` - Shell scripts

### 5. Explicitly Excluded Modules (Require Manual Testing)

These modules are excluded because they:
- Require GPU resources (expensive to test in CI)
- Require large datasets (not practical for CI)
- Are integration points that are tested via E2E tests
- Are legacy code paths that are being phased out

#### `containers/inference/inference_service.py`
- **Reason**: Core inference service tested via integration and E2E tests
- **Status**: Covered by `CI/tests/test_inference.py` and `CI/tests/test_e2e.py`
- **Coverage Type**: Integration/E2E testing

#### `src/models/train/model_training.py`
- **Reason**: Model training requires GPU and large datasets
- **Status**: Tested via `CI/tests/test_model_training.py` (mocked GPU)
- **Coverage Type**: Unit tests with mocks

#### `src/datapipeline/dataloader.py`
- **Reason**: Data loading requires large datasets and GCS access
- **Status**: Tested via `CI/tests/test_dataloader.py` (mocked data)
- **Coverage Type**: Unit tests with mocks

#### `src/datapipeline/bg_removal/batch_processor.py`
- **Reason**: Batch processing requires GPU and large image datasets
- **Status**: Tested via `CI/tests/test_bg_removal.py` (mocked processing)
- **Coverage Type**: Unit tests with mocks

## Tested Modules

### Unit Tests (`CI/tests/test_*.py`)

1. **`test_dataloader.py`**
   - Tests: `src/datapipeline/dataloader.py` (mocked)
   - Coverage: Core data loading logic

2. **`test_bg_removal.py`**
   - Tests: `src/datapipeline/bg_removal/*.py` (mocked GPU operations)
   - Coverage: Background removal algorithms

3. **`test_scraper.py`** and **`test_scraper_extract.py`**
   - Tests: `src/datapipeline/scraper/*.py`
   - Coverage: Web scraping functionality

4. **`test_model_training.py`**
   - Tests: `src/models/train/*.py` (mocked GPU)
   - Coverage: Model training logic

5. **`test_inference.py`**
   - Tests: `containers/inference/*.py` (mocked inference service)
   - Coverage: Inference API and service logic

6. **`test_api.py`**
   - Tests: `containers/inference/api_server.py`
   - Coverage: API endpoints and request handling

### Integration Tests (`CI/tests/integration/test_pipeline.py`)

- Tests multiple modules working together
- Tests data flow through the pipeline
- Tests background removal integration
- Tests inference service with mocked dependencies

### End-to-End Tests (`CI/tests/test_e2e.py`)

- Tests complete pipeline from data loading to inference
- Tests with real (but small) test data
- Tests inference with background removal integration

## Modules Requiring Additional Coverage

To reach and maintain **60% coverage**, the following modules may need additional test coverage:

### Priority 1: Core Business Logic
1. **`containers/inference/api_server.py`**
   - Current: Basic API tests exist
   - Needed: More edge case testing, error handling

2. **`containers/inference/build_catalog_index.py`**
   - Current: May have limited coverage
   - Needed: Test catalog index building logic

3. **`containers/inference/build_user_wardrobe.py`**
   - Current: May have limited coverage
   - Needed: Test wardrobe building logic

### Priority 2: Data Pipeline
4. **`src/datapipeline/scraper/extract_images.py`**
   - Current: Basic tests exist
   - Needed: More edge cases, error handling

5. **`src/models/eval/evaluation.py`**
   - Current: May have limited coverage
   - Needed: Test evaluation metrics and scoring

6. **`src/models/eval/quick_eval.py`**
   - Current: May have limited coverage
   - Needed: Test quick evaluation logic

### Priority 3: Configuration and Training
7. **`src/models/train/fine_tune_config.py`**
   - Current: May have limited coverage
   - Needed: Test configuration loading and validation

8. **`src/models/train/run_fine_tuning.py`**
   - Current: May have limited coverage (requires GPU)
   - Needed: More mocked unit tests

## Coverage Measurement

Coverage is measured using:
- **Tool**: `pytest-cov` (coverage.py)
- **Configuration**: `CI/config/.coveragerc`
- **Minimum Requirement**: 60% line coverage
- **Reports**: 
  - HTML: `CI/coverage_html/index.html`
  - XML: `CI/coverage.xml` (for CI tools)

## Running Coverage Locally

```bash
# Run all tests with coverage
./CI/scripts/run_tests.sh all

# View HTML report
open CI/coverage_html/index.html

# Or run directly
pytest CI/tests/ \
  --cov=src \
  --cov=containers \
  --cov-config=CI/config/.coveragerc \
  --cov-report=html:CI/coverage_html \
  --cov-report=term-missing \
  --cov-fail-under=60
```

## CI/CD Coverage Checks

The GitHub Actions workflow (`/.github/workflows/ci-cd.yml`) automatically:
1. Runs unit tests with coverage
2. Runs integration tests with coverage
3. Combines coverage reports
4. Fails if coverage is below 60%
5. Uploads coverage reports as artifacts

## Improving Coverage

To improve coverage:

1. **Identify gaps**: Run coverage and review `CI/coverage_html/index.html`
2. **Add unit tests**: Create tests in `CI/tests/test_*.py`
3. **Add integration tests**: Add to `CI/tests/integration/test_pipeline.py`
4. **Test edge cases**: Add tests for error conditions and boundary cases
5. **Mock external dependencies**: Use `pytest-mock` for GPU, GCS, etc.

## Notes

- **GPU-dependent code**: Tested with mocks in unit tests, full testing in E2E
- **GCS-dependent code**: Tested with mocks in unit tests, full testing in E2E
- **Large dataset code**: Tested with small sample data in tests
- **Integration points**: Tested via integration and E2E tests rather than unit tests

## Coverage Goals

- **Current Target**: 60% minimum (production requirement)
- **Future Target**: 70%+ (stretch goal)
- **Critical Paths**: 80%+ (API endpoints, inference service)

---

**Last Updated**: 2025-01-XX  
**Coverage Tool**: coverage.py 7.3.0+  
**Test Framework**: pytest 7.4.0+

