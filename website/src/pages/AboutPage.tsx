import { useNavigate } from 'react-router-dom';
import { Sparkles, Upload, Wand2, Heart, MessageCircle, ArrowRight, ArrowLeft, Star, CheckCircle, Zap, Shirt, Grid3x3, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function AboutPage() {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/app');
  };

  const steps = [
    {
      number: 'Step 1',
      title: 'Your Clothes',
      description: 'Upload photos of your wardrobe items. Our AI automatically analyzes and tags your items, organizing your collection with smart categorization. You can add items quickly without taking perfect photos.',
      icon: Upload,
      details: 'In a matter of seconds, you can get all of your favorite clothes into the app. Start with our wardrobe templates or create your own from scratch. You can always add photos later, take screenshots, or even grab a URL.'
    },
    {
      number: 'Step 2',
      title: 'AI Recommendations',
      description: 'Get expertly styled outfit recommendations every day, personalized for your style and preferences. Our fine-tuned FashionCLIP model understands fashion compatibility.',
      icon: Wand2,
      details: 'Choose a recommended outfit, edit the ones you like, or build your own. Our AI suggests perfect combinations based on your existing wardrobe, helping you discover new ways to style what you already own.'
    },
    {
      number: 'Step 3',
      title: 'Love What You Wear',
      description: 'Save time, clear the clutter, and stop spending money. Be free to be you. Sustainable fashion is about knowing your personal style so you can be more intentional.',
      icon: Heart,
      details: 'It\'s not about more clothes, it\'s about the right clothes. Shop less. Look better than ever. StyleMe helps you maximize your existing wardrobe and make smarter fashion choices.'
    },
    {
      number: 'Step 4',
      title: 'Ask StyleMe',
      description: 'Get personalized style advice anytime. We\'ve combined StyleMe\'s fashion expertise with AI technology that understands your personal style and wardrobe.',
      icon: MessageCircle,
      details: 'Powered by advanced AI. Created by StyleMe. Ask questions about styling, get outfit suggestions, or learn about fashion compatibility. Your personal stylist is always available.'
    }
  ];

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-6 flex items-center justify-between">
        <button 
          onClick={() => navigate('/')}
          className="flex items-center gap-2 hover:opacity-70 transition-opacity"
        >
          <div className="w-10 h-10 bg-stone-900 rounded-lg flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl brand-font-normal text-stone-900 tracking-tight">StyleMe</span>
        </button>
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="text-stone-700 hover:bg-stone-100"
          >
            <ArrowLeft className="mr-2 w-4 h-4" />
            Back
          </Button>
          <Button
            variant="outline"
            onClick={handleGetStarted}
            className="border-stone-300 hover:bg-stone-100 text-stone-700"
          >
            Get Started
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-16 text-center relative">
        {/* Decorative icons in background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-5">
          <Shirt className="absolute top-10 left-10 w-32 h-32 text-stone-900" />
          <Heart className="absolute top-20 right-20 w-24 h-24 text-stone-900" />
          <Sparkles className="absolute bottom-10 left-20 w-28 h-28 text-stone-900" />
          <Star className="absolute bottom-20 right-10 w-20 h-20 text-stone-900" />
        </div>
        
        <div className="max-w-4xl mx-auto relative z-10">
          {/* Icon above title */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-stone-100 rounded-full flex items-center justify-center">
              <Sparkles className="w-10 h-10 text-stone-700" />
            </div>
          </div>
          
          <h1 className="text-5xl md:text-6xl subtle-artistic-font text-stone-900 mb-4 leading-tight">
            Be Your Own Personal Stylist
          </h1>
          <p className="text-xl md:text-2xl text-stone-600 mb-8 leading-relaxed">
            The smart closet and personal styling app that helps you create perfect outfits
            from your existing wardrobe.
          </p>
          
          {/* Feature highlights with icons */}
          <div className="flex flex-wrap justify-center gap-6">
            <div className="flex items-center gap-2 text-stone-600">
              <Zap className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">AI-Powered</span>
            </div>
            <div className="flex items-center gap-2 text-stone-600">
              <Heart className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">Personal Style</span>
            </div>
            <div className="flex items-center gap-2 text-stone-600">
              <Grid3x3 className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">Smart Closet</span>
            </div>
            <div className="flex items-center gap-2 text-stone-600">
              <Star className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">Expert Styling</span>
            </div>
          </div>
        </div>
      </section>

      {/* Steps Section */}
      <section className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Sparkles className="w-6 h-6 text-stone-600" />
              <h2 className="text-3xl subtle-artistic-font text-stone-900">LET'S TALK DETAILS</h2>
              <Sparkles className="w-6 h-6 text-stone-600" />
            </div>
            <p className="text-lg text-stone-600 flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5 text-stone-500" />
              Save money and time. It's not about more clothes, it's about the right clothes.
            </p>
          </div>

          <div className="space-y-16">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={index} className="flex flex-col md:flex-row gap-8">
                  {/* Step Number, Icon and Title */}
                  <div className="flex-shrink-0 md:w-64">
                    <div className="flex flex-col items-start gap-4">
                      <div className="w-16 h-16 bg-stone-900 rounded-lg flex items-center justify-center">
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-stone-500 uppercase tracking-wider mb-1">
                          {step.number}
                        </div>
                        <h3 className="text-2xl subtle-artistic-font text-stone-900">
                          {step.title}
                        </h3>
                      </div>
                    </div>
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 space-y-4 pt-2">
                    <p className="text-lg text-stone-700 leading-relaxed">
                      {step.description}
                    </p>
                    <p className="text-stone-600 leading-relaxed italic">
                      {step.details}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6 py-20 relative">
        {/* Decorative icons */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-5">
          <Shirt className="absolute top-10 right-20 w-40 h-40 text-stone-900" />
          <Sparkles className="absolute bottom-10 left-20 w-36 h-36 text-stone-900" />
        </div>
        
        <div className="max-w-4xl mx-auto bg-stone-900 rounded-lg p-12 text-center text-white shadow-lg relative z-10">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center backdrop-blur-sm">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
          </div>
          <h2 className="text-4xl subtle-artistic-font mb-4 flex items-center justify-center gap-3">
            <Star className="w-8 h-8 text-white" />
            Ready to transform your wardrobe?
            <Star className="w-8 h-8 text-white" />
          </h2>
          <p className="text-xl mb-8 text-stone-300 flex items-center justify-center gap-2">
            <CheckCircle className="w-5 h-5" />
            Join StyleMe and discover new outfit combinations from your existing clothes.
          </p>
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <div className="flex items-center gap-2 text-stone-300">
              <Zap className="w-4 h-4" />
              <span className="text-sm">AI-Powered</span>
            </div>
            <div className="flex items-center gap-2 text-stone-300">
              <Heart className="w-4 h-4" />
              <span className="text-sm">Personal Style</span>
            </div>
            <div className="flex items-center gap-2 text-stone-300">
              <Shield className="w-4 h-4" />
              <span className="text-sm">Secure & Private</span>
            </div>
          </div>
          <Button
            size="lg"
            onClick={handleGetStarted}
            className="bg-white text-stone-900 hover:bg-stone-100 text-lg px-8 py-6 rounded-md shadow-md"
          >
            Get Started
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-6 py-12 border-t border-stone-200">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center mb-8">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-stone-900 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl brand-font-normal text-stone-900">StyleMe</span>
            </div>
            <div className="flex items-center gap-6">
              <button
                onClick={() => navigate('/')}
                className="text-stone-600 hover:text-stone-900 text-sm transition-colors"
              >
                Home
              </button>
              <button
                onClick={handleGetStarted}
                className="text-stone-600 hover:text-stone-900 text-sm transition-colors"
              >
                Get Started
              </button>
            </div>
          </div>
          <p className="text-center text-stone-600 text-sm">
            © 2025 StyleMe. AI-powered wardrobe styling.
          </p>
        </div>
      </footer>
    </div>
  );
}

