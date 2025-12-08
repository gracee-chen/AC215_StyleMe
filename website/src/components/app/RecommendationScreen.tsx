import { useState, useEffect } from 'react';
import { ClothingItem, getRecommendations } from '@/services/api';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { Button } from '@/components/ui/button';
import { Save, Shirt, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface RecommendationScreenProps {
  items: ClothingItem[];
  selectedItem: ClothingItem | null;
  userId: string;
  onSelectItem: (item: ClothingItem) => void;
}

export function RecommendationScreen({ items, selectedItem, userId, onSelectItem }: RecommendationScreenProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedItem && selectedItem.image) {
      loadRecommendations();
    }
  }, [selectedItem]);

  const loadRecommendations = async () => {
    if (!selectedItem) return;
    
    setLoading(true);
    setError(null);
    
    try {
      let imageData: string | File;
      
      if (selectedItem.image.startsWith('http')) {
        try {
          const response = await fetch(selectedItem.image);
          if (!response.ok) throw new Error('Failed to fetch image');
          const blob = await response.blob();
          imageData = new File([blob], 'query.jpg', { type: 'image/jpeg' });
        } catch (fetchError) {
          imageData = selectedItem.image;
        }
      } else if (selectedItem.image.startsWith('data:')) {
        imageData = selectedItem.image;
      } else {
        imageData = selectedItem.image;
      }
      
      const result = await getRecommendations(userId, imageData, {
        threshold: 0.7,
        wardrobe_k: 5,
        catalog_k: 3
      });
      
      setRecommendations(result.items);
    } catch (err) {
      console.error('Failed to get recommendations:', err);
      setError(err instanceof Error ? err.message : 'Failed to get recommendations');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleItemSelect = (item: ClothingItem) => {
    onSelectItem(item);
    setIsDialogOpen(false);
  };

  return (
    <div className="min-h-screen bg-stone-50 pb-20">
      {/* Header */}
      <div className="pt-8 pb-4 bg-white px-6 shadow-sm sticky top-0 z-10 text-center border-b border-stone-200">
        <h1 className="text-xl font-bold text-stone-900 tracking-wide">Complete the Look</h1>
      </div>

      <div className="p-6 space-y-8">
        {/* Select Item Button & Display */}
        <div className="flex flex-col items-center space-y-6">
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                variant="outline"
                className="w-full py-6 rounded-lg border-dashed border-2 border-stone-300 hover:border-stone-400 hover:bg-stone-50 text-stone-600 hover:text-stone-900 transition-all"
              >
                <Shirt className="mr-2" size={20} />
                {selectedItem ? "Change Item" : "Select Item to Style"}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-h-[80vh] flex flex-col bg-white">
              <DialogHeader>
                <DialogTitle>Select an Item</DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-3 gap-2 overflow-y-auto p-1">
                {items.map((item) => (
                  <button 
                    key={item.id}
                    onClick={() => handleItemSelect(item)}
                    className="aspect-square rounded-lg overflow-hidden bg-gray-100 relative hover:opacity-80 transition-opacity"
                  >
                    <ImageWithFallback 
                      src={item.image}
                      alt={item.category}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            </DialogContent>
          </Dialog>

          {selectedItem && (
            <div className="w-full aspect-square rounded-lg overflow-hidden bg-white shadow-md border border-stone-200">
              <ImageWithFallback 
                src={selectedItem.image}
                alt="Selected"
                className="w-full h-full object-cover"
              />
            </div>
          )}
        </div>

        {/* Recommendations */}
        {selectedItem && (
          <>
            {loading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-stone-600 mb-4" />
                <p className="text-stone-600">Finding perfect matches...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                <p className="text-red-600">{error}</p>
                <Button 
                  onClick={loadRecommendations}
                  variant="outline"
                  className="mt-4"
                >
                  Try Again
                </Button>
              </div>
            ) : recommendations.length > 0 ? (
              <>
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-stone-500 uppercase tracking-wider">
                    Recommended Items ({recommendations.length})
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    {recommendations.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => onSelectItem(item)}
                        className="group relative aspect-square rounded-lg overflow-hidden bg-white shadow-sm hover:shadow-md transition-all border border-stone-200"
                      >
                        <ImageWithFallback 
                          src={item.image}
                          alt={item.title || item.category}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        {item.similarity && (
                          <div className="absolute top-2 right-2 bg-stone-900/70 text-white text-xs px-2 py-1 rounded">
                            {Math.round(item.similarity * 100)}%
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                <Button className="w-full py-6 text-base font-semibold bg-stone-900 hover:bg-stone-800 text-white rounded-lg shadow-md">
                  <Save className="mr-2" size={20} />
                  Save Look
                </Button>
              </>
            ) : (
              <div className="text-center py-12 bg-white rounded-lg border border-stone-200">
                <p className="text-stone-500">No recommendations found. Try a different item.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

