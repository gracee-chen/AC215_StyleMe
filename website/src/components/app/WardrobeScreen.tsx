import { useState, useMemo } from 'react';
import { ClothingItem } from '@/services/api';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { UploadScreen } from './UploadScreen';

interface WardrobeScreenProps {
  items: ClothingItem[];
  onItemClick: (item: ClothingItem) => void;
  userId: string;
  onAddItem: (file: File, addToWardrobe: boolean) => Promise<void>;
}

// Fixed categories - map any input to these fixed categories
const FIXED_CATEGORIES = ['tops', 'bottoms', 'layers', 'shoes', 'dresses', 'accessories'];

// Color tag colors - Morandi beige/brown tones
const getColorTagColor = (color: string) => {
  const colorMap: Record<string, string> = {
    'Black': 'bg-[#3A3A3A] text-white border-[#2A2A2A]',
    'White': 'bg-[#F5F3F0] text-[#6B5D4F] border-[#E5E0D8]',
    'Gray': 'bg-[#D4D0C8] text-[#5A5650] border-[#C4BEB5]',
    'Beige': 'bg-[#E8E0D5] text-[#6B5D4F] border-[#D8CBB8]',
    'Brown': 'bg-[#C8B8A8] text-[#5A4A3A] border-[#B8A898]',
    'Navy': 'bg-[#A8B0B8] text-[#4A525A] border-[#98A0A8]',
    'Blue': 'bg-[#B8C0C8] text-[#4A525A] border-[#A8B0B8]',
    'Green': 'bg-[#B8C8B8] text-[#4A5A4A] border-[#A8B8A8]',
    'Red': 'bg-[#D8B8B8] text-[#6A4A4A] border-[#C8A8A8]',
    'Pink': 'bg-[#E8D0D0] text-[#6A5A5A] border-[#D8C0C0]',
    'Purple': 'bg-[#C8B8C8] text-[#5A4A5A] border-[#B8A8B8]',
    'Yellow': 'bg-[#E8D8B8] text-[#6A5A4A] border-[#D8C8A8]',
    'Orange': 'bg-[#E8C8A8] text-[#6A5A4A] border-[#D8B898]',
    'Cream': 'bg-[#F0E8D8] text-[#6B5D4F] border-[#E0D8C8]',
    'Khaki': 'bg-[#D8C8A8] text-[#5A4A3A] border-[#C8B898]',
  };
  return colorMap[color] || 'bg-[#E8E0D5] text-[#6B5D4F] border-[#D8CBB8]';
};

// Style tag colors - use same as ItemDetailsScreen
const getStyleTagColor = (style: string) => {
  if (!style) return 'bg-[#FFE5E5] text-[#B85C5C] border-[#FFD5D5]';
  
  // Normalize to match STYLES array format (capitalize first letter)
  const normalized = style.charAt(0).toUpperCase() + style.slice(1).toLowerCase();
  
  // Use the same color scheme as ItemDetailsScreen's getStyleColor
  const styleMap: Record<string, string> = {
    'Casual': 'bg-[#FFE5E5] text-[#B85C5C] border-[#FFD5D5]',
    'Formal': 'bg-[#E5E5FF] text-[#5C5CB8] border-[#D5D5FF]',
    'Sporty': 'bg-[#E5FFE5] text-[#5CB85C] border-[#D5FFD5]',
    'Elegant': 'bg-[#FFE5F5] text-[#B85C9C] border-[#FFD5F0]',
    'Bohemian': 'bg-[#FFF5E5] text-[#B89C5C] border-[#FFEED5]',
    'Minimalist': 'bg-[#F0F0F0] text-[#7A7A7A] border-[#E0E0E0]',
    'Vintage': 'bg-[#F5E5D5] text-[#9C7A5C] border-[#F0D5C5]',
    'Modern': 'bg-[#E5F5FF] text-[#5C9CB8] border-[#D5F0FF]',
    'Classic': 'bg-[#FFE5D5] text-[#B87A5C] border-[#FFD5C5]',
    'Edgy': 'bg-[#E5D5FF] text-[#7A5CB8] border-[#D5C5FF]',
    'Feminine': 'bg-[#FFE5F0] text-[#B85C8C] border-[#FFD5E8]',
    'Masculine': 'bg-[#D5E5FF] text-[#5C7AB8] border-[#C5D5FF]',
    'Chic': 'bg-[#F5E5F5] text-[#9C5C9C] border-[#F0D5F0]',
  };
  return styleMap[normalized] || styleMap[style] || 'bg-[#FFE5E5] text-[#B85C5C] border-[#FFD5D5]';
};

