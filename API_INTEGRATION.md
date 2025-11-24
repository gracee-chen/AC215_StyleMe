# API & Frontend Integration - Implementation Summary

## Overview
This document describes the implementation of APIs that connect the backend services (model, database, data pipeline) to the frontend, and the frontend interface that consumes these APIs.

## Backend API Implementation

### Flask API Server (`containers/inference/api_server.py`)
A Flask-based REST API server that wraps the existing `InferenceService` and provides HTTP endpoints for the frontend.

#### Key Features:
- **CORS enabled** for frontend communication
- **Image upload support** (base64 and multipart/form-data)
- **RESTful endpoints** for all major operations
- **Error handling** with proper HTTP status codes
- **Image serving** for wardrobe items

#### API Endpoints:

1. **GET `/health`**
   - Health check endpoint
   - Returns: `{status: 'healthy', service: 'StyleMe Inference API'}`

2. **POST `/api/upload`**
   - Upload an image to user's wardrobe
   - Body: `{user_id: string, image: base64_string}` or multipart/form-data
   - Returns: Upload confirmation with image path

3. **POST `/api/recommend`**
   - Get recommendations for a query image
   - Body: `{user_id: string, image: base64_string, threshold?: number, wardrobe_k?: number, catalog_k?: number, gender?: string}`
   - Returns: List of recommended items with metadata

4. **GET `/api/wardrobe/<user_id>`**
   - Get user's wardrobe items
   - Returns: List of wardrobe items with metadata

5. **GET `/api/wardrobe/<user_id>/image/<filename>`**
   - Serve wardrobe images
   - Returns: Image file

6. **POST `/api/wardrobe/<user_id>/rebuild`**
   - Rebuild wardrobe index for a user
   - Returns: Success confirmation

### Docker Configuration
- Updated `docker-compose.yml` to expose API on port 5000
- Added `RUN_API_SERVER` environment variable
- Updated entrypoint script to support API server mode

### Dependencies
Added to `containers/inference/requirements.txt`:
- `flask>=2.3.0`
- `flask-cors>=4.0.0`
- `werkzeug>=2.3.0`

## Frontend Implementation

### API Client (`frontend/src/services/api.ts`)
A TypeScript service module that provides type-safe API calls to the backend.

#### Key Features:
- **Type-safe interfaces** for all API responses
- **Base64 conversion** utilities for image handling
- **Error handling** with proper error messages
- **URL normalization** for image paths

#### Functions:
- `healthCheck()` - Check API health
- `uploadImage(userId, image)` - Upload image to wardrobe
- `getRecommendations(userId, image, options)` - Get style recommendations
- `getWardrobe(userId)` - Get user's wardrobe
- `rebuildWardrobeIndex(userId)` - Rebuild wardrobe index
- `getImageUrl(imagePath)` - Convert relative paths to full URLs
- `fileToBase64(file)` - Convert File to base64 string

### Updated Components

#### App.tsx
- Integrated API calls for wardrobe loading
- Added user ID state management
- Implemented image upload handling
- Added loading states

#### HomeScreen.tsx
- Integrated UploadScreen component
- Updated to use API types instead of mock data
- Added proper file upload handling

#### UploadScreen.tsx
- Complete rewrite to handle actual file uploads
- Support for camera and gallery selection
- Image preview functionality
- Upload progress and success states
- Integration with API upload endpoint

#### RecommendationScreen.tsx
- Integrated with recommendation API
- Real-time recommendation loading
- Error handling and retry functionality
- Loading states and progress indicators
- Displays similarity scores

#### WardrobeScreen.tsx
- Updated to use API types
- Displays real wardrobe items from API

#### ItemDetailsScreen.tsx
- Updated to use API types
- Maintains existing functionality

## Data Flow

### Image Upload Flow:
```
User selects image
  ↓
UploadScreen converts to File/Base64
  ↓
POST /api/upload
  ↓
Backend saves to wardrobes/{user_id}/images/
  ↓
Frontend reloads wardrobe
```

### Recommendation Flow:
```
User selects item from wardrobe
  ↓
RecommendationScreen loads item image
  ↓
POST /api/recommend with image
  ↓
Backend InferenceService processes:
  - Generates embedding
  - Searches wardrobe index
  - Falls back to catalog if needed
  ↓
Returns formatted recommendations
  ↓
Frontend displays results
```

## Configuration

### Environment Variables

**Backend:**
- `PORT` - API server port (default: 5000)
- `FLASK_DEBUG` - Debug mode (default: false)
- `RUN_API_SERVER` - Enable API server mode (default: false)

**Frontend:**
- `VITE_API_URL` - Backend API URL (default: http://localhost:5000)

## Running the System

### Start Backend API:
```bash
# Using docker-compose
docker-compose --profile api up inference

# Or set environment variable
RUN_API_SERVER=true docker-compose up inference
```

### Start Frontend:
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`
The API will be available at `http://localhost:5000`

## Testing the Integration

1. **Upload an image:**
   - Navigate to Home screen
   - Click "ADD ITEM"
   - Select image from camera or gallery
   - Image should upload and appear in wardrobe

2. **Get recommendations:**
   - Select an item from wardrobe
   - Click "Complete the Look"
   - Recommendations should load and display

3. **View wardrobe:**
   - Navigate to Wardrobe tab
   - Should see all uploaded items

## Next Steps / Improvements

1. **Authentication**: Add user authentication system
2. **Image Optimization**: Compress images before upload
3. **Caching**: Cache recommendations to reduce API calls
4. **Error Recovery**: Better error messages and recovery flows
5. **Loading States**: More granular loading indicators
6. **Image Preview**: Better image preview in upload flow
7. **Batch Upload**: Support multiple image uploads at once

