import { useState } from 'react';
import { Send, Bot, User, Sparkles, Camera, ImageIcon, X } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface Message {
  id: number;
  type: 'user' | 'bot';
  content: string;
  userImage?: string;
  outfit?: {
    top: string;
    bottom: string;
    shoes: string;
    accessories?: string;
  };
  explanation?: string;
  isInstantMatch?: boolean;
}

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: 'bot',
      content: "Hi! I'm your AI style assistant. Upload a photo of an item for instant outfit matching, or ask me about styles and occasions!",
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [showImageUpload, setShowImageUpload] = useState(false);

  const suggestedQuestions = [
    "What should I wear to a job interview?",
    "Suggest a date night outfit",
    "Business casual for a meeting",
    "Comfortable travel outfit",
    "What to wear to a wedding?",
    "Casual brunch with friends",
  ];

  const handleImageUpload = () => {
    // Simulate taking a photo of a black shirt
    const uploadedImageUrl = "https://images.unsplash.com/photo-1730952875153-c5c052698508?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHRvcHMlMjBzaGlydHN8ZW58MXx8fHwxNzU4Njg5MTY3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral";

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: "I uploaded this black shirt",
      userImage: uploadedImageUrl,
    };

    // Instant AI response for photo upload
    const botResponse: Message = {
      id: Date.now() + 1,
      type: 'bot',
      content: "Perfect! I can see this is a classic black button-up shirt. Here's a complete outfit that matches its versatile, smart-casual style:",
      outfit: {
        top: uploadedImageUrl,
        bottom: "https://images.unsplash.com/photo-1634564235572-cd6f37694266?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqZWFucyUyMHBhbnRzJTIwYm90dG9tc3xlbnwxfHx8fDE3NTg2ODkxNjl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
        shoes: "https://images.unsplash.com/photo-1651573091103-530884aa68ff?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHNob2VzJTIwc25lYWtlcnN8ZW58MXx8fHwxNzU4Njg5MTcxfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
      },
      explanation: "This combination works because the black shirt is a timeless piece that pairs beautifully with dark denim for a classic look. The white sneakers add a modern, casual touch while keeping the overall style approachable and versatile for multiple occasions.",
      isInstantMatch: true,
    };

    setMessages(prev => [...prev, userMessage, botResponse]);
    setShowImageUpload(false);
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
    };

    const { content, outfit, explanation } = getBotResponse(inputValue);
    const botResponse: Message = {
      id: Date.now() + 1,
      type: 'bot',
      content,
      outfit,
      explanation,
    };

    setMessages(prev => [...prev, userMessage, botResponse]);
    setInputValue('');
  };

  const getBotResponse = (question: string): { content: string; outfit?: any; explanation?: string } => {
    const q = question.toLowerCase();
    
    if (q.includes('interview')) {
      return {
        content: "For a job interview, projecting confidence and professionalism is key. Here's a polished outfit that strikes the perfect balance:",
        outfit: {
          top: "https://images.unsplash.com/photo-1730952875153-c5c052698508?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHRvcHMlMjBzaGlydHN8ZW58MXx8fHwxNzU4Njg5MTY3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          bottom: "https://images.unsplash.com/photo-1634564235572-cd6f37694266?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqZWFucyUyMHBhbnRzJTIwYm90dG9tc3xlbnwxfHx8fDE3NTg2ODkxNjl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          shoes: "https://images.unsplash.com/photo-1651573091103-530884aa68ff?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHNob2VzJTIwc25lYWtlcnN8ZW58MXx8fHwxNzU4Njg5MTcxfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
        },
        explanation: "This combination works because it's professional yet not overly formal. The crisp shirt shows attention to detail, dark denim provides modern sophistication, and clean white shoes keep the look fresh and approachable - perfect for making a positive impression."
      };
    }
    
    if (q.includes('date night')) {
      return {
        content: "For date night, you want to look effortlessly elegant and feel confident. Here's a romantic yet chic ensemble:",
        outfit: {
          top: "https://images.unsplash.com/photo-1495121605193-b116b5b9c5fe?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwY2xvdGhpbmclMjBvdXRmaXR8ZW58MXx8fHwxNzU4Njg5MTY0fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          bottom: "https://images.unsplash.com/photo-1634564235572-cd6f37694266?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqZWFucyUyMHBhbnRzJTIwYm90dG9tc3xlbnwxfHx8fDE3NTg2ODkxNjl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          shoes: "https://images.unsplash.com/photo-1651573091103-530884aa68ff?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHNob2VzJTIwc25lYWtlcnN8ZW58MXx8fHwxNzU4Njg5MTcxfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
        },
        explanation: "This outfit balances romance with comfort. The flowing top adds feminine elegance, well-fitted denim creates a flattering silhouette, and stylish shoes complete the look without being overdressed - perfect for dinner or a casual evening out."
      };
    }
    
    if (q.includes('business casual') || q.includes('meeting')) {
      return {
        content: "Business casual requires professional polish with a relaxed edge. Here's an outfit that commands respect while staying approachable:",
        outfit: {
          top: "https://images.unsplash.com/photo-1730952875153-c5c052698508?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHRvcHMlMjBzaGlydHN8ZW58MXx8fHwxNzU4Njg5MTY3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          bottom: "https://images.unsplash.com/photo-1634564235572-cd6f37694266?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqZWFucyUyMHBhbnRzJTIwYm90dG9tc3xlbnwxfHx8fDE3NTg2ODkxNjl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          shoes: "https://images.unsplash.com/photo-1651573091103-530884aa68ff?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHNob2VzJTIwc25lYWtlcnN8ZW58MXx8fHwxNzU4Njg5MTcxfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
        },
        explanation: "This combination hits the business casual sweet spot perfectly. The structured shirt conveys professionalism, dark denim offers contemporary style while remaining appropriate, and clean sneakers show you're confident and modern in your approach."
      };
    }
    
    if (q.includes('travel')) {
      return {
        content: "Travel outfits should prioritize comfort without sacrificing style. Here's a practical yet put-together look:",
        outfit: {
          top: "https://images.unsplash.com/photo-1730952875153-c5c052698508?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHRvcHMlMjBzaGlydHN8ZW58MXx8fHwxNzU4Njg5MTY3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          bottom: "https://images.unsplash.com/photo-1634564235572-cd6f37694266?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqZWFucyUyMHBhbnRzJTIwYm90dG9tc3xlbnwxfHx8fDE3NTg2ODkxNjl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
          shoes: "https://images.unsplash.com/photo-1651573091103-530884aa68ff?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx3b21lbiUyMHNob2VzJTIwc25lYWtlcnN8ZW58MXx8fHwxNzU4Njg5MTcxfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
        },
        explanation: "Perfect for long flights or road trips! The breathable shirt keeps you comfortable, stretchy denim moves with you during travel, and supportive sneakers are ideal for walking through airports or exploring new destinations."
      };
    }
    
    return {
      content: "Great question! Based on current trends and your style profile, here are my recommendations:",
      explanation: "This versatile combination can be dressed up or down depending on the occasion, making it a perfect go-to outfit choice."
    };
  };

  const handleSuggestedQuestion = (question: string) => {
    setInputValue(question);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-pink-100 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-purple-500 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-800">Style Assistant</h1>
            <p className="text-sm text-gray-500">Online • Ready to help</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'bot' && (
              <div className="w-8 h-8 bg-gradient-to-br from-pink-500 to-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            
            <div className={`max-w-[80%] ${message.type === 'user' ? 'order-1' : ''}`}>
              <Card
                className={`p-3 border-0 ${
                  message.type === 'user'
                    ? 'bg-gradient-to-r from-pink-500 to-purple-500 text-white rounded-t-2xl rounded-bl-2xl'
                    : 'bg-white/70 backdrop-blur-sm text-gray-800 rounded-t-2xl rounded-br-2xl'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                {/* User uploaded image */}
                {message.userImage && (
                  <div className="mt-2 w-24 h-24 rounded-xl overflow-hidden bg-gray-100">
                    <ImageWithFallback 
                      src={message.userImage}
                      alt="Uploaded item"
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
              </Card>

              {/* Outfit Preview */}
              {message.outfit && (
                <Card className="mt-3 bg-white/70 backdrop-blur-sm border-0 rounded-2xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-purple-500" />
                    <span className="text-sm font-medium text-gray-700">
                      {message.isInstantMatch ? 'Instant Match' : 'Suggested Outfit'}
                    </span>
                    {message.isInstantMatch && (
                      <div className="ml-auto bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">
                        AI Match
                      </div>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <div className="w-full h-20 rounded-xl overflow-hidden bg-gray-100">
                        <ImageWithFallback 
                          src={message.outfit.top}
                          alt="Top"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <p className="text-xs text-gray-600 mt-1 text-center">Top</p>
                    </div>
                    <div className="flex-1">
                      <div className="w-full h-20 rounded-xl overflow-hidden bg-gray-100">
                        <ImageWithFallback 
                          src={message.outfit.bottom}
                          alt="Bottom"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <p className="text-xs text-gray-600 mt-1 text-center">Bottom</p>
                    </div>
                    <div className="flex-1">
                      <div className="w-full h-20 rounded-xl overflow-hidden bg-gray-100">
                        <ImageWithFallback 
                          src={message.outfit.shoes}
                          alt="Shoes"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <p className="text-xs text-gray-600 mt-1 text-center">Shoes</p>
                    </div>
                  </div>
                  
                  {/* Style Explanation */}
                  {message.explanation && (
                    <div className="mt-3 p-3 bg-purple-50 rounded-xl">
                      <p className="text-xs text-purple-700 font-medium mb-1">Why this works:</p>
                      <p className="text-xs text-purple-600">{message.explanation}</p>
                    </div>
                  )}
                  
                  <div className="flex gap-2 mt-3">
                    <Button className="flex-1 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 text-white rounded-xl text-sm">
                      Try This Outfit
                    </Button>
                    <Button variant="outline" size="sm" className="rounded-xl border-pink-200 text-pink-600 hover:bg-pink-50">
                      Save
                    </Button>
                  </div>
                </Card>
              )}
            </div>

            {message.type === 'user' && (
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-gray-600" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="p-4 border-t border-pink-100">
          <p className="text-sm text-gray-600 mb-3">Try these options:</p>
          
          {/* Photo Upload Option */}
          <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-0 rounded-2xl p-4 mb-4">
            <div className="flex items-center gap-3 mb-2">
              <Camera className="w-5 h-5 text-purple-600" />
              <span className="font-medium text-gray-800">Upload a clothing item</span>
            </div>
            <p className="text-sm text-gray-600 mb-3">Get instant outfit suggestions by uploading a photo</p>
            <Button 
              onClick={handleImageUpload}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl text-sm"
            >
              <Camera className="w-4 h-4 mr-2" />
              Take Photo / Upload
            </Button>
          </Card>
          
          {/* Or divider */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-gray-200"></div>
            <span className="text-xs text-gray-500">or ask about</span>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>
          
          {/* Text Questions */}
          <div className="grid grid-cols-2 gap-2">
            {suggestedQuestions.map((question, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleSuggestedQuestion(question)}
                className="text-left justify-start rounded-xl border-pink-200 text-gray-600 hover:bg-pink-50 text-xs p-2 h-auto"
              >
                {question}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-pink-100 bg-white/80 backdrop-blur-sm">
        <div className="flex gap-2">
          <Button
            onClick={() => setShowImageUpload(true)}
            variant="outline"
            className="rounded-2xl border-pink-200 text-gray-600 hover:bg-pink-50 px-3"
          >
            <Camera size={16} />
          </Button>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about styling, occasions, or trends..."
            className="flex-1 rounded-2xl border-pink-200 bg-white/70"
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <Button
            onClick={handleSendMessage}
            className="bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 text-white rounded-2xl px-4"
          >
            <Send size={16} />
          </Button>
        </div>
        
        {/* Image Upload Modal */}
        {showImageUpload && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="bg-white m-4 p-6 rounded-3xl max-w-sm w-full">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-800">Upload Item Photo</h3>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setShowImageUpload(false)}
                  className="p-1"
                >
                  <X size={16} />
                </Button>
              </div>
              
              <div className="space-y-3">
                <Button 
                  onClick={handleImageUpload}
                  className="w-full bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 text-white rounded-2xl py-3"
                >
                  <Camera className="w-5 h-5 mr-2" />
                  Take Photo
                </Button>
                
                <Button 
                  onClick={handleImageUpload}
                  variant="outline"
                  className="w-full rounded-2xl border-pink-200 text-gray-600 hover:bg-pink-50 py-3"
                >
                  <ImageIcon className="w-5 h-5 mr-2" />
                  Choose from Gallery
                </Button>
              </div>
              
              <p className="text-xs text-gray-500 text-center mt-4">
                Upload any clothing item to get instant outfit suggestions
              </p>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}