function normalizeCategory(category: string): string {
  if (!category || category.trim() === '' || category === 'Unknown' || category === 'OTHER') {
    return 'tops'; // This should not happen if we filter properly, but keep as fallback
  }
  
  const normalized = category.trim();
  
  // If already one of our fixed categories, return it (case-insensitive check)
  const normalizedLower = normalized.toLowerCase();
  for (const fixedCat of FIXED_CATEGORIES) {
    if (normalizedLower === fixedCat.toLowerCase()) {
      return fixedCat.toLowerCase(); // Always return lowercase
    }
  }
  
  // Map common variations to fixed categories
  const lower = category.toLowerCase().trim();
  
  // Direct matches
  if (lower === 'shirt' || lower === 'shirts' || lower === 'top' || lower === 'tops') return 'tops';
  if (lower === 'pants' || lower === 'pant' || lower === 'bottom' || lower === 'bottoms') return 'bottoms';
  if (lower === 'dress' || lower === 'dresses') return 'dresses';
  if (lower === 'jacket' || lower === 'jackets' || lower === 'layer' || lower === 'layers') return 'layers';
  if (lower === 'shoes' || lower === 'shoe') return 'shoes';
  if (lower === 'accessories' || lower === 'accessory') return 'accessories';
  
  // Pattern matches - prioritize most specific matches first
  // IMPORTANT: Check for shoes FIRST to avoid misclassification to tops
  if (lower.includes('boot') || lower.includes('sneaker') || lower.includes('sandal') || 
      lower.includes('heel') || lower.includes('flat') || lower.includes('shoe') ||
      lower.includes('slipper') || lower.includes('loafer') || lower.includes('pump') ||
      lower.includes('oxford') || lower.includes('moccasin') || lower.includes('clog')) {
    return 'shoes';
  }
  // IMPORTANT: Check for 'dress' BEFORE 'top' to avoid misclassification
  if (lower.includes('dress') && !lower.includes('undress') && !lower.includes('address')) {
    return 'dresses';
  }
  if (lower.includes('shirt') || lower.includes('top') || lower.includes('blouse') || 
      lower.includes('t-shirt') || lower.includes('tee') || lower.includes('tank')) {
    return 'tops';
  }
  if (lower.includes('pant') || lower.includes('jean') || lower.includes('trouser') || 
      lower.includes('short') || lower.includes('legging') || lower.includes('bottom')) {
    return 'bottoms';
  }
  if (lower.includes('jacket') || lower.includes('coat') || lower.includes('blazer') || 
      lower.includes('cardigan') || lower.includes('sweater') || lower.includes('hoodie') || 
      lower.includes('vest') || lower.includes('outerwear') || lower.includes('layer')) {
    return 'layers';
  }
  if (lower.includes('accessory') || lower.includes('bag') || lower.includes('hat') || 
      lower.includes('scarf') || lower.includes('belt') || lower.includes('jewelry')) {
    return 'accessories';
  }
  
  return 'tops';
}

