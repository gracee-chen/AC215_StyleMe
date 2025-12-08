import { Sparkles, Shirt, ArrowLeft, MessageCircle } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

export function BottomNavigation() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const getActiveScreen = () => {
    const path = location.pathname;
    if (path.includes('/wardrobe')) return 'wardrobe';
    if (path.includes('/chat')) return 'chat';
    return 'home';
  };

  const activeScreen = getActiveScreen();

  const navItems = [
    { id: 'wardrobe', icon: Shirt, label: 'Wardrobe', path: '/app/wardrobe' },
    { id: 'home', icon: Sparkles, label: 'Recommendation', path: '/app/home' },
    { id: 'chat', icon: MessageCircle, label: 'Stylist', path: '/app/chat' },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-stone-50 border-t border-stone-200 pb-safe pt-2 px-6 z-50">
      <div className="flex justify-between items-center max-w-md mx-auto">
        {/* Back to Home button */}
        <button
          onClick={() => navigate('/')}
          className="flex flex-col items-center p-2 rounded-xl transition-all duration-200 w-20 text-stone-600 hover:text-stone-900"
          title="Back to Home"
        >
          <ArrowLeft size={24} strokeWidth={2} />
          <span className="text-[10px] font-medium mt-1">Home</span>
        </button>

        {/* Main navigation items */}
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeScreen === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className={`flex flex-col items-center p-2 rounded-xl transition-all duration-200 w-20 ${
                isActive
                  ? 'text-stone-900'
                  : 'text-stone-500 hover:text-stone-700'
              }`}
            >
              <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-[10px] font-medium mt-1 ${isActive ? 'text-stone-900' : 'text-stone-500'}`}>
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

