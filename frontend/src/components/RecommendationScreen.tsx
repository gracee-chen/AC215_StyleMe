import { useState } from 'react';
import { ClothingItem } from './mockData';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { Button } from './ui/button';
import { Save, Shirt } from 'lucide-react';
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
  onSelectItem: (item: ClothingItem) => void;
}

export function RecommendationScreen({ items, selectedItem, onSelectItem }: RecommendationScreenProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Mock outfit construction
  const outfit = {
    top: selectedItem?.category === 'Tops' ? selectedItem : items.find(i => i.category === 'Tops'),
    bottom: selectedItem?.category === 'Bottoms' ? selectedItem : items.find(i => i.category === 'Bottoms'),
    shoes: selectedItem?.category === 'Shoes' ? selectedItem : items.find(i => i.category === 'Shoes'),
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
                {/* Full Outfit Block */}
                <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Recommended Outfit</h3>
                    <div className="bg-white p-4 rounded-2xl shadow-sm flex justify-between items-center gap-2">
                         {[outfit.top, outfit.bottom, outfit.shoes].map((part, idx) => (
                             <div key={idx} className="flex-1 aspect-[3/4] bg-gray-50 rounded-lg overflow-hidden">
                                 {part ? (
                                     <ImageWithFallback 
                                        src={part.image}
                                        alt="Outfit Part"
                                        className="w-full h-full object-cover"
                                     />
                                 ) : (
                                     <div className="w-full h-full flex items-center justify-center text-gray-300 bg-gray-100">
                                         <span className="text-xs">?</span>
                                     </div>
                                 )}
                             </div>
                         ))}
                    </div>
                </div>

                {/* Save Button */}
                <Button className="w-full py-6 text-base font-semibold bg-pink-500 hover:bg-pink-600 text-white rounded-2xl shadow-lg shadow-pink-100">
                    <Save className="mr-2" size={20} />
                    Save Look
                </Button>
            </>
        )}
      </div>
    </div>
  );
}
