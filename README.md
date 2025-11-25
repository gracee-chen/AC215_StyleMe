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

StyleMe implements a comprehensive CI/CD pipeline using **GitHub Actions** that automatically runs on every push and pull request. The pipeline is configured in `.github/workflows/ci.yml` and executes four sequential jobs to ensure code quality and reliability. The **Build and Lint** job performs automated build verification and code quality checks using Flake8, setting up Python 3.10 environments, installing system and Python dependencies from `requirements.txt` and `CI/requirements-dev.txt`, and running linting on `src/`, `containers/`, and `scripts/` directories with a maximum line length of 120 characters. The **Run Tests** job executes all test suites in parallel using pytest with markers for different test types, including unit tests for data loading, background removal, web scraping, model training, and inference utilities; integration tests for pipeline component interactions; and end-to-end tests that verify the complete pipeline from data ingestion to inference. Tests are run using `pytest-xdist` for parallel execution, excluding slow tests that require external resources like GCS or GPU. The **Report Coverage** job generates and displays code coverage reports with a minimum requirement of 50%, producing reports in both HTML format (accessible via `CI/coverage_html/index.html`) and XML format (`CI/coverage.xml`) for integration with CI tools. The current coverage stands at 60.53%, exceeding the minimum requirement, and coverage results are uploaded as GitHub Actions artifacts and displayed in the CI summary. The **CI Summary** job aggregates all check results and provides a final status overview, ensuring all checks pass before code can be merged.

![CI Pipeline Overview](path/to/ci_pipeline_overview.png)

_Figure: CI Pipeline workflow overview showing all four jobs completed successfully_

![Build and Lint Job Details](path/to/build_and_lint_details.png)

_Figure: Build and Lint job execution steps and timing_

![Coverage Report Details](path/to/coverage_report_details.png)

_Figure: Detailed code coverage report with file-level statistics_

![Coverage and CI Summary Cards](path/to/coverage_ci_summary_cards.png)

_Figure: Coverage Report Summary and CI Pipeline Summary cards_

---

### Section 4: Data Versioning and Reproducibility

StyleMe implements **DVC (Data Version Control)** for managing datasets, model checkpoints, and large artifacts to ensure reproducibility and track data lineage throughout the project lifecycle. The system versions three types of artifacts: catalog indices (FAISS indices, embeddings, and metadata generated from GCS source data via `build_catalog_index.py`), user wardrobes (per-user FAISS indices and embeddings), and model checkpoints (trained model weights automatically linked to the data versions used during training). Source data in Google Cloud Storage (`gs://styleme-data-bucket/`) is tracked via metadata snapshots in `manifest.json`, which record which GCS files were used, track gender filters (men/women/all), and maintain history of data states. The versioning system operates at three levels: Git commits for every data change, Git tags for named milestones (e.g., `catalog-v_men_women_20251123`), and GCS snapshots for source data state. Each experiment record includes the data version reference, GCS snapshot tag, full configuration (hyperparameters, model settings), and training results, enabling complete reproducibility by linking model versions to training configs to catalog versions to GCS source state.

![Data Versioning](path/to/data_versioning.png)

**Documentation**: See [Data Versioning Guide](docs/data_versioning.md) for complete methodology, usage instructions, and reproducibility workflow.

---

### Section 5: Model Fine-Tuning

StyleMe fine-tunes a **FashionCLIP model** (based on OpenAI CLIP ViT-B/32) to learn fashion compatibility relationships from curated product data. The fine-tuning process uses a **triplet loss** objective with partial layer freezing (4 layers frozen, reduced from baseline 8) to adapt the pre-trained vision-language model to fashion-specific compatibility patterns. Training is performed on versioned datasets tracked via DVC tags (e.g., `catalog-v_men_women_20251123`), with each experiment automatically generating unique IDs (`fine_tune_YYYYMMDD_HHMMSS`), comprehensive metadata records, and model checkpoints (best and final models saved). The system enforces GPU requirements, implements early stopping based on validation accuracy, and optimizes I/O to prevent training interruptions. Current baseline performance shows ~41% triplet accuracy and 42-43% compatibility scores, with fine-tuning targeting >70% triplet accuracy and >50% compatibility scores through optimized hyperparameters (learning rate 2e-5, batch size 24, margin 0.5) and improved convergence strategies. All experiments are fully reproducible through DVC versioning, linking model checkpoints to training configurations, catalog versions, and GCS source data states.

**Documentation**: See [Model Training Guide](docs/model_training.md) for complete training workflow, configuration details, experiment tracking, and deployment strategies.
