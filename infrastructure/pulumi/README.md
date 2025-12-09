# Pulumi Infrastructure for StyleMe

This directory contains Pulumi code to automate the provisioning and deployment of StyleMe infrastructure on Google Cloud Platform (GCP).

## 📋 What This Does

1. **Provisions GKE Cluster**: Creates a Kubernetes cluster on GCP
2. **Creates Node Pools**: 
   - Default node pool for regular workloads
   - GPU node pool for training workloads
3. **Deploys Kubernetes Manifests**: Automatically deploys all K8s resources from the `k8s/` directory

## 🚀 Prerequisites

1. **Pulumi CLI** installed:
   ```bash
   curl -fsSL https://get.pulumi.com | sh
   ```

2. **Node.js** (v18+) and npm installed

3. **GCP Account** with:
   - Billing enabled
   - Required APIs enabled (container.googleapis.com, compute.googleapis.com)
   - Service account with appropriate permissions

4. **GCP Credentials** configured:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

5. **Pulumi GCP Plugin**:
   ```bash
   pulumi plugin install resource gcp v6.0.0
   ```

## 📦 Setup

1. **Install dependencies**:
   ```bash
   cd infrastructure/pulumi
   npm install
   ```

2. **Configure Pulumi**:
   ```bash
   # Login to Pulumi (first time only)
   pulumi login
   
   # Create a new stack (or use existing)
   pulumi stack init dev
   
   # Set configuration
   pulumi config set gcp:project styleme-475201
   pulumi config set gcp:region us-central1
   pulumi config set gcp:zone us-central1-a
   pulumi config set clusterName styleme-cluster
   pulumi config set nodeCount 2
   pulumi config set gpuNodeCount 1
   ```

## 🚀 Deployment

### Preview Changes

```bash
pulumi preview
```

### Deploy Infrastructure

```bash
pulumi up
```

This will:
1. Create the GKE cluster
2. Create node pools (default + GPU)
3. Deploy all Kubernetes manifests
4. Output the cluster connection info

### Get Cluster Connection Info

After deployment, Pulumi will output the kubeconfig. You can also get it:

```bash
# Get kubeconfig
pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml

# Or use gcloud
gcloud container clusters get-credentials styleme-cluster --zone us-central1-a
```

## 🔧 Configuration Options

You can customize the deployment by setting Pulumi config values:

```bash
# Cluster name
pulumi config set clusterName my-cluster

# Number of nodes in default pool
pulumi config set nodeCount 3

# Number of GPU nodes
pulumi config set gpuNodeCount 2

# GCP project
pulumi config set gcp:project my-project-id

# Region/Zone
pulumi config set gcp:region us-east1
pulumi config set gcp:zone us-east1-b
```

## 📊 What Gets Created

### GCP Resources

- **GKE Cluster**: `styleme-cluster` (or configured name)
- **Default Node Pool**: For regular workloads (n1-standard-2)
- **GPU Node Pool**: For training workloads (n1-standard-4 with NVIDIA T4)

### Kubernetes Resources

All resources from `k8s/` directory:
- ConfigMap
- PersistentVolumeClaim
- Ingestion Job
- Preprocessing Job
- Training Job
- Inference Deployment + Service

## 🧹 Cleanup

To destroy all resources:

```bash
pulumi destroy
```

**⚠️ Warning**: This will delete the entire cluster and all data!

## 🔍 Troubleshooting

### Pulumi can't find GCP credentials

```bash
gcloud auth application-default login
```

### Cluster creation fails

- Check that billing is enabled on your GCP project
- Verify you have permissions to create GKE clusters
- Check quota limits for your region

### Kubernetes manifests fail to deploy

- Ensure the cluster is fully ready before deploying manifests
- Check that Docker images are built and pushed to a registry
- Verify image names in the K8s manifests match your registry

### GPU nodes not available

- Check that GPU quota is available in your region
- Verify the GPU type (nvidia-tesla-t4) is available in your zone
- Check node pool status: `kubectl get nodes -l accelerator=nvidia-tesla-t4`

## 📚 Next Steps

After infrastructure is deployed:

1. **Build and push Docker images** (see `k8s/QUICK_START.md`)
2. **Update image names** in Kubernetes manifests
3. **Set up CI/CD** to automatically deploy on merges to main
4. **Configure monitoring** and logging

## 🔗 Related Documentation

- [Kubernetes Deployment Guide](../k8s/README.md)
- [Pulumi GCP Documentation](https://www.pulumi.com/docs/clouds/gcp/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)

