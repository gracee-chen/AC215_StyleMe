# Continuous Integration and Testing

This directory contains all CI/CD configuration, tests, and scripts for StyleMe 10.0.

## 📁 Directory Structure

```
CI/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions workflow
├── config/                            # Configuration files
│   ├── .flake8                        # Flake8 linting configuration
│   ├── .coveragerc                    # Coverage configuration
│   └── pytest.ini                     # Pytest configuration
├── tests/                             # Test files
│   ├── test_dataloader.py            # Unit tests for dataloader
│   ├── test_bg_removal.py            # Unit tests for background removal
│   ├── test_scraper.py               # Unit tests for scraper
│   ├── test_model_training.py        # Unit tests for model training
│   ├── test_inference.py             # Unit tests for inference
│   ├── test_e2e.py                    # End-to-end tests
│   ├── integration/                   # Integration tests
│   │   └── test_pipeline.py
│   └── fixtures/                      # Test fixtures and sample data
│       └── sample_data.json
├── scripts/                           # Helper scripts
│   ├── run_tests.sh                   # Run tests locally
│   ├── run_lint.sh                    # Run linting locally
│   └── setup_ci_env.sh                # Setup CI environment
├── requirements-dev.txt               # Development dependencies
└── README.md                          # This file
```

## 🚀 Quick Start

### Setup CI Environment

```bash
# Run setup script
./CI/scripts/setup_ci_env.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r CI/requirements-dev.txt
```

### Run Tests Locally

```bash
# Run all tests
./CI/scripts/run_tests.sh

# Run specific test types
./CI/scripts/run_tests.sh unit          # Unit tests only
./CI/scripts/run_tests.sh integration   # Integration tests only
./CI/scripts/run_tests.sh e2e           # End-to-end tests only
```

### Run Linting Locally

```bash
./CI/scripts/run_lint.sh
```

## 📋 CI Pipeline Requirements

The CI pipeline must fulfill the following requirements:

### ✅ 1. Build and Lint
- **Automated Build**: Verifies code can be built/imported
- **Code Quality Checks**: Uses Flake8 for Python linting
- **Runs on**: Every push and pull request

### ✅ 2. Run Tests
- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test multiple modules working together
- **End-to-End Tests**: Test complete pipeline
- **Runs on**: Every push and pull request

### ✅ 3. Report Coverage
- **Generate Coverage Reports**: HTML and XML formats
- **Minimum Coverage**: 60% (production requirement)
- **Display Coverage**: In CI artifacts and summary
- **Runs on**: Every push and pull request
- **Documentation**: See [COVERAGE_DOCUMENTATION.md](./COVERAGE_DOCUMENTATION.md)

## 🔧 Configuration Files

### Flake8 Configuration (`.flake8`)
- Max line length: 120 characters
- Excludes: `__pycache__`, `venv`, `experiments`, etc.
- Per-file ignores for `__init__.py`

### Coverage Configuration (`.coveragerc`)
- Sources: `src/`, `containers/`
- Omits: test files, examples, documentation
- Minimum coverage: 60% (production requirement)
- Reports: HTML and XML formats
- See [COVERAGE_DOCUMENTATION.md](./COVERAGE_DOCUMENTATION.md) for details

### Pytest Configuration (`pytest.ini`)
- Test paths: `CI/tests`
- Coverage: `src/`, `containers/`
- Markers: `unit`, `integration`, `e2e`, `slow`, `gpu`, `docker`
- Fail under: 60% coverage (production requirement)

## 🧪 Test Structure

### Unit Tests
Located in `CI/tests/test_*.py`:
- `test_dataloader.py` - Tests for data loading functionality
- `test_bg_removal.py` - Tests for background removal
- `test_scraper.py` - Tests for web scraping
- `test_model_training.py` - Tests for model training
- `test_inference.py` - Tests for inference service (includes bg_removal integration tests)

### Integration Tests
Located in `CI/tests/integration/`:
- `test_pipeline.py` - Tests for pipeline components working together (includes bg_removal integration)

### End-to-End Tests
Located in `CI/tests/test_e2e.py`:
- Complete pipeline tests from data loading to inference
- Tests for inference with background removal integration

## 📊 Coverage Reports

Coverage reports are generated in:
- **HTML**: `CI/coverage_html/` (view in browser)
- **XML**: `CI/coverage.xml` (for CI tools)

View coverage locally:
```bash
pytest CI/tests/ --cov=src --cov=containers --cov-report=html:CI/coverage_html
open CI/coverage_html/index.html
```

