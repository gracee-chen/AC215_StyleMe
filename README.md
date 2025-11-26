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
├── containers/                   # Docker container definitions
│   ├── ingestion/               # Data collection service
│   ├── preprocessing/           # Data cleaning service
│   ├── training/                # Model training service
│   └── inference/               # Inference service
├── src/                          
│   ├── datapipeline/             # Data processing module
│   │   ├── dataloader.py         # Dataset and DataLoader
│   │   └── bg_removal/           # Background removal
│   └── models/                   # Model training and inference
│       ├── train/                # Training module
│       │   ├── run_fine_tuning.py # Fine-tuning script
│       │   ├── fine_tune_config.py # Fine-tuning configuration
│       │   └── experiments/      # Experiment results
│       └── eval/                 # Evaluation rubrics
├── CI/                          # CI/CD configuration
│   ├── tests/                    # Test suites (unit, integration, e2e)
│   └── scripts/                 # CI helper scripts
├── data_versioning/             # DVC configuration
│   ├── dvc_manager.py           # DVC management script
│   └── gcs_snapshot_tracker.py  # GCS snapshot tracking
├── scripts/                     # Utility scripts
├── catalog/                     # FAISS catalog indices (versioned)
├── wardrobes/                   # User uploaded wardrobes
├── queries/                     # User input queries
├── results/                     # Inference output results
├── docs/                        # Documentation
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

**1. Clone Repository**
```bash
git clone <repository-url> && cd styleme9.0
```

**2. Initial Setup**
```bash
make setup  # Or manually: mkdir -p data logs catalog wardrobes queries results
```

**3. Run Complete Pipeline**
```bash
make run  # Or: docker compose --profile pipeline up --build
```

**4. Run Individual Services**
```bash
make run-ingestion      # Data collection only
make run-preprocessing  # Data processing only
make run-training       # Model training only
make run-inference      # Inference only
```

### Fine-Tuning Model

```bash
cd src/models/train
python run_fine_tuning.py --config fine_tune_config.py --data-version catalog-v_men_women_20251123
```
**Note**: GPU is required for fine-tuning. The script will exit if GPU is not available.

### Running Inference

```bash
# Using Makefile
make infer USER=grace QUERY=grace_query_01 THRESHOLD=0.3 GENDER=women

# Or manually
docker compose run inference python /app/inference_service.py \
    --user-id user_001 --query /app/queries/user_001/req_001/query.jpg \
    --output /app/results/user_001/req_001.json
```

### View Results

```bash
cat results/user_001/req_001.json              # Check inference results
ls src/models/train/experiments/               # View training experiments
make logs                                      # Check logs
```

---

## Part II: Application Components

### Documentation Index

All detailed documentation for each component is available in the following guides:

