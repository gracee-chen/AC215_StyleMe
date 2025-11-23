import { useState, useRef } from 'react';
import { Camera, Upload, Image as ImageIcon, Sparkles, Tag, Check } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';

interface UploadScreenProps {
  userId: string;
  onUpload: (file: File) => Promise<void>;
  onComplete?: () => void;
}

export function UploadScreen({ userId, onUpload, onComplete }: UploadScreenProps) {
  const [uploadStep, setUploadStep] = useState('upload'); // 'upload', 'processing', 'tagging', 'success'
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const suggestedTags = [
    'Casual', 'Formal', 'Summer', 'Winter', 'Work', 'Weekend',
    'Cotton', 'Silk', 'Denim', 'Black', 'White', 'Blue',
    'Shirt', 'Pants', 'Dress', 'Shoes', 'Accessories'
  ];

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setUploadStep('tagging');
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
      await onUpload(selectedFile);
      setUploadStep('success');
      setTimeout(() => {
        setUploadStep('upload');
        setSelectedFile(null);
        setPreviewUrl(null);
        setSelectedTags([]);
        if (onComplete) onComplete();
      }, 2000);
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStep('upload');
      alert('Failed to upload image. Please try again.');
    }
  };

  if (uploadStep === 'processing') {
    return (
      <div className="p-4 flex items-center justify-center min-h-[600px]">
        <Card className="bg-white/70 backdrop-blur-sm border-0 rounded-3xl p-8 text-center max-w-sm w-full">
          <div className="animate-spin w-16 h-16 mx-auto mb-4">
            <Sparkles className="w-16 h-16 text-purple-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Processing Image</h2>
          <p className="text-gray-600 mb-4">Our AI is removing the background and analyzing your item...</p>
          <div className="space-y-2 text-sm text-gray-500">
            <div className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              <span>Uploading image...</span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              <span>Removing background...</span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              <span>Adding to wardrobe...</span>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (uploadStep === 'success') {
    return (
      <div className="p-4 flex items-center justify-center min-h-[600px]">
        <Card className="bg-white/70 backdrop-blur-sm border-0 rounded-3xl p-8 text-center max-w-sm w-full">
          <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
            <Check className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Upload Successful!</h2>
          <p className="text-gray-600">Your item has been added to your wardrobe.</p>
        </Card>
      </div>
    );
  }

  if (uploadStep === 'tagging') {
    return (
      <div className="p-4 space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">Tag Your Item</h1>
          <p className="text-gray-600 mt-1">Help our AI understand your item better</p>
        </div>

        <Card className="bg-white/70 backdrop-blur-sm border-0 rounded-3xl p-6">
          {previewUrl ? (
            <div className="w-32 h-32 mx-auto rounded-2xl mb-4 overflow-hidden">
              <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
            </div>
          ) : (
            <div className="w-32 h-32 mx-auto bg-gray-100 rounded-2xl mb-4 flex items-center justify-center">
              <ImageIcon className="w-16 h-16 text-gray-400" />
            </div>
          )}
          <p className="text-center text-gray-600 mb-6">Preview of your item</p>

          <div className="space-y-4">
            <div>
              <Label htmlFor="item-name">Item Name</Label>
              <Input 
                id="item-name"
                placeholder="e.g., Blue Cotton T-Shirt"
                className="mt-2 rounded-xl border-pink-200"
              />
            </div>

            <div>
              <Label>Suggested Tags</Label>
              <div className="flex flex-wrap gap-2 mt-2">
                {suggestedTags.map((tag) => (
                  <Badge
                    key={tag}
                    variant={selectedTags.includes(tag) ? "default" : "outline"}
                    className={`cursor-pointer rounded-full px-3 py-1 ${
                      selectedTags.includes(tag)
                        ? 'bg-gradient-to-r from-pink-500 to-purple-500 text-white'
                        : 'border-pink-200 text-gray-600 hover:bg-pink-50'
                    }`}
                    onClick={() => toggleTag(tag)}
                  >
                    {tag}
                    {selectedTags.includes(tag) && (
                      <Check className="w-3 h-3 ml-1" />
                    )}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <Label htmlFor="custom-tags">Add Custom Tags</Label>
              <Input 
                id="custom-tags"
                placeholder="Add custom tags separated by commas"
                className="mt-2 rounded-xl border-pink-200"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <Button 
              variant="outline" 
              onClick={() => setUploadStep('upload')}
              className="flex-1 rounded-xl border-pink-200 text-gray-600"
            >
              Back
            </Button>
            <Button 
              onClick={handleFinish}
              className="flex-1 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 text-white rounded-xl"
            >
              Add to Closet
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-800">Upload Item</h1>
        <p className="text-gray-600 mt-1">Add new items to your virtual closet</p>
      </div>

      {/* Hidden file inputs */}
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

      {/* Upload Options */}
      <div className="space-y-4">
        <Card className="bg-white/70 backdrop-blur-sm border-0 rounded-3xl p-6 hover:shadow-lg transition-all duration-200">
          <button 
            onClick={() => handleUploadClick('camera')}
            className="w-full text-left"
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-pink-100 to-purple-100 rounded-2xl flex items-center justify-center">
                <Camera className="w-8 h-8 text-purple-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-800">Take Photo</h3>
                <p className="text-sm text-gray-600">Use your camera to capture an item</p>
              </div>
            </div>
          </button>
        </Card>

        <Card className="bg-white/70 backdrop-blur-sm border-0 rounded-3xl p-6 hover:shadow-lg transition-all duration-200">
          <button 
            onClick={() => handleUploadClick('gallery')}
            className="w-full text-left"
          >
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-pink-100 to-purple-100 rounded-2xl flex items-center justify-center">
                <Upload className="w-8 h-8 text-purple-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-800">Upload from Gallery</h3>
                <p className="text-sm text-gray-600">Choose from your photo library</p>
              </div>
            </div>
          </button>
        </Card>
      </div>

      {/* Features */}
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-0 rounded-3xl p-6">
        <h3 className="font-semibold text-gray-800 mb-4">What happens next?</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-purple-600" />
            </div>
            <span className="text-sm text-gray-700">AI removes background automatically</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
              <Tag className="w-4 h-4 text-purple-600" />
            </div>
            <span className="text-sm text-gray-700">Smart tagging for easy organization</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
              <Check className="w-4 h-4 text-purple-600" />
            </div>
            <span className="text-sm text-gray-700">Added to your virtual closet</span>
          </div>
        </div>
      </Card>

    </div>
  );
}
}