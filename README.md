# Personal Wardrobe AI Stylist

## Team Members
Chufei Peng, Grace Chen, Siyao Zhu, Angel Chen

## Group Name
Stylist

## Project Description
In this project, we aim to develop an AI-powered personal wardrobe stylist that helps users create cohesive outfits from their existing wardrobes. The system leverages curated product data and compatibility information ("complete the look") to learn relationships between clothing items. It integrates a data-cleaning and caption-generation pipeline with a FashionCLIP-based compatibility model to recommend matching items. The goal is to provide an intelligent outfit suggestion tool that understands real-world style relationships and personalizes recommendations based on visual and textual cues.

## Milestone 3 Overview
This milestone focused on **enhancing the containerized pipeline with GPU optimization, improved model training configurations, and comprehensive evaluation metrics**. We implemented GPU-accelerated training, refined hyperparameter tuning, and developed robust evaluation frameworks to validate model performance across different training scenarios.

## 📁 Project Structure

```
StyleMe/
├── containers/                   # Dockerfiles
│   ├── ingestion/                
│   ├── preprocessing/           
│   └── training/     
├── data/                         # Training data
│   ├── json/                     # Captioned data
│   │   ├── men_data/             
│   │   └── women_data/           
│   └── images/                   # Product images
├── scripts/
│   ├── run_pipeline.py
├── src/                          
│   ├── datapipeline/             # Data processing module
│   │   ├── dataloader.py           
│   │   └── ...        
│   └── models/                   # Model training and inference
│       ├── train/                # Training module
│       │   ├── requirements.txt  
│       │   ├── config.py         
│       │   ├── model_training.py # FashionCLIP training
│       │   ├── config_gpu.py     # GPU configuration
│       │   ├── experiments/      # Experiment results
│       │   └── ...    
│       └── eval/                 # Evaluation Rubrics
│           ├── evaluation.py     
│           └── quick_eval.py     
├── install_nvidia_driver.sh     # GPU driver installation
├── cuda_installer.py            # CUDA setup automation
├── install_gpu_driver.py        # GPU driver management
├── docker-compose.yml           # Container orchestration
├── docker-compose.yml.backup    # Backup configuration
└── README.md
```

## 1. Virtual Environment Setup

Virtual machine environment configured to support containerized deep learning and machine learning workloads. This instance provides GPU-accelerated computing with pre-installed deep learning frameworks, enabling efficient model training, inference, and deployment through Docker containers.

### Configuration
```
Name:             styleme-dev2
Project:          styleme-475201
Zone:             us-central1-c
Machine:          n1-standard-8 (8 vCPUs, 30 GB RAM, 1x NVIDIA V100)
OS:               Debian 11 + PyTorch 2.4 + CUDA 12.4 + Python 3.10
Storage:          200 GB Balanced Persistent Disk
Network:          Internal: 10.128.0.3 | External: 35.232.244.20
Console:          https://console.cloud.google.com/compute/instancesDetail/zones/us-central1-c/instances/styleme-dev2
```

### Access
```bash
gcloud compute ssh styleme-dev2 --zone=us-central1-c --project=styleme-475201
nvidia-smi  # Verify GPU
```
<img width="1460" height="1064" alt="image" src="https://github.com/user-attachments/assets/3dd8ae94-d4d9-431c-aebe-8416f14b8957" />

<img width="1374" height="728" alt="1eb0b34a740bd87dcd64581b13fa7ca6" src="https://github.com/user-attachments/assets/8ef0add6-9a4b-4a6a-acb9-957a99b5a4d9" />

_Figure 1. Screenshots of GCP instance and running container._

## 2. End-to-End Containerized Pipeline

The pipeline consists of modular components orchestrated with Docker Compose, now enhanced with GPU acceleration and improved container management.

| Stage | Description | Example Tasks |
|--------|--------------|----------------|
| **📥 Ingestion** | Collects and stores curated product data | Web scraping, GCS upload |
| **🔄 Preprocessing** | Cleans and deduplicates images | Resize, validate, filter |
| **🤖 Training** | Fine-tunes FashionCLIP with GPU acceleration | Triplet training, checkpointing, GPU optimization |

### Run Instruction

