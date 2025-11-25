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
├── midterm_presentation/                          
│   ├── StyleMeMidterm.pdf 
├── containers/                   # Docker container definitions
│   ├── ingestion/               # Data collection service
│   ├── preprocessing/            # Data cleaning service
│   ├── training/                # Model training service
│   └── inference/               # Inference service
├── queries/                     # User Input
│   ├── user1/
│   ├── ...
├── results/                     # Inference Output
│   ├── user1/
│   ├── ...
├── wardrobes/                   # User uploaded wardrobes
│   ├── user1/
│   ├── ...                     
├── catalog/                     # FAISS catalog indices (versioned)
│   ├── v_men_women_20251123/
│   └── ...
├── src/                          
│   ├── datapipeline/             # Data processing module
│   │   ├── dataloader.py         # Dataset and DataLoader
│   │   ├── bg_removal/           # Background removal
│   │   └── ...        
│   └── models/                   # Model training and inference
│       ├── train/                # Training module
│       │   ├── requirements.txt  
│       │   ├── config.py         
│       │   ├── model_training.py # FashionCLIP training
│       │   ├── run_fine_tuning.py # Fine-tuning script
│       │   ├── fine_tune_config.py # Fine-tuning configuration
│       │   ├── experiments/      # Experiment results
│       │   └── ...    
│       └── eval/                 # Evaluation rubrics
│           ├── evaluation.py     
│           └── quick_eval.py     
├── CI/                          # CI/CD configuration
│   ├── tests/                    # Test suites (unit, integration, e2e)
│   ├── config/                   # Linting and coverage config
│   ├── scripts/                 # CI helper scripts
│   └── README.md                # CI documentation
├── data_versioning/             # DVC configuration
│   ├── dvc_manager.py           # DVC management script
│   ├── gcs_snapshot_tracker.py  # GCS snapshot tracking
│   └── README.md                # Data versioning guide
├── install_nvidia_driver.sh     # GPU driver installation
├── cuda_installer.py            # CUDA setup automation
├── install_gpu_driver.py        # GPU driver management
├── docker-compose.yml           # Container orchestration
├── Makefile                     # Build and run commands
└── README.md
```

### Infrastructure Overview

Our system follows a containerized microservices architecture with four specialized services: **ingestion** for data collection, **preprocessing** for data cleaning and validation, **training** for model development with GPU support, and **inference** for serving recommendations. Data is stored in Google Cloud Storage (GCS) with ~13k curated product images and metadata. The system uses Docker Compose for orchestration and supports flexible deployment through service profiles.

---

## Milestone 4 Overview

This milestone focused on **production-ready deployment with comprehensive CI/CD, data versioning, and model fine-tuning**. We implemented a complete CI/CD pipeline using GitHub Actions for automated testing, linting, and coverage reporting. We established a robust data versioning system using DVC to manage datasets and model checkpoints, ensuring reproducibility throughout the project lifecycle. Additionally, we developed an optimized model fine-tuning pipeline with comprehensive experiment tracking, enabling systematic model improvement and deployment.

---

## Part I: Setup and Running Instructions

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- GPU support (for training, optional for inference)
- GCP credentials (for GCS access)

### Quick Start

#### 1. Clone Repository
```bash
git clone <repository-url>
cd styleme9.0
```

#### 2. Initial Setup
```bash
# Create necessary directories
make setup

# Or manually:
mkdir -p data logs catalog wardrobes queries results
```

#### 3. Run Complete Pipeline
```bash
# Build and run all services
make run

# Or using docker compose directly
docker compose --profile pipeline up --build
```

#### 4. Run Individual Services
```bash
make run-ingestion      # Data collection only
make run-preprocessing # Data processing only
make run-training      # Model training only
make run-inference     # Inference only
```

### Fine-Tuning Model

```bash
# Navigate to training directory
cd src/models/train

# Run fine-tuning with data version
python run_fine_tuning.py \
    --config fine_tune_config.py \
    --data-version catalog-v_men_women_20251123
```

**Note**: GPU is required for fine-tuning. The script will exit if GPU is not available.

### Running Inference

```bash
# Run inference for specific user query
make infer USER=grace QUERY=grace_query_01 THRESHOLD=0.3 GENDER=women

# Or manually:
docker compose run inference python /app/inference_service.py \
    --user-id user_001 \
    --query /app/queries/user_001/req_001/query.jpg \
    --output /app/results/user_001/req_001.json
```

### View Results

```bash
# Check inference results
cat results/user_001/req_001.json

# View training experiments
ls src/models/train/experiments/

