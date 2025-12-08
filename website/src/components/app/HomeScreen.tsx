import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Plus, Loader2, Sparkles, AlertCircle, Shirt, Heart, Star, Wand2, Zap, Grid3x3, Tag, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { ClothingItem, getRecommendations, getImageUrl, healthCheck } from '@/services/api';
import { UploadScreen } from './UploadScreen';
import { FashionLookDisplay } from './FashionLookDisplay';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface HomeScreenProps {
  items: ClothingItem[];
  userId: string;
  onAddItem: (file: File, addToWardrobe?: boolean, metadata?: {
    category?: string;
    color?: string;
    style?: string;
    material?: string;
    pattern?: string;
    season?: string;
    occasion?: string;
    description?: string;
  }) => Promise<void>;
  onItemClick: (item: ClothingItem) => void;
}

export function HomeScreen({ items, userId, onAddItem, onItemClick }: HomeScreenProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [uploadedItem, setUploadedItem] = useState<ClothingItem | null>(null);
  // Separate state for wardrobe and catalog recommendations
  const [wardrobeRecommendations, setWardrobeRecommendations] = useState<ClothingItem[]>([]);
  const [catalogRecommendations, setCatalogRecommendations] = useState<ClothingItem[]>([]);
  const [wardrobeReason, setWardrobeReason] = useState<string | undefined>(undefined);
  const [catalogReason, setCatalogReason] = useState<string | undefined>(undefined);
  // Keep old state for backward compatibility during transition
  const [recommendations, setRecommendations] = useState<ClothingItem[]>([]);
  const [recommendationType, setRecommendationType] = useState<'wardrobe' | 'catalog'>('wardrobe');
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Check API health on mount
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        await healthCheck();
        setApiStatus('online');
      } catch (err) {
        console.error('API health check failed:', err);
        setApiStatus('offline');
      }
    };
    checkApiHealth();
  }, []);

  // Auto-trigger recommendations when coming from "Complete the Look"
  useEffect(() => {
    const state = location.state as { completeTheLook?: boolean; item?: ClothingItem } | null;
    if (state?.completeTheLook && state?.item) {
      const item = state.item;
      
      // Convert item image URL to File for recommendations
      const fetchImageAndGetRecommendations = async () => {
        try {
          setLoadingRecommendations(true);
          setError(null);
          
          // Fetch the image
          const response = await fetch(item.image);
          const blob = await response.blob();
          const file = new File([blob], 'item.jpg', { type: blob.type });
          
          // Format the item for display first
          const uploadedItemData: ClothingItem = {
            ...item,
            id: item.id || 'complete-look-item',
            image: item.image,
          };
          
          setUploadedItem(uploadedItemData);
          
          // Normalize category from frontend format to backend format
          // Frontend: "tops", "bottoms", "layers", "shoes", "dresses", "accessories"
          // Backend: "Tops", "Pants", "Jackets", "Shoes", "Dresses", "Accessories"
          const normalizeCategoryForBackend = (cat: string): string | undefined => {
            if (!cat) return undefined;
            const lower = cat.toLowerCase();
            const mapping: Record<string, string> = {
              'tops': 'Tops',
              'bottoms': 'Pants',
              'layers': 'Jackets',
              'shoes': 'Shoes',
              'dresses': 'Dresses',
              'accessories': 'Accessories'
            };
            return mapping[lower] || undefined;
          };
          
          // Always get BOTH wardrobe and catalog recommendations
          console.log('🔍 Fetching recommendations...');
          const queryCategory = normalizeCategoryForBackend(item.category);
          console.log('📋 Query category:', queryCategory, 'from item.category:', item.category);
          const result = await getRecommendations(userId, file, {
            threshold: 0.7,
            wardrobe_k: 5,  // Always search wardrobe
            catalog_k: 5,   // Always search catalog
            query_category: queryCategory
          });
          
          console.log('✅ Recommendations received:', {
            wardrobe_count: result.wardrobe_items?.length || 0,
            catalog_count: result.catalog_items?.length || 0,
            wardrobe_reason: result.wardrobe_reason,
            catalog_reason: result.catalog_reason
          });
          
          // Format wardrobe recommendations
          const formattedWardrobeRecs = (result.wardrobe_items || []).map(recItem => ({
            ...recItem,
            image: getImageUrl(recItem.image),
            dateAdded: typeof recItem.dateAdded === 'number' 
              ? new Date(recItem.dateAdded * 1000) 
              : new Date(recItem.dateAdded),
          }));
          
          // Format catalog recommendations
          const formattedCatalogRecs = (result.catalog_items || []).map(recItem => ({
            ...recItem,
            image: getImageUrl(recItem.image),
            dateAdded: typeof recItem.dateAdded === 'number' 
              ? new Date(recItem.dateAdded * 1000) 
              : new Date(recItem.dateAdded),
          }));
          
          // Store both separately
          setWardrobeRecommendations(formattedWardrobeRecs);
          setCatalogRecommendations(formattedCatalogRecs);
          
          // Also store reasons for empty results
          setWardrobeReason(result.wardrobe_reason);
          setCatalogReason(result.catalog_reason);
          
          // Clear loading state
          setLoadingRecommendations(false);
          
          // Clear the state to prevent re-triggering
          navigate(location.pathname, { replace: true, state: {} });
        } catch (recommendError) {
          console.error('Failed to get recommendations:', recommendError);
          setError(recommendError instanceof Error ? recommendError.message : 'Failed to get recommendations');
          setLoadingRecommendations(false);
          
          // Still show the item even if recommendations fail
          const uploadedItemData: ClothingItem = {
            ...item,
            id: item.id || 'complete-look-item',
            image: item.image,
          };
          setUploadedItem(uploadedItemData);
          
          // Clear the state
          navigate(location.pathname, { replace: true, state: {} });
        }
      };
      
      fetchImageAndGetRecommendations();
    }
  }, [location.state, userId, navigate, location.pathname, recommendationType]);

  const handleItemClick = (item: ClothingItem) => {
    onItemClick(item);
    navigate('/app/item-details');
  };

  // When an item is uploaded, automatically get recommendations
  const handleUploadComplete = async (file: File, addToWardrobe: boolean, metadata?: {
    category?: string;
    color?: string;
    style?: string;
    material?: string;
    pattern?: string;
    season?: string;
    occasion?: string;
    description?: string;
  }) => {
    try {
      // Upload the item to wardrobe only if user selected to add it
      if (addToWardrobe) {
        try {
          console.log('📤 HomeScreen handleUploadComplete received metadata:', metadata);
          await onAddItem(file, true, metadata);
        } catch (uploadError) {
          // If upload fails, don't close dialog and let UploadScreen handle the error
          console.error('Upload failed:', uploadError);
          throw uploadError; // Re-throw to be caught by UploadScreen
        }
      }
      
      // Close upload dialog
      setIsUploadDialogOpen(false);
      
      // Always get recommendations, regardless of whether item was added to wardrobe
      setLoadingRecommendations(true);
      setError(null);
      
      try {
        // Get recommendations based on current selection
        // For wardrobe: try wardrobe first, fallback to catalog if no results
        // For catalog: only search catalog
        const result = await getRecommendations(userId, file, {
          threshold: 0.7,
          wardrobe_k: recommendationType === 'wardrobe' ? 5 : 0,
          catalog_k: recommendationType === 'wardrobe' ? 3 : 5  // Fallback for wardrobe, primary for catalog
        });
        
        // Format the uploaded item with preview
        const uploadedItemData: ClothingItem = {
          id: 'uploaded-item',
          image: URL.createObjectURL(file),
          category: 'Your Item',
          color: 'Unknown',
          dateAdded: new Date(),
          title: 'Uploaded Item',
        };
        
        setUploadedItem(uploadedItemData);
        
        // Format recommendations
        const formattedRecs = result.items.map(item => ({
          ...item,
          image: getImageUrl(item.image),
          dateAdded: typeof item.dateAdded === 'number' 
            ? new Date(item.dateAdded * 1000) 
            : new Date(item.dateAdded),
        }));
        
        setRecommendations(formattedRecs);
      } catch (recommendError) {
        console.error('Failed to get recommendations:', recommendError);
        setError(recommendError instanceof Error ? recommendError.message : 'Failed to get recommendations');
        setLoadingRecommendations(false);
        // Still show the uploaded item even if recommendations fail
        const uploadedItemData: ClothingItem = {
          id: 'uploaded-item',
          image: URL.createObjectURL(file),
          category: 'Your Item',
          color: 'Unknown',
          dateAdded: new Date(),
          title: 'Uploaded Item',
        };
        setUploadedItem(uploadedItemData);
      }
    } catch (err) {
      // This catch is for upload errors - let UploadScreen handle it
      console.error('Upload process failed:', err);
      throw err; // Re-throw so UploadScreen can show the error
    }
  };

  // Reset when dialog closes
  const handleDialogClose = (open: boolean) => {
    setIsUploadDialogOpen(open);
    if (!open) {
      // Reset state when dialog closes
      setUploadedItem(null);
      setWardrobeRecommendations([]);
      setCatalogRecommendations([]);
      setWardrobeReason(undefined);
      setCatalogReason(undefined);
      setRecommendations([]);
      setError(null);
    }
  };

  // Fetch recommendations when recommendation type changes
  const handleRecommendationTypeChange = async (type: 'wardrobe' | 'catalog') => {
    if (!uploadedItem) return;
    
    setRecommendationType(type);
    setLoadingRecommendations(true);
    setError(null);
    
    try {
      // Fetch the image
      const response = await fetch(uploadedItem.image);
      const blob = await response.blob();
      const file = new File([blob], 'item.jpg', { type: blob.type });
      
      // Get recommendations based on selected type
      // For wardrobe: try wardrobe first, fallback to catalog if no results
      // For catalog: only search catalog
      const result = await getRecommendations(userId, file, {
        threshold: 0.7,
        wardrobe_k: type === 'wardrobe' ? 5 : 0,
        catalog_k: type === 'wardrobe' ? 3 : 5  // Fallback for wardrobe, primary for catalog
      });
      
      // Format recommendations
      const formattedRecs = result.items.map(item => ({
        ...item,
        image: getImageUrl(item.image),
        dateAdded: typeof item.dateAdded === 'number' 
          ? new Date(item.dateAdded * 1000) 
          : new Date(item.dateAdded),
      }));
      
      setRecommendations(formattedRecs);
    } catch (recommendError) {
      console.error('Failed to get recommendations:', recommendError);
      setError(recommendError instanceof Error ? recommendError.message : 'Failed to get recommendations');
    } finally {
      setLoadingRecommendations(false);
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

      <div className="p-6 space-y-8">
        {/* API Status Warning */}
        {apiStatus === 'offline' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-900">API Server Unavailable</p>
              <p className="text-xs text-yellow-700 mt-1">
                Cannot connect to the backend server. Please make sure the API server is running.
              </p>
            </div>
          </div>
        )}


        {/* Add Item CTA - show uploaded item or upload button */}
        <div className="flex flex-col items-center space-y-4 mt-4">
          {uploadedItem ? (
            <div className="w-full bg-gradient-to-br from-stone-50 via-white to-stone-50 rounded-xl border border-stone-200 p-8">
              <div className="flex flex-col items-center justify-center space-y-4">
                <div className="w-32 h-40 rounded-lg overflow-hidden border border-stone-200 bg-white">
                  <ImageWithFallback 
                    src={uploadedItem.image}
                    alt={uploadedItem.title || uploadedItem.category}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="text-center">
                  <h3 className="text-xl subtle-artistic-font text-stone-900 mb-1">Your Item</h3>
                  <p className="text-sm text-stone-500">{uploadedItem.title || uploadedItem.category}</p>
                </div>
              </div>
            </div>
          ) : (
            <Dialog open={isUploadDialogOpen} onOpenChange={handleDialogClose}>
              <DialogTrigger asChild>
                <div className="w-full bg-gradient-to-br from-stone-50 via-white to-stone-50 rounded-xl border border-stone-200 hover:border-stone-300 hover:shadow-lg transition-all duration-300 p-8 cursor-pointer group relative overflow-hidden">
                  {/* Animated background icons on hover - randomly distributed with playful rotation */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none overflow-hidden rounded-xl">
                    {/* Generate icons with random positions for playful distribution */}
                    {(() => {
                      const icons = [Shirt, Heart, Star, Sparkles, Wand2, Zap, Grid3x3, Tag, TrendingUp];
                      const positions = [];
                      
                      // Generate 50 icons with random positions
                      for (let i = 0; i < 50; i++) {
                        const Icon = icons[i % icons.length];
                        // Random positioning with some padding from edges
                        const topPercent = 5 + Math.random() * 85; // 5% to 90%
                        const leftPercent = 3 + Math.random() * 90; // 3% to 93%
                        // Random size between 3-7 for more variety
                        const size = 3 + Math.random() * 4;
                        // Random rotation angle for playful tilt
                        const rotation = (Math.random() - 0.5) * 30; // -15 to +15 degrees
                        // Random delay for staggered animation
                        const delay = Math.random() * 2;
                        // Random animation type
                        const animationType = Math.random() > 0.5 ? 'float' : 'floatReverse';
                        // Random animation duration for more organic feel
                        const duration = 2.5 + Math.random() * 1.5; // 2.5s to 4s
                        
                        positions.push(
                          <Icon
                            key={`icon-${i}`}
                            className={`absolute text-stone-300`}
                            style={{
                              top: `${topPercent}%`,
                              left: `${leftPercent}%`,
                              width: `${size * 4}px`,
                              height: `${size * 4}px`,
                              transform: `rotate(${rotation}deg)`,
                              animation: `${animationType} ${duration}s ease-in-out infinite`,
                              animationDelay: `${delay}s`,
                            }}
                          />
                        );
                      }
                      return positions;
                    })()}
                  </div>
                  
                  <div className="flex flex-col items-center justify-center space-y-4 relative z-10">
                    <div className="relative">
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-stone-200 to-stone-300 flex items-center justify-center group-hover:from-stone-300 group-hover:to-stone-400 transition-all duration-300 shadow-md group-hover:shadow-lg group-hover:scale-110">
                        <Plus size={36} className="text-stone-700 group-hover:text-stone-900 transition-colors" strokeWidth={2.5} />
                      </div>
                      <div className="absolute -top-1 -right-1 w-6 h-6 bg-stone-900 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Sparkles size={14} className="text-white" />
                      </div>
                    </div>
                    <div className="text-center">
                      <h3 className="text-xl subtle-artistic-font text-stone-900 mb-1">Add New Item</h3>
                      <p className="text-sm text-stone-500">Upload to get style recommendations</p>
                    </div>
                  </div>
                </div>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[90vw] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add New Item</DialogTitle>
                </DialogHeader>
                <UploadScreen 
                  userId={userId}
                  onUpload={handleUploadComplete}
                  onComplete={(addToWardrobe) => {
                    // Navigation is handled in handleUploadComplete
                  }}
                  mode="recommendation"
                />
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Complete the Look Section - show title always, content only after upload */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-lg subtle-artistic-font text-stone-900">Complete the Look</h2>
            {uploadedItem && !loadingRecommendations && (
              <button
                onClick={() => {
                  setUploadedItem(null);
                  setWardrobeRecommendations([]);
                  setCatalogRecommendations([]);
                  setWardrobeReason(undefined);
                  setCatalogReason(undefined);
                  setRecommendations([]);
                  setError(null);
                }}
                className="text-sm text-stone-500 hover:text-stone-700"
              >
                Clear
              </button>
            )}
          </div>
          
          {/* Both recommendation sections - always show both */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* From Your Wardrobe Section */}
            <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <Shirt className="w-5 h-5 text-stone-700" />
                <h3 className="text-base font-semibold text-stone-900">From Your Wardrobe</h3>
              </div>
              
              {loadingRecommendations && uploadedItem ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-stone-600 mb-2" />
                  <p className="text-sm text-stone-500">Finding matches...</p>
                </div>
              ) : error && uploadedItem ? (
                <div className="text-center py-8 text-red-500">
                  <p className="text-sm">{error}</p>
                </div>
              ) : uploadedItem && wardrobeRecommendations.length > 0 ? (
                <div className="grid grid-cols-4 gap-2">
                  {wardrobeRecommendations.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleItemClick(item)}
                      className="group relative aspect-square rounded-lg overflow-hidden bg-stone-50 border border-stone-200 hover:shadow-md transition-all"
                    >
                      <ImageWithFallback 
                        src={item.image}
                        alt={item.title || item.category}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    </button>
                  ))}
                </div>
              ) : uploadedItem ? (
                <div className="text-center py-8 text-stone-500">
                  <p className="text-sm">
                    {wardrobeReason === 'empty_wardrobe' 
                      ? 'Currently no available clothes in wardrobe'
                      : wardrobeReason === 'no_matches' || wardrobeReason === 'low_score'
                      ? 'Currently no matching recommendation from wardrobe. Please see shopping recommendations'
                      : 'No matches in your wardrobe'}
                  </p>
                </div>
              ) : (
                <div className="text-center py-12 text-stone-400">
                  <p className="text-sm">Upload an item to see recommendations</p>
                </div>
              )}
            </div>

            {/* Shop Recommendations Section */}
            <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-stone-700" />
                <h3 className="text-base font-semibold text-stone-900">Shop Recommendations</h3>
              </div>
              
              {loadingRecommendations && uploadedItem ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-stone-600 mb-2" />
                  <p className="text-sm text-stone-500">Finding matches...</p>
                </div>
              ) : error && uploadedItem ? (
                <div className="text-center py-8 text-red-500">
                  <p className="text-sm">{error}</p>
                </div>
              ) : uploadedItem && catalogRecommendations.length > 0 ? (
                <div className="grid grid-cols-4 gap-2">
                  {catalogRecommendations.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleItemClick(item)}
                      className="group relative aspect-square rounded-lg overflow-hidden bg-stone-50 border border-stone-200 hover:shadow-md transition-all"
                    >
                      <ImageWithFallback 
                        src={item.image}
                        alt={item.title || item.category}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    </button>
                  ))}
                </div>
              ) : uploadedItem ? (
                <div className="text-center py-8 text-stone-500">
                  <p className="text-sm">
                    {catalogReason === 'no_catalog_matches'
                      ? 'No matching items found in catalog'
                      : 'No catalog recommendations'}
                  </p>
                </div>
              ) : (
                <div className="text-center py-12 text-stone-400">
                  <p className="text-sm">Upload an item to see recommendations</p>
                </div>
              )}
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
