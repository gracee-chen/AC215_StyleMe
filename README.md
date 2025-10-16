# Personal Wardrobe AI Stylist

## 📁 Project Structure

```
project 215/
├── data/                           # Training data
│   ├── Data caption/              # Captioned data from angel branch
│   │   ├── men_data/             # Male product data
│   │   └── women_data/           # Female product data
│   └── images/                   # Product images (6761 files)
├── src/                           # Source code
│   ├── datapipeline/              # Data processing module
│   │   ├── __init__.py           # Package initialization
│   │   └── dataloader.py         # Data loader and triplet generation
│   └── models/                    # Model training and inference
│       ├── __init__.py           # Package initialization
│       ├── train/                # Training module
│       │   ├── config.py         # Configuration management
│       │   ├── requirements.txt  # Python dependencies
│       │   ├── run_training.sh   # Training script
│       │   ├── model_training.py # FashionCLIP training
│       │   └── inference.py      # Personal wardrobe AI stylist
│       └── eval/                 # Evaluation module
│           ├── evaluation.py     # Complete evaluation
│           ├── quick_eval.py     # Quick evaluation
│           └── README.md         # Evaluation documentation
```

## 🎯 Key Features

### **Data Processing (src/datapipeline/)**
- **Complete Data Usage**: Uses ALL available data (3173 items, 3157 compatibility relationships)
- **Smart Triplet Generation**: Builds compatibility graph from `complete_the_look` descriptions
- **Automatic Train/Val Split**: 80/20 split for training and validation

### **Model Training (src/models/train/)**
- **FashionCLIP Architecture**: Based on CLIP ViT-B/32
- **Layer Freezing**: Freezes first 8 layers, trains last 4 layers
- **Triplet Loss**: Margin=0.5 for fashion compatibility learning
- **Auto Checkpointing**: Saves best model and training history

### **Model Evaluation (src/models/eval/)**
- **Complete Evaluation**: Multi-dimensional model assessment
- **Quick Evaluation**: Fast validation of basic functionality
- **Performance Metrics**: Precision, Recall, F1-Score, NDCG, AUC

### **Training Configuration**
- **Batch Size**: 16 (optimized for memory)
- **Learning Rate**: 1e-5 (fine-tuning rate)
- **Epochs**: 20 (sufficient training)
- **Target Accuracy**: 85% (early stopping)

## 🐳 Virtual Environment Setup

### **Containerized Architecture**
The project uses Docker containers to provide isolated, reproducible environments for each component:

- **📥 Ingestion Container**: Data scraping and collection
- **🔄 Preprocessing Container**: Image processing and data cleaning  
- **🤖 Training Container**: Model training with GPU support
- **🔮 Inference Container**: Model serving and API endpoints

### **Quick Setup with Docker**
```bash
# Build all containers
make build

# Run complete pipeline
make run

# Or run individual services
make run-ingestion    # Data collection
make run-preprocessing # Data processing
make run-training     # Model training
make run-inference    # Model serving
```

### **Development Environment**
```bash
# Set up local development environment
make dev-setup

# This installs all dependencies using uv package manager
# Creates isolated environments for each service
```

### **Container Configuration**
Each container has its own:
- **Base Image**: Optimized for the specific task (PyTorch for ML, Python slim for data processing)
- **Dependencies**: Managed via `pyproject.toml` with `uv` package manager
- **Environment Variables**: Properly configured for each service
- **Volume Mounts**: Persistent data and experiment storage

### **GPU Support**
Training containers include NVIDIA GPU support:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## 🚀 End-to-End Containerized Pipeline

### **Complete Pipeline Architecture**
The project implements a fully containerized end-to-end pipeline with four main components:

1. **📥 Data Ingestion** - Web scraping and data collection
2. **🔄 Data Preprocessing** - Image processing and data cleaning
3. **🤖 Model Training** - FashionCLIP training with GPU support
4. **🔮 Model Inference** - API serving and recommendations

