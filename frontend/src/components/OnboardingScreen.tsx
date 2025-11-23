import { Button } from "./ui/button";

interface OnboardingScreenProps {
  onGetStarted: () => void;
}

export function OnboardingScreen({ onGetStarted }: OnboardingScreenProps) {
  return (
    <div className="h-full flex flex-col items-center justify-center p-8 bg-white">
      <div className="w-full max-w-xs flex flex-col items-center space-y-16">
        {/* Logo Placeholder */}
        <div className="w-48 h-16 bg-gray-100 text-gray-900 flex items-center justify-center font-bold tracking-widest text-2xl rounded-lg">
          StyleMe
        </div>

        <div className="space-y-8 text-center w-full">
            {/* Tagline */}
            <h1 className="text-3xl font-light text-gray-900 leading-tight">
            Your wardrobe,<br />
            <span className="font-semibold">styled smarter.</span>
            </h1>

            {/* Explainer Box */}
            <div className="w-full p-6 bg-pink-50/50 border border-pink-100 text-center rounded-3xl">
            <p className="text-gray-600 text-lg">
                Upload your clothes to get simple outfit suggestions.
            </p>
            </div>
        </div>

        {/* CTA Button */}
        <Button 
          onClick={onGetStarted}
          className="w-full py-7 text-base font-semibold bg-gray-900 hover:bg-gray-800 text-white rounded-2xl tracking-wider uppercase"
        >
          Get Started
        </Button>
      </div>
    </div>
  );
}
