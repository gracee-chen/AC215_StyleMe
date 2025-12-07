# Frontend Replacement Guide

## Overview

This guide explains how to replace the current frontend with a new website version while maintaining the Cloud Run backend connection.

---

## Current Frontend Location

The frontend code is located in:
```
/home/chufeip/styleme12.0/frontend/
```

**Key Files:**
- `frontend/src/services/api.ts` - API client configuration
- `frontend/.env` - Environment variables (API URL)
- `frontend/src/App.tsx` - Main application component
- `frontend/src/components/` - All React components

---

## Step 1: Backup Current Frontend (Optional)

```bash
cd /home/chufeip/styleme12.0
cp -r frontend frontend.backup
```

---

## Step 2: Replace Frontend Code

You have two options:

### Option A: Replace Entire Frontend Directory

```bash
# Stop the current dev server (Ctrl+C if running)

# Remove old frontend
cd /home/chufeip/styleme12.0
rm -rf frontend/*

# Copy your new website version
cp -r /path/to/your/new/frontend/* frontend/
```

### Option B: Replace Specific Components

If you want to keep some structure, you can replace specific files:
- Replace `frontend/src/` with your new source code
- Keep `frontend/package.json` and dependencies (or update as needed)
- Keep configuration files like `vite.config.ts`

---

## Step 3: Configure API Connection

### Update API URL

The frontend connects to Cloud Run via environment variable. You need to configure this in your new frontend:

**Option 1: Using .env file (Recommended)**

Create or update `frontend/.env`:
```bash
cd frontend
echo "VITE_API_URL=https://styleme-inference-nty2g5pcpa-uc.a.run.app" > .env
```

**Option 2: Update API client directly**

If your new frontend has a different structure, find where it configures the API base URL and set it to:
```
https://styleme-inference-nty2g5pcpa-uc.a.run.app
```

**Current API Configuration:**
- File: `frontend/src/services/api.ts`
- Line 6: `const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';`

---

## Step 4: Update Dependencies (If Needed)

```bash
cd frontend
npm install
```

---

## Step 5: Test the Connection

1. **Verify API URL is set correctly:**
   ```bash
   cd frontend
   cat .env
   # Should show: VITE_API_URL=https://styleme-inference-nty2g5pcpa-uc.a.run.app
   ```

2. **Test Cloud Run backend:**
   ```bash
   curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health
   # Should return: {"status":"healthy","service":"StyleMe Inference API"}
   ```

3. **Start dev server:**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Test in browser:**
   - Open http://localhost:3000
   - Check browser console (F12) for API connection
   - Test uploading images
   - Test getting recommendations

---

## API Endpoints Your Frontend Should Use

Your new frontend needs to call these endpoints:

### Base URL
```
https://styleme-inference-nty2g5pcpa-uc.a.run.app
```

### Available Endpoints

1. **Health Check**
   - `GET /health`
   - Returns: `{"status":"healthy","service":"StyleMe Inference API"}`

2. **Upload Image**
   - `POST /api/upload`
   - Body: `{"user_id": "string", "image": "base64_string"}` or multipart/form-data
   - Returns: Upload confirmation

3. **Get Recommendations**
   - `POST /api/recommend`
   - Body: `{"user_id": "string", "image": "base64_string", "threshold": 0.7, "wardrobe_k": 5, "catalog_k": 3, "gender": "men"|"women"}`
   - Returns: List of recommended items

4. **Get Wardrobe**
   - `GET /api/wardrobe/<user_id>`
   - Returns: List of wardrobe items

5. **Get Wardrobe Image**
   - `GET /api/wardrobe/<user_id>/image/<filename>`
   - Returns: Image file

See `docs/api_integration.md` for detailed API documentation.

---

## Environment Variables Reference

### Required for Frontend

- **`VITE_API_URL`** - Backend API URL
  - Staging/Testing: `https://styleme-inference-nty2g5pcpa-uc.a.run.app`
  - Production: Same URL (or update as needed)

### How to Set

1. **Development (.env file):**
   ```bash
   echo "VITE_API_URL=https://styleme-inference-nty2g5pcpa-uc.a.run.app" > frontend/.env
   ```

2. **Production Build:**
   - Set environment variable before build
   - Or update in your hosting platform's environment settings

---

## Important Notes

1. **CORS is enabled** - The Cloud Run API server has CORS enabled, so your frontend can make requests from any domain.

2. **HTTPS Required** - Cloud Run uses HTTPS, so make sure your frontend makes HTTPS requests (not HTTP).

3. **Environment Variables** - Vite requires `VITE_` prefix for environment variables to be exposed to client-side code.

4. **API Client** - Your new frontend needs to make HTTP requests to the endpoints listed above. You can use:
   - `fetch()` API (native JavaScript)
   - `axios` library
   - Or any HTTP client library

---

## Troubleshooting

### Frontend can't connect to API

1. Check `.env` file has correct URL:
   ```bash
   cat frontend/.env
   ```

2. Check Cloud Run is accessible:
   ```bash
   curl https://styleme-inference-nty2g5pcpa-uc.a.run.app/health
   ```

3. Check browser console for CORS errors

### API calls failing

1. Verify endpoint URLs are correct
2. Check request format matches API documentation
3. Check Cloud Run logs:
   ```bash
   gcloud run services logs read styleme-inference --region us-central1
   ```

---

## Quick Start Checklist

- [ ] Backup current frontend (optional)
- [ ] Copy new frontend code to `frontend/` directory
- [ ] Create/update `.env` file with Cloud Run URL
- [ ] Install dependencies: `npm install`
- [ ] Test API connection
- [ ] Start dev server: `npm run dev`
- [ ] Test all features in browser
- [ ] Update API client code if needed

---

## Cloud Run Backend Information

- **Service Name**: `styleme-inference`
- **Region**: `us-central1`
- **URL**: `https://styleme-inference-nty2g5pcpa-uc.a.run.app`
- **Status**: ✅ Running and accessible

