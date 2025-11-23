import { useState, useEffect } from 'react';
import { HomeScreen } from './components/HomeScreen';
import { WardrobeScreen } from './components/WardrobeScreen';
import { RecommendationScreen } from './components/RecommendationScreen';
import { ItemDetailsScreen } from './components/ItemDetailsScreen';
import { OnboardingScreen } from './components/OnboardingScreen';
import { BottomNavigation } from './components/BottomNavigation';
import { ClothingItem, getWardrobe, uploadImage, getImageUrl } from './services/api';

export default function App() {
  const [activeScreen, setActiveScreen] = useState('onboarding');
  const [items, setItems] = useState<ClothingItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<ClothingItem | null>(null);
  const [userId, setUserId] = useState<string>('default_user');
  const [loading, setLoading] = useState(false);

  // Load wardrobe on mount and when userId changes
  useEffect(() => {
    if (userId && activeScreen !== 'onboarding') {
      loadWardrobe();
    }
  }, [userId, activeScreen]);

  const loadWardrobe = async () => {
    try {
      setLoading(true);
      const response = await getWardrobe(userId);
      // Convert dateAdded from timestamp to Date if needed and fix image URLs
      const formattedItems = response.items.map(item => ({
        ...item,
        dateAdded: typeof item.dateAdded === 'number' 
          ? new Date(item.dateAdded * 1000) 
          : new Date(item.dateAdded),
        image: getImageUrl(item.image) // Convert relative paths to full URLs
      }));
      setItems(formattedItems);
    } catch (error) {
      console.error('Failed to load wardrobe:', error);
      // Keep empty array on error
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigate = (screen: string) => {
    setActiveScreen(screen);
  };

  const handleSelectItem = (item: ClothingItem) => {
    setSelectedItem(item);
    setActiveScreen('item-details');
  };

  const handleCompleteLook = (item: ClothingItem) => {
    setSelectedItem(item);
    setActiveScreen('recommend');
  };
  
  const handleDeleteItem = (id: string) => {
    setItems(items.filter(i => i.id !== id));
    setActiveScreen('wardrobe');
  };

  const handleAddItem = async (file: File) => {
    try {
      setLoading(true);
      await uploadImage(userId, file);
      // Reload wardrobe after upload
      await loadWardrobe();
    } catch (error) {
      console.error('Failed to upload image:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGetStarted = () => {
    // For now, use a default user ID
    // In production, this would come from authentication
    setUserId('default_user');
    setActiveScreen('home');
  };

  const renderScreen = () => {
    switch (activeScreen) {
      case 'onboarding':
        return <OnboardingScreen onGetStarted={handleGetStarted} />;
      case 'home':
        return (
          <HomeScreen 
            items={items} 
            userId={userId}
            onAddItem={handleAddItem}
            onItemClick={handleSelectItem}
          />
        );
      case 'wardrobe':
        return (
          <WardrobeScreen 
            items={items} 
            onItemClick={handleSelectItem}
          />
        );
      case 'recommend':
        return (
          <RecommendationScreen 
            items={items} 
            userId={userId}
            selectedItem={selectedItem}
            onSelectItem={(item) => setSelectedItem(item)}
          />
        );
      case 'item-details':
         if (!selectedItem) return <HomeScreen items={items} onAddItem={handleAddItem} onItemClick={handleSelectItem} />;
         return (
            <ItemDetailsScreen 
              item={selectedItem} 
              onBack={() => setActiveScreen('wardrobe')}
              onCompleteTheLook={handleCompleteLook}
              onDelete={handleDeleteItem}
            />
         );
      default:
        return <HomeScreen items={items} onAddItem={handleAddItem} onItemClick={handleSelectItem} />;
    }
  };

  const showBottomNav = activeScreen !== 'onboarding' && activeScreen !== 'item-details';

  return (
    <div className="h-screen w-full max-w-md mx-auto bg-gray-50 flex flex-col overflow-hidden">
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto hide-scrollbar">
        {renderScreen()}
      </div>
      
      {/* Bottom Navigation */}
      {showBottomNav && (
        <BottomNavigation 
          activeScreen={activeScreen} 
          onScreenChange={setActiveScreen} 
        />
      )}
    </div>
  );
}
