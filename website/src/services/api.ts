/**
 * API Client for StyleMe Backend
 * Handles all API calls to the inference service
 */

// Note: Docker maps container port 5000 to host port 5001
// If running API server directly (not in Docker), use port 5000
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

export interface ClothingItem {
  id: string;
  image: string;
  filename?: string;  // Filename for deletion
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
  image: File | string,
  metadata?: {
    category?: string;
    color?: string;
    style?: string;
    material?: string;
    pattern?: string;
    season?: string;
    occasion?: string;
    description?: string;
  }
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('user_id', userId);
  
  try {
    if (typeof image === 'string') {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          image: image,
          metadata: metadata || {},
        }),
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to upload image';
        try {
          const error = await response.json();
          errorMessage = error.error || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      return response.json();
    } else {
      formData.append('file', image);
      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata));
      }
      
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to upload image';
        try {
          const error = await response.json();
          errorMessage = error.error || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      return response.json();
    }
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to server. Please make sure the API server is running on ' + API_BASE_URL);
    }
    throw error;
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
      let errorMessage = 'Failed to get recommendations';
      try {
        const error = await response.json();
        errorMessage = error.error || error.message || errorMessage;
        // Handle specific error messages
        if (errorMessage.includes('No trained model') || errorMessage.includes('train')) {
          errorMessage = 'No trained model found. Please train a model first.';
        }
        // Include hint if available
        if (error.hint) {
          errorMessage += ` ${error.hint}`;
        }
      } catch (e) {
        errorMessage = `Server error: ${response.status} ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    
    // Check if response indicates an error even with 200 status
    if (data.error) {
      throw new Error(data.error);
    }
    
    return data;
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
      let errorMessage = 'Failed to get recommendations';
      try {
        const error = await response.json();
        errorMessage = error.error || error.message || errorMessage;
        // Handle specific error messages
        if (errorMessage.includes('No trained model') || errorMessage.includes('train')) {
          errorMessage = 'No trained model found. Please train a model first.';
        }
        // Include hint if available
        if (error.hint) {
          errorMessage += ` ${error.hint}`;
        }
      } catch (e) {
        errorMessage = `Server error: ${response.status} ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    
    // Check if response indicates an error even with 200 status
    if (data.error) {
      throw new Error(data.error);
    }
    
    return data;
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
  
  const data = await response.json();
  
  // Helper function to normalize category - prioritize shoes and dresses
  const normalizeCategory = (category: string): string => {
    if (!category || category.trim() === '' || category === 'Unknown' || category === 'OTHER') {
      return 'tops';
    }
    const lower = category.toLowerCase().trim();
    const FIXED_CATEGORIES = ['tops', 'bottoms', 'layers', 'shoes', 'dresses', 'accessories'];
    
    // Direct exact matches
    for (const cat of FIXED_CATEGORIES) {
      if (lower === cat.toLowerCase()) {
        return cat.toLowerCase();
      }
    }
    
    // Direct mapping
    if (lower === 'shirt' || lower === 'shirts' || lower === 'top' || lower === 'tops') return 'tops';
    if (lower === 'pants' || lower === 'pant' || lower === 'bottom' || lower === 'bottoms') return 'bottoms';
    if (lower === 'dress' || lower === 'dresses') return 'dresses';
    if (lower === 'jacket' || lower === 'jackets' || lower === 'layer' || lower === 'layers') return 'layers';
    if (lower === 'shoes' || lower === 'shoe') return 'shoes';
    if (lower === 'accessories' || lower === 'accessory') return 'accessories';
    
    // Pattern matches - prioritize shoes FIRST
    if (lower.includes('boot') || lower.includes('sneaker') || lower.includes('sandal') || 
        lower.includes('heel') || lower.includes('flat') || lower.includes('shoe') ||
        lower.includes('slipper') || lower.includes('loafer') || lower.includes('pump') ||
        lower.includes('oxford') || lower.includes('moccasin') || lower.includes('clog')) {
      return 'shoes';
    }
    // Check dress BEFORE top
    if (lower.includes('dress') && !lower.includes('undress') && !lower.includes('address')) {
      return 'dresses';
    }
    if (lower.includes('shirt') || lower.includes('top') || lower.includes('blouse') || 
        lower.includes('t-shirt') || lower.includes('tee') || lower.includes('tank')) {
      return 'tops';
    }
    if (lower.includes('pant') || lower.includes('jean') || lower.includes('trouser') || 
        lower.includes('short') || lower.includes('legging') || lower.includes('bottom')) {
      return 'bottoms';
    }
    if (lower.includes('jacket') || lower.includes('coat') || lower.includes('blazer') || 
        lower.includes('cardigan') || lower.includes('sweater') || lower.includes('hoodie') || 
        lower.includes('vest') || lower.includes('outerwear') || lower.includes('layer')) {
      return 'layers';
    }
    if (lower.includes('accessory') || lower.includes('bag') || lower.includes('hat') || 
        lower.includes('scarf') || lower.includes('belt') || lower.includes('jewelry')) {
      return 'accessories';
    }
    return 'tops';
  };

  // Helper function to normalize color - prioritize brown/beige/green before white
  const normalizeColor = (color: string): string => {
    if (!color || color.trim() === '') {
      return 'White';
    }
    const lower = color.toLowerCase().trim();
    const FIXED_COLORS = ['Black', 'White', 'Gray', 'Beige', 'Brown', 'Navy', 'Blue', 
      'Green', 'Red', 'Pink', 'Purple', 'Yellow', 'Orange', 'Cream', 'Khaki'];
    
    // Direct exact matches
    for (const col of FIXED_COLORS) {
      if (lower === col.toLowerCase()) {
        return col;
      }
    }
    
    // Pattern matches - prioritize green/brown/beige BEFORE white
    if (lower.includes('green') || lower.includes('emerald') || lower.includes('forest') || 
        lower.includes('olive') || lower.includes('sage') || lower.includes('mint') ||
        lower.includes('lime') || lower.includes('teal') || lower.includes('jade')) return 'Green';
    if (lower.includes('maroon') || lower.includes('burgundy') || lower.includes('crimson') ||
        lower.includes('wine') || lower.includes('cherry') || (lower.includes('dark') && lower.includes('red'))) return 'Red';
    if (lower.includes('black') || lower.includes('ebony') || lower.includes('charcoal')) return 'Black';
    // Check brown/beige BEFORE white
    if (lower.includes('brown') || lower.includes('chocolate') || lower.includes('coffee') ||
        lower.includes('caramel') || lower.includes('taupe') || lower.includes('camel') ||
        lower.includes('suede') || lower.includes('leather')) return 'Brown';
    if (lower.includes('beige') || lower.includes('tan') || lower.includes('nude') ||
        lower.includes('sand') || lower.includes('cream')) return 'Beige';
    // Check white AFTER brown/beige/green
    if (lower.includes('white') || lower.includes('ivory') || lower.includes('snow')) return 'White';
    if (lower.includes('gray') || lower.includes('grey') || lower.includes('silver')) return 'Gray';
    if (lower.includes('navy') || (lower.includes('dark') && lower.includes('blue'))) return 'Navy';
    if (lower.includes('blue') && !lower.includes('navy')) return 'Blue';
    if (lower.includes('red') || lower.includes('scarlet') || lower.includes('ruby')) return 'Red';
    if (lower.includes('pink') || lower.includes('rose') || lower.includes('salmon') ||
        lower.includes('magenta') || lower.includes('fuchsia')) return 'Pink';
    if (lower.includes('purple') || lower.includes('violet') || lower.includes('lavender') ||
        lower.includes('plum') || lower.includes('mauve')) return 'Purple';
    if (lower.includes('yellow') || lower.includes('gold') || lower.includes('lemon') ||
        lower.includes('amber')) return 'Yellow';
    if (lower.includes('orange') || lower.includes('coral') || lower.includes('peach') ||
        lower.includes('tangerine')) return 'Orange';
    if (lower.includes('khaki')) return 'Khaki';
    return 'White';
  };

  // Merge metadata - prioritize backend metadata, fallback to localStorage
  const itemsWithMetadata = data.items.map((item: ClothingItem) => {
    // Extract filename from image path
    const imagePath = item.image;
    const filename = imagePath.split('/').pop() || '';
    
    // Use backend metadata if available (from JSON file)
    if (item.category && item.category !== 'Unknown' && (item as any).style) {
      // Backend has metadata, use it
      const normalizedCategory = normalizeCategory(item.category || 'tops');
      const normalizedColor = normalizeColor(item.color || 'White');
      return {
        ...item,
        category: normalizedCategory,
        color: normalizedColor,
        style: (item as any).style || 'Casual',
        material: (item as any).material || '',
        pattern: (item as any).pattern || '',
      };
    }
    
    // Fallback to localStorage if backend doesn't have metadata
    try {
      const metadataKey = `wardrobe_metadata_${userId}_${filename}`;
      const metadataStr = localStorage.getItem(metadataKey);
      if (metadataStr) {
        const metadata = JSON.parse(metadataStr);
        // Normalize category and color to ensure they match our fixed categories/colors
        const normalizedCategory = normalizeCategory(metadata.category || item.category || 'tops');
        const normalizedColor = normalizeColor(metadata.color || item.color || 'White');
        return {
          ...item,
          category: normalizedCategory,
          color: normalizedColor,
          style: metadata.style || 'Casual',
          material: metadata.material || '',
          pattern: metadata.pattern || '',
        };
      }
    } catch (e) {
      console.warn('Failed to load metadata for item:', e);
    }
    
    // If no metadata found, normalize and ensure all three tags exist with fallback values
    const normalizedCategory = normalizeCategory(
      item.category === 'Unknown' || item.category === 'OTHER' || !item.category 
        ? 'tops' 
        : item.category
    );
    const normalizedColor = normalizeColor(
      item.color === 'Unknown' || !item.color 
        ? 'White' 
        : item.color
    );
    return {
      ...item,
      category: normalizedCategory,
      color: normalizedColor,
      style: (item as any).style || 'Casual',
    };
  });
  
  return {
    ...data,
    items: itemsWithMetadata,
  };
}

/**
 * Delete a wardrobe item (image and metadata)
 */
export async function deleteWardrobeItem(userId: string, filename: string): Promise<{ success: boolean; message: string }> {
  // URL encode the filename to handle special characters
  const encodedFilename = encodeURIComponent(filename);
  
  console.log('Deleting item:', { userId, filename, encodedFilename, apiUrl: `${API_BASE_URL}/api/wardrobe/${userId}/item/${encodedFilename}` });
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/wardrobe/${userId}/item/${encodedFilename}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: `HTTP ${response.status}: ${response.statusText}` }));
      console.error('Delete failed:', error);
      throw new Error(error.error || error.message || `Failed to delete item: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error('Network error:', error);
      throw new Error(`Cannot connect to server at ${API_BASE_URL}. Please make sure the API server is running.`);
    }
    throw error;
  }
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

