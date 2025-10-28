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
├── midterm_presentation/                          
│   ├── StyleMeMidterm.pdf 
├── containers/                   # Dockerfiles
│   ├── inference/                  
│   └── ...
├── queries/                     # User Input
│   ├── user1/
│   ├── ...
├── results/                     # Inference Output
│   ├── user1/
│   ├── ...
├── wardrobes/                   # User uploaded wardrobes
│   ├── user1/
│   ├── ...                     
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
│       └── eval/                 # Evaluation rubrics
│           ├── evaluation.py     
│           └── quick_eval.py     
├── install_nvidia_driver.sh     # GPU driver installation
├── cuda_installer.py            # CUDA setup automation
├── install_gpu_driver.py        # GPU driver management
├── docker-compose.yml           # Container orchestration
├── docker-compose.yml.backup    # Backup configuration
└── README.md
```

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

### Midterm Presentation

Filename: StyleMeMidterm.pdf
