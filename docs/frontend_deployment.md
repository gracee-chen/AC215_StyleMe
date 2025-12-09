# Frontend Deployment Guide

This guide explains how to deploy the StyleMe frontend to Google Cloud Platform (GCP).

## Overview

The frontend is deployed as a **static website** served via **Cloud Run** using **nginx**. The deployment process:

1. Builds the React app with production environment variables
2. Packages it in a Docker container with nginx
3. Deploys to Cloud Run

## Prerequisites

- GCP project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed and running
- Artifact Registry repository created:
  ```bash
  gcloud artifacts repositories create styleme-repo \
    --repository-format=docker \
    --location=us-central1 \
    --project=styleme-475201
  ```

## Quick Deployment

### Option 1: Use Deployment Script (Recommended)

```bash
# Deploy with default API URL (Cloud Run inference service)
./scripts/deploy_frontend_cloudrun.sh

# Deploy with custom API URL
./scripts/deploy_frontend_cloudrun.sh https://your-custom-api-url.com
```

### Option 2: Manual Deployment

1. **Set up environment variables:**
   ```bash
   cd website
   cp .env.production.example .env.production
   # Edit .env.production with your API URL
   ```

2. **Build the frontend:**
   ```bash
   npm install
   npm run build
   ```

3. **Build and push Docker image:**
   ```bash
   docker build -f Dockerfile.static -t us-central1-docker.pkg.dev/styleme-475201/styleme-repo/frontend:latest .
   docker push us-central1-docker.pkg.dev/styleme-475201/styleme-repo/frontend:latest
   ```

4. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy styleme-frontend \
     --image us-central1-docker.pkg.dev/styleme-475201/styleme-repo/frontend:latest \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --memory 512Mi \
     --cpu 1 \
     --port 8080 \
     --project styleme-475201
   ```

## Environment Variables

### Local Development

For local development, create `.env.local` (or use `.env`):

```bash
VITE_API_URL=http://localhost:5001
VITE_OPENAI_API_KEY=your_key_here  # Optional
```

### Production

For production builds, create `.env.production`:

```bash
VITE_API_URL=https://styleme-inference-nty2g5pcpa-uc.a.run.app
VITE_OPENAI_API_KEY=your_key_here  # Optional
```

**Important:** Vite environment variables are **baked into the build** at build time. You must rebuild the frontend if you change the API URL.

## Switching Between Environments

### Local Development
```bash
cd website
# Ensure .env or .env.local has localhost URL
npm run dev
```

### Production Build (Local Testing)
```bash
cd website
# Ensure .env.production has production URL
npm run build
npm run preview  # Test the production build locally
```

### Deploy to Cloud
```bash
./scripts/deploy_frontend_cloudrun.sh
```

## Architecture

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Cloud Run      │
│  (nginx)        │  ← Frontend (Static HTML/JS/CSS)
│  Port: 8080     │
└────────┬────────┘
         │ API Calls
         ▼
┌─────────────────┐
│  Cloud Run      │
│  (Flask API)    │  ← Backend (Inference Service)
│  Port: 8080     │
└─────────────────┘
```

## Configuration

### Cloud Run Settings

- **Memory**: 512Mi (sufficient for static site)
- **CPU**: 1 vCPU
- **Timeout**: 300 seconds
- **Max Instances**: 10 (auto-scaling)
- **Min Instances**: 0 (scale to zero when not in use)
- **Port**: 8080 (nginx default)

### Cost Optimization

- **Min Instances = 0**: Frontend scales to zero when not in use
- **512Mi Memory**: Minimal memory for static site
- **1 vCPU**: Sufficient for serving static files

## Troubleshooting

### Build Fails

1. Check Node.js version (requires 18+):
   ```bash
   node --version
   ```

2. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

### Deployment Fails

1. Check Docker is running:
   ```bash
   docker ps
   ```

2. Verify Artifact Registry access:
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

3. Check service account permissions:
   ```bash
   gcloud projects get-iam-policy styleme-475201
   ```

### API Calls Fail After Deployment

1. Verify API URL in `.env.production` is correct
2. Check CORS settings on backend API
3. Verify backend API is accessible:
   ```bash
   curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health
   ```

### Environment Variables Not Working

Remember: Vite environment variables are **baked in at build time**. If you change `.env.production`, you must:
1. Rebuild: `npm run build`
2. Rebuild Docker image
3. Redeploy to Cloud Run

## Updating the Deployment

To update the frontend after making changes:

```bash
# Just run the deployment script again
./scripts/deploy_frontend_cloudrun.sh
```

The script will:
1. Rebuild the frontend
2. Build a new Docker image
3. Push to Artifact Registry
4. Deploy to Cloud Run (updates existing service)

## Monitoring

### View Logs
```bash
gcloud run services logs read styleme-frontend \
  --region us-central1 \
  --project styleme-475201
```

### View Service Details
```bash
gcloud run services describe styleme-frontend \
  --region us-central1 \
  --project styleme-475201
```

### Get Service URL
```bash
gcloud run services describe styleme-frontend \
  --region us-central1 \
  --format="value(status.url)" \
  --project styleme-475201
```

## Alternative: Cloud Storage + Cloud CDN

For even better performance and lower cost, you could deploy to Cloud Storage with Cloud CDN:

1. Build the frontend: `npm run build`
2. Upload to Cloud Storage bucket
3. Configure Cloud CDN for the bucket
4. Set up custom domain (optional)

This approach is more cost-effective for high-traffic static sites but requires more setup.

## Security Considerations

1. **API Keys**: Never commit `.env.production` with real API keys to git
2. **CORS**: Ensure backend API allows requests from your frontend domain
3. **HTTPS**: Cloud Run automatically provides HTTPS
4. **Authentication**: Consider adding authentication if needed

## Next Steps

- Set up custom domain (optional)
- Configure Cloud CDN for better performance
- Set up monitoring and alerts
- Configure CI/CD pipeline for automatic deployments

