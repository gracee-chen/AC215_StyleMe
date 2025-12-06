import { useState } from 'react';
import { X } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

export default function FeedbackBanner() {
  const [isVisible, setIsVisible] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    rating: '',
    feedback: '',
    suggestions: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Here you would typically send the data to your backend
    console.log('Feedback submitted:', formData);
    alert('Thank you for your feedback! We appreciate your input and will consider your suggestions.');
    setIsDialogOpen(false);
    setFormData({
      name: '',
      email: '',
      rating: '',
      feedback: '',
      suggestions: ''
    });
  };

  if (!isVisible) return null;

  return (
    <>
      <div className="bg-stone-800 text-stone-100 py-3 px-4 relative">
        <div className="container mx-auto flex items-center justify-center gap-2 text-sm md:text-base">
          <span>Have feedback? We'd love to hear from you.</span>
          <button
            onClick={() => setIsDialogOpen(true)}
            className="underline hover:text-white font-medium transition-colors ml-1"
          >
            Share your thoughts
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="absolute right-4 top-1/2 -translate-y-1/2 hover:opacity-70 transition-opacity text-stone-300"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl subtle-artistic-font text-stone-900">
              Share Your Feedback
            </DialogTitle>
            <DialogDescription className="text-stone-600">
              Your feedback helps us improve StyleMe. We appreciate your time and input.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-6 mt-4">
            {/* Basic Information */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="name" className="text-stone-700">
                  Name <span className="text-stone-500 font-normal">(optional)</span>
                </Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter your name"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="email" className="text-stone-700">
                  Email <span className="text-stone-500 font-normal">(optional)</span>
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="your@email.com"
                  className="mt-1"
                />
              </div>
            </div>

            {/* Rating */}
            <div>
              <Label className="text-stone-700 mb-3 block">
                How would you rate your experience with StyleMe?
              </Label>
              <div className="flex flex-wrap gap-3">
                {['Excellent', 'Good', 'Fair', 'Poor', 'Very Poor'].map((option, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => setFormData({ ...formData, rating: option })}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      formData.rating === option
                        ? 'bg-stone-900 text-white hover:bg-stone-800 shadow-sm'
                        : 'bg-stone-100 text-stone-700 hover:bg-stone-200 border border-stone-200'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            {/* Feedback Content */}
            <div>
              <Label htmlFor="feedback" className="text-stone-700">
                Your Feedback <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="feedback"
                value={formData.feedback}
                onChange={(e) => setFormData({ ...formData, feedback: e.target.value })}
                placeholder="Please share your thoughts, suggestions, or any issues you've encountered..."
                className="mt-1 min-h-[120px]"
                required
              />
            </div>

            {/* Suggestions */}
            <div>
              <Label htmlFor="suggestions" className="text-stone-700">
                Suggestions for Improvement <span className="text-stone-500 font-normal">(optional)</span>
              </Label>
              <Textarea
                id="suggestions"
                value={formData.suggestions}
                onChange={(e) => setFormData({ ...formData, suggestions: e.target.value })}
                placeholder="How can we make StyleMe better for you?"
                className="mt-1 min-h-[100px]"
              />
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
                className="flex-1 border-stone-300 text-stone-700 hover:bg-stone-100"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-stone-900 hover:bg-stone-800 text-white shadow-sm"
                disabled={!formData.feedback.trim()}
              >
                Submit Feedback
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}