export function WardrobeScreen({ items, onItemClick, userId, onAddItem }: WardrobeScreenProps) {
  const navigate = useNavigate();
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);

  // Group items by category - only include items with complete tags (category, color, style)
  const itemsByCategory = useMemo(() => {
    const grouped: Record<string, ClothingItem[]> = {};
    
    items.forEach(item => {
      // Ensure all items have complete tags - use fallback if missing
      // This ensures every uploaded item will be displayed
      const category = normalizeCategory(item.category || 'tops');
      const color = item.color && item.color.trim() !== '' && item.color !== 'Unknown' 
        ? item.color 
        : 'White';
      const style = (item as any).style && (item as any).style.trim() !== '' 
        ? (item as any).style 
        : 'Casual';
      
      // Update item with ensured tags
      const itemWithTags = {
        ...item,
        category,
        color,
        style
      };
      
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(itemWithTags);
    });

    // Sort categories by predefined order
    const categoryOrder = ['layers', 'tops', 'bottoms', 'shoes', 'dresses', 'accessories'];
    const sorted: Record<string, ClothingItem[]> = {};
    categoryOrder.forEach(cat => {
      if (grouped[cat]) {
        sorted[cat] = grouped[cat];
      }
    });
    
    // Add any remaining categories
    Object.keys(grouped).forEach(cat => {
      if (!sorted[cat]) {
        sorted[cat] = grouped[cat];
      }
    });

    return sorted;
  }, [items]);

  const totalItems = items.length;

  const handleUploadComplete = async (file: File, addToWardrobe: boolean) => {
    // In wardrobe page, always add to wardrobe (don't show recommendations)
    try {
      await onAddItem(file, true);
      // Small delay to ensure metadata is saved before closing
      await new Promise(resolve => setTimeout(resolve, 100));
      setIsUploadDialogOpen(false);
    } catch (error) {
      console.error('Upload failed:', error);
      // Don't close dialog on error
    }
  };

  return (
        <div className="min-h-screen bg-stone-50 pb-20">
      {/* Header */}
      <div className="pt-8 pb-4 bg-stone-50 px-6 flex justify-center items-center shadow-sm sticky top-0 z-10 border-b border-stone-200">
        <div className="w-32 h-10 bg-stone-900 text-white flex items-center justify-center text-base rounded tracking-widest">
          <span className="brand-font-normal text-lg">StyleMe</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-4 py-6">
        {/* Header Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-sm text-stone-500 mb-1">{totalItems} ITEMS</p>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl subtle-artistic-font text-stone-900">YOUR WARDROBE</h1>
                <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
                  <DialogTrigger asChild>
                    <button className="w-8 h-8 rounded-full bg-stone-900 text-white flex items-center justify-center hover:bg-stone-800 transition-colors">
                      <Plus size={20} />
                    </button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[90vw] max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Add New Item</DialogTitle>
                    </DialogHeader>
                    <UploadScreen 
                      userId={userId}
                      onUpload={handleUploadComplete}
                      onComplete={() => {}}
                      mode="wardrobe"
                    />
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
        </div>

        {/* Categories */}
        {Object.keys(itemsByCategory).length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-stone-200">
            <p className="text-stone-500 mb-4">No items yet. Add your first piece.</p>
            <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
              <DialogTrigger asChild>
                <button className="px-4 py-2 bg-stone-900 text-white rounded-md hover:bg-stone-800 transition-colors">
                  Add Item
                </button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[90vw] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add New Item</DialogTitle>
                </DialogHeader>
                <UploadScreen 
                  userId={userId}
                  onUpload={handleUploadComplete}
                  onComplete={() => {}}
                  mode="wardrobe"
                />
              </DialogContent>
            </Dialog>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(itemsByCategory).map(([category, categoryItems]) => (
              <div key={category} className="space-y-3">
                <div className="flex items-center gap-3 pb-2 border-b border-stone-200">
                  <h2 className="text-2xl font-bold text-stone-900 uppercase tracking-wide category-title-font">
                    {category}
                  </h2>
                  <span className="text-sm font-medium text-stone-500 bg-stone-100 px-2 py-0.5 rounded-full">
                    {categoryItems.length}
                  </span>
                </div>
                <div className="grid grid-cols-8 gap-2">
                  {categoryItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => {
                        onItemClick(item);
                        navigate('/app/item-details');
                      }}
                      className="bg-white rounded-lg overflow-hidden border border-stone-200 hover:shadow-md transition-all group"
                    >
                      <div className="aspect-square relative overflow-hidden bg-white">
                        <ImageWithFallback 
                          src={item.image}
                          alt={item.title || item.category}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      </div>
                      <div className="p-1.5 space-y-1">
                        <div className="flex items-center gap-1 flex-wrap">
                          {item.color && (
                            <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${getColorTagColor(item.color)}`}>
                              {item.color}
                            </span>
                          )}
                          {(item as any).style && (
                            <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${getStyleTagColor((item as any).style)}`}>
                              {(item as any).style}
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

