import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Sparkles, Upload, Wand2, Grid3x3, ArrowRight, Shirt, Heart, Zap, CheckCircle, Star, TrendingUp, Users, Shield, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import FeedbackBanner from '@/components/FeedbackBanner';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';

// Brand item component with logo
function BrandItem({ brand }: { brand: { name: string; logo: string } }) {
  const [logoError, setLogoError] = useState(false);
  
  return (
    <div className="flex items-center gap-3 text-2xl font-semibold text-stone-700 whitespace-nowrap tracking-wide hover:text-stone-900 transition-colors group">
      {!logoError ? (
        <img 
          src={brand.logo}
          alt={`${brand.name} logo`}
          className="w-6 h-6 object-contain opacity-70 group-hover:opacity-100 transition-opacity"
          onError={() => setLogoError(true)}
        />
      ) : (
        <Shirt className="w-5 h-5 text-stone-400 group-hover:text-stone-600 transition-colors" />
      )}
      {brand.name}
    </div>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/app');
  };

  // Brand data with logos
  const brands = [
    { name: 'Net-a-Porter', logo: 'https://logo.clearbit.com/net-a-porter.com' },
    { name: 'SSENSE', logo: 'https://logo.clearbit.com/ssense.com' },
    { name: 'Matches Fashion', logo: 'https://logo.clearbit.com/matchesfashion.com' },
    { name: 'Mytheresa', logo: 'https://logo.clearbit.com/mytheresa.com' },
    { name: '24S', logo: 'https://logo.clearbit.com/24s.com' },
    { name: 'Moda Operandi', logo: 'https://logo.clearbit.com/modaoperandi.com' },
    { name: 'Farfetch', logo: 'https://logo.clearbit.com/farfetch.com' },
    { name: 'The Outnet', logo: 'https://logo.clearbit.com/theoutnet.com' },
    { name: 'FWRD', logo: 'https://logo.clearbit.com/fwrd.com' },
    { name: 'Revolve', logo: 'https://logo.clearbit.com/revolve.com' },
  ];

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Feedback Banner */}
      <FeedbackBanner />
      
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-stone-900 rounded-lg flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl brand-font-normal text-stone-900 tracking-tight">StyleMe</span>
        </div>
        <Button
          variant="outline"
          onClick={handleGetStarted}
          className="border-stone-300 hover:bg-stone-100 text-stone-700"
        >
          Get Started
        </Button>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 text-center relative">
        {/* Decorative icons in background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-5">
          <Shirt className="absolute top-20 left-10 w-32 h-32 text-stone-900" />
          <Heart className="absolute top-40 right-20 w-24 h-24 text-stone-900" />
          <Sparkles className="absolute bottom-20 left-20 w-28 h-28 text-stone-900" />
          <Star className="absolute bottom-40 right-10 w-20 h-20 text-stone-900" />
        </div>
        
        <div className="max-w-4xl mx-auto relative z-10">
          {/* Icon above title */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-stone-100 rounded-full flex items-center justify-center">
              <Sparkles className="w-10 h-10 text-stone-700" />
            </div>
          </div>
          
          <h1 className="text-6xl md:text-7xl subtle-artistic-font text-stone-900 mb-6 leading-tight">
            Your wardrobe,
            <br />
            <span className="text-stone-700">
              styled smarter.
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-stone-600 mb-8 leading-relaxed">
            AI-powered fashion recommendations that help you create perfect outfits
            from your existing wardrobe.
          </p>
          
          {/* Feature highlights with icons */}
          <div className="flex flex-wrap justify-center gap-6 mb-12">
            <div className="flex items-center gap-2 text-stone-600">
              <Zap className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">AI-Powered</span>
            </div>
            <div className="flex items-center gap-2 text-stone-600">
              <Shield className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">Smart Matching</span>
            </div>
            <div className="flex items-center gap-2 text-stone-600">
              <Clock className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">Save Time</span>
            </div>
            <div className="flex items-center gap-2 text-stone-600">
              <TrendingUp className="w-5 h-5 text-stone-700" />
              <span className="text-sm font-medium">Better Style</span>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              onClick={handleGetStarted}
              className="bg-stone-900 hover:bg-stone-800 text-white text-lg px-8 py-6 rounded-md shadow-md hover:shadow-lg transition-all"
            >
              Get Started
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/about')}
              className="border-2 border-stone-300 text-stone-700 text-lg px-8 py-6 rounded-md hover:bg-stone-100"
            >
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Brands Section - Scrolling */}
      <section className="py-10 bg-white border-y border-stone-200 overflow-hidden relative">
        <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none"></div>
        <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none"></div>
        <div className="relative">
          <div className="flex animate-scroll">
            {/* First set of brands */}
            <div className="flex items-center gap-20 px-20 shrink-0">
              {brands.map((brand, idx) => (
                <BrandItem key={`brand-1-${idx}`} brand={brand} />
              ))}
            </div>
            {/* Duplicate set for seamless loop */}
            <div className="flex items-center gap-20 px-20 shrink-0">
              {brands.map((brand, idx) => (
                <BrandItem key={`brand-2-${idx}`} brand={brand} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-16">
            <Zap className="w-8 h-8 text-stone-700" />
            <h2 className="text-4xl subtle-artistic-font text-center text-stone-900">
              How It Works
            </h2>
            <Zap className="w-8 h-8 text-stone-700" />
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-lg p-8 shadow-sm hover:shadow-md transition-all border border-stone-200 group">
              <div className="w-16 h-16 bg-stone-100 rounded-lg flex items-center justify-center mb-6 group-hover:bg-stone-200 transition-colors">
                <Upload className="w-8 h-8 text-stone-700" />
              </div>
              <h3 className="text-2xl subtle-artistic-font text-stone-900 mb-4 flex items-center gap-2">
                Upload Your Clothes
                <CheckCircle className="w-5 h-5 text-stone-500" />
              </h3>
              <p className="text-stone-600 leading-relaxed">
                Simply upload photos of your wardrobe items. Our AI automatically analyzes and tags
                your items, organizing your collection with smart categorization.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-lg p-8 shadow-sm hover:shadow-md transition-all border border-stone-200 group">
              <div className="w-16 h-16 bg-stone-100 rounded-lg flex items-center justify-center mb-6 group-hover:bg-stone-200 transition-colors">
                <Wand2 className="w-8 h-8 text-stone-700" />
              </div>
              <h3 className="text-2xl subtle-artistic-font text-stone-900 mb-4 flex items-center gap-2">
                AI-Powered Matching
                <Star className="w-5 h-5 text-stone-500" />
              </h3>
              <p className="text-stone-600 leading-relaxed">
                Our fine-tuned FashionCLIP model understands fashion compatibility and suggests
                perfect outfit combinations.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-lg p-8 shadow-sm hover:shadow-md transition-all border border-stone-200 group">
              <div className="w-16 h-16 bg-stone-100 rounded-lg flex items-center justify-center mb-6 group-hover:bg-stone-200 transition-colors">
                <Grid3x3 className="w-8 h-8 text-stone-700" />
              </div>
              <h3 className="text-2xl subtle-artistic-font text-stone-900 mb-4 flex items-center gap-2">
                Complete the Look
                <Heart className="w-5 h-5 text-stone-500" />
              </h3>
              <p className="text-stone-600 leading-relaxed">
                Select any item from your wardrobe and get personalized recommendations to complete
                your outfit.
              </p>
            </div>
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
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm">Proven results</span>
            </div>
            <div className="flex items-center gap-2 text-stone-300">
              <Shield className="w-4 h-4" />
              <span className="text-sm">Secure & private</span>
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
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <div className="w-8 h-8 bg-stone-900 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl brand-font-normal text-stone-900">StyleMe</span>
          </div>
          <p className="text-stone-600 text-sm">
            © 2025 StyleMe. AI-powered wardrobe styling.
          </p>
        </div>
      </footer>
    </div>
  );
}

