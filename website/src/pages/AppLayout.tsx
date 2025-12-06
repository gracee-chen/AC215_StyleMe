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
          // Save metadata with filename key for future loads
          const metadataKey = `wardrobe_metadata_${userId}_${filename}`;
          localStorage.setItem(metadataKey, JSON.stringify(latestMetadata));
          
          // Clear latest key after use
          localStorage.removeItem(latestMetadataKey);
          
          console.log('Applied latest metadata to item:', filename, latestMetadata);
          
          return {
            ...item,
            category: latestMetadata.category || item.category || 'tops',
            color: latestMetadata.color || item.color || 'White',
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
            return {
              ...item,
              category: metadata.category || item.category || 'tops',
              color: metadata.color || item.color || 'White',
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
        // This ensures every item has complete tags and will be displayed
        return {
          ...item,
          category: item.category === 'Unknown' || item.category === 'OTHER' || !item.category 
            ? 'tops'  // Use valid category instead of 'OTHER'
            : item.category,
          color: item.color === 'Unknown' || !item.color 
            ? 'White'  // Use valid color instead of 'Unknown'
            : item.color,
          style: (item as any).style || 'Casual',  // Always ensure style exists
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