```bash
# Build all containers
make build

# Run the complete pipeline
make run

# GPU-specific training
docker-compose up training
```

<img width="1184" height="850" alt="image" src="https://github.com/user-attachments/assets/1512e319-423e-45d4-8caf-9a0e7fcf57a7" />

<img width="1314" height="1280" alt="image" src="https://github.com/user-attachments/assets/bfe621ce-3b12-4851-beca-2571e4e1f4d9" />

_Figure 2. Console output showing successful end-to-end pipeline run._

## 3. Data Ingestion & Preprocessing

We processed ~13k curated product images and corresponding JSON metadata for both men's and women's fashion. Each record contains structured product details and "complete the look" compatibility annotations. Our preprocessing pipeline standardizes, cleans, and captions each product entry to ensure consistency and data readiness.

### Pipeline Highlights
- Standardized captions generated for every product image
- Automatic filtering and removal of duplicate entries
- Consolidation of compatibility pairs from "complete the look" field
- Enhanced data validation and error handling

<img width="946" height="665" alt="截屏2025-10-16 19 20 43" src="https://github.com/user-attachments/assets/2c0a1f35-361f-4c37-bc6a-43b7c66f7b2e" />

_Figure 3. Example of cleaned JSON metadata and generated captions._

## 4. Model Preparation, Training & Evaluation

The FashionCLIP-based model learns compatibility relationships between clothing items using triplet loss. Before training, we constructed triplets (anchor, positive, negative) and split data into training and validation sets. The training process now includes GPU optimization and enhanced monitoring.

### Architecture Overview
- **Model**: FashionCLIP (ViT-B/32)
- **Fine-Tuning**: Last 4 layers (first 8 frozen)
- **Loss Function**: Triplet margin loss (margin = 0.5)
- **Checkpointing**: Automatically saves best model
- **GPU Acceleration**: CUDA-enabled training with NVIDIA V100

<img width="848" height="286" alt="image" src="https://github.com/user-attachments/assets/f26890db-c401-4fa8-9745-763972343019" />

_Figure 4. An illustration of FashionCLIP fine-tuning with triplet loss for outfit compatibility._

### Training Experiments

#### Experiment 1: Initial Configuration
<img width="4470" height="1466" alt="image" src="https://github.com/user-attachments/assets/cef27aa1-25c5-4221-a6e8-6cdb06732033" />

**Configurations:**
- **Target Accuracy**: 0.75
- **Batch Size**: 32
- **Epochs**: 20
- **Learning Rate**: 1e-6
- **Patience**: 5
- **GPU Memory**: Optimized for V100

#### Experiment 2: Refined Hyperparameters
<img width="4470" height="1466" alt="image" src="https://github.com/user-attachments/assets/8625de81-592d-440d-b90b-efea8c1164ed" />

**Configurations:**
- **Target Accuracy**: 0.75
- **Batch Size**: 16 (reduced for stability)
- **Epochs**: 30 (increased for convergence)
- **Learning Rate**: 1e-5 (increased for faster learning)
- **Patience**: 8 (extended early stopping)
- **Monitoring**: Enhanced training progress tracking

### Training Results
- **Best Validation Accuracy**: 0.78
- **Training Time**: ~45 minutes per epoch
- **Model Checkpoints**: Automatically saved at best performance
- **Loss Convergence**: Stable triplet loss reduction observed

## 5. Updates from Milestone 2

This milestone represents significant enhancements to our Personal Wardrobe AI Stylist system, building upon the foundation established in Milestone 2. 

### Data Management and Security

We have successfully migrated our entire data infrastructure to Google Cloud Platform (GCP), which has significantly improved our data management capabilities. The migration to **GCS (Google Cloud Storage)** provides us with robust data versioning and automatic backup systems that ensure we never lose important training data. Our ~13k curated product images and corresponding JSON metadata are now securely stored in versioned buckets with proper access controls and encryption. To maintain data quality, we implemented automated validation pipelines that check data integrity throughout different processing stages. The containerized architecture ensures secure data access through environment-based configuration and isolated service boundaries.

<img width="1656" height="470" alt="image" src="https://github.com/user-attachments/assets/2a859fd3-6d27-421e-92c7-8ed6552d4dc7" />