# Check logs
make logs
```

---

## Part II: Application Components

### Section 1: App Design, Setup, and Code Organization

StyleMe follows a **containerized microservices architecture** with four specialized services (ingestion, preprocessing, training, and inference) that operate independently while maintaining seamless communication through Docker networking. The system processes fashion images through a pipeline that includes data collection, cleaning, model training, and real-time recommendation generation using FAISS-based similarity search. The user interface is a mobile-first React-based SPA built with TypeScript, Vite, and Tailwind CSS that allows users to upload wardrobe items, view their collections organized by category, and receive personalized fashion recommendations. The architecture emphasizes modularity, scalability, and reproducibility through versioned datasets and model checkpoints managed with DVC, with automated testing and code quality checks via CI/CD pipelines.

**Documentation**: See [Application Design Document](docs/Application%20design%20doc.md) for detailed solution architecture, technical architecture, system components, and design patterns.

---

### Section 2: APIs & Frontend

#### Backend APIs

The inference service provides a programmatic interface for fashion recommendations:

**Inference API** (`containers/inference/inference_service.py`)

```python
# API Endpoint (via Docker container)
python inference_service.py \
    --user-id <user_id> \
    --query <query_image_path> \
    --output <output_json_path> \
    [--threshold <similarity_threshold>] \
    [--gender <men/women/all>]
```

**Response Format:**
```json
{
  "user_id": "user_001",
  "query_image": "/app/queries/user_001/req_001/query.jpg",
  "timestamp": "2025-11-24T10:30:00",
  "used_wardrobe": false,
  "threshold": 0.7,
  "fallback_reason": "empty_wardrobe",
  "num_results": 3,
  "items": [
    {
      "rank": 1,
      "id": "30586307",
      "title": "Polo Ralph Lauren gilet",
      "brand": "Polo Ralph Lauren",
      "price": "$336",
      "url": "https://www.farfetch.com/...",
      "category": "Men, Clothing, Jackets",
      "image_path": "30586307_index1.jpg",
      "similarity": 0.892
    }
  ]
}
```

#### Frontend Integration

While StyleMe currently focuses on backend services, the architecture supports frontend integration:

**Current Interface:**
- File-based input/output (queries/ and results/ directories)
- JSON API responses
- Docker container endpoints

**Frontend-Ready Features:**
- RESTful API structure (can be wrapped in Flask/FastAPI)
- Image upload/download support
- Metadata-rich responses (product info, URLs, images)
- User session management (wardrobe per user_id)

**Integration Points:**
1. **Query Submission**: Upload images to `queries/{user_id}/`
2. **Wardrobe Management**: Add images to `wardrobes/{user_id}/images/`
3. **Result Retrieval**: Read JSON from `results/{user_id}/`

#### API Workflow

```
User Query Image
    ↓
[Upload to queries/{user_id}/]
    ↓
[Inference Service]
    ↓
[Generate Embedding]
    ↓
[Search Wardrobe Index] → Score >= threshold?
    ↓ YES                    ↓ NO
[Return Wardrobe Items]  [Search Catalog Index]
                              ↓
                         [Return Top-3 Products]
    ↓
