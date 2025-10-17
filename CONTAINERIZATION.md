# StyleMe 6.0 - Containerized Pipeline

This document describes the containerized version of the StyleMe 6.0 Personal Wardrobe AI Stylist.

## 🏗️ Architecture

The pipeline consists of three main components:

1. **📥 Ingestion** - Data scraping and collection
2. **🔄 Preprocessing** - Image processing and data cleaning  
3. **🤖 Training** - Model training with GPU support

## 🚀 Quick Start

### One-Command Execution
```bash
# Run complete pipeline
make run

# Or using docker compose directly
docker compose --profile pipeline up --build
```

### Individual Components
```bash
# Build all containers
make build

# Run individual services
make run-ingestion      # Data collection only
make run-preprocessing  # Data processing only  
make run-training       # Model training only
```

## 📁 Directory Structure

```
styleme6.0/
├── containers/
│   ├── ingestion/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── entrypoint.sh
│   ├── preprocessing/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── entrypoint.sh
│   └── training/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── entrypoint.sh
├── docker-compose.yml
├── Makefile
└── scripts/
    └── run_pipeline.py
```

## 🔧 Container Details

### Ingestion Container
- **Base Image**: `python:3.9-slim`
- **Purpose**: Data scraping and collection
- **Dependencies**: requests, tqdm, beautifulsoup4, selenium
- **Entry Point**: `src/datapipeline/scraper/extract_images.py`

### Preprocessing Container  
- **Base Image**: `python:3.9-slim`
- **Purpose**: Image processing and data cleaning
- **Dependencies**: opencv-python, pillow, torch, rembg
- **Entry Point**: Background removal and image preprocessing

### Training Container
- **Base Image**: `pytorch/pytorch:2.0.1-cuda11.7-devel`
- **Purpose**: Model training with GPU support
- **Dependencies**: torch, transformers, matplotlib, scikit-learn
- **Entry Point**: `src/models/train/model_training.py`

## 📊 Data Flow

```
Data Source → Ingestion → Preprocessing → Training → Experiments
     ↓            ↓            ↓            ↓           ↓
/home/grace_   ./data/     ./data/     ./data/   ./src/models/
chen/data      (JSON)      (Images)    (Ready)   train/experiments/
     ↓            ↓            ↓            ↓           ↓
 20 JSON     20 JSON     20 JSON     20 JSON    Model
 13,104      13,104      13,104      13,104     Checkpoints
 Images      Images      Images      Images     & Results
```

**Note**: The ingestion container automatically copies data from `/home/grace_chen/data` to `./data/` for processing.

## 🎯 Key Features

- **No Code Modification**: Original code remains unchanged
- **GPU Support**: Automatic GPU detection and utilization
- **Volume Mounts**: Persistent data and experiment storage
- **Dependency Isolation**: Each component has its own environment
- **One-Command Execution**: Complete pipeline with `make run`

## 📋 Available Commands

```bash
make help           # Show all available commands
make setup          # Initial setup (create directories)
make build          # Build all containers
make run            # Run complete pipeline
make run-ingestion  # Run only data ingestion
make run-preprocessing # Run only data preprocessing
make run-training   # Run only model training
make logs           # Show logs from all services
make clean          # Clean up containers and volumes
make test           # Test pipeline setup
make status         # Check pipeline status
```

## 🔍 Monitoring

### View Logs
```bash
# All services
make logs

# Specific service
docker compose logs training
docker compose logs preprocessing
docker compose logs ingestion
```

### Check Status
```bash
make status
```

## 🧹 Cleanup

```bash
# Clean up everything
make clean

# Remove specific containers
docker compose down
```

## 🎮 GPU Requirements

The training container requires NVIDIA GPU support:

```bash
# Check GPU availability
nvidia-smi

# Install NVIDIA Docker runtime (if needed)
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

## 📁 Output Locations

- **Data**: `./data/` (JSON files and images)
- **Experiments**: `./src/models/train/experiments/` (model checkpoints and results)
- **Logs**: `./logs/` (container execution logs)

## 🚨 Troubleshooting

### Common Issues

1. **GPU not detected**: Ensure NVIDIA Docker runtime is installed
2. **Permission errors**: Check file permissions in mounted volumes
3. **Out of memory**: Reduce batch size in training configuration
4. **Data not found**: Ensure data exists in `/home/grace_chen/data`

### Debug Commands

```bash
# Check container status
docker compose ps

# Inspect specific container
docker compose exec training bash

# View detailed logs
docker compose logs -f training
```

## 🎯 Production Deployment

For production deployment on GCP or other cloud platforms:

1. Upload the entire project directory
2. Ensure GPU instances are available
3. Run: `make run`
4. Monitor via: `make logs`

The pipeline will automatically:
- Load data from the configured paths
- Process and clean the data
- Train the FashionCLIP model
- Save results to the experiments directory