_Figure 5. GCP Cloud Storage bucket showing organized data structure with images and JSON folders_

### Infrastructure Enhancements

Our infrastructure has undergone significant improvements with a comprehensive four-service architecture that supports end-to-end data processing and model training. We implemented a robust Docker Compose configuration featuring four specialized containers: **ingestion** for data collection, **preprocessing** for data cleaning and validation, **training** for model development with GPU support, and **inference** for serving recommendations. Each service operates independently while maintaining seamless communication through our custom `styleme-network`.

The architecture includes sophisticated dependency management where preprocessing depends on ingestion, and training depends on preprocessing, ensuring proper data flow through the pipeline. We implemented comprehensive logging across all services with centralized log management, and each container has optimized resource allocation including GPU support for the training service. The system supports flexible deployment through Docker profiles, allowing us to run individual services or the complete pipeline as needed.

<img width="2638" height="1242" alt="Docker Compose Infrastructure" src="https://github.com/user-attachments/assets/4e06d506-ad78-40a4-926e-f7cd3b6d9557" />

_Figure 6. Docker Compose infrastructure showing multi-service architecture with ingestion, preprocessing, training, and inference containers_


### Model Training Optimization

Our model training process has been substantially refined through systematic hyperparameter optimization. We implemented comprehensive hyperparameter tuning that explores different learning rates and batch sizes to achieve optimal convergence patterns. The training system includes improved early stopping mechanisms to prevent overfitting, automated checkpoint management to save models at peak performance, and comprehensive training monitoring with real-time loss and accuracy visualization. The training pipeline supports efficient batch processing and memory management for handling large datasets effectively.

**Configurations:**
- **Target Accuracy**: 0.85
- **Batch Size**: 32 (optimized for GPU training)
- **Epochs**: 20
- **Learning Rate**: 5e-6 (fine-tuned for stable convergence)
- **Patience**: 10 (early stopping)
- **Optimizer**: AdamW with weight decay 0.005
- **Scheduler**: CosineAnnealingLR
- **Triplet Margin**: 0.7 (increased for better feature separation)
- **Data Workers**: 4 (parallel data loading)

### Evaluation Framework Development

We developed a comprehensive evaluation framework with two specialized modules: `quick_eval.py` for rapid model validation and `evaluation.py` for in-depth assessment. During training, we monitor a composite fashion compatibility score that combines multiple metrics to provide a holistic view of model performance. This training score consists of **Triplet Accuracy (50%)** measuring how well the model distinguishes compatible from incompatible items, **Margin Score (25%)** evaluating the separation quality between positive and negative pairs, **Separation Score (15%)** assessing absolute distance separation, and **Distance Ratio Score (10%)** measuring relative distance quality. Our scoring methodology is inspired by recent advances in vision-language models and metric learning, particularly the CLIP architecture (Radford et al., 2021) and triplet loss optimization techniques (Hermans et al., 2017). We set performance thresholds at 85%+ for production readiness and 70%+ for promising performance, following industry standards for fashion recommendation systems.

### User-based Inference

We designed a user-based inference pipeline centered around personalized retrieval and dynamic decision-making. The system operates through two main stages: a Wardrobe Index for user-owned items and a Catalog Index for global recommendations. Upon receiving a query image, our pipeline first generates its embedding using the fine-tuned Fashion-CLIP model and compares it against the user’s wardrobe embeddings to identify the most compatible pieces based on cosine similarity. If the wardrobe lacks suitable matches or the top similarity score falls below a defined threshold, the system seamlessly transitions to the global catalog index, retrieving the top-3 purchasable items with associated metadata such as title, price, brand, and shopping URL. This two-tier inference structure ensures both personalization and scalability—leveraging pre-computed embeddings, fast approximate nearest-neighbor search, and adaptive similarity thresholds for real-time performance.

## 6. Application Mock-up

The Personal Wardrobe Stylist prototype generates outfit recommendations from a user's wardrobe image, now with improved inference capabilities and better compatibility scoring.

<img width="1201" height="638" alt="image" src="https://github.com/user-attachments/assets/868368f1-4d18-4a4c-a4cb-d65d363941a8" />
