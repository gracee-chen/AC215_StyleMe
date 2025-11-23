# Vertex AI Migration Guide

This guide outlines how to migrate the StyleMe 9.0 project from local Docker-based deployment to Google Cloud Vertex AI.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Comparison](#architecture-comparison)
3. [Prerequisites](#prerequisites)
4. [Migration Steps](#migration-steps)
5. [Training on Vertex AI](#training-on-vertex-ai)
6. [Deploying to Vertex AI Endpoints](#deploying-to-vertex-ai-endpoints)
7. [Using Vertex AI Pipelines](#using-vertex-ai-pipelines)
8. [Cost Optimization](#cost-optimization)
9. [Monitoring and Logging](#monitoring-and-logging)

## Overview

### Current Architecture
- **Local Docker Compose**: Multi-container pipeline (ingestion, preprocessing, training, inference)
- **Local GPU Training**: Training runs on local GPU instances
- **Local Inference**: Inference service runs in Docker containers
- **GCS Storage**: Data already stored in Google Cloud Storage

### Target Architecture
- **Vertex AI Training**: Custom training jobs on managed GPU instances
- **Vertex AI Endpoints**: Managed model serving with auto-scaling
- **Vertex AI Pipelines**: Orchestrated ML workflows using Kubeflow
- **Cloud Storage**: Continue using GCS for data and model artifacts
- **Artifact Registry**: Store Docker images for training and serving

## Architecture Comparison

| Component | Current | Vertex AI |
|-----------|---------|-----------|
| Training | Local Docker + GPU | Vertex AI Custom Training |
| Model Storage | Local filesystem | GCS + Vertex AI Model Registry |
| Inference | Docker container | Vertex AI Endpoints |
| Orchestration | Docker Compose | Vertex AI Pipelines (Kubeflow) |
| Data Storage | GCS | GCS (unchanged) |
| Monitoring | Local logs | Cloud Logging + Vertex AI Monitoring |

## Prerequisites

### 1. GCP Setup

```bash
# Set project
export PROJECT_ID="styleme-475201"
export REGION="us-central1"
export BUCKET_NAME="styleme-data-bucket"

gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    aiplatform.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    containerregistry.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com
```

### 2. Service Account Setup

```bash
# Create service account for Vertex AI
gcloud iam service-accounts create vertex-ai-sa \
    --display-name="Vertex AI Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vertex-ai-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vertex-ai-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vertex-ai-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"
```

### 3. Artifact Registry Setup

```bash
# Create Artifact Registry repository for Docker images
gcloud artifacts repositories create styleme-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="StyleMe Docker images"

# Configure Docker authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

## Migration Steps

### Step 1: Prepare Docker Images for Vertex AI

#### 1.1 Training Image

The training Dockerfile needs minimal changes. Ensure it:
- Uses a base image compatible with Vertex AI
- Installs dependencies correctly
- Has proper entrypoint for Vertex AI training

#### 1.2 Inference Image

The inference image needs to be adapted for Vertex AI Prediction:
- Implement prediction handler compatible with Vertex AI
- Support health checks
- Handle request/response in Vertex AI format

### Step 2: Push Images to Artifact Registry

```bash
# Build and tag training image
docker build -f containers/training/Dockerfile -t \
    ${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/training:latest .

# Build and tag inference image
docker build -f containers/inference/Dockerfile -t \
    ${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/inference:latest .

# Push images
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/training:latest
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/inference:latest
```

## Training on Vertex AI

### Option 1: Custom Training Job (Recommended)

Vertex AI Custom Training allows you to run your existing training code with minimal changes.

#### Training Script Structure

```python
# vertex_ai_migration/training/train_vertex_ai.py
"""
Vertex AI Custom Training Entry Point
"""
import os
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-version', required=True)
    parser.add_argument('--experiment-id', default=None)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--learning-rate', type=float, default=5e-6)
    
    args = parser.parse_args()
    
    # Vertex AI sets these environment variables
    AIP_MODEL_DIR = os.environ.get('AIP_MODEL_DIR', '/gcs/model')
    AIP_CHECKPOINT_DIR = os.environ.get('AIP_CHECKPOINT_DIR', '/gcs/checkpoints')
    
    # Run training (use existing run_fine_tuning.py logic)
    # ...
```

#### Submit Training Job

```bash
# vertex_ai_migration/scripts/submit_training_job.sh
gcloud ai custom-jobs create \
    --region=$REGION \
    --display-name="styleme-training-$(date +%Y%m%d-%H%M%S)" \
    --worker-pool-spec=machine-type=n1-standard-4,replica-count=1,container-image-uri=${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/training:latest \
    --args="--data-version=catalog-v_men_women_20251123,--epochs=20,--batch-size=32" \
    --service-account=vertex-ai-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

### Option 2: Python Package Training

Package your training code and submit as a Python package job.

## Deploying to Vertex AI Endpoints

### 1. Create Prediction Handler

Vertex AI requires a specific prediction interface. Create a handler:

```python
# vertex_ai_migration/serving/prediction_handler.py
"""
Vertex AI Prediction Handler
"""
import json
import base64
from typing import Any, Dict, List
from inference_service import InferenceService

class PredictionHandler:
    def __init__(self):
        self.service = InferenceService(
            catalog_dir=os.environ.get('CATALOG_DIR', '/gcs/catalog'),
            experiments_dir=os.environ.get('EXPERIMENTS_DIR', '/gcs/models'),
            wardrobes_dir=os.environ.get('WARDROBES_DIR', '/gcs/wardrobes')
        )
    
    def predict(self, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle prediction requests from Vertex AI"""
        predictions = []
        
        for instance in instances:
            # Decode base64 image if needed
            if 'image_bytes' in instance:
                image_data = base64.b64decode(instance['image_bytes'])
            elif 'image_path' in instance:
                image_path = instance['image_path']
            else:
                raise ValueError("Either 'image_bytes' or 'image_path' required")
            
            # Run inference
            result = self.service.inference(
                user_id=instance.get('user_id', 'default'),
                query_image_path=image_path,
                threshold=instance.get('threshold', 0.7),
                wardrobe_k=instance.get('wardrobe_k', 5),
                catalog_k=instance.get('catalog_k', 3),
                gender=instance.get('gender')
            )
            
            predictions.append(result)
        
        return predictions
```

### 2. Deploy Model to Endpoint

```bash
# vertex_ai_migration/scripts/deploy_model.sh
# 1. Upload model to Vertex AI Model Registry
gcloud ai models upload \
    --region=$REGION \
    --display-name="styleme-fashionclip" \
    --container-image-uri=${REGION}-docker.pkg.dev/${PROJECT_ID}/styleme-repo/inference:latest \
    --artifact-uri=gs://${BUCKET_NAME}/models/latest

# 2. Create endpoint
ENDPOINT_ID=$(gcloud ai endpoints create \
    --region=$REGION \
    --display-name="styleme-inference-endpoint" \
    --format="value(name)")

# 3. Deploy model to endpoint
gcloud ai endpoints deploy-model $ENDPOINT_ID \
    --region=$REGION \
    --model=MODEL_ID \
    --machine-type=n1-standard-4 \
    --min-replica-count=1 \
    --max-replica-count=3 \
    --traffic-split=100
```

### 3. Make Predictions

```python
# vertex_ai_migration/serving/predict_client.py
from google.cloud import aiplatform

endpoint = aiplatform.Endpoint(
    endpoint_name="projects/{}/locations/{}/endpoints/{}".format(
        PROJECT_ID, REGION, ENDPOINT_ID
    )
)

# Prepare request
instances = [{
    "user_id": "user_001",
    "image_path": "gs://bucket/path/to/image.jpg",
    "threshold": 0.7,
    "wardrobe_k": 5,
    "catalog_k": 3,
    "gender": "men"
}]

# Make prediction
predictions = endpoint.predict(instances=instances)
```

## Using Vertex AI Pipelines

Vertex AI Pipelines (Kubeflow) can orchestrate the entire ML workflow.

### Pipeline Components

1. **Data Ingestion Component**: Load data from GCS
2. **Preprocessing Component**: Process images
3. **Training Component**: Train model on Vertex AI
4. **Evaluation Component**: Evaluate model performance
5. **Deployment Component**: Deploy to endpoint if metrics pass

### Example Pipeline

```python
# vertex_ai_migration/pipelines/training_pipeline.py
from kfp.v2 import dsl
from kfp.v2.dsl import component, pipeline, Input, Output, Dataset, Model

@component(
    base_image=f"{REGION}-docker.pkg.dev/{PROJECT_ID}/styleme-repo/training:latest",
    packages_to_install=["google-cloud-storage"]
)
def train_model(
    data_version: str,
    epochs: int,
    batch_size: int,
    model: Output[Model]
):
    """Training component"""
    import subprocess
    subprocess.run([
        "python", "src/models/train/run_fine_tuning.py",
        "--data-version", data_version,
        "--epochs", str(epochs),
        "--batch-size", str(batch_size)
    ])
    # Save model to output path
    model.uri = "/gcs/model/latest"

@pipeline(name="styleme-training-pipeline")
def training_pipeline(
    data_version: str = "catalog-v_men_women_20251123",
    epochs: int = 20,
    batch_size: int = 32
):
    train_op = train_model(
        data_version=data_version,
        epochs=epochs,
        batch_size=batch_size
    )

# Compile and submit
from kfp.v2 import compiler
compiler.Compiler().compile(
    pipeline_func=training_pipeline,
    package_path="training_pipeline.json"
)

from google.cloud import aiplatform
aiplatform.PipelineJob(
    display_name="styleme-training",
    template_path="training_pipeline.json",
    pipeline_root=f"gs://{BUCKET_NAME}/pipelines",
    parameter_values={
        "data_version": "catalog-v_men_women_20251123",
        "epochs": 20,
        "batch_size": 32
    }
).run()
```

## Cost Optimization

### Training Costs
- Use preemptible VMs for training (up to 80% savings)
- Choose appropriate machine types (n1-standard-4 vs n1-highmem-4)
- Use spot VMs for non-critical training jobs

### Inference Costs
- Configure auto-scaling based on traffic
- Use minimum replicas = 0 for development
- Choose appropriate machine types (CPU vs GPU)

### Storage Costs
- Use lifecycle policies for old model versions
- Compress model artifacts
- Archive old training data

## Monitoring and Logging

### Cloud Logging
All Vertex AI jobs automatically log to Cloud Logging:
- Training logs: `resource.type="aiplatform.googleapis.com/TrainingJob"`
- Prediction logs: `resource.type="aiplatform.googleapis.com/Endpoint"`

### Vertex AI Monitoring
- Track model performance metrics
- Monitor prediction latency
- Set up alerts for errors

### Example Monitoring Query

```bash
# View training logs
gcloud logging read "resource.type=aiplatform.googleapis.com/TrainingJob" --limit=50

# View prediction logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Endpoint" --limit=50
```

## Next Steps

1. **Test Training Job**: Submit a small training job to verify setup
2. **Test Deployment**: Deploy a test model to an endpoint
3. **Set Up Pipeline**: Create and run a complete pipeline
4. **Monitor Costs**: Set up billing alerts
5. **Optimize**: Fine-tune machine types and scaling

## Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Custom Training Guide](https://cloud.google.com/vertex-ai/docs/training/create-custom-job)
- [Model Deployment Guide](https://cloud.google.com/vertex-ai/docs/predictions/deploy-model-api)
- [Kubeflow Pipelines](https://www.kubeflow.org/docs/components/pipelines/)

