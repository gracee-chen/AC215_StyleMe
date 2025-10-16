# Personal Wardrobe AI Stylist

## Team Members
Chufei Peng, Grace Chen, Siyao Zhu, Angel Chen

## Group Name
Stylist

## Project Description
In this project, we aim to develop an AI-powered personal wardrobe stylist that helps users create cohesive outfits from their existing wardrobes. The system leverages curated product data and compatibility information (“complete the look”) to learn relationships between clothing items. It integrates a data-cleaning and caption-generation pipeline with a FashionCLIP-based compatibility model to recommend matching items. The goal is to provide an intelligent outfit suggestion tool that understands real-world style relationships and personalizes recommendations based on visual and textual cues.

## Milestone 2 Overview
This milestone focused on building a **scalable, containerized end-to-end pipeline** for data processing, model training, and evaluation. We developed standardized data handling, generated item captions, fine-tuned a FashionCLIP model, and validated the pipeline’s reproducibility within Docker environments.

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
│       │   ├── experiments/      # Experiment results
│       │   └── ...    
│       └── eval/                 # Evaluation Rubrics
│           ├── evaluation.py     
│           └── quick_eval.py     
├── ...
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



<img width="1374" height="728" alt="1eb0b34a740bd87dcd64581b13fa7ca6" src="https://github.com/user-attachments/assets/8ef0add6-9a4b-4a6a-acb9-957a99b5a4d9" />

_Figure 1. Screenshot of running containers or GCP instances._


## 2. End-to-End Containerized Pipeline

The pipeline consists of modular components orchestrated with Docker Compose.

| Stage | Description | Example Tasks |
|--------|--------------|----------------|
| **📥 Ingestion** | Collects and stores curated product data | Web scraping, GCS upload |
| **🔄 Preprocessing** | Cleans and deduplicates images | Resize, validate, filter |
| **🤖 Training** | Fine-tunes FashionCLIP | Triplet training, checkpointing |
| **🔮 Inference** | Generates outfit recommendations | FastAPI endpoints, testing |

### Run Instruction

```
make build
make run
```

[Insert Screenshot Placeholder]

_Figure 2. Console output showing successful end-to-end pipeline run._


## 3. Data Ingestion & Preprocessing

We processed ~6,700 curated product images and corresponding JSON metadata for both men’s and women’s fashion. Each record contains structured product details and “complete the look” compatibility annotations. The pipeline standardizes, cleans, and captions each product entry to ensure consistency and model readiness.

### Pipeline Highlights
- Standardized captions generated for every product image
- Automatic filtering and removal of duplicate entries
- Consolidation of compatibility pairs from “complete the look” field

<img width="946" height="665" alt="截屏2025-10-16 19 20 43" src="https://github.com/user-attachments/assets/2c0a1f35-361f-4c37-bc6a-43b7c66f7b2e" />

_Figure 3. Example of cleaned JSON metadata and generated captions._

## 4. Model Preparation, Training & Evaluation

The FashionCLIP-based model learns compatibility relationships between clothing items using triplet loss. Before training, we constructed triplets (anchor, positive, negative) and split data into training and validation sets.

### Architecture Overview
- **Model**: FashionCLIP (ViT-B/32)
- **Fine-Tuning**: Last 4 layers (first 8 frozen)
- **Loss Function**: Triplet margin loss (margin = 0.5)
- **Checkpointing**: Automatically saves best model

<img width="1011" height="299" alt="image" src="https://github.com/user-attachments/assets/99a911cf-9345-49d2-9345-227747667b3f" />

_Figure 4. An illustration of FashionCLIP fine-tuning with triplet loss for outfit compatibility._

### Training Configuration

| Parameter | Value |
|------------|--------|
| Batch Size | 16 |
| Learning Rate | 1e-5 |
| Epochs | 20 |
| Target Accuracy | 85% |

[Insert Training Curve Placeholder]  
_Figure 5. Training log showing loss and accuracy progression._

### Evaluation Metrics
- Precision, Recall, F1-score
- NDCG, AUC for ranked retrieval
- QuickEval for fast validation

## 5. Application Mock-up

The Personal Wardrobe Stylist prototype generates outfit recommendations from a user’s wardrobe image.

<img width="1201" height="638" alt="image" src="https://github.com/user-attachments/assets/868368f1-4d18-4a4c-a4cb-d65d363941a8" />



