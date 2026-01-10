import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, Activity, Target, CreditCard, Calculator, 
  Globe, Radio, Users, Settings, ArrowRight, Check, Sparkles
} from 'lucide-react';

const tourSteps = [
  {
    title: "Welcome to CrossCurrent Finance Center! 🎉",
    content: "Your complete trading profit management platform for the Merin Trading Platform. Let's get you started with a quick tour!",
    icon: Sparkles,
  },
  {
    title: "Profit Tracker",
    content: "Track your deposits and see your actual vs projected profits. Add deposits when you fund your Merin account, and watch your account value grow.\n\n• Withdrawal simulation shows 3% Merin fee + $1 Binance fee\n• Processing time: 1-2 business days",
    icon: TrendingUp,
    path: '/profit-tracker',
  },
  {
    title: "Trade Monitor",
    content: "Your trading command center!\n\n• Check the active trading signal (product, direction, time)\n• LOT Calculator: Your LOT size × 15 = Exit Value\n• Check in when ready, wait for the exit alert\n• Enter your actual exit value after the trade\n• Forward profits to your Profit Tracker",
    icon: Activity,
    path: '/trade-monitor',
  },
  {
    title: "LOT Size Formula",
    content: "The exit calculation is simple:\n\nLOT Size × 15 = Exit Value\n\nFor example:\n• 0.01 LOT = $0.15 exit\n• 0.10 LOT = $1.50 exit\n• 1.00 LOT = $15.00 exit\n\nSet your default LOT size in Profile Settings!",
    icon: Calculator,
  },
  {
    title: "World Timer",
    content: "Trading signals are based on Philippine/Taiwan/Singapore time (GMT+8).\n\nSet your timezone in Profile Settings so the Trade Monitor shows your local time. This helps you know exactly when to enter and exit trades!",
    icon: Globe,
    path: '/profile',
  },
  {
    title: "Profit Planner",
    content: "Set financial goals and track your progress!\n\n• Create goals for items you want to buy\n• Add contributions from your trading profits\n• Get suggestions on when to withdraw\n• Celebrate when you reach your goals!",
    icon: Target,
    path: '/goals',
  },
  {
    title: "Debt Management",
    content: "Plan your debt repayments using trading profits.\n\n• Add your debts with due dates\n• See withdrawal deadlines (1-2 days before due)\n• Track payments and remaining balances\n• Plan your monthly commitment",
    icon: CreditCard,
    path: '/debt',
  },
  {
    title: "For Admins",
    content: "Admins can:\n• Post daily trading signals (product, time, direction)\n• Manage platform members\n• Connect external apps via API Center\n• Customize platform settings\n\nSuper Admins have full control over all features.",
    icon: Radio,
  },
  {
    title: "You're All Set! 🚀",
    content: "Remember:\n\n1. Set your timezone in Profile Settings\n2. Check the Trade Monitor for daily signals\n3. Use LOT × 15 to calculate your exit\n4. Forward profits to your Profit Tracker\n5. Plan your goals and debt payments\n\nHappy trading!",
    icon: Check,
  },
];

export const OnboardingTour = ({ isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onClose();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    onClose();
  };

  const step = tourSteps[currentStep];
  const Icon = step.icon;
  const isLastStep = currentStep === tourSteps.length - 1;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="glass-card border-zinc-800 max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <Icon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">Step {currentStep + 1} of {tourSteps.length}</p>
              <DialogTitle className="text-white">{step.title}</DialogTitle>
            </div>
          </div>
        </DialogHeader>

        <div className="mt-4">
          <div className="text-zinc-300 whitespace-pre-line text-sm leading-relaxed">
            {step.content}
          </div>
        </div>

        {/* Progress dots */}
        <div className="flex justify-center gap-2 mt-6">
          {tourSteps.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentStep(index)}
              className={`w-2 h-2 rounded-full transition-all ${
                index === currentStep 
                  ? 'w-6 bg-blue-500' 
                  : index < currentStep 
                    ? 'bg-blue-500/50' 
                    : 'bg-zinc-700'
              }`}
            />
          ))}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-zinc-800">
          <Button
            variant="ghost"
            onClick={handleSkip}
            className="text-zinc-400 hover:text-white"
          >
            Skip Tour
          </Button>
          <div className="flex gap-2">
            {currentStep > 0 && (
              <Button
                variant="outline"
                onClick={handlePrev}
                className="btn-secondary"
              >
                Previous
              </Button>
            )}
            <Button
              onClick={handleNext}
              className="btn-primary gap-2"
            >
              {isLastStep ? (
                <>
                  Get Started <Check className="w-4 h-4" />
                </>
              ) : (
                <>
                  Next <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Hook to manage onboarding state
export const useOnboarding = () => {
  const [showTour, setShowTour] = useState(false);

  useEffect(() => {
    const hasSeenTour = localStorage.getItem('crosscurrent_tour_completed');
    if (!hasSeenTour) {
      setShowTour(true);
    }
  }, []);

  const completeTour = () => {
    localStorage.setItem('crosscurrent_tour_completed', 'true');
    setShowTour(false);
  };

  const resetTour = () => {
    localStorage.removeItem('crosscurrent_tour_completed');
    setShowTour(true);
  };

  return { showTour, completeTour, resetTour };
};
