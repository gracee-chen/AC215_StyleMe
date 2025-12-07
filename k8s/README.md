# Kubernetes Deployment Guide for StyleMe

This directory contains Kubernetes manifests for deploying StyleMe to a Kubernetes cluster (GKE or AWS EKS).

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Kubernetes cluster** (GKE or EKS) with kubectl configured
2. **Docker images** built and pushed to a container registry (GCR, ECR, or Docker Hub)
3. **GCP credentials** configured (for GCS access)
4. **kubectl** installed and configured to connect to your cluster
5. **GPU nodes** (for training job) - if using GKE, ensure you have a GPU node pool

## 📁 File Structure

```
k8s/
├── 01-configmap.yaml              # Shared configuration
├── 02-persistent-volume-claim.yaml  # Shared storage
├── 03-ingestion-job.yaml          # Data ingestion (runs once)
├── 04-preprocessing-job.yaml      # Data preprocessing (runs once)
├── 05-training-job.yaml           # Model training (runs once, needs GPU)
├── 06-inference-deployment.yaml   # API server (long-running)
└── README.md                      # This file
```

## 🚀 Step-by-Step Deployment

### Step 1: Build and Push Docker Images

You need to build and push your container images to a registry:

```bash
# Set your registry (example for GCR)
export REGISTRY=gcr.io/your-project-id
# Or for Docker Hub:
# export REGISTRY=your-dockerhub-username

# Build and push each image
docker build -f containers/ingestion/Dockerfile -t $REGISTRY/styleme-ingestion:latest .
docker push $REGISTRY/styleme-ingestion:latest

docker build -f containers/preprocessing/Dockerfile -t $REGISTRY/styleme-preprocessing:latest .
docker push $REGISTRY/styleme-preprocessing:latest

docker build -f containers/training/Dockerfile -t $REGISTRY/styleme-training:latest .
docker push $REGISTRY/styleme-training:latest

docker build -f containers/inference/Dockerfile -t $REGISTRY/styleme-inference:latest .
docker push $REGISTRY/styleme-inference:latest
```

### Step 2: Update Image Names in Manifests

Edit each YAML file and replace `styleme-*:latest` with your actual image names:

```bash
# Example: Replace in all files
sed -i '' "s|styleme-ingestion:latest|$REGISTRY/styleme-ingestion:latest|g" k8s/*.yaml
sed -i '' "s|styleme-preprocessing:latest|$REGISTRY/styleme-preprocessing:latest|g" k8s/*.yaml
sed -i '' "s|styleme-training:latest|$REGISTRY/styleme-training:latest|g" k8s/*.yaml
sed -i '' "s|styleme-inference:latest|$REGISTRY/styleme-inference:latest|g" k8s/*.yaml
```

### Step 3: Configure GCP Credentials (for GCS access)

Create a Kubernetes Secret with your GCP service account key:

```bash
# Option 1: If you have a service account JSON key file
kubectl create secret generic gcp-credentials \
  --from-file=key.json=/path/to/your/service-account-key.json

# Option 2: If using Workload Identity (recommended for GKE)
# Follow GKE Workload Identity setup guide
```

Then update the manifests to mount this secret (you may need to add volume mounts).

### Step 4: Deploy in Order

Deploy the manifests in this specific order:

```bash
# 1. ConfigMap (shared configuration)
kubectl apply -f k8s/01-configmap.yaml

# 2. PersistentVolumeClaim (shared storage)
kubectl apply -f k8s/02-persistent-volume-claim.yaml

# 3. Wait for PVC to be ready
kubectl wait --for=condition=Ready pvc/styleme-data-pvc --timeout=60s

# 4. Ingestion Job (loads data)
kubectl apply -f k8s/03-ingestion-job.yaml

# 5. Wait for ingestion to complete
kubectl wait --for=condition=complete job/styleme-ingestion --timeout=600s

# 6. Preprocessing Job
kubectl apply -f k8s/04-preprocessing-job.yaml

# 7. Wait for preprocessing to complete
kubectl wait --for=condition=complete job/styleme-preprocessing --timeout=600s

# 8. Training Job (requires GPU)
kubectl apply -f k8s/05-training-job.yaml

# 9. Wait for training to complete (this may take a while)
kubectl wait --for=condition=complete job/styleme-training --timeout=3600s

# 10. Inference Deployment (API server)
kubectl apply -f k8s/06-inference-deployment.yaml

# 11. Wait for deployment to be ready
kubectl wait --for=condition=available deployment/styleme-inference --timeout=300s
```

