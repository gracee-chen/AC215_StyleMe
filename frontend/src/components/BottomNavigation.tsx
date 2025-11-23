import { Home, Shirt, Sparkles } from 'lucide-react';

interface BottomNavigationProps {
  activeScreen: string;
  onScreenChange: (screen: string) => void;
}

export function BottomNavigation({ activeScreen, onScreenChange }: BottomNavigationProps) {
  const navItems = [
    { id: 'wardrobe', icon: Shirt, label: 'Wardrobe' },
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'recommend', icon: Sparkles, label: 'Recommend' },
  ];

  return (
    <div className="bg-white border-t border-gray-100 pb-safe pt-2 px-6">
      <div className="flex justify-between items-center">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeScreen === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onScreenChange(item.id)}
              className={`flex flex-col items-center p-2 rounded-xl transition-all duration-200 w-20 ${
                isActive
                  ? 'text-gray-900'
                  : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-[10px] font-medium mt-1 ${isActive ? 'text-gray-900' : 'text-gray-400'}`}>
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
