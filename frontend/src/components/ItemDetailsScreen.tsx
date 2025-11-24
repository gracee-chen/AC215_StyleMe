import { ArrowLeft, Trash2, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { ClothingItem } from '../services/api';
import { useState } from 'react';

interface ItemDetailsScreenProps {
  item: ClothingItem;
  onBack: () => void;
  onCompleteTheLook: (item: ClothingItem) => void;
  onDelete: (id: string) => void;
}

export function ItemDetailsScreen({ item, onBack, onCompleteTheLook, onDelete }: ItemDetailsScreenProps) {
  const [category, setCategory] = useState(item.category);
  const [color, setColor] = useState(item.color);

  return (
    <div className="h-full bg-white flex flex-col">
      {/* Header */}
      <div className="pt-8 pb-4 px-6 flex items-center justify-between relative z-10">
        <Button variant="ghost" size="icon" onClick={onBack} className="-ml-2 text-gray-800 hover:bg-gray-100 rounded-full">
          <ArrowLeft size={24} />
        </Button>
        <h1 className="text-base font-bold text-gray-900 tracking-wide uppercase">Item Details</h1>
        <div className="w-10" /> {/* Spacer for centering */}
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Large Image */}
        <div className="w-full aspect-square bg-gray-50 relative">
          <ImageWithFallback 
            src={item.image}
            alt={category}
            className="w-full h-full object-cover"
          />
        </div>

        <div className="p-6 space-y-8">
            {/* Metadata */}
            <div className="space-y-4">
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right text-gray-500 font-normal">Category</Label>
                    <Input 
                        value={category} 
                        onChange={(e) => setCategory(e.target.value)}
                        className="col-span-3 border-0 border-b border-gray-200 rounded-none px-0 focus-visible:ring-0 focus-visible:border-pink-500 bg-transparent text-gray-900 font-medium"
                    />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right text-gray-500 font-normal">Color</Label>
                    <Input 
                        value={color} 
                        onChange={(e) => setColor(e.target.value)}
                        className="col-span-3 border-0 border-b border-gray-200 rounded-none px-0 focus-visible:ring-0 focus-visible:border-pink-500 bg-transparent text-gray-900 font-medium"
                    />
                </div>
            </div>

            {/* Primary CTA */}
            <Button 
                onClick={() => onCompleteTheLook(item)}
                className="w-full py-6 text-sm font-semibold bg-gray-900 hover:bg-gray-800 text-white rounded-2xl tracking-wider uppercase shadow-lg shadow-gray-200"
            >
                Complete the Look
            </Button>

            {/* Secondary Actions */}
            <div className="flex gap-4 pt-4">
                <Button 
                    variant="outline" 
                    className="flex-1 py-6 rounded-xl border-gray-200 text-red-500 hover:text-red-600 hover:bg-red-50 hover:border-red-100"
                    onClick={() => onDelete(item.id)}
                >
                    <Trash2 size={18} className="mr-2" />
                    Delete
                </Button>
                <Button 
                    variant="outline" 
                    className="flex-1 py-6 rounded-xl border-gray-200 text-gray-600 hover:bg-gray-50"
                >
                    <RefreshCw size={18} className="mr-2" />
                    Replace
                </Button>
            </div>
        </div>
      </div>
    </div>
  );
}
