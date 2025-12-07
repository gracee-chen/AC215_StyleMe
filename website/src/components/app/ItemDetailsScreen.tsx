import { ArrowLeft, Trash2, RefreshCw, Save, Check, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { ClothingItem } from '@/services/api';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '@/pages/AppLayout';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ItemDetailsScreenProps {
  item: ClothingItem;
  onBack: () => void;
  onCompleteTheLook: (item: ClothingItem) => void;
  onDelete: (id: string) => void;
}

// Fixed categories - simplified list
const CATEGORIES = [
  'tops', 'bottoms', 'layers', 'shoes', 'dresses', 'accessories'
];

// Fixed colors - common clothing colors
const COLORS = [
  'Black', 'White', 'Gray', 'Beige', 'Brown', 'Navy', 'Blue', 
  'Green', 'Red', 'Pink', 'Purple', 'Yellow', 'Orange', 'Cream', 'Khaki'
];

// Fixed styles - common clothing styles
const STYLES = [
  'Casual', 'Formal', 'Sporty', 'Elegant', 'Bohemian', 'Minimalist', 
  'Vintage', 'Modern', 'Classic', 'Edgy', 'Feminine', 'Masculine', 'Chic'
];

// Rococo color scheme for Category - soft pastels with pink, lavender, gold, and cream tones
const getCategoryColor = (category: string) => {
  const rococoColors: Record<string, string> = {
    'tops': 'bg-[#F5E6E8] text-[#8B6F7A] border-[#E8D4D8]', // Soft pink
    'bottoms': 'bg-[#E8E0F0] text-[#7A6F8B] border-[#D8D0E8]', // Lavender
    'layers': 'bg-[#F0E8D8] text-[#8B7A6F] border-[#E8D8C8]', // Cream gold
    'shoes': 'bg-[#E8F0E8] text-[#6F8B7A] border-[#D8E8D8]', // Mint green
    'dresses': 'bg-[#F5E8F0] text-[#8B6F8B] border-[#E8D8E8]', // Rose pink
    'accessories': 'bg-[#F0E8E8] text-[#8B7A7A] border-[#E8D8D8]', // Blush
  };
  return rococoColors[category] || rococoColors['tops'];
};

// Color: Soft beige/brown tones (Morandi earth tones)
const getColorColor = (color: string) => {
  const morandiBeige: Record<string, string> = {
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
  return morandiBeige[color] || 'bg-[#E8E0D5] text-[#6B5D4F] border-[#D8CBB8]';
};

// Macaron color scheme for Style - vibrant yet soft pastels
const getStyleColor = (style: string) => {
  if (!style) return 'bg-[#FFE5E5] text-[#B85C5C] border-[#FFD5D5]';
  
  // Normalize to match STYLES array format (capitalize first letter)
  const normalized = style.charAt(0).toUpperCase() + style.slice(1).toLowerCase();
  
  const macaronColors: Record<string, string> = {
    'Casual': 'bg-[#FFE5E5] text-[#B85C5C] border-[#FFD5D5]', // Strawberry macaron
    'Formal': 'bg-[#E5E5FF] text-[#5C5CB8] border-[#D5D5FF]', // Blueberry macaron
    'Sporty': 'bg-[#E5FFE5] text-[#5CB85C] border-[#D5FFD5]', // Matcha macaron
    'Elegant': 'bg-[#FFE5F5] text-[#B85C9C] border-[#FFD5F0]', // Rose macaron
    'Bohemian': 'bg-[#FFF5E5] text-[#B89C5C] border-[#FFEED5]', // Vanilla macaron
    'Minimalist': 'bg-[#F0F0F0] text-[#7A7A7A] border-[#E0E0E0]', // White macaron
    'Vintage': 'bg-[#F5E5D5] text-[#9C7A5C] border-[#F0D5C5]', // Caramel macaron
    'Modern': 'bg-[#E5F5FF] text-[#5C9CB8] border-[#D5F0FF]', // Sky blue macaron
    'Classic': 'bg-[#FFE5D5] text-[#B87A5C] border-[#FFD5C5]', // Peach macaron
    'Edgy': 'bg-[#E5D5FF] text-[#7A5CB8] border-[#D5C5FF]', // Lavender macaron
    'Feminine': 'bg-[#FFE5F0] text-[#B85C8C] border-[#FFD5E8]', // Pink macaron
    'Masculine': 'bg-[#D5E5FF] text-[#5C7AB8] border-[#C5D5FF]', // Steel blue macaron
    'Chic': 'bg-[#F5E5F5] text-[#9C5C9C] border-[#F0D5F0]', // Lilac macaron
  };
  return macaronColors[normalized] || macaronColors[style] || 'bg-[#FFE5E5] text-[#B85C5C] border-[#FFD5D5]';
};

export function ItemDetailsScreen({ item, onBack, onCompleteTheLook, onDelete }: ItemDetailsScreenProps) {
  const navigate = useNavigate();
  const { loadWardrobe, userId } = useAppContext();
  const [category, setCategory] = useState(item.category === 'Unknown' ? 'tops' : (item.category || 'tops'));
  const [color, setColor] = useState(item.color === 'Unknown' ? 'White' : (item.color || 'White'));
  const [style, setStyle] = useState((item as any).style || 'Casual');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  
  // Save metadata function
  const saveMetadata = async () => {
    try {
      setIsSaving(true);
      // Extract filename from image path
      const imagePath = item.image;
      const filename = imagePath.split('/').pop() || '';
      
      const metadataKey = `wardrobe_metadata_${userId}_${filename}`;
      const existingMetadata = localStorage.getItem(metadataKey);
      let metadata = existingMetadata ? JSON.parse(existingMetadata) : {};
      
      metadata = {
        ...metadata,
        category: category,
        color: color,
        style: style,
        timestamp: Date.now(),
      };
      
      localStorage.setItem(metadataKey, JSON.stringify(metadata));
      console.log('Saved metadata:', metadata);
      
      // Refresh wardrobe to show updated tags
      await loadWardrobe();
      
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e) {
      console.warn('Failed to save metadata:', e);
      alert('Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleManualAnalyze = async () => {
    if (!item.image || isAnalyzing) return;

    setIsAnalyzing(true);
    setHasAnalyzed(true);

    try {
      // Convert image URL to File for analysis
      const response = await fetch(item.image);
      const blob = await response.blob();
      const file = new File([blob], 'item.jpg', { type: blob.type });

      const analysis = await analyzeClothingItem(file);
      
      // Auto-fill the fields
      if (analysis.category) {
        // Map AI category to our categories
        const normalizedCategory = normalizeCategoryForSelect(analysis.category);
        setCategory(normalizedCategory);
      }
      if (analysis.color) {
        // Normalize color to our color list
        const normalizedColor = normalizeColorForSelect(analysis.color);
        setColor(normalizedColor);
      }
      if (analysis.style) {
        // Normalize style to our style list
        const normalizedStyle = normalizeStyleForSelect(analysis.style);
        setStyle(normalizedStyle);
      }
      
      // Save metadata
      try {
        const imagePath = item.image;
        const filename = imagePath.split('/').pop() || '';
        const metadataKey = `wardrobe_metadata_${userId}_${filename}`;
        localStorage.setItem(metadataKey, JSON.stringify(analysis));
      } catch (e) {
        console.warn('Failed to save analysis metadata:', e);
      }
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Normalize AI category to our fixed category list - MUST return one of the fixed categories
  const normalizeCategoryForSelect = (aiCategory: string): string => {
    const FIXED_CATEGORIES = ['tops', 'bottoms', 'layers', 'shoes', 'dresses', 'accessories'];
    
    if (!aiCategory) return 'tops'; // Default to tops if no category provided
    
    const lower = aiCategory.toLowerCase().trim();
    
    // Direct exact matches (case-insensitive)
    for (const cat of FIXED_CATEGORIES) {
      if (lower === cat.toLowerCase()) {
        return cat;
      }
    }
    
    // Direct mapping from AI categories
    if (lower === 'shirt' || lower === 'shirts' || lower === 'top' || lower === 'tops') {
      return 'tops';
    }
    if (lower === 'pants' || lower === 'pant' || lower === 'bottom' || lower === 'bottoms') {
      return 'bottoms';
    }
    if (lower === 'dress' || lower === 'dresses') {
      return 'dresses';
    }
    if (lower === 'jacket' || lower === 'jackets' || lower === 'layer' || lower === 'layers') {
      return 'layers';
    }
    if (lower === 'shoes' || lower === 'shoe') {
      return 'shoes';
    }
    if (lower === 'accessories' || lower === 'accessory') {
      return 'accessories';
    }
    
    // Pattern matches - prioritize most specific matches first
    if (lower.includes('dress')) {
      return 'dresses';
    }
    if (lower.includes('top') || lower.includes('blouse') || lower.includes('t-shirt') || 
        lower.includes('tee') || lower.includes('tank') || lower.includes('shirt')) {
      return 'tops';
    }
    if (lower.includes('jean') || lower.includes('trouser') || lower.includes('short') ||
        lower.includes('pant') || lower.includes('bottom') || lower.includes('legging')) {
      return 'bottoms';
    }
    if (lower.includes('coat') || lower.includes('blazer') || lower.includes('cardigan') || 
        lower.includes('sweater') || lower.includes('hoodie') || lower.includes('vest') ||
        lower.includes('jacket') || lower.includes('layer') || lower.includes('outerwear')) {
      return 'layers';
    }
    if (lower.includes('sneaker') || lower.includes('boot') || lower.includes('sandal') ||
        lower.includes('heel') || lower.includes('flat') || lower.includes('shoe')) {
      return 'shoes';
    }
    if (lower.includes('bag') || lower.includes('hat') || lower.includes('scarf') ||
        lower.includes('belt') || lower.includes('jewelry') || lower.includes('accessory')) {
      return 'accessories';
    }
    
    // If no match found, return default (tops)
    return 'tops';
  };

  // Normalize AI color to our fixed color list - MUST return one of the fixed colors
  const normalizeColorForSelect = (aiColor: string): string => {
    if (!aiColor) return 'White'; // Default to White if no color provided
    
    const lower = aiColor.toLowerCase().trim();
    
    // Direct exact matches (case-insensitive)
    for (const col of COLORS) {
      if (lower === col.toLowerCase()) {
        return col;
      }
    }
    
    // Pattern matches - prioritize most specific matches first
    // IMPORTANT: Check for green-related colors BEFORE white to avoid misclassification
    if (lower.includes('green') || lower.includes('emerald') || lower.includes('forest') || 
        lower.includes('olive') || lower.includes('sage') || lower.includes('mint') ||
        lower.includes('lime') || lower.includes('teal') || lower.includes('jade')) return 'Green';
    
    // Check for maroon/burgundy/dark red BEFORE general red
    if (lower.includes('maroon') || lower.includes('burgundy') || lower.includes('crimson') ||
        lower.includes('wine') || lower.includes('cherry') || (lower.includes('dark') && lower.includes('red'))) return 'Red';
    
    if (lower.includes('black') || lower.includes('ebony') || lower.includes('charcoal')) return 'Black';
    // Check white AFTER green to avoid misclassifying green items with white accents
    if (lower.includes('white') || lower.includes('ivory') || lower.includes('snow')) return 'White';
    if (lower.includes('gray') || lower.includes('grey') || lower.includes('silver')) return 'Gray';
    if (lower.includes('beige') || lower.includes('tan') || lower.includes('nude')) return 'Beige';
    if (lower.includes('brown') || lower.includes('chocolate') || lower.includes('coffee') ||
        lower.includes('caramel') || lower.includes('taupe')) return 'Brown';
    if (lower.includes('navy') || (lower.includes('dark') && lower.includes('blue'))) return 'Navy';
    if (lower.includes('blue') && !lower.includes('navy')) return 'Blue';
    // General red check (after maroon/burgundy)
    if (lower.includes('red') || lower.includes('scarlet') || lower.includes('ruby')) return 'Red';
    if (lower.includes('pink') || lower.includes('rose') || lower.includes('salmon') ||
        lower.includes('magenta') || lower.includes('fuchsia')) return 'Pink';
    if (lower.includes('purple') || lower.includes('violet') || lower.includes('lavender') ||
        lower.includes('plum') || lower.includes('mauve')) return 'Purple';
    if (lower.includes('yellow') || lower.includes('gold') || lower.includes('lemon') ||
        lower.includes('amber')) return 'Yellow';
    if (lower.includes('orange') || lower.includes('coral') || lower.includes('peach') ||
        lower.includes('tangerine')) return 'Orange';
    if (lower.includes('cream') || lower.includes('off-white')) return 'Cream';
    if (lower.includes('khaki')) return 'Khaki';
    
    // Try to find closest match by substring
    for (const col of COLORS) {
      if (lower.includes(col.toLowerCase()) || col.toLowerCase().includes(lower)) {
        return col;
      }
    }
    
    // If no match found, return default (White)
    return 'White';
  };

  // Normalize AI style to our fixed style list - MUST return one of the fixed styles
  const normalizeStyleForSelect = (aiStyle: string): string => {
    if (!aiStyle) return 'Casual'; // Default to Casual if no style provided
    
    const lower = aiStyle.toLowerCase().trim();
    
    // Direct exact matches (case-insensitive)
    for (const sty of STYLES) {
      if (lower === sty.toLowerCase()) {
        return sty;
      }
    }
    
    // Pattern matches - prioritize most specific matches first
    if (lower.includes('casual') || lower.includes('everyday') || lower.includes('relaxed')) return 'Casual';
    if (lower.includes('formal') || lower.includes('business') || lower.includes('professional')) return 'Formal';
    if (lower.includes('sporty') || lower.includes('athletic') || lower.includes('active') || lower.includes('sport')) return 'Sporty';
    if (lower.includes('elegant') || lower.includes('sophisticated') || lower.includes('refined')) return 'Elegant';
    if (lower.includes('bohemian') || lower.includes('boho') || lower.includes('free-spirited')) return 'Bohemian';
    if (lower.includes('minimalist') || lower.includes('minimal') || lower.includes('simple')) return 'Minimalist';
    if (lower.includes('vintage') || lower.includes('retro') || lower.includes('antique')) return 'Vintage';
    if (lower.includes('modern') || lower.includes('contemporary') || lower.includes('trendy')) return 'Modern';
    if (lower.includes('classic') || lower.includes('traditional') || lower.includes('timeless')) return 'Classic';
    if (lower.includes('edgy') || lower.includes('bold') || lower.includes('rebellious')) return 'Edgy';
    if (lower.includes('feminine') || lower.includes('girly') || lower.includes('delicate')) return 'Feminine';
    if (lower.includes('masculine') || lower.includes('menswear') || lower.includes('rugged')) return 'Masculine';
    if (lower.includes('chic') || lower.includes('stylish') || lower.includes('fashionable')) return 'Chic';
    
    // Try to find closest match by substring
    for (const sty of STYLES) {
      if (lower.includes(sty.toLowerCase()) || sty.toLowerCase().includes(lower)) {
        return sty;
      }
    }
    
    // If no match found, return default (Casual)
    return 'Casual';
  };

  const handleCompleteLook = async () => {
    // Navigate to home page with item data to trigger automatic recommendations
    navigate('/app/home', { 
      state: { 
        completeTheLook: true,
        item: item 
      } 
    });
  };

  const handleAskStylist = async () => {
    // Navigate to chat page with item image
    navigate('/app/chat', {
      state: {
        itemImage: item.image,
        itemTitle: item.title || item.category
      }
    });
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this item?')) {
      onDelete(item.id);
      navigate('/app/wardrobe');
    }
  };

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Header */}
      <div className="pt-8 pb-4 px-6 flex items-center justify-between relative z-10 border-b border-stone-200">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={onBack} 
          className="-ml-2 text-stone-700 hover:bg-stone-100 rounded-full"
        >
          <ArrowLeft size={24} />
        </Button>
        <h1 className="text-2xl subtle-artistic-font text-stone-900">Item Details</h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="flex flex-col md:flex-row gap-6 max-w-6xl mx-auto">
          {/* Left: Image */}
          <div className="flex-shrink-0 md:w-1/2">
            <div className="bg-white rounded-2xl p-4 shadow-md border border-stone-200">
              <div className="aspect-square rounded-xl overflow-hidden bg-stone-50">
                <ImageWithFallback 
                  src={item.image}
                  alt={category}
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>

          {/* Right: Description */}
          <div className="flex-1 md:w-1/2 space-y-6">
            {/* Metadata */}
            <div className="bg-white rounded-2xl p-6 shadow-md border border-stone-200 space-y-4">
              <h2 className="text-2xl subtle-artistic-font text-stone-900 mb-4">Item Details</h2>
              
              <div className="space-y-4">
                <div>
                  <Label className="text-stone-600 font-normal text-sm mb-2 block lowercase subtle-artistic-font">category</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="border-stone-300 rounded-lg focus:border-stone-500 bg-stone-50 text-stone-900 h-auto min-h-[40px] py-2">
                      <SelectValue placeholder="Select category">
                        {category ? (
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getCategoryColor(category)}`}>
                            {category}
                          </span>
                        ) : (
                          <span className="text-stone-500">Select category</span>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      {CATEGORIES.map((cat) => (
                        <SelectItem key={cat} value={cat} className="cursor-pointer">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getCategoryColor(cat)}`}>
                            {cat}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-stone-600 font-normal text-sm mb-2 block lowercase subtle-artistic-font">color</Label>
                  <Select value={color} onValueChange={setColor}>
                    <SelectTrigger className="border-stone-300 rounded-lg focus:border-stone-500 bg-stone-50 text-stone-900 h-auto min-h-[40px] py-2">
                      <SelectValue placeholder="Select color">
                        {color ? (
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getColorColor(color)}`}>
                            {color}
                          </span>
                        ) : (
                          <span className="text-stone-500">Select color</span>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      {COLORS.map((col) => (
                        <SelectItem key={col} value={col} className="cursor-pointer">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getColorColor(col)}`}>
                            {col}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-stone-600 font-normal text-sm mb-2 block lowercase subtle-artistic-font">style</Label>
                  <Select value={style} onValueChange={setStyle}>
                    <SelectTrigger className="border-stone-300 rounded-lg focus:border-stone-500 bg-stone-50 text-stone-900 h-auto min-h-[40px] py-2">
                      <SelectValue placeholder="Select style">
                        {style ? (
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStyleColor(style)}`}>
                            {style}
                          </span>
                        ) : (
                          <span className="text-stone-500">Select style</span>
                        )}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      {STYLES.map((sty) => (
                        <SelectItem key={sty} value={sty} className="cursor-pointer">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStyleColor(sty)}`}>
                            {sty}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {item.title && (
                  <div>
                    <Label className="text-stone-600 font-normal text-sm mb-2 block">Title</Label>
                    <p className="text-stone-900 font-medium">{item.title}</p>
                  </div>
                )}
                {item.brand && (
                  <div>
                    <Label className="text-stone-600 font-normal text-sm mb-2 block">Brand</Label>
                    <p className="text-stone-900 font-medium">{item.brand}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              {/* Primary Actions - Main CTAs in one row */}
              <div className="flex gap-2">
                <Button 
                  onClick={handleCompleteLook}
                  className="flex-[3] py-5 text-sm font-semibold bg-stone-900 hover:bg-stone-800 text-white rounded-lg shadow-md"
                >
                  Complete the Look
                </Button>
                
                <Button 
                  onClick={handleAskStylist}
                  className="flex-[1] py-5 text-sm font-semibold bg-stone-100 hover:bg-stone-200 text-stone-700 border border-stone-300 rounded-lg px-2"
                >
                  <MessageCircle size={18} className="md:mr-2" />
                  <span className="hidden md:inline">Ask Stylist</span>
                </Button>
              </div>

              {/* Save and Delete - Side by side */}
              <div className="flex gap-2">
                <Button 
                  onClick={saveMetadata}
                  disabled={isSaving}
                  className={`flex-1 py-4 text-sm font-medium rounded-lg ${
                    saveSuccess 
                      ? 'bg-green-600 hover:bg-green-700 text-white' 
                      : 'bg-stone-100 hover:bg-stone-200 text-stone-700 border border-stone-300'
                  }`}
                >
                  {isSaving ? (
                    <>
                      <RefreshCw size={16} className="mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : saveSuccess ? (
                    <>
                      <Check size={16} className="mr-2" />
                      Saved!
                    </>
                  ) : (
                    <>
                      <Save size={16} className="mr-2" />
                      Save Changes
                    </>
                  )}
                </Button>

                <Button 
                  onClick={handleDelete}
                  className="flex-1 py-4 text-sm font-medium rounded-lg bg-stone-100 hover:bg-stone-200 text-red-600 hover:text-red-700 border border-stone-300"
                >
                  <Trash2 size={16} className="mr-2" />
                  Delete
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

