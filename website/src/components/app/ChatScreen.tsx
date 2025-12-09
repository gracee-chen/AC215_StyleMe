import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { MessageCircle, Send, Image as ImageIcon, Loader2, X, Sparkles, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { sendChatMessage, ChatMessage, ItemAnalysis } from '@/services/api';

// Utility function to convert image file to base64
async function imageToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

interface Message {
  id: string;
  type: 'user' | 'stylist';
  content: string;
  imageUrl?: string;
  timestamp: Date;
}

export function ChatScreen() {
  const location = useLocation();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'stylist',
      content: "Hi! I'm your AI stylist. What would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<ItemAnalysis | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hasProcessedLocationState = useRef(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Pre-fill image when coming from ItemDetailsScreen (only once)
  useEffect(() => {
    if (hasProcessedLocationState.current) return;
    
    const state = location.state as { itemImage?: string; itemTitle?: string } | null;
    if (state?.itemImage) {
      // Just set the image preview, don't auto-send
      setImagePreview(state.itemImage);
      // Clear the state to prevent re-triggering
      window.history.replaceState({}, document.title);
      hasProcessedLocationState.current = true;
    }
  }, [location.state]);

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSendMessage = async () => {
    const text = inputValue.trim();
    if (!text && !selectedImage && !imagePreview) return;

    // Save image preview URL before clearing
    const currentImagePreview = imagePreview;
    const currentSelectedImage = selectedImage;

    // Clear image preview immediately - use direct state updates for immediate effect
    setImagePreview(null);
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: text || (currentImagePreview ? 'What styling advice can you give me about this item?' : ''),
      imageUrl: currentImagePreview || undefined,
      timestamp: new Date(),
    };

    // Don't add user message yet - we'll add it after converting image to base64
    // This ensures the message in history has the base64 image for future conversations
    setInputValue('');
    setIsLoading(true);

    try {
      // Convert current image to base64 if present (using saved values)
      // This ensures we have base64 for the current message and can store it in history
      let imageBase64: string | undefined;
      if (currentSelectedImage) {
        // If we have a File object, convert it to base64
        imageBase64 = await imageToBase64(currentSelectedImage);
      } else if (currentImagePreview && !currentImagePreview.startsWith('data:')) {
        // If imagePreview is a URL (not base64), convert it to base64
        try {
          const response = await fetch(currentImagePreview);
          if (!response.ok) {
            throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
          }
          const blob = await response.blob();
          const file = new File([blob], 'image.jpg', { type: blob.type });
          imageBase64 = await imageToBase64(file);
        } catch (error) {
          console.error('Failed to convert URL to base64:', error);
          // If conversion fails, we'll continue without the image
          imageBase64 = undefined;
        }
      } else if (currentImagePreview && currentImagePreview.startsWith('data:')) {
        // imagePreview is already a base64 data URL
        imageBase64 = currentImagePreview;
      }

      // Update user message with base64 image (if available)
      if (imageBase64) {
        userMessage.imageUrl = imageBase64;
      }

      // Prepare messages for API - include images from history (they should already be base64)
      // Previous messages with images will have base64 data URLs, which work fine
      const chatMessages: ChatMessage[] = messages
        .filter((msg) => msg.type === 'stylist' || msg.content)
        .map((msg) => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content,
          // Include imageUrl from previous messages - they should be base64 data URLs
          // If it's a localhost URL, we'll skip it (it wasn't converted properly)
          imageUrl: msg.imageUrl && msg.imageUrl.startsWith('data:') ? msg.imageUrl : undefined,
        }));

      // Add current user message with base64 image
      chatMessages.push({
        role: 'user',
        content: userMessage.content,
        imageUrl: userMessage.imageUrl, // This is now base64 if available
      });

      // Add user message to state with base64 image (for display and future conversations)
      setMessages((prev) => [...prev, userMessage]);
      
      // Convert image to File if we have base64 from URL, otherwise use the File object
      let imageFileForAPI: File | undefined = currentSelectedImage;
      if (!imageFileForAPI && imageBase64 && imageBase64.startsWith('data:')) {
        // Convert base64 data URL to File object for the API call
        try {
          const response = await fetch(imageBase64);
          const blob = await response.blob();
          imageFileForAPI = new File([blob], 'image.jpg', { type: blob.type });
        } catch (error) {
          console.warn('Could not convert base64 to File, continuing without image:', error);
        }
      }
      
      const response = await sendChatMessage(chatMessages, imageFileForAPI);

      if (response.error) {
        // Show user-friendly error message
        let errorContent = "Sorry, I'm having trouble connecting right now.";
        
        // Provide specific guidance for quota errors
        if (response.error.includes('quota') || response.error.includes('billing')) {
          errorContent = "Sorry, I'm having trouble connecting right now. " + response.error + " For more information, please visit https://platform.openai.com/account/billing";
        } else if (response.error.includes('rate limit')) {
          errorContent = "I'm receiving too many requests right now. Please wait a moment and try again.";
        } else if (response.error.includes('downloading') || response.error.includes('fetch')) {
          // If it's an image download error, provide a more helpful message
          errorContent = "Sorry, I couldn't load the image. Please try uploading the image again or continue with a text message.";
        } else {
          errorContent = `Sorry, I'm having trouble connecting right now. ${response.error}`;
        }
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'stylist',
          content: errorContent,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else {
        // Add stylist response
        const stylistMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'stylist',
          content: response.message,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, stylistMessage]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'stylist',
        content: "I'm sorry, something went wrong. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleAnalyzeItem = async () => {
    if (!selectedImage) return;

    setIsAnalyzing(true);
    try {
      const analysis = await analyzeClothingItem(selectedImage);
      setAnalysisResult(analysis);

      // Format analysis as a structured message
      const analysisParts: string[] = [];
      
      if (analysis.category) {
        analysisParts.push(`**Category**: ${analysis.category}`);
      }
      if (analysis.color) {
        analysisParts.push(`**Color**: ${analysis.color}`);
      }
      if (analysis.style) {
        analysisParts.push(`**Style**: ${analysis.style}`);
      }
      if (analysis.material) {
        analysisParts.push(`**Material**: ${analysis.material}`);
      }
      if (analysis.pattern) {
        analysisParts.push(`**Pattern**: ${analysis.pattern}`);
      }
      if (analysis.season) {
        analysisParts.push(`**Season**: ${analysis.season}`);
      }
      if (analysis.occasion) {
        analysisParts.push(`**Occasion**: ${analysis.occasion}`);
      }
      if (analysis.description) {
        analysisParts.push(`\n**Description**: ${analysis.description}`);
      }

      const analysisText = analysisParts.length > 0
        ? `Here's my detailed analysis of this item:\n\n${analysisParts.join('\n')}`
        : `I analyzed the item, but couldn't extract specific details. Could you describe it to me?`;

      const analysisMessage: Message = {
        id: Date.now().toString(),
        type: 'stylist',
        content: analysisText,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, analysisMessage]);
    } catch (error) {
      console.error('Analysis failed:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'stylist',
        content: `Sorry, I couldn't analyze this item. ${error instanceof Error ? error.message : 'Please try again.'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const suggestedQuestions = [
    "I need a holiday party outfit!",
    "How do I wear wide-leg jeans?",
    "I need some new work clothes.",
    "What do I wear with this sweater?",
  ];

  return (
    <div className="min-h-screen bg-stone-50 pb-20 flex flex-col">
      {/* Header */}
      <div className="pt-8 pb-4 bg-stone-50 px-6 flex justify-center items-center shadow-sm sticky top-0 z-10 border-b border-stone-200">
        <div className="w-32 h-10 bg-stone-900 text-white flex items-center justify-center text-base rounded tracking-widest">
          <span className="brand-font-normal text-lg">StyleMe</span>
        </div>
      </div>

      {/* Chat Title */}
      <div className="bg-stone-50 px-6 py-8 text-center relative overflow-hidden border-b border-stone-200">
        <h1 className="text-3xl subtle-artistic-font text-stone-800 mb-2">AI Stylist</h1>
        <p className="text-stone-500 text-sm font-medium">Your personal fashion advisor, powered by AI</p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 bg-stone-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start gap-2 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'stylist' && (
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-stone-800 to-stone-900 flex items-center justify-center text-white flex-shrink-0 shadow-md border-2 border-stone-700/30">
                <Sparkles className="w-5 h-5" strokeWidth={2} />
              </div>
            )}
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-white text-stone-900 shadow-sm border border-stone-200'
                  : 'bg-gradient-to-br from-stone-50 to-stone-100 text-stone-900 border border-stone-200 shadow-sm'
              }`}
            >
              
              {message.imageUrl && (
                <div className={`mb-2 rounded-lg overflow-hidden ${
                  message.type === 'user' 
                    ? 'border-2 border-stone-200' 
                    : 'border-2 border-stone-300'
                }`}>
                  <img
                    src={message.imageUrl}
                    alt="Uploaded item"
                    className="w-full h-auto max-h-48 object-cover"
                  />
                </div>
              )}
              
              <p className={`text-sm leading-relaxed whitespace-pre-wrap ${
                message.type === 'user' ? 'text-stone-900' : 'text-stone-900'
              }`}>
                {message.content}
              </p>
              {message.type === 'stylist' && (
                <div className="mt-2 flex items-center gap-1 text-xs text-stone-400">
                  <Sparkles className="w-3 h-3" />
                  <span>AI Stylist</span>
                </div>
              )}
            </div>
            {message.type === 'user' && (
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-stone-300 to-stone-400 flex items-center justify-center text-white flex-shrink-0 shadow-md border-2 border-stone-500/30">
                <User className="w-5 h-5" strokeWidth={2} />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-stone-800 to-stone-900 flex items-center justify-center text-white flex-shrink-0 shadow-md border-2 border-stone-700/30">
              <Sparkles className="w-5 h-5" strokeWidth={2} />
            </div>
            <div className="bg-stone-100 text-stone-900 rounded-2xl px-4 py-3 flex items-center gap-2 border border-stone-200">
              <Loader2 className="w-4 h-4 animate-spin text-stone-600" />
              <span className="text-sm">AI Stylist is typing...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length <= 1 && (
        <div className="px-4 pb-4 space-y-2">
          <p className="text-xs text-stone-500 px-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => setInputValue(question)}
                className="px-3 py-2 bg-white border border-stone-200 rounded-full text-xs text-stone-700 hover:bg-stone-100 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Image Preview */}
      {imagePreview && (
        <div className="px-4 pb-2">
          <div className="relative inline-block">
            <div className="w-24 h-24 rounded-lg overflow-hidden border-2 border-stone-300 bg-white">
              <img
                src={imagePreview}
                alt="Preview"
                className="w-full h-full object-cover"
              />
            </div>
            <button
              onClick={removeImage}
              className="absolute -top-2 -right-2 w-6 h-6 bg-stone-900 text-white rounded-full flex items-center justify-center hover:bg-stone-800 transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="bg-stone-50 border-t border-stone-200 px-4 py-3 sticky bottom-0">
        <div className="flex items-end gap-2">
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            onChange={handleImageSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-stone-600 hover:text-stone-900 hover:bg-stone-100 rounded-lg transition-colors"
            title="Upload image"
          >
            <ImageIcon size={20} />
          </button>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask your stylist..."
            className="flex-1 rounded-lg border-stone-300 focus:border-stone-500"
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={(!inputValue.trim() && !selectedImage) || isLoading}
            className="bg-stone-900 hover:bg-stone-800 text-white rounded-lg px-4"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

