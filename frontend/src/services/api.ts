/**
 * API Client for StyleMe Backend
 * Handles all API calls to the inference service
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export interface ClothingItem {
  id: string;
  image: string;
  category: string;
  color: string;
  dateAdded: Date | number;
  title?: string;
  brand?: string;
  price?: string;
  url?: string;
  similarity?: number;
  rank?: number;
}

export interface RecommendationResponse {
  success: boolean;
  user_id: string;
  used_wardrobe: boolean;
  items: ClothingItem[];
  num_results: number;
  threshold: number;
}

export interface WardrobeResponse {
  success: boolean;
  user_id: string;
  items: ClothingItem[];
  num_items: number;
}

export interface UploadResponse {
  success: boolean;
  user_id: string;
  image_path: string;
  message: string;
}

/**
 * Convert file to base64 string
 */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result);
      } else {
        reject(new Error('Failed to convert file to base64'));
      }
    };
    reader.onerror = (error) => reject(error);
  });
}

/**
 * Health check endpoint
 */
export async function healthCheck(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}

/**
 * Upload an image to user's wardrobe
 */
export async function uploadImage(
  userId: string,
  image: File | string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('user_id', userId);
  
  if (typeof image === 'string') {
    // Base64 string
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        image: image,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to upload image');
    }
    
    return response.json();
  } else {
    // File object
    formData.append('file', image);
    
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to upload image');
    }
    
    return response.json();
  }
}

/**
 * Get recommendations for a query image
 */
export async function getRecommendations(
  userId: string,
  image: File | string,
  options?: {
    threshold?: number;
    wardrobe_k?: number;
    catalog_k?: number;
    gender?: 'men' | 'women';
  }
): Promise<RecommendationResponse> {
  const formData = new FormData();
  formData.append('user_id', userId);
  
  if (typeof image === 'string') {
    // Base64 string
    const response = await fetch(`${API_BASE_URL}/api/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        image: image,
        threshold: options?.threshold || 0.7,
        wardrobe_k: options?.wardrobe_k || 5,
        catalog_k: options?.catalog_k || 3,
        gender: options?.gender,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get recommendations');
    }
    
    return response.json();
  } else {
    // File object
    formData.append('file', image);
    if (options?.threshold) formData.append('threshold', options.threshold.toString());
    if (options?.wardrobe_k) formData.append('wardrobe_k', options.wardrobe_k.toString());
    if (options?.catalog_k) formData.append('catalog_k', options.catalog_k.toString());
    if (options?.gender) formData.append('gender', options.gender);
    
    const response = await fetch(`${API_BASE_URL}/api/recommend`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get recommendations');
    }
    
    return response.json();
  }
}

/**
 * Get user's wardrobe items
 */
export async function getWardrobe(userId: string): Promise<WardrobeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/wardrobe/${userId}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get wardrobe');
  }
  
  return response.json();
}

/**
 * Rebuild wardrobe index for a user
 */
export async function rebuildWardrobeIndex(userId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/wardrobe/${userId}/rebuild`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to rebuild wardrobe index');
  }
  
  return response.json();
}

/**
 * Get wardrobe image URL
 */
export function getWardrobeImageUrl(userId: string, filename: string): string {
  return `${API_BASE_URL}/api/wardrobe/${userId}/image/${filename}`;
}

/**
 * Convert relative image path to full URL
 */
export function getImageUrl(imagePath: string): string {
  if (imagePath.startsWith('http')) {
    return imagePath;
  }
  if (imagePath.startsWith('/api/')) {
    return `${API_BASE_URL}${imagePath}`;
  }
  return imagePath;
}