[JSON Response in results/{user_id}/]
```

**Documentation**: 
- [API Integration Guide](API_INTEGRATION.md) - Complete API and frontend integration documentation
- [Inference Guide](containers/inference/INFERENCE_README.md) - Detailed inference system documentation

---

### Section 3: Continuous Integration and Testing

StyleMe implements a CI/CD pipeline using **GitHub Actions** that automatically runs on every push and pull request. The pipeline is configured in `.github/workflows/ci.yml` and executes four jobs in sequence: Build and Lint, Run Tests, Report Coverage, and CI Summary.

![CI Pipeline Overview](path/to/ci_pipeline_overview.png)

_Figure: CI Pipeline Summary showing workflow triggered via push, with all four jobs (Build and Lint: 3m 44s, Run Tests: 3m 47s, Report Coverage: 2m 24s, CI Summary: 3s) completed successfully. Total duration: 6m 24s_

**1. Build and Lint**
The pipeline performs automated build and code quality checks using Flake8. It sets up Python 3.10 environment, installs system and Python dependencies, and runs Flake8 linting on `src/`, `containers/`, and `scripts/` directories. The job includes steps for code checkout, disk cleanup, dependency installation, and code formatting checks.

![Build and Lint Job Details](path/to/build_and_lint_details.png)

_Figure: Build and Lint job execution showing detailed steps: Set up job (1s), Checkout code (1s), Clean up disk space (1m 21s), Set up Python 3.10 (8s), Install system dependencies (12s), Install Python dependencies (1m 55s), Run Flake8 linting (2s), Check code formatting (1s). Total duration: 3m 44s_

**2. Run Tests**
All test suites are executed in parallel:
- **Unit Tests**: Data loading, background removal, web scraping, model training, and inference utilities
- **Integration Tests**: Pipeline component integration
- **End-to-End Tests**: Complete pipeline from data to inference

Tests are run using pytest with markers for different test types (`unit`, `integration`, `e2e`). The test job runs in parallel with Build and Lint, taking approximately 3m 47s.

**3. Report Coverage**
Code coverage reports are generated and displayed in CI. The coverage job generates detailed reports showing file-level statistics and overall coverage percentage.

![Coverage Report Details](path/to/coverage_report_details.png)

_Figure: Report Coverage job showing detailed coverage output with file-level statistics (e.g., background_removal.py: 47.62%, extract_images.py: 68.94%), total coverage of 60.53%, and summary indicating "Required test coverage of 50% reached. Total coverage: 60.53%". Reports generated: XML (CI/coverage.xml) and HTML (CI/coverage_html/)_

- Minimum coverage requirement: **50%** (enforced with `--cov-fail-under=50`)
- Reports generated: HTML (`CI/coverage_html/`) and XML (`CI/coverage.xml`)
- Coverage displayed in CI summary and uploaded as GitHub Actions artifacts
- Current coverage: **60.53%** (exceeds minimum requirement)

![Coverage and CI Summary Cards](path/to/coverage_ci_summary_cards.png)

_Figure: Coverage Report Summary card showing coverage reports generated (XML: CI/coverage.xml, HTML: CI/coverage_html/) with minimum coverage requirement of 50%. CI Pipeline Summary card showing all checks passed: Build and Lint: success, Tests: success, Coverage: success, with note "All checks must pass for merge"_

---

### Section 4: Data Versioning and Reproducibility

#### Data Versioning Strategy

StyleMe implements **DVC (Data Version Control)** for managing datasets, model checkpoints, and large artifacts. This ensures reproducibility and tracks data lineage throughout the project lifecycle.

#### Chosen Method: DVC

**Justification:**
- **Git-friendly**: Works alongside Git without bloating repositories
- **Large file support**: Handles datasets and model checkpoints efficiently
- **Reproducibility**: Links code versions to data versions
- **GCS integration**: Tracks source data state in Google Cloud Storage
- **Flexibility**: Supports local and remote storage backends

**Alternative Considered**: Git LFS
- **Rejected**: Less flexible for ML workflows, requires additional setup

#### Versioning Workflow

**1. Catalog Versions**
Each catalog build is versioned with DVC tags:
```bash
# Add catalog to DVC
python data_versioning/dvc_manager.py add-catalog v_men_women_20251123

# Create version tag
python data_versioning/dvc_manager.py tag catalog-v_men_women_20251123 -m "Catalog: Men + Women"
```

**2. GCS Snapshots**
Source data state is recorded in `manifest.json`:
```bash
# Record GCS source state
python data_versioning/gcs_snapshot_tracker.py \
    catalog/v_men_women_20251123/manifest.json \
    --bucket styleme-data-bucket \
    --project styleme-475201
```

**3. Model Checkpoints**
Trained models are versioned with data version references:
```bash
# Add model checkpoint
python data_versioning/dvc_manager.py add-model fine_tune_20251123_163849

# Automatically links to data version used during training
```

#### Version History

**Three Levels of Versioning:**

1. **Git Commits**: Every commit creates a version
   ```bash
   git log --oneline --all -- "*.dvc"
   ```

2. **Git Tags**: Named milestones
   ```bash
   python data_versioning/dvc_manager.py list-tags
   ```

3. **GCS Snapshots**: Source data state
   ```bash
   cat catalog/v_*/manifest.json | grep gcs_source
   ```

**View History:**
```bash
# View all version history
python data_versioning/dvc_manager.py history

# View specific data version
python data_versioning/dvc_manager.py history catalog/v_men_women_20251123
```

#### Data Retrieval Instructions

**Pull Latest:**
```bash
python data_versioning/dvc_manager.py pull
```

**Checkout Specific Version:**
```bash
# Checkout by tag
python data_versioning/dvc_manager.py checkout catalog-v_men_women_20251123

# Or using DVC directly
dvc checkout catalog/v_men_women_20251123.dvc
```

**Push to Remote:**
```bash
python data_versioning/dvc_manager.py push
```

**Status Check:**
```bash
python data_versioning/dvc_manager.py status
```

#### Versioned Artifacts

- **Catalog Indices** (`catalog/v_*/`): FAISS indices, embeddings, metadata
- **Wardrobes** (`wardrobes/{user_id}/`): User wardrobe indices
- **Model Checkpoints** (`src/models/train/experiments/*/checkpoints/`): Trained models
- **Experiment Records** (`src/models/train/experiments/*/experiment_record.json`): Training metadata

#### Reproducibility

Each experiment record includes:
- `data_version`: DVC tag reference
- `gcs_snapshot_tag`: GCS source state
- Full configuration (hyperparameters, model settings)
- Training results (accuracy, loss, metrics)

**Reproduce Experiment:**
1. Checkout data version: `dvc checkout catalog-v_men_women_20251123`
2. Use config from `experiment_record.json`
3. Run training with recorded hyperparameters

**Documentation**: See `data_versioning/README.md` for complete guide.

---

### Section 5: Model Fine-Tuning

#### Training Scripts and Configuration

**Main Fine-Tuning Script**: `src/models/train/run_fine_tuning.py`

**Key Features:**
- Data versioning support (links to DVC tags)
- GPU requirement enforcement
- Automatic experiment tracking
- Checkpoint management (best and final models)
- Comprehensive logging

**Usage:**
```bash
cd src/models/train
python run_fine_tuning.py \
    --config fine_tune_config.py \
    --data-version catalog-v_men_women_20251123
