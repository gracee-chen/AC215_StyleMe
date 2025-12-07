import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';
import { HomeScreen } from '@/components/app/HomeScreen';
import { WardrobeScreen } from '@/components/app/WardrobeScreen';
import { ItemDetailsScreen } from '@/components/app/ItemDetailsScreen';
import { ChatScreen } from '@/components/app/ChatScreen';
import { BottomNavigation } from '@/components/app/BottomNavigation';
import { ClothingItem, getWardrobe, uploadImage, getImageUrl } from '@/services/api';

// Create context for sharing state
interface AppContextType {
  items: ClothingItem[];
  selectedItem: ClothingItem | null;
  setSelectedItem: (item: ClothingItem | null) => void;
  userId: string;
  loadWardrobe: () => Promise<void>;
  handleAddItem: (file: File) => Promise<void>;
  handleDeleteItem: (id: string) => void;
}

const AppContext = createContext<AppContextType | null>(null);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppLayout');
  }
  return context;
};

// Normalize category to fixed categories - ensure shoes and dresses are prioritized
function normalizeCategory(category: string): string {
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
}

// Normalize color to fixed colors - ensure brown/beige/green are prioritized before white
function normalizeColor(color: string): string {
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
}

export default function AppLayout() {
  const location = useLocation();
  const [items, setItems] = useState<ClothingItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<ClothingItem | null>(null);
  const [userId] = useState<string>('default_user');
  const [loading, setLoading] = useState(false);

  // Load wardrobe on mount
  useEffect(() => {
    loadWardrobe();
  }, []);

  const loadWardrobe = async () => {
    try {
      setLoading(true);
      const response = await getWardrobe(userId);
      
      // Get latest metadata if available (for newly uploaded items)
      const latestMetadataKey = `wardrobe_metadata_${userId}_latest`;
      let latestMetadata = null;
      try {
        const latestStr = localStorage.getItem(latestMetadataKey);
        if (latestStr) {
          latestMetadata = JSON.parse(latestStr);
          console.log('Found latest metadata:', latestMetadata);
        }
      } catch (e) {
        console.warn('Failed to parse latest metadata:', e);
      }
      
      const formattedItems = response.items.map((item, index) => {
        // Extract filename from image path
        const imagePath = item.image;
        const filename = imagePath.split('/').pop() || '';
        
        // If this is the newest item (last in array) and we have latest metadata, apply it
        if (latestMetadata && index === response.items.length - 1) {
          // Normalize category and color to ensure they match our fixed categories/colors
          const normalizedCategory = normalizeCategory(latestMetadata.category || item.category || 'tops');
          const normalizedColor = normalizeColor(latestMetadata.color || item.color || 'White');
          
          // Save metadata with filename key for future loads (with normalized values)
          const metadataKey = `wardrobe_metadata_${userId}_${filename}`;
          const normalizedMetadata = {
            ...latestMetadata,
            category: normalizedCategory,
            color: normalizedColor,
          };
          localStorage.setItem(metadataKey, JSON.stringify(normalizedMetadata));
          
          // Clear latest key after use
          localStorage.removeItem(latestMetadataKey);
          
          console.log('Applied latest metadata to item:', filename, {
            original: latestMetadata,
            normalized: normalizedMetadata
          });
          
          return {
            ...item,
            category: normalizedCategory,
            color: normalizedColor,
            style: latestMetadata.style || 'Casual',
            material: latestMetadata.material || '',
            pattern: latestMetadata.pattern || '',
            dateAdded: typeof item.dateAdded === 'number' 
              ? new Date(item.dateAdded * 1000) 
              : new Date(item.dateAdded),
            image: getImageUrl(item.image)
          };
        }
        
        // For existing items, try to load metadata from localStorage
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
              dateAdded: typeof item.dateAdded === 'number' 
                ? new Date(item.dateAdded * 1000) 
                : new Date(item.dateAdded),
              image: getImageUrl(item.image)
            };
          }
        } catch (e) {
          console.warn('Failed to load metadata for item:', filename, e);
        }
        
        // Default: ensure all three tags exist with fallback values
        // Normalize category and color to ensure they match our fixed categories/colors
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
          dateAdded: typeof item.dateAdded === 'number' 
            ? new Date(item.dateAdded * 1000) 
            : new Date(item.dateAdded),
          image: getImageUrl(item.image)
        };
      });
      
      setItems(formattedItems);
    } catch (error) {
      console.error('Failed to load wardrobe:', error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectItem = (item: ClothingItem) => {
    setSelectedItem(item);
  };

  const handleCompleteLook = (item: ClothingItem) => {
    setSelectedItem(item);
  };
  
  const handleDeleteItem = (id: string) => {
    setItems(items.filter(i => i.id !== id));
    if (selectedItem?.id === id) {
      setSelectedItem(null);
    }
  };

  const handleAddItem = async (file: File, addToWardrobe: boolean) => {
    if (!addToWardrobe) return; // Only add to wardrobe if user selected to
    try {
      setLoading(true);
      await uploadImage(userId, file);
      await loadWardrobe();
    } catch (error) {
      console.error('Failed to upload image:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const contextValue: AppContextType = {
    items,
    selectedItem,
    setSelectedItem,
    userId,
    loadWardrobe,
    handleAddItem,
    handleDeleteItem,
  };

  const showBottomNav = !location.pathname.includes('/item-details');

  return (
    <AppContext.Provider value={contextValue}>
      <div className="min-h-screen bg-stone-50">
        <Routes>
          <Route
            path="home"
            element={
              <HomeScreen 
                items={items} 
                userId={userId}
                onAddItem={handleAddItem}
                onItemClick={handleSelectItem}
              />
            }
          />
          <Route
            path="wardrobe"
            element={
              <WardrobeScreen 
                items={items} 
                onItemClick={handleSelectItem}
                userId={userId}
                onAddItem={handleAddItem}
              />
            }
          />
          <Route
            path="chat"
            element={<ChatScreen />}
          />
          <Route
            path="item-details"
            element={
              selectedItem ? (
                <ItemDetailsScreen 
                  item={selectedItem} 
                  onBack={() => window.history.back()}
                  onCompleteTheLook={handleCompleteLook}
                  onDelete={handleDeleteItem}
                />
              ) : (
                <Navigate to="/app/home" replace />
              )
            }
          />
          <Route path="*" element={<Navigate to="/app/home" replace />} />
        </Routes>
        
        {showBottomNav && <BottomNavigation />}
      </div>
    </AppContext.Provider>
  );
}

