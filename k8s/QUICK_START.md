# Quick Start - Kubernetes Deployment

## ✅ What's Been Created

All Kubernetes manifests are ready! Here's what you have:

1. **01-configmap.yaml** - Shared configuration (GCP settings, paths, etc.)
2. **02-persistent-volume-claim.yaml** - Shared storage for all services
3. **03-ingestion-job.yaml** - One-time job to load data
4. **04-preprocessing-job.yaml** - One-time job to preprocess data
5. **05-training-job.yaml** - One-time job to train model (needs GPU)
6. **06-inference-deployment.yaml** - Long-running API server
7. **deploy.sh** - Automated deployment script
8. **README.md** - Full documentation

## 🚀 Next Steps (Before Deploying)

### 1. Build and Push Docker Images

```bash
# Set your registry
export REGISTRY=gcr.io/your-project-id  # or your Docker Hub username

# Build and push
docker build -f containers/ingestion/Dockerfile -t $REGISTRY/styleme-ingestion:latest .
docker push $REGISTRY/styleme-ingestion:latest

docker build -f containers/preprocessing/Dockerfile -t $REGISTRY/styleme-preprocessing:latest .
docker push $REGISTRY/styleme-preprocessing:latest

docker build -f containers/training/Dockerfile -t $REGISTRY/styleme-training:latest .
docker push $REGISTRY/styleme-training:latest

docker build -f containers/inference/Dockerfile -t $REGISTRY/styleme-inference:latest .
docker push $REGISTRY/styleme-inference:latest
```

### 2. Update Image Names in YAML Files

Replace `styleme-*:latest` with your actual image names in all YAML files:

```bash
# Quick replace (adjust REGISTRY first)
export REGISTRY=gcr.io/your-project-id
sed -i '' "s|styleme-ingestion:latest|$REGISTRY/styleme-ingestion:latest|g" k8s/*.yaml
sed -i '' "s|styleme-preprocessing:latest|$REGISTRY/styleme-preprocessing:latest|g" k8s/*.yaml
sed -i '' "s|styleme-training:latest|$REGISTRY/styleme-training:latest|g" k8s/*.yaml
sed -i '' "s|styleme-inference:latest|$REGISTRY/styleme-inference:latest|g" k8s/*.yaml
```

### 3. Deploy

**Option A: Use the automated script**
```bash
cd k8s
./deploy.sh
```

**Option B: Manual deployment (see README.md for details)**
```bash
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-persistent-volume-claim.yaml
# ... etc (see README.md)
```

## ⚠️ Important Reminders

1. **GPU Required**: Training job needs GPU nodes. Make sure your cluster has a GPU node pool.
2. **Storage**: The PVC uses default storage class. For GKE, you may need ReadWriteMany support.
3. **GCP Credentials**: Set up service account authentication for GCS access.
4. **Image Registry**: All images must be accessible from your cluster.

## 📊 After Deployment

```bash
# Check status
kubectl get pods -l app=styleme

# Get service URL
kubectl get service styleme-inference-service

# View logs
kubectl logs -l component=inference

# Scale for demo
kubectl scale deployment styleme-inference --replicas=4
```

## 🐛 Troubleshooting

See `README.md` for detailed troubleshooting guide.