| Section | Topic | Documentation |
|---------|-------|---------------|
| [Section 1](#section-1-app-design-setup-and-code-organization) | App Design, Setup, and Code Organization | [Application Design Document](docs/Application%20design%20doc.md) |
| [Section 2](#section-2-apis-frontend) | APIs & Frontend | [API Integration Guide](docs/api_integration.md) |
| [Section 3](#section-3-continuous-integration-and-testing) | Continuous Integration and Testing | — |
| [Section 4](#section-4-data-versioning-and-reproducibility) | Data Versioning and Reproducibility | [Data Versioning Guide](docs/data_versioning.md) |
| [Section 5](#section-5-model-fine-tuning) | Model Fine-Tuning | [Model Training Guide](docs/model_training.md) |

**Note**: Each section below provides a brief overview. For complete details, methodology, usage instructions, and technical specifications, please refer to the corresponding documentation linked above.

---

### Section 1: App Design, Setup, and Code Organization

StyleMe follows a **containerized microservices architecture** with four specialized services (ingestion, preprocessing, training, and inference) that operate independently while maintaining seamless communication through Docker networking. The system processes fashion images through a pipeline that includes data collection, cleaning, model training, and real-time recommendation generation using FAISS-based similarity search. The user interface is a mobile-first React-based SPA built with TypeScript, Vite, and Tailwind CSS that allows users to upload wardrobe items, view their collections organized by category, and receive personalized fashion recommendations. The architecture emphasizes modularity, scalability, and reproducibility through versioned datasets and model checkpoints managed with DVC, with automated testing and code quality checks via CI/CD pipelines.

<img width="661" height="641" alt="image" src="https://github.com/user-attachments/assets/f5d10522-d1d4-4e97-a48a-c5fdbc533687" />

<img width="735" height="503" alt="image" src="https://github.com/user-attachments/assets/f672f392-b33d-4949-9875-d395a8447beb" />


**Documentation**: See [Application Design Document](docs/Application%20design%20doc.md) for detailed solution architecture, technical architecture, system components, and design patterns.

---

### Section 2: APIs & Frontend

StyleMe provides a comprehensive API interface through the inference service (`containers/inference/inference_service.py`) that enables fashion recommendation queries via command-line or programmatic access. The system supports file-based input/output workflows where users upload query images to `queries/{user_id}/` directories and receive JSON responses with ranked product recommendations in `results/{user_id}/`. The API implements a two-tier search strategy: it first searches the user's personal wardrobe index (if available and similarity scores meet the threshold), and falls back to the catalog index for product recommendations when the wardrobe is empty or no matches are found. The frontend is a React-based single-page application built with TypeScript, Vite, and Tailwind CSS that provides a mobile-first interface for uploading wardrobe items, viewing collections organized by category, and receiving personalized fashion recommendations. The architecture supports seamless integration between the backend inference service and frontend through RESTful API structures, image upload/download capabilities, metadata-rich JSON responses, and per-user session management.

**Documentation**: See [API Integration Guide](docs/api_integration.md) for complete API specifications, frontend integration details, request/response formats, and workflow documentation.

---

### Section 3: Continuous Integration and Testing

StyleMe implements a comprehensive CI/CD pipeline using **GitHub Actions** that automatically runs on every push and pull request. The pipeline is configured in `.github/workflows/ci.yml` and executes four sequential jobs to ensure code quality and reliability. The **Build and Lint** job performs automated build verification and code quality checks using Flake8, setting up Python 3.10 environments, installing system and Python dependencies from `requirements.txt` and `CI/requirements-dev.txt`, and running linting on `src/`, `containers/`, and `scripts/` directories with a maximum line length of 120 characters. The **Run Tests** job executes all test suites in parallel using pytest with markers for different test types, including unit tests for data loading, background removal, web scraping, model training, and inference utilities; integration tests for pipeline component interactions; and end-to-end tests that verify the complete pipeline from data ingestion to inference. Tests are run using `pytest-xdist` for parallel execution, excluding slow tests that require external resources like GCS or GPU. The **Report Coverage** job generates and displays code coverage reports with a minimum requirement of 50%, producing reports in both HTML format (accessible via `CI/coverage_html/index.html`) and XML format (`CI/coverage.xml`) for integration with CI tools. The current coverage stands at 60.53%, exceeding the minimum requirement, and coverage results are uploaded as GitHub Actions artifacts and displayed in the CI summary. The **CI Summary** job aggregates all check results and provides a final status overview, ensuring all checks pass before code can be merged.

<table>
<tr>
<td width="50%" style="padding: 5px;">
  <img src="https://github.com/user-attachments/assets/84a4466c-37b0-4a95-8d0d-5e5be45805af" alt="CI Pipeline workflow overview" style="width: 100%;" />
  <p style="text-align: center; font-size: 0.85em; margin-top: 5px;"><em>CI Pipeline workflow overview</em></p>
</td>
<td width="50%" style="padding: 5px;">
  <img src="https://github.com/user-attachments/assets/84666ccf-022d-49fe-bc1f-7044ab7393c8" alt="Build and Lint job execution" style="width: 100%;" />
  <p style="text-align: center; font-size: 0.85em; margin-top: 5px;"><em>Build and Lint job execution</em></p>
</td>
</tr>
<tr>
<td width="50%" style="padding: 5px;">
  <img src="https://github.com/user-attachments/assets/11fe2951-52ed-4838-b946-5af56b15f3b5" alt="Code coverage report" style="width: 100%;" />
  <p style="text-align: center; font-size: 0.85em; margin-top: 5px;"><em>Code coverage report</em></p>
</td>
<td width="50%" style="padding: 5px;">
  <img src="https://github.com/user-attachments/assets/93215b8e-fb93-4c31-91c2-9a2ebcb1fc29" alt="Coverage and CI summary" style="width: 100%;" />
  <p style="text-align: center; font-size: 0.85em; margin-top: 5px;"><em>Coverage and CI summary</em></p>
</td>
</tr>
</table>

---

### Section 4: Data Versioning and Reproducibility

StyleMe implements **DVC (Data Version Control)** for managing datasets, model checkpoints, and large artifacts to ensure reproducibility and track data lineage throughout the project lifecycle. The system versions three types of artifacts: catalog indices (FAISS indices, embeddings, and metadata generated from GCS source data via `build_catalog_index.py`), user wardrobes (per-user FAISS indices and embeddings), and model checkpoints (trained model weights automatically linked to the data versions used during training). Source data in Google Cloud Storage (`gs://styleme-data-bucket/`) is tracked via metadata snapshots in `manifest.json`, which record which GCS files were used, track gender filters (men/women/all), and maintain history of data states. The versioning system operates at three levels: Git commits for every data change, Git tags for named milestones (e.g., `catalog-v_men_women_20251123`), and GCS snapshots for source data state. Each experiment record includes the data version reference, GCS snapshot tag, full configuration (hyperparameters, model settings), and training results, enabling complete reproducibility by linking model versions to training configs to catalog versions to GCS source state.

**Documentation**: See [Data Versioning Guide](docs/data_versioning.md) for complete methodology, usage instructions, and reproducibility workflow.

---

### Section 5: Model Fine-Tuning

StyleMe fine-tunes a **FashionCLIP model** (based on OpenAI CLIP ViT-B/32) to learn fashion compatibility relationships from curated product data. The fine-tuning process uses a **triplet loss** objective with partial layer freezing (4 layers frozen, reduced from baseline 8) to adapt the pre-trained vision-language model to fashion-specific compatibility patterns. Training is performed on versioned datasets tracked via DVC tags (e.g., `catalog-v_men_women_20251123`), with each experiment automatically generating unique IDs (`fine_tune_YYYYMMDD_HHMMSS`), comprehensive metadata records, and model checkpoints (best and final models saved). The system enforces GPU requirements, implements early stopping based on validation accuracy, and optimizes I/O to prevent training interruptions. Current baseline performance shows ~41% triplet accuracy and 42-43% compatibility scores, with fine-tuning targeting >70% triplet accuracy and >50% compatibility scores through optimized hyperparameters (learning rate 2e-5, batch size 24, margin 0.5) and improved convergence strategies. All experiments are fully reproducible through DVC versioning, linking model checkpoints to training configurations, catalog versions, and GCS source data states.

**Documentation**: See [Model Training Guide](docs/model_training.md) for complete training workflow, configuration details, experiment tracking, and deployment strategies.