### Step 5: Get Service URL

```bash
# Get the external IP of the LoadBalancer service
kubectl get service styleme-inference-service

# The EXTERNAL-IP column will show your public URL
# Access the API at: http://<EXTERNAL-IP>/health
```

## 🔍 Verification

### Check Pod Status

```bash
# Check all pods
kubectl get pods -l app=styleme

# Check specific component
kubectl get pods -l component=inference
kubectl get pods -l component=ingestion
```

### Check Logs

```bash
# Inference service logs
kubectl logs -l component=inference --tail=50

# Ingestion job logs
kubectl logs job/styleme-ingestion

# Training job logs
kubectl logs job/styleme-training
```

### Test API

```bash
# Get service IP
EXTERNAL_IP=$(kubectl get service styleme-inference-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl http://$EXTERNAL_IP/health
```

## 🔄 Scaling Demo (for Milestone 5 requirement)

To demonstrate scaling behavior:

```bash
# Scale up inference deployment
kubectl scale deployment styleme-inference --replicas=4

# Watch pods scaling up
kubectl get pods -l component=inference -w

# Scale down
kubectl scale deployment styleme-inference --replicas=2
```

## 🧹 Cleanup

To remove everything:

```bash
# Delete in reverse order
kubectl delete -f k8s/06-inference-deployment.yaml
kubectl delete -f k8s/05-training-job.yaml
kubectl delete -f k8s/04-preprocessing-job.yaml
kubectl delete -f k8s/03-ingestion-job.yaml
kubectl delete -f k8s/02-persistent-volume-claim.yaml
kubectl delete -f k8s/01-configmap.yaml
```

## ⚠️ Important Notes

1. **Storage Class**: The PVC uses the default storage class. For GKE, you may need to use a storage class that supports `ReadWriteMany` (like NFS). Adjust `02-persistent-volume-claim.yaml` if needed.

2. **GPU Nodes**: The training job requires GPU. Ensure your cluster has GPU nodes:
   ```bash
   # For GKE, create a GPU node pool
   gcloud container node-pools create gpu-pool \
     --cluster=your-cluster-name \
     --machine-type=n1-standard-4 \
     --accelerator type=nvidia-tesla-t4,count=1 \
     --num-nodes=1
   ```

3. **Image Pull Secrets**: If using a private registry, you'll need to create image pull secrets and reference them in the pod specs.

4. **Resource Limits**: Adjust CPU/memory limits in the manifests based on your cluster capacity.

5. **Dependencies**: The jobs have basic dependency handling via init containers. For production, consider using a workflow engine like Argo Workflows.

## 🐛 Troubleshooting

### Pods stuck in Pending

```bash
# Check why pod is pending
kubectl describe pod <pod-name>

# Common issues:
# - Insufficient resources (CPU/memory/GPU)
# - PVC not bound (check storage class)
# - Image pull errors
```

### Jobs failing

```bash
# Check job status
kubectl describe job <job-name>

# Check logs
kubectl logs job/<job-name>
```

### Service not accessible

```bash
# Check service endpoints
kubectl get endpoints styleme-inference-service

# Check if pods are ready
kubectl get pods -l component=inference
```

## 📚 Next Steps

After Kubernetes deployment works:
1. Set up Pulumi to automate this infrastructure
2. Integrate deployment into GitHub Actions CI/CD
3. Set up monitoring and logging
4. Configure auto-scaling based on load