### **One-Command Pipeline Execution**
```bash
# Run complete pipeline from start to finish
make run

# Or using docker compose directly
docker compose --profile pipeline up --build
```

### **Individual Component Execution**
```bash
# Build all containers
make build

# Run individual services
make run-ingestion     # Data collection only
make run-preprocessing # Data processing only  
make run-training      # Model training only
make run-inference     # Model serving only

# Test with sample data
make test
```

### **Pipeline Evidence**
- **Input**: `input/sample.txt` - Sample fashion image for testing
- **Output**: `output/test_result.txt` - Pipeline execution results
- **Logs**: `logs/pipeline.log` - Complete execution logs

## 🚀 Quick Start

### **1. Container Setup (Recommended)**
```bash
# Build and run complete pipeline
make build
make run
```

### **2. Traditional Setup (Alternative)**
```bash
cd src/models/train
pip install -r requirements.txt
./run_training.sh
```

### **3. Monitor Training**
```bash
# Training will show real-time progress:
# - Loss decreasing from 1.0+ to 0.3-
# - Accuracy increasing from 0.0 to 85%+
# - Automatic best model saving
```

## 📊 Training Results

### **Data Statistics**
- **Total Items**: 3173 products
- **Compatibility Relationships**: 3157 pairs
- **Train Batches**: 1262 (80% of data)
- **Val Batches**: 316 (20% of data)

### **Expected Performance**
- **Training Time**: 10-20 hours on V100 GPU
- **Target Accuracy**: >85% triplet accuracy
- **Model Size**: ~500MB (CLIP ViT-B/32)

## 🎨 Inference Usage

### **Personal Wardrobe Stylist**
```python
from src.models.train.inference import FashionStylist

# Initialize stylist
stylist = FashionStylist('fashion_clip_checkpoints/best_model.pth')

# Load user wardrobe
stylist.load_user_wardrobe('user_wardrobe/')

# Get outfit recommendations
recommendations = stylist.get_complete_outfit('shirt_001.jpg')
```

## 🔧 Configuration

### **Data Settings**
```python
DATA_CONFIG = {
    'data_dir': 'data',
    'image_dir': 'data/images',
    'max_samples_per_file': None,  # Use ALL data
    'compatibility_threshold': 2,
    'max_compatible_items': 3,
}
```

### **Training Settings**
```python
TRAINING_CONFIG = {
    'batch_size': 16,
    'epochs': 20,
    'learning_rate': 1e-5,
    'target_accuracy': 0.85,
}
```

## 📈 Monitoring

### **Real-time Metrics**
- **Loss**: Real-time loss decrease
- **Accuracy**: Triplet accuracy improvement
- **Learning Rate**: Automatic adjustment

### **Saved Files**
```
fashion_clip_checkpoints/
├── best_model.pth              # Best performing model
├── final_model.pth             # Final epoch model
├── training_history.json       # Complete training log
└── training_curves.png         # Loss/accuracy curves
```

## 🏗️ Container Services Details

### **Service Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingestion     │───▶│  Preprocessing   │───▶│    Training     │───▶│   Inference     │
│                 │    │                  │    │                 │    │                 │
│ • Data scraping │    │ • Image cleaning │    │ • Model training│    │ • API serving   │
│ • Web crawling  │    │ • Background rm  │    │ • GPU support   │    │ • FastAPI       │
│ • Data storage  │    │ • Data validation│    │ • Checkpointing │    │ • Port 8000     │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Container Specifications**

| Service | Base Image | Dependencies | Purpose |
|---------|------------|--------------|---------|
| **Ingestion** | `python:3.9-slim` | requests, beautifulsoup4, selenium | Web scraping and data collection |
| **Preprocessing** | `python:3.9-slim` | opencv-python, pillow, torch | Image processing and cleaning |
| **Training** | `pytorch/pytorch:2.0.1-cuda11.7` | torch, transformers, scikit-learn | Model training with GPU |
| **Inference** | `pytorch/pytorch:2.0.1-cuda11.7` | fastapi, uvicorn, torch | Model serving and API |

