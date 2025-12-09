# Environment Setup Guide

This guide explains how to configure the frontend for different environments (local vs production).

## Environment Files

The frontend uses Vite, which reads environment variables from `.env` files. Vite automatically loads:
- `.env` - Default (loaded in all cases)
- `.env.local` - Local overrides (gitignored, loaded in all cases)
- `.env.production` - Production only (loaded when `npm run build`)

## Quick Setup

### For Local Development

1. Create `.env.local` in the `website/` directory:
   ```bash
   VITE_API_URL=http://localhost:5001
   VITE_OPENAI_API_KEY=your_key_here  # Optional
   ```

2. Start dev server:
   ```bash
   npm run dev
   ```

### For Production Deployment

1. Create `.env.production` in the `website/` directory:
   ```bash
   VITE_API_URL=https://styleme-inference-nty2g5pcpa-uc.a.run.app
   VITE_OPENAI_API_KEY=your_key_here  # Optional
   ```

2. Build and deploy:
   ```bash
   ./scripts/deploy_frontend_cloudrun.sh
   ```

## Environment Variable Priority

When multiple files exist, Vite loads them in this order (later files override earlier ones):
1. `.env`
2. `.env.local`
3. `.env.production` (only during `npm run build`)

## Current Setup

- **Local**: Uses `.env` or `.env.local` → points to `http://localhost:5001`
- **Production**: Uses `.env.production` → points to Cloud Run URL

## Important Notes

⚠️ **Vite environment variables are baked into the build at build time!**

- If you change `.env.production`, you **must rebuild** the frontend
- The built JavaScript files contain the API URL hardcoded
- You cannot change the API URL after deployment without rebuilding

## Switching Between Environments

### Switch to Local Development
```bash
cd website
# Edit .env or .env.local to use localhost
echo "VITE_API_URL=http://localhost:5001" > .env.local
npm run dev
```

### Switch to Production (for testing)
```bash
cd website
# Edit .env.production to use Cloud Run URL
echo "VITE_API_URL=https://styleme-inference-nty2g5pcpa-uc.a.run.app" > .env.production
npm run build
npm run preview  # Test production build locally
```

### Deploy to Cloud
```bash
# The deployment script automatically uses .env.production
./scripts/deploy_frontend_cloudrun.sh
```

## Troubleshooting

### API calls going to wrong URL

1. Check which `.env` file is being used:
   - Development: `.env` or `.env.local`
   - Production build: `.env.production`

2. Verify the file has the correct URL:
   ```bash
   cat .env.local        # For local dev
   cat .env.production   # For production
   ```

3. For production: Rebuild after changing `.env.production`:
   ```bash
   npm run build
   ```

### Environment variables not working

- Make sure variable names start with `VITE_` (Vite requirement)
- Restart dev server after changing `.env` files
- Rebuild after changing `.env.production`

