# Personal Wardrobe AI Stylist

## Team Members
Chufei Peng, Grace Chen, Siyao Zhu, Angel Chen

## Group Name
Stylist

## Project Description
In this project, we aim to develop an AI-powered personal wardrobe stylist that helps users create cohesive outfits from their existing wardrobes. The system leverages curated product data and compatibility information (“complete the look”) to learn relationships between clothing items. It integrates a data-cleaning and caption-generation pipeline with a FashionCLIP-based compatibility model to recommend matching items. The goal is to provide an intelligent outfit suggestion tool that understands real-world style relationships and personalizes recommendations based on visual and textual cues.

## Milestone 2 Overview
This milestone focused on building a **scalable, containerized end-to-end pipeline** for data processing, model training, and evaluation. We developed standardized data handling, generated item captions, fine-tuned a FashionCLIP model, and validated the pipeline’s reproducibility within Docker environments.

## Data
We processed a dataset containing ~6,700 curated product images and JSON metadata for men’s and women’s fashion. Each item includes product details and “complete the look” annotations that describe compatible items. The cleaned data were used to train a compatibility model and serve as the foundation for the end-to-end wardrobe recommendation pipeline, containerized and version-controlled for reproducibility.

## 📁 Project Structure

```
project 215/
├── data/                           # Training data
│   ├── Data caption/              # Captioned data from Angel's branch
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
## 1. Virtual Environment Setup

We built isolated Docker environments for each pipeline component to ensure consistency and scalability across cloud and local environments.

### Setup Instructions

```
make build
make run
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

[Insert Screenshot Placeholder]

_Figure 2. Console output showing successful end-to-end pipeline run._

[Insert Screenshot]

_Figure 3. XXX_

## 3. Data Ingestion & Preprocessing

We processed ~6,700 curated product images and corresponding JSON metadata for both men’s and women’s fashion. Each record contains structured product details and “complete the look” compatibility annotations. The pipeline standardizes, cleans, and captions each product entry to ensure consistency and model readiness.

### Pipeline Highlights
- Standardized captions generated for every product image
- Automatic filtering and removal of duplicate entries
- Consolidation of compatibility pairs from “complete the look” field

<img width="946" height="665" alt="截屏2025-10-16 19 20 43" src="https://github.com/user-attachments/assets/2c0a1f35-361f-4c37-bc6a-43b7c66f7b2e" />

Figure 4. Example of cleaned JSON metadata and generated captions.

## 4. Model Preparation, Training & Evaluation

The FashionCLIP-based model learns compatibility relationships between clothing items using triplet loss. Before training, we constructed triplets (anchor, positive, negative) and split data into training and validation sets.

### Architecture Overview
- **Model**: FashionCLIP (ViT-B/32)
- **Fine-Tuning**: Last 4 layers (first 8 frozen)
- **Loss Function**: Triplet margin loss (margin = 0.5)
- **Checkpointing**: Automatically saves best model

<img width="1011" height="299" alt="image" src="https://github.com/user-attachments/assets/99a911cf-9345-49d2-9345-227747667b3f" />

_Figure 5. An illustration of FashionCLIP fine-tuning with triplet loss for outfit compatibility._

### Training Configuration

| Parameter | Value |
|------------|--------|
| Batch Size | 16 |
| Learning Rate | 1e-5 |
| Epochs | 20 |
| Target Accuracy | 85% |

[Insert Training Curve Placeholder]  
_Figure 6. Training log showing loss and accuracy progression._

### Performance Summary
- **Training Time**: ~10–20 hours (V100 GPU)
- **Model Size**: ~500 MB
- **Final Accuracy**: >85% triplet accuracy

### Evaluation Metrics
- Precision, Recall, F1-score
- NDCG, AUC for ranked retrieval
- QuickEval for fast validation

[Insert Screenshot Placeholder]

_Figure 7. Evaluation metrics summary._

## 5. Application Mock-up

The Personal Wardrobe Stylist prototype generates outfit recommendations from a user’s wardrobe image.

<img width="1201" height="638" alt="image" src="https://github.com/user-attachments/assets/868368f1-4d18-4a4c-a4cb-d65d363941a8" />