## 🔄 GitHub Actions CI/CD Pipeline

The CI/CD pipeline runs automatically on:
- **Push** to `main` or `master` branches
- **Pull Requests** to `main` or `master` branches

### Workflow Jobs

#### For All Branches (PRs and main):
1. **lint**: Runs Flake8 code quality checks
2. **unit-tests**: Runs unit test suite with coverage
3. **integration-tests**: Runs integration test suite with coverage
4. **e2e-tests**: Runs end-to-end test suite
5. **coverage**: Generates combined coverage report (requires ≥60%)
6. **ci-summary**: Provides summary of all checks

#### For Main Branch Only (after merge):
7. **build-images**: Builds and pushes Docker images to Artifact Registry
8. **deploy-k8s**: Deploys updated images to Kubernetes cluster

### Workflow Features

- ✅ Runs on Python 3.10
- ✅ Caches pip dependencies
- ✅ Parallel job execution
- ✅ Coverage artifacts upload (HTML + XML)
- ✅ Detailed test reports
- ✅ Automatic Docker image building
- ✅ Automatic Kubernetes deployment
- ✅ Image tagging with commit SHA and date

### Setup Instructions

See **[CD_SETUP_GUIDE.md](./CD_SETUP_GUIDE.md)** for detailed setup instructions.

**Quick Setup Checklist:**
1. Create GCP service account with required permissions
2. Add `GCP_SA_KEY` secret to GitHub repository
3. Verify Artifact Registry repository exists
4. Verify GKE cluster exists and is accessible
5. Push to `main` branch to trigger deployment

## 📝 Writing New Tests

### Unit Test Example

```python
import pytest
from src.datapipeline.dataloader import FashionTripletDataset

@pytest.mark.unit
def test_dataset_initialization():
    """Test that dataset initializes correctly"""
    dataset = FashionTripletDataset(...)
    assert len(dataset) > 0
```

### Background Removal Integration Tests

The CI includes comprehensive tests for background removal integration:
- **Unit tests**: Test bg_removal initialization and RGBA conversion
- **Integration tests**: Test complete inference flow with bg_removal
- **E2E tests**: Test end-to-end pipeline with background removal

Test fixtures are available in `CI/tests/fixtures/test_images.py` for creating test images with/without backgrounds.

### Integration Test Example

```python
import pytest

@pytest.mark.integration
def test_data_loading_workflow():
    """Test complete data loading workflow"""
    # Test multiple modules together
    ...
```

### End-to-End Test Example

```python
import pytest

@pytest.mark.e2e
def test_complete_pipeline():
    """Test complete pipeline from data to inference"""
    # Test full pipeline
    ...
```

## 🐛 Troubleshooting

### Tests Fail Locally

1. **Check dependencies**: `pip install -r CI/requirements-dev.txt`
2. **Check Python version**: Requires Python 3.9+
3. **Check virtual environment**: Activate venv before running tests

### Linting Fails

1. **Check Flake8 config**: `CI/config/.flake8`
2. **Fix line length**: Max 120 characters
3. **Check excluded files**: Some files are excluded from linting

### Coverage Below 60%

1. **Add more tests**: Write tests for uncovered code
2. **Check coverage report**: `CI/coverage_html/index.html`
3. **Review omissions**: See [COVERAGE_DOCUMENTATION.md](./COVERAGE_DOCUMENTATION.md)
4. **Identify gaps**: Review coverage report to find untested modules

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## ✅ CI Checklist

Before pushing, ensure:
- [ ] All tests pass locally: `./CI/scripts/run_tests.sh`
- [ ] Linting passes: `./CI/scripts/run_lint.sh`
- [ ] Coverage >= 60%: Check coverage report
- [ ] New tests added for new features
- [ ] Documentation updated if needed

## 🎯 CI Requirements Summary

✅ **Build and Lint**: Automated build and Flake8 code quality checks  
✅ **Run Tests**: Unit, integration, and end-to-end test suites  
✅ **Report Coverage**: Generate and display coverage reports (minimum 60%)  
✅ **GitHub Actions**: Runs on every push and pull request  
✅ **Docker Build**: Automatic image building on main branch  
✅ **Kubernetes Deployment**: Automatic deployment on main branch  

All requirements are fulfilled! 🎉

## 📚 Additional Documentation

- **[CD_SETUP_GUIDE.md](./CD_SETUP_GUIDE.md)**: Step-by-step CI/CD setup instructions
- **[COVERAGE_DOCUMENTATION.md](./COVERAGE_DOCUMENTATION.md)**: Detailed coverage documentation and untested modules

