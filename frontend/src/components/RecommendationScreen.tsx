import { useState, useEffect } from 'react';
import { ClothingItem, getRecommendations, fileToBase64, getImageUrl } from '../services/api';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { Button } from './ui/button';
import { Save, Shirt, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog"

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

  // Get recommendations when selectedItem changes
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
      // Convert image URL to file if needed, or use base64
      let imageData: string | File;
      
      // If image is a URL (from API or external), fetch it and convert to File
      if (selectedItem.image.startsWith('http')) {
        try {
          const response = await fetch(selectedItem.image);
          if (!response.ok) throw new Error('Failed to fetch image');
          const blob = await response.blob();
          imageData = new File([blob], 'query.jpg', { type: blob.type || 'image/jpeg' });
        } catch (fetchError) {
          // If fetch fails (e.g., CORS issue), try using base64
          // First try to convert URL to base64 by fetching
          console.warn('Direct fetch failed, trying alternative method:', fetchError);
          // For API URLs, pass the URL directly - backend can handle it
          imageData = selectedItem.image;
        }
      } else if (selectedItem.image.startsWith('data:')) {
        // Already base64
        imageData = selectedItem.image;
      } else {
        // Relative path or local path - pass as-is, backend will handle
        imageData = selectedItem.image;
      }
      
      const result = await getRecommendations(userId, imageData, {
        threshold: 0.7,
        wardrobe_k: 5,
        catalog_k: 3
      });
      
      // Ensure all image URLs are properly formatted using getImageUrl helper
      const formattedItems = result.items.map(item => ({
        ...item,
        image: getImageUrl(item.image)
      }));
      
      setRecommendations(formattedItems);
    } catch (err) {
      console.error('Failed to get recommendations:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to get recommendations';
      setError(errorMessage);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleItemSelect = (item: ClothingItem) => {
    onSelectItem(item);
    setIsDialogOpen(false);
  }

  return (
    <div className="h-full bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="pt-8 pb-4 bg-white px-6 shadow-sm z-10 text-center">
        <h1 className="text-xl font-bold text-gray-900 tracking-wide">Complete the Look</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Select Item Button & Display */}
        <div className="flex flex-col items-center space-y-6">
            
            {/* Select/Change Item Button - Always visible or visible when needed based on flow */}
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                    <Button 
                        variant="outline"
                        className="w-full py-6 rounded-2xl border-dashed border-2 border-pink-200 hover:border-pink-500 hover:bg-pink-50 text-gray-500 hover:text-pink-600 transition-all"
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

            {/* Selected Item Large Image */}
            {selectedItem && (
                <div className="w-full aspect-square rounded-3xl overflow-hidden bg-white shadow-md">
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
                        <Loader2 className="w-8 h-8 animate-spin text-pink-500 mb-4" />
                        <p className="text-gray-600">Finding perfect matches...</p>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-center">
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
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                Recommended Items ({recommendations.length})
                            </h3>
                            <div className="grid grid-cols-2 gap-4">
                                {recommendations.map((item) => (
                                    <button
                                        key={item.id}
                                        onClick={() => onSelectItem(item)}
                                        className="group relative aspect-square rounded-2xl overflow-hidden bg-white shadow-sm hover:shadow-md transition-all"
                                    >
                                        <ImageWithFallback 
                                            src={item.image}
                                            alt={item.title || item.category}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                        />
                                        {item.similarity && (
                                            <div className="absolute top-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
                                                {Math.round(item.similarity * 100)}%
                                            </div>
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Save Button */}
                        <Button className="w-full py-6 text-base font-semibold bg-pink-500 hover:bg-pink-600 text-white rounded-2xl shadow-lg shadow-pink-100">
                            <Save className="mr-2" size={20} />
                            Save Look
                        </Button>
                    </>
                ) : (
                    <div className="text-center py-12 bg-white rounded-2xl border border-gray-100">
                        <p className="text-gray-400">No recommendations found. Try a different item.</p>
                    </div>
                )}
            </>
        )}
      </div>
    </div>
  );
}
