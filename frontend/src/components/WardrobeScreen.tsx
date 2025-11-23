import { useState } from 'react';
import { ClothingItem } from '../services/api';
import { ImageWithFallback } from './figma/ImageWithFallback';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select"

interface WardrobeScreenProps {
  items: ClothingItem[];
  onItemClick: (item: ClothingItem) => void;
}

export function WardrobeScreen({ items, onItemClick }: WardrobeScreenProps) {
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [colorFilter, setColorFilter] = useState('all');

  const categories = ['All', 'Tops', 'Bottoms', 'Outerwear', 'Shoes', 'Accessories'];
  const colors = ['All', 'White', 'Black', 'Blue', 'Red', 'Green', 'Yellow', 'Grey', 'Brown', 'Cream', 'Khaki', 'Floral'];

  const filteredItems = items.filter(item => {
    const matchCategory = categoryFilter === 'all' || categoryFilter === 'All' || item.category.toLowerCase() === categoryFilter.toLowerCase();
    const matchColor = colorFilter === 'all' || colorFilter === 'All' || item.color.toLowerCase() === colorFilter.toLowerCase();
    return matchCategory && matchColor;
  });

  return (
    <div className="h-full bg-gray-50 flex flex-col">
        {/* Header */}
        <div className="pt-8 pb-4 bg-white px-6 shadow-sm z-10">
            <h1 className="text-xl font-bold text-gray-900 tracking-wide text-center">MY WARDROBE</h1>
        </div>

        {/* Filters */}
        <div className="px-4 py-4 flex gap-2 overflow-x-auto hide-scrollbar">
             <div className="flex gap-2 min-w-full">
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                    <SelectTrigger className="w-[110px] rounded-full bg-white border-gray-200 text-xs font-medium h-9">
                        <SelectValue placeholder="Category" />
                    </SelectTrigger>
                    <SelectContent>
                        {categories.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                    </SelectContent>
                </Select>

                <Select value={colorFilter} onValueChange={setColorFilter}>
                    <SelectTrigger className="w-[100px] rounded-full bg-white border-gray-200 text-xs font-medium h-9">
                        <SelectValue placeholder="Color" />
                    </SelectTrigger>
                    <SelectContent>
                        {colors.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                    </SelectContent>
                </Select>
                 {/* Placeholder for 'All' or sort if needed, user asked for "All / Category / Color" dropdowns. 
                     Usually 'All' is implicit in the dropdowns. 
                     The sketch shows [All v] [Category v] [Color v].
                     Maybe the first one is "Sort"? Or "Type"?
                     I'll add a Sort dropdown or just stick to Category/Color as they are the most useful.
                     Let's add a "Sort" or "View" dropdown for the 3rd one to match visual weight.
                  */}
                 <Select defaultValue="newest">
                    <SelectTrigger className="w-[100px] rounded-full bg-white border-gray-200 text-xs font-medium h-9">
                        <SelectValue placeholder="Sort" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="newest">Newest</SelectItem>
                        <SelectItem value="oldest">Oldest</SelectItem>
                    </SelectContent>
                </Select>
            </div>
        </div>

        {/* Grid */}
        <div className="flex-1 p-4 overflow-y-auto">
            {filteredItems.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
                    No items found matching filters.
                </div>
            ) : (
                <div className="grid grid-cols-3 gap-3">
                    {filteredItems.map((item) => (
                        <button 
                            key={item.id}
                            onClick={() => onItemClick(item)}
                            className="aspect-square rounded-xl overflow-hidden bg-white shadow-sm relative group"
                        >
                            <ImageWithFallback 
                                src={item.image}
                                alt={item.category}
                                className="w-full h-full object-cover"
                            />
                        </button>
                    ))}
                </div>
            )}
        </div>
    </div>
  );
}
