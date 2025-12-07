# Pulumi Quick Start

## ✅ What's Been Created

Complete Pulumi infrastructure code that:
1. ✅ Provisions GKE cluster
2. ✅ Creates default node pool (for regular workloads)
3. ✅ Creates GPU node pool (for training)
4. ✅ Deploys all Kubernetes manifests automatically

## 🚀 Quick Setup (5 minutes)

### 1. Install Pulumi

```bash
curl -fsSL https://get.pulumi.com | sh
```

### 2. Install Dependencies

```bash
cd infrastructure/pulumi
npm install
```

### 3. Configure

```bash
# Login (first time only)
pulumi login

# Create stack
pulumi stack init dev

# Set config
pulumi config set gcp:project styleme-475201
pulumi config set gcp:region us-central1
pulumi config set gcp:zone us-central1-a
```

### 4. Deploy

```bash
# Preview first
pulumi preview

# Deploy
pulumi up
```

That's it! Your cluster will be created and all K8s resources deployed.

## 📝 Before You Deploy

**Important**: Make sure you've:
1. ✅ Built and pushed Docker images to a registry
2. ✅ Updated image names in `k8s/*.yaml` files
3. ✅ Configured GCP credentials (`gcloud auth application-default login`)

## 🔍 After Deployment

```bash
# Get cluster connection
pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml
export KUBECONFIG=$PWD/kubeconfig.yaml

# Or use gcloud
gcloud container clusters get-credentials styleme-cluster --zone us-central1-a

# Check status
kubectl get pods -l app=styleme
kubectl get service styleme-inference-service
```

## 🧹 Cleanup

```bash
pulumi destroy
```

## 📚 Full Documentation

See `README.md` for detailed instructions.

