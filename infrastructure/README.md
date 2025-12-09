# StyleMe Infrastructure

This directory contains infrastructure automation code for deploying StyleMe to production.

## 📁 Structure

```
infrastructure/
└── pulumi/              # Pulumi infrastructure as code
    ├── index.ts        # Main Pulumi code (GKE cluster + K8s deployment)
    ├── Pulumi.yaml     # Pulumi project config
    ├── package.json    # Node.js dependencies
    ├── tsconfig.json   # TypeScript config
    ├── README.md       # Detailed documentation
    └── QUICK_START.md  # Quick setup guide
```

## ✅ What's Complete

### Kubernetes Manifests (`k8s/` directory)
- ✅ ConfigMap for shared configuration
- ✅ PersistentVolumeClaim for shared storage
- ✅ Ingestion Job
- ✅ Preprocessing Job
- ✅ Training Job (GPU-enabled)
- ✅ Inference Deployment + Service
- ✅ Deployment scripts and documentation

### Pulumi Infrastructure (`infrastructure/pulumi/`)
- ✅ GKE cluster provisioning
- ✅ Default node pool (for regular workloads)
- ✅ GPU node pool (for training)
- ✅ Automatic Kubernetes manifest deployment
- ✅ Configuration management
- ✅ Documentation

## 🚀 Next Steps

### 1. Install Pulumi (if not already installed)

```bash
curl -fsSL https://get.pulumi.com | sh
```

### 2. Set Up Pulumi Project

```bash
cd infrastructure/pulumi
npm install
pulumi login
pulumi stack init dev
pulumi config set gcp:project styleme-475201
```

### 3. Build and Push Docker Images

Before deploying, you need to build and push your container images:

```bash
export REGISTRY=gcr.io/your-project-id

docker build -f containers/ingestion/Dockerfile -t $REGISTRY/styleme-ingestion:latest .
docker push $REGISTRY/styleme-ingestion:latest

# Repeat for preprocessing, training, inference
```

### 4. Update Image Names in K8s Manifests

Update the image names in `k8s/*.yaml` files to match your registry.

### 5. Deploy with Pulumi

```bash
cd infrastructure/pulumi
pulumi preview  # Review changes
pulumi up       # Deploy
```

## 📚 Documentation

- **Kubernetes**: See `../k8s/README.md` for K8s deployment details
- **Pulumi**: See `pulumi/README.md` for detailed Pulumi setup
- **Quick Start**: See `pulumi/QUICK_START.md` for fast setup

## 🎯 Milestone 5 Checklist

- [x] Kubernetes manifests created
- [x] Pulumi infrastructure code created
- [ ] Docker images built and pushed
- [ ] Pulumi deployment tested
- [ ] CI/CD integration (GitHub Actions)
- [ ] Scaling demonstration
- [ ] Documentation complete

## 🔗 Related Files

- `../k8s/` - Kubernetes manifests
- `../docker-compose.yml` - Local development setup
- `../.github/workflows/` - CI/CD pipelines (to be updated)

