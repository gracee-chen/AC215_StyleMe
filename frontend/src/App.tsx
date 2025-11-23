import { useState } from 'react';
import { HomeScreen } from './components/HomeScreen';
import { WardrobeScreen } from './components/WardrobeScreen';
import { RecommendationScreen } from './components/RecommendationScreen';
import { ItemDetailsScreen } from './components/ItemDetailsScreen';
import { OnboardingScreen } from './components/OnboardingScreen';
import { BottomNavigation } from './components/BottomNavigation';
import { initialItems, ClothingItem } from './components/mockData';

export default function App() {
  const [activeScreen, setActiveScreen] = useState('onboarding');
  const [items, setItems] = useState<ClothingItem[]>(initialItems);
  const [selectedItem, setSelectedItem] = useState<ClothingItem | null>(null);

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

  const handleAddItem = (newItem: any) => {
     // In a real app, this would handle file upload
     // For now, we'll simulate adding an item
     const item: ClothingItem = {
         id: Math.random().toString(36).substr(2, 9),
         image: "https://images.unsplash.com/photo-1551488852-0801464bdd52?auto=format&fit=crop&q=80&w=500", // Placeholder
         category: 'Tops',
         color: 'New Color',
         dateAdded: new Date()
     };
     setItems([item, ...items]);
  };

  const renderScreen = () => {
    switch (activeScreen) {
      case 'onboarding':
        return <OnboardingScreen onGetStarted={() => setActiveScreen('home')} />;
      case 'home':
        return (
          <HomeScreen 
            items={items} 
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
