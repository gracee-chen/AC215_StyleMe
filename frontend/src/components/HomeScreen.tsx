import { Plus } from 'lucide-react';
import { Button } from './ui/button';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { ClothingItem } from '../services/api';
import { UploadScreen } from './UploadScreen';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog"

interface HomeScreenProps {
  items: ClothingItem[];
  userId: string;
  onAddItem: (file: File) => Promise<void>;
  onItemClick: (item: ClothingItem) => void;
}

export function HomeScreen({ items, userId, onAddItem, onItemClick }: HomeScreenProps) {
  const recentItems = items.slice(0, 4);

  return (
    <div className="h-full bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="pt-8 pb-4 bg-white px-6 flex justify-center items-center shadow-sm z-10">
        <div className="w-24 h-8 bg-gray-900 text-white flex items-center justify-center font-bold text-sm rounded tracking-widest">
          StyleMe
        </div>
      </div>

      <div className="flex-1 p-6 space-y-8 overflow-y-auto">
        {/* Add Item CTA */}
        <div className="flex flex-col items-center space-y-4 mt-4">
            <Dialog>
                <DialogTrigger asChild>
                    <Button 
                        className="w-full h-48 rounded-3xl bg-white border-2 border-dashed border-gray-200 hover:border-pink-200 hover:bg-pink-50/30 text-gray-400 hover:text-pink-500 flex flex-col gap-4 transition-all duration-300 shadow-sm"
                        variant="ghost"
                    >
                        <div className="w-16 h-16 rounded-full bg-gray-50 flex items-center justify-center mb-2">
                            <Plus size={32} />
                        </div>
                        <span className="font-medium text-lg">ADD ITEM</span>
                    </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[90vw] max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Add New Item</DialogTitle>
                    </DialogHeader>
                    <UploadScreen 
                      userId={userId}
                      onUpload={onAddItem}
                      onComplete={() => {}}
                    />
                </DialogContent>
            </Dialog>
        </div>

        {/* Recently Added Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-lg font-semibold text-gray-900">Recently Added</h2>
            {items.length > 0 && (
                <span className="text-xs text-gray-400">{items.length} items</span>
            )}
          </div>

          {items.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-3xl border border-gray-100">
              <p className="text-gray-400">No items yet. Add your first piece.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {recentItems.map((item) => (
                <button 
                  key={item.id}
                  onClick={() => onItemClick(item)}
                  className="group relative aspect-square rounded-2xl overflow-hidden bg-white shadow-sm hover:shadow-md transition-all"
                >
                  <ImageWithFallback 
                    src={item.image}
                    alt={item.category}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
