#!/bin/bash
# Deployment script for StyleMe Kubernetes manifests
# This script deploys all components in the correct order

set -e  # Exit on any error

echo "🚀 StyleMe Kubernetes Deployment"
echo "================================"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    echo "   Please configure kubectl to connect to your cluster"
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"
echo ""

# Step 1: ConfigMap
echo "📝 Step 1/6: Deploying ConfigMap..."
kubectl apply -f 01-configmap.yaml
echo "✅ ConfigMap deployed"
echo ""

# Step 2: PersistentVolumeClaim
echo "💾 Step 2/6: Deploying PersistentVolumeClaim..."
kubectl apply -f 02-persistent-volume-claim.yaml
echo "⏳ Waiting for PVC to be ready..."
kubectl wait --for=condition=Ready pvc/styleme-data-pvc --timeout=60s || {
    echo "⚠️  Warning: PVC not ready, but continuing..."
}
echo "✅ PVC deployed"
echo ""

# Step 3: Ingestion Job
echo "📥 Step 3/6: Deploying Ingestion Job..."
kubectl apply -f 03-ingestion-job.yaml
echo "⏳ Waiting for ingestion to complete (this may take a few minutes)..."
kubectl wait --for=condition=complete job/styleme-ingestion --timeout=600s || {
    echo "⚠️  Warning: Ingestion job not complete, check logs with: kubectl logs job/styleme-ingestion"
}
echo "✅ Ingestion job deployed"
echo ""

# Step 4: Preprocessing Job
echo "🔄 Step 4/6: Deploying Preprocessing Job..."
kubectl apply -f 04-preprocessing-job.yaml
echo "⏳ Waiting for preprocessing to complete..."
kubectl wait --for=condition=complete job/styleme-preprocessing --timeout=600s || {
    echo "⚠️  Warning: Preprocessing job not complete, check logs with: kubectl logs job/styleme-preprocessing"
}
echo "✅ Preprocessing job deployed"
echo ""

# Step 5: Training Job
echo "🤖 Step 5/6: Deploying Training Job (requires GPU)..."
kubectl apply -f 05-training-job.yaml
echo "⏳ Waiting for training to complete (this may take 30+ minutes)..."
echo "   You can check progress with: kubectl logs job/styleme-training -f"
kubectl wait --for=condition=complete job/styleme-training --timeout=3600s || {
    echo "⚠️  Warning: Training job not complete, check logs with: kubectl logs job/styleme-training"
    echo "   Training may take longer than 1 hour, check status manually"
}
echo "✅ Training job deployed"
echo ""

# Step 6: Inference Deployment
echo "🌐 Step 6/6: Deploying Inference Service..."
kubectl apply -f 06-inference-deployment.yaml
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/styleme-inference --timeout=300s || {
    echo "⚠️  Warning: Deployment not ready, check status with: kubectl get pods -l component=inference"
}
echo "✅ Inference service deployed"
echo ""

# Get service URL
echo "================================"
echo "✅ Deployment Complete!"
echo "================================"
echo ""
echo "📊 Status:"
kubectl get pods -l app=styleme
echo ""
echo "🌐 Service URL:"
kubectl get service styleme-inference-service
echo ""
EXTERNAL_IP=$(kubectl get service styleme-inference-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -n "$EXTERNAL_IP" ]; then
    echo "✅ API available at: http://$EXTERNAL_IP"
    echo "   Health check: http://$EXTERNAL_IP/health"
else
    echo "⏳ Waiting for LoadBalancer IP to be assigned..."
    echo "   Check with: kubectl get service styleme-inference-service"
fi
echo ""
echo "📝 Useful commands:"
echo "   View logs: kubectl logs -l component=inference"
echo "   Scale up: kubectl scale deployment styleme-inference --replicas=4"
echo "   Check status: kubectl get all -l app=styleme"

