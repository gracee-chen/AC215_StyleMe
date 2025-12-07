import { useState, useRef } from 'react';
import { Camera, Upload, Image as ImageIcon, Sparkles, Tag, Check, AlertCircle, RefreshCw, Clock, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { analyzeClothingItem } from '@/services/chatgpt';

// Fixed category mapping - AI returns simple categories, we map to display categories
// MUST return one of: 'tops', 'bottoms', 'layers', 'shoes', 'dresses', 'accessories'
// Always returns a valid category, choosing the closest match if needed
const normalizeCategoryForSelect = (aiCategory: string): string => {
  const FIXED_CATEGORIES = ['tops', 'bottoms', 'layers', 'shoes', 'dresses', 'accessories'];
  
  if (!aiCategory || aiCategory.trim() === '') {
    return 'tops'; // Default fallback
  }
  
  const lower = aiCategory.toLowerCase().trim();
  
  // Direct exact matches (case-insensitive)
  for (const cat of FIXED_CATEGORIES) {
    if (lower === cat.toLowerCase()) {
      return cat;
    }
  }
  
  // Direct mapping from AI categories to our fixed categories
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
  // IMPORTANT: Check for shoes FIRST to avoid misclassification to tops
  // Shoes are footwear - boots, sneakers, sandals, heels, flats, etc.
  if (lower.includes('boot') || lower.includes('sneaker') || lower.includes('sandal') || 
      lower.includes('heel') || lower.includes('flat') || lower.includes('shoe') ||
      lower.includes('slipper') || lower.includes('loafer') || lower.includes('pump') ||
      lower.includes('oxford') || lower.includes('moccasin') || lower.includes('clog')) {
    return 'shoes';
  }
  // IMPORTANT: Check for 'dress' BEFORE 'top' to avoid misclassification
  // A dress is a one-piece garment, so 'dress' should take priority
  if (lower.includes('dress') && !lower.includes('undress') && !lower.includes('address')) {
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
  if (lower.includes('bag') || lower.includes('hat') || lower.includes('scarf') || 
      lower.includes('belt') || lower.includes('jewelry') || lower.includes('accessory')) {
    return 'accessories';
  }
  
  // If no match found, return default (tops) - always return a valid category
  return 'tops';
};

// Normalize AI color to our fixed color list - MUST return one of the fixed colors
// Always returns a valid color, choosing the closest match if needed
const normalizeColorForSelect = (aiColor: string): string => {
  const FIXED_COLORS = [
    'Black', 'White', 'Gray', 'Beige', 'Brown', 'Navy', 'Blue', 
    'Green', 'Red', 'Pink', 'Purple', 'Yellow', 'Orange', 'Cream', 'Khaki'
  ];
  
  if (!aiColor || aiColor.trim() === '') {
    return 'White'; // Default fallback
  }
  
  const lower = aiColor.toLowerCase().trim();
  
  // Direct exact matches (case-insensitive)
  for (const col of FIXED_COLORS) {
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
  // Check brown/beige BEFORE white to avoid misclassifying brown/tan items as white
  if (lower.includes('brown') || lower.includes('chocolate') || lower.includes('coffee') ||
      lower.includes('caramel') || lower.includes('taupe') || lower.includes('camel') ||
      lower.includes('suede') || lower.includes('leather')) return 'Brown';
  if (lower.includes('beige') || lower.includes('tan') || lower.includes('nude') ||
      lower.includes('sand') || lower.includes('cream')) return 'Beige';
  // Check white AFTER brown/beige to avoid misclassifying brown items as white
  if (lower.includes('white') || lower.includes('ivory') || lower.includes('snow')) return 'White';
  if (lower.includes('gray') || lower.includes('grey') || lower.includes('silver')) return 'Gray';
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
  for (const col of FIXED_COLORS) {
    if (lower.includes(col.toLowerCase()) || col.toLowerCase().includes(lower)) {
      return col;
    }
  }
  
  // If no match found, return default (White) - always return a valid color
  return 'White';
};

// Normalize AI style to our fixed style list - MUST return one of the fixed styles
// Always returns a valid style, choosing the closest match if needed
const normalizeStyleForSelect = (aiStyle: string): string => {
  const FIXED_STYLES = [
    'Casual', 'Formal', 'Sporty', 'Elegant', 'Bohemian', 'Minimalist', 
    'Vintage', 'Modern', 'Classic', 'Edgy', 'Feminine', 'Masculine', 'Chic'
  ];
  
  if (!aiStyle || aiStyle.trim() === '') {
    return 'Casual'; // Default fallback
  }
  
  const lower = aiStyle.toLowerCase().trim();
  
  // Direct exact matches (case-insensitive)
  for (const sty of FIXED_STYLES) {
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
  for (const sty of FIXED_STYLES) {
    if (lower.includes(sty.toLowerCase()) || sty.toLowerCase().includes(lower)) {
      return sty;
    }
  }
  
  // If no match found, return default (Casual) - always return a valid style
  return 'Casual';
};

interface UploadScreenProps {
  userId: string;
  onUpload: (file: File, addToWardrobe: boolean) => Promise<void>;
  onComplete?: (addToWardrobe: boolean) => void;
  mode?: 'recommendation' | 'wardrobe'; // Different modes for different pages
}

export function UploadScreen({ userId, onUpload, onComplete, mode = 'recommendation' }: UploadScreenProps) {
  const [uploadStep, setUploadStep] = useState('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  // In wardrobe mode, always add to wardrobe; in recommendation mode, default to true but can be toggled
  const [addToWardrobe, setAddToWardrobe] = useState(mode === 'wardrobe' ? true : true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      
      // In wardrobe mode, skip tagging and directly upload
      if (mode === 'wardrobe') {
        // Set state first, then call handleFinish with the file directly
        setUploadStep('processing');
        try {
          // Analyze the item with AI FIRST - always succeeds with fallback values
          let analysis;
          try {
            analysis = await analyzeClothingItem(file);
            console.log('Item analysis:', analysis);
          } catch (analysisError) {
            // If analysis fails, use fallback values - never fail the upload
            console.warn('Analysis failed, using fallback values:', analysisError);
            analysis = {
              category: 'shirt',
              color: 'white',
              style: 'casual',
              description: 'Analysis failed, using default tags'
            };
          }
          
          // Ensure all three fields exist (should always be true due to fallbacks)
          if (!analysis.category) analysis.category = 'shirt';
          if (!analysis.color) analysis.color = 'white';
          if (!analysis.style) analysis.style = 'casual';
          
          // Log raw analysis for debugging
          console.log('Raw AI analysis:', {
            category: analysis.category,
            color: analysis.color,
            style: analysis.style,
            description: analysis.description
          });
          
          // Normalize category to our fixed categories (always returns a valid category)
          const normalizedCategory = normalizeCategoryForSelect(analysis.category);
          
          // Normalize color to our fixed color list (always returns a valid color)
          const normalizedColor = normalizeColorForSelect(analysis.color);
          
          // Normalize style to our fixed style list (always returns a valid style)
          const normalizedStyle = normalizeStyleForSelect(analysis.style);
          
          console.log('Normalized features:', {
            originalCategory: analysis.category,
            normalizedCategory: normalizedCategory,
            originalColor: analysis.color,
            normalizedColor: normalizedColor,
            originalStyle: analysis.style,
            normalizedStyle: normalizedStyle
          });
          
          // Upload the file
          await onUpload(file, true);
          
          // After upload, save metadata with "latest" key for immediate matching
          // The loadWardrobe will match this to the newest item
          const metadata = {
            category: normalizedCategory,
            color: normalizedColor,
            style: normalizedStyle,
            material: analysis.material || '',
            pattern: analysis.pattern || '',
            season: analysis.season || '',
            occasion: analysis.occasion || '',
            description: analysis.description || '',
            timestamp: Date.now(),
          };
          
          // Save with "latest" key - will be matched to newest item in loadWardrobe
          localStorage.setItem(`wardrobe_metadata_${userId}_latest`, JSON.stringify(metadata));
          console.log('Saved metadata to latest key:', metadata);
          
          setUploadStep('success');
          setTimeout(() => {
          setUploadStep('upload');
          setSelectedFile(null);
          setPreviewUrl(null);
          setAddToWardrobe(true);
          if (onComplete) onComplete(true);
          }, 2000);
        } catch (error) {
          console.error('Upload failed:', error);
          const message = error instanceof Error ? error.message : '上传失败。请检查网络连接并重试。';
          setErrorMessage(message);
          setUploadStep('error');
        }
      } else {
        // For recommendation mode, go to confirmation step
        setUploadStep('confirm-upload');
      }
    }
  };

  const handleUploadClick = (source: 'camera' | 'gallery') => {
    if (source === 'camera') {
      cameraInputRef.current?.click();
    } else {
      fileInputRef.current?.click();
    }
  };

  const handleFinish = async () => {
    if (!selectedFile) return;
    
    setUploadStep('processing');
    try {
      // In wardrobe mode, analyze the item first, then upload
      if (mode === 'wardrobe') {
        try {
          // Analyze the item with AI
          const analysis = await analyzeClothingItem(selectedFile);
          console.log('Item analysis:', analysis);
          // Analysis results are logged, can be used later if needed
          // For now, we just upload the image
        } catch (analysisError) {
          console.warn('Analysis failed, continuing with upload:', analysisError);
          // Continue with upload even if analysis fails
        }
      }
      
      await onUpload(selectedFile, addToWardrobe);
      setUploadStep('success');
      setTimeout(() => {
        setUploadStep('upload');
        setSelectedFile(null);
        setPreviewUrl(null);
        setAddToWardrobe(true);
        if (onComplete) onComplete(addToWardrobe);
      }, 2000);
    } catch (error) {
      console.error('Upload failed:', error);
      const message = error instanceof Error ? error.message : 'Failed to upload image. Please check your connection and try again.';
      setErrorMessage(message);
      setUploadStep('error');
    }
  };

  if (uploadStep === 'processing') {
    return (
      <div className="p-4 flex items-center justify-center min-h-[400px]">
        <div className="bg-white border border-stone-200 rounded-lg p-8 text-center max-w-sm w-full shadow-sm">
          <div className="animate-spin w-16 h-16 mx-auto mb-4">
            <Loader2 className="w-16 h-16 text-stone-600" />
          </div>
          <h2 className="text-xl font-semibold text-stone-900 mb-2">
            {mode === 'wardrobe' ? 'Adding to Wardrobe' : 'Processing Image'}
          </h2>
          <p className="text-stone-600 mb-4">
            {mode === 'wardrobe' 
              ? 'AI is analyzing your item and adding it to your wardrobe...'
              : 'Our AI is removing the background and analyzing your item...'}
          </p>
        </div>
      </div>
    );
  }

  if (uploadStep === 'success') {
    return (
      <div className="p-4 flex items-center justify-center min-h-[400px]">
        <div className="bg-white border border-stone-200 rounded-lg p-8 text-center max-w-sm w-full shadow-sm">
          <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold text-stone-900 mb-2">Upload Successful!</h2>
          <p className="text-stone-600">
            {addToWardrobe 
              ? 'Your item has been added to your wardrobe.' 
              : 'Your item is ready for recommendations.'}
          </p>
        </div>
      </div>
    );
  }

  if (uploadStep === 'error') {
    return (
      <div className="p-4 flex items-center justify-center min-h-[400px]">
        <div className="bg-white border border-red-200 rounded-lg p-8 text-center max-w-sm w-full shadow-sm">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-semibold text-stone-900 mb-2">Upload Failed</h2>
          <p className="text-stone-600 mb-4">{errorMessage || 'Failed to upload image. Please try again.'}</p>
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => {
                setUploadStep('upload');
                setErrorMessage(null);
              }}
              className="flex-1 rounded-md border-stone-300 text-stone-600"
            >
              Go Back
            </Button>
            <Button 
              onClick={() => {
                if (selectedFile) {
                  handleFinish();
                } else {
                  setUploadStep('upload');
                  setErrorMessage(null);
                }
              }}
              className="flex-1 bg-stone-900 hover:bg-stone-800 text-white rounded-md"
            >
              <RefreshCw className="w-4 h-4 mr-2 inline" />
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (uploadStep === 'confirm-upload') {
    return (
      <div className="p-4 space-y-6">
        <div>
          <h1 className="text-2xl subtle-artistic-font text-stone-900">Complete the Look</h1>
          <p className="text-stone-600 mt-1">Get personalized outfit recommendations for your item</p>
        </div>

        <div className="bg-white border border-stone-200 rounded-lg p-6 shadow-sm">
          {previewUrl && (
            <div className="w-32 h-32 mx-auto rounded-lg mb-4 overflow-hidden border border-stone-200">
              <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
            </div>
          )}
          <p className="text-center text-stone-600 mb-6">Preview of your item</p>

          <div className="pt-4 border-t border-stone-200">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <Label htmlFor="add-to-wardrobe" className="text-base font-medium text-stone-900">
                  Add to Wardrobe
                </Label>
                <p className="text-xs text-stone-500 mt-1">
                  Save this item to your personal wardrobe collection
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAddToWardrobe(!addToWardrobe)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  addToWardrobe ? 'bg-stone-900' : 'bg-stone-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    addToWardrobe ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            {!addToWardrobe && (
              <p className="text-xs text-stone-500 mt-2 italic">
                This item will be used for recommendations only, not saved to your wardrobe.
              </p>
            )}
          </div>
        </div>

        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={() => setUploadStep('upload')}
            className="flex-1 rounded-md border-stone-300 text-stone-600"
          >
            Back
          </Button>
          <Button 
            onClick={handleFinish}
            className="flex-1 bg-stone-900 hover:bg-stone-800 text-white rounded-md"
          >
            Ready to Recommend
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-stone-900">Upload Item</h1>
        <p className="text-stone-600 mt-1">Add new items to your virtual closet</p>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />
      <input
        type="file"
        ref={cameraInputRef}
        accept="image/*"
        capture="environment"
        onChange={handleFileSelect}
        className="hidden"
      />

      <div className="space-y-4">
        <div className="w-full text-left bg-white border border-stone-200 rounded-lg p-6 opacity-60 cursor-not-allowed relative">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-stone-100 rounded-lg flex items-center justify-center">
              <Camera className="w-8 h-8 text-stone-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-stone-600">Take Photo</h3>
                <span className="text-xs bg-stone-200 text-stone-600 px-2 py-0.5 rounded-full">Coming Soon</span>
              </div>
              <p className="text-sm text-stone-500 mt-1">Available in future app version. Stay tuned!</p>
            </div>
          </div>
        </div>

        <button 
          onClick={() => handleUploadClick('gallery')}
          className="w-full text-left bg-white border border-stone-200 rounded-lg p-6 hover:shadow-md transition-all duration-200"
        >
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-stone-100 rounded-lg flex items-center justify-center">
              <Upload className="w-8 h-8 text-stone-700" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-stone-900">Upload from Gallery</h3>
              <p className="text-sm text-stone-600">Choose from your photo library</p>
            </div>
          </div>
        </button>
      </div>

      <div className="bg-white border border-stone-200 rounded-lg p-6">
        <h3 className="font-semibold text-stone-900 mb-4">What happens next?</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center border border-stone-200">
              <Sparkles className="w-4 h-4 text-stone-700" />
            </div>
            <span className="text-sm text-stone-700">AI removes background automatically</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center border border-stone-200">
              <Tag className="w-4 h-4 text-stone-700" />
            </div>
            <span className="text-sm text-stone-700">Smart tagging for easy organization</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center border border-stone-200">
              <Check className="w-4 h-4 text-stone-700" />
            </div>
            <span className="text-sm text-stone-700">Added to your virtual closet</span>
          </div>
        </div>
      </div>
    </div>
  );
}