### **Volume Mounts**
```yaml
volumes:
  - ./data:/app/data              # Training data
  - ./experiments:/app/experiments # Model checkpoints
  - ./input:/app/input            # Inference input
  - ./output:/app/output          # Inference output
  - ./logs:/app/logs              # Application logs
```

### **Environment Variables**
```bash
# Common variables
PYTHONPATH=/app/src
DATA_DIR=/app/data
LOG_LEVEL=INFO

# Training specific
CUDA_VISIBLE_DEVICES=0
EXPERIMENTS_DIR=/app/experiments

# Inference specific
MODEL_PATH=/app/experiments
INPUT_DIR=/app/input
OUTPUT_DIR=/app/output
```

## 🎯 GCP Deployment

### **Recommended Instance**
```
Machine Type: n1-standard-4
GPU: 1x NVIDIA Tesla V100
Cost: ~$50 for 20 hours
```

### **Container Deployment Steps**
1. Upload code to GCP
2. Build containers: `make build`
3. Run pipeline: `make run`
4. Monitor via Docker logs: `make logs`

### **Traditional Deployment (Alternative)**
1. Upload code to GCP
2. Install dependencies: `pip install -r requirements.txt`
3. Start training: `./run_training.sh`
4. Monitor via SSH

## 📦 Pipeline Deliverables

### **Dockerfiles + Build Instructions**
- ✅ `containers/ingestion/Dockerfile` - Data scraping container
- ✅ `containers/preprocessing/Dockerfile` - Data processing container  
- ✅ `containers/training/Dockerfile` - Model training container
- ✅ `containers/inference/Dockerfile` - Model serving container

### **pyproject.toml (using uv) for Each Container**
- ✅ `containers/ingestion/pyproject.toml` - Web scraping dependencies
- ✅ `containers/preprocessing/pyproject.toml` - Image processing dependencies
- ✅ `containers/training/pyproject.toml` - ML training dependencies
- ✅ `containers/inference/pyproject.toml` - API serving dependencies

### **Scripts and docker-compose.yml**
- ✅ `docker-compose.yml` - Complete service orchestration
- ✅ `scripts/run_pipeline.py` - End-to-end pipeline execution
- ✅ `scripts/test_pipeline.py` - Pipeline testing and validation
- ✅ `Makefile` - Simplified build and run commands

### **Documentation and Run Instructions**
- ✅ `README.md` - Complete setup and usage documentation
- ✅ `PIPELINE_DOCUMENTATION.md` - Detailed pipeline architecture
- ✅ One-command execution: `make run` or `docker compose --profile pipeline up --build`

### **Evidence of End-to-End Functionality**
- ✅ **Input**: `input/sample.txt` - Sample test data
- ✅ **Output**: `output/test_result.txt` - Pipeline execution results
- ✅ **Logs**: `logs/pipeline.log` - Complete execution logs
- ✅ **Pipeline Script**: `scripts/run_pipeline.py` - Automated end-to-end execution

## 💡 Key Improvements

1. **Complete Data Usage**: No artificial limits, uses all 3173 items
2. **Modular Structure**: Clean separation of data processing and models
3. **Containerized Environment**: Isolated, reproducible Docker containers for each service
4. **Modern Package Management**: Uses `uv` for fast, reliable dependency management
5. **GPU-Ready Training**: NVIDIA GPU support with proper resource allocation
6. **Service Orchestration**: Docker Compose for easy pipeline management
7. **Development Tools**: Makefile for simplified container operations
8. **Automatic Optimization**: Smart batch sizing and learning rate scheduling
9. **Robust Monitoring**: Comprehensive checkpointing and visualization
10. **End-to-End Pipeline**: Complete containerized workflow from data ingestion to inference

**Ready for production training on GCP with full containerization!** 🚀