```

**Configuration Files:**
- `fine_tune_config.py`: Optimized hyperparameters for fine-tuning
- `config.py`: Default training configuration

**Hyperparameters:**
```python
TRAINING_CONFIG = {
    'batch_size': 24,
    'epochs': 12,
    'learning_rate': 2e-5,
    'patience': 8,
    'target_accuracy': 0.70
}

MODEL_CONFIG = {
    'model_name': 'openai/clip-vit-base-patch32',
    'freeze_layers': 4,
    'feature_dim': 512
}

TRIPLET_CONFIG = {
    'margin': 0.5,
    'distance_metric': 'euclidean'
}
```

#### Dataset References (Versioned)

All fine-tuning experiments use **versioned datasets** tracked via DVC:

**Data Versioning:**
- Catalog versions tagged with DVC (e.g., `catalog-v_men_women_20251123`)
- GCS source state recorded in `manifest.json`
- Experiment records link to data versions

**Example Experiment Record:**
```json
{
  "experiment_id": "fine_tune_20251123_165320",
  "timestamp": "2025-11-23T16:53:20",
  "data_version": "catalog-v_men_women_20251123",
  "config": {
    "model": {
      "architecture": "openai/clip-vit-base-patch32",
      "frozen_layers": 4
    },
    "training": {
      "epochs": 12,
      "batch_size": 24,
      "learning_rate": 2e-5
    }
  }
}
```

#### Experiment Logs

**Experiment Structure:**
```
experiments/fine_tune_YYYYMMDD_HHMMSS/
├── experiment_record.json    # Complete experiment metadata
├── checkpoints/
│   ├── best_model.pth       # Best model checkpoint
│   └── final_model.pth     # Final model checkpoint
└── training_history.json     # Per-epoch metrics
```

**Experiment Tracking:**
- Automatic experiment ID generation (`fine_tune_YYYYMMDD_HHMMSS`)
- Full configuration logging
- Training metrics (loss, accuracy per epoch)
- Best model checkpoint (highest validation accuracy)
- Final model checkpoint (end of training)

**View Experiments:**
```bash
# List all experiments
ls src/models/train/experiments/

# View experiment record
cat src/models/train/experiments/fine_tune_*/experiment_record.json

# View experiment summary
cat src/models/train/experiments/EXPERIMENT_SUMMARY.md
```

#### Key Results Summary

**Current Performance:**
- **Best Compatibility Score**: 42.26% - 43.37%
- **Triplet Accuracy**: ~41% (target: >70%)
- **Status**: Ongoing fine-tuning to improve performance

**Fine-Tuning Improvements:**
- Optimized hyperparameters (learning rate, batch size, margin)
- Reduced frozen layers (8 → 4) for more fine-tuning
- Increased epochs (20-30 → 50) for better convergence
- I/O optimization to prevent training interruptions

**Expected Improvements:**
- Triplet Accuracy: 41% → 60-70%
- Compatibility Score: 43% → 55-65%
- Better inference quality and recommendations

#### Deployment Strategy

**Model Deployment Workflow:**

1. **Fine-Tune Model**
   ```bash
   python run_fine_tuning.py --data-version catalog-v_men_women_20251123
   ```

2. **Evaluate Results**
   - Check `experiment_record.json` for metrics
   - Compare with baseline performance
   - Validate on test set

3. **Version Model**
   ```bash
   python data_versioning/dvc_manager.py add-model fine_tune_YYYYMMDD_HHMMSS
   ```

4. **Update Inference Service**
   - Copy `best_model.pth` to inference container
   - Update model path in inference configuration
   - Rebuild inference container

5. **Deploy**
   ```bash
   docker compose build inference
   docker compose up inference
   ```

**Model Selection Criteria:**
- Best validation accuracy > 70%
- Improved compatibility score vs. baseline
- Stable training (no overfitting)
- Successful test set evaluation

**Documentation**: See [Model Fine-Tuning Guide](src/models/train/MODEL_FINE_TUNING.md) for complete fine-tuning guide.
