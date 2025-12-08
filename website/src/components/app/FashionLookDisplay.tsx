import { ClothingItem } from '@/services/api';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { Sparkles } from 'lucide-react';

interface FashionLookDisplayProps {
  mainItem: ClothingItem;
  recommendations: ClothingItem[];
  onItemClick: (item: ClothingItem) => void;
}

export function FashionLookDisplay({ mainItem, recommendations, onItemClick }: FashionLookDisplayProps) {
  // Take top 6 recommendations for display
  const displayItems = recommendations.slice(0, 6);
  
  // Calculate positions for overlapping layout (similar to fashion collage)
  const getItemStyle = (index: number) => {
    const positions = [
      { top: '5%', left: '8%', zIndex: 6, rotation: -8, width: 140, height: 180 },
      { top: '10%', left: '30%', zIndex: 5, rotation: 5, width: 120, height: 150 },
      { top: '3%', left: '55%', zIndex: 4, rotation: -5, width: 130, height: 170 },
      { top: '15%', left: '75%', zIndex: 3, rotation: 8, width: 110, height: 140 },
      { top: '50%', left: '10%', zIndex: 2, rotation: -3, width: 100, height: 130 },
      { top: '55%', left: '65%', zIndex: 1, rotation: 6, width: 115, height: 145 },
    ];
    
    return positions[index] || { top: '0%', left: '0%', zIndex: 1, rotation: 0, width: 100, height: 130 };
  };

  return (
    <div className="bg-white rounded-lg border border-stone-200 p-6 shadow-sm">
      {/* Title */}
      <div className="flex items-center justify-center gap-2 mb-6">
        <Sparkles className="w-5 h-5 text-stone-600" />
        <h3 className="text-xl font-semibold text-stone-900">Complete the Look</h3>
        <Sparkles className="w-5 h-5 text-stone-600" />
      </div>

      {/* Fashion Collage Display */}
      <div className="relative bg-white rounded-lg overflow-hidden mb-6" style={{ minHeight: '600px', background: 'linear-gradient(to bottom, #fafafa, #ffffff)' }}>
        {/* Main item in center - larger and prominent */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
          <div className="relative w-56 h-72 rounded-lg overflow-hidden shadow-xl border-2 border-stone-300 bg-white">
            <ImageWithFallback 
              src={mainItem.image}
              alt={mainItem.category}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 via-black/50 to-transparent p-4">
              <p className="text-white text-base font-semibold truncate">
                {mainItem.title || mainItem.category}
              </p>
              {mainItem.price && (
                <p className="text-white/90 text-sm mt-1 font-medium">{mainItem.price}</p>
              )}
            </div>
          </div>
        </div>

        {/* Recommended items around - fashion collage style */}
        {displayItems.map((item, index) => {
          const style = getItemStyle(index);
          
          return (
            <button
              key={item.id}
              onClick={() => onItemClick(item)}
              className="absolute group cursor-pointer transition-all duration-300 hover:scale-110 hover:z-50"
              style={{
                top: style.top,
                left: style.left,
                zIndex: style.zIndex,
                transform: `rotate(${style.rotation}deg)`,
                width: `${style.width}px`,
                height: `${style.height}px`,
              }}
            >
              <div className="relative w-full h-full rounded-lg overflow-hidden shadow-lg border-2 border-white bg-white group-hover:shadow-2xl transition-all">
                <ImageWithFallback 
                  src={item.image}
                  alt={item.title || item.category}
                  className="w-full h-full object-cover"
                />
                {/* Item info overlay - always visible but more prominent on hover */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/60 to-transparent p-2.5">
                  <p className="text-white text-xs font-semibold truncate">
                    {item.title || item.category}
                  </p>
                  {item.brand && (
                    <p className="text-white/90 text-[10px] mt-0.5 truncate">{item.brand}</p>
                  )}
                  {item.price && (
                    <p className="text-white font-bold text-sm mt-1">{item.price}</p>
                  )}
                </div>
                {/* Similarity badge */}
                {item.similarity && (
                  <div className="absolute top-2 right-2 bg-stone-900/90 text-white text-[10px] px-2 py-1 rounded-full backdrop-blur-sm font-medium">
                    {Math.round(item.similarity * 100)}%
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Item list below collage */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-stone-700 mb-3">Recommended Items</h4>
        <div className="grid grid-cols-2 gap-3">
          {recommendations.slice(0, 4).map((item) => (
            <button
              key={item.id}
              onClick={() => onItemClick(item)}
              className="flex items-center gap-3 p-3 bg-white rounded-lg hover:bg-stone-100 transition-colors border border-stone-200"
            >
              <div className="w-16 h-16 rounded-md overflow-hidden flex-shrink-0">
                <ImageWithFallback 
                  src={item.image}
                  alt={item.title || item.category}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1 min-w-0 text-left">
                <p className="text-sm font-medium text-stone-900 truncate">
                  {item.title || item.category}
                </p>
                {item.brand && (
                  <p className="text-xs text-stone-600 truncate">{item.brand}</p>
                )}
                <div className="flex items-center justify-between mt-1">
                  {item.price && (
                    <p className="text-sm font-semibold text-stone-900">{item.price}</p>
                  )}
                  {item.similarity && (
                    <span className="text-xs text-stone-500">
                      {Math.round(item.similarity * 100)}% match
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

