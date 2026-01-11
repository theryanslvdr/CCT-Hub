import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, Activity, Target, CreditCard, Calculator, 
  Globe, Radio, Users, Settings, ArrowRight, Check, Sparkles,
  Play, ChevronLeft, ChevronRight, Eye, MousePointer, Rocket
} from 'lucide-react';

// Interactive tour steps with navigation targets
const tourSteps = [
  {
    id: 'welcome',
    title: "Welcome to CrossCurrent Finance Center! 🎉",
    content: "Your complete trading profit management platform for the Merin Trading Platform. Let's take an interactive tour of your new trading dashboard!",
    icon: Sparkles,
    type: 'modal',
    highlight: null,
    action: null,
  },
  {
    id: 'dashboard',
    title: "Your Dashboard",
    content: "This is your home base. See your total balance, recent trades, and quick stats at a glance. Everything you need to track your trading performance.",
    icon: TrendingUp,
    type: 'page',
    path: '/dashboard',
    highlight: '[data-testid="balance-card"]',
    tip: "💡 Click on cards to explore more details",
  },
  {
    id: 'profit-tracker',
    title: "Profit Tracker",
    content: "Track deposits, withdrawals, and watch your account grow! The projection system shows you potential earnings based on daily compounding.\n\n• Add deposits when you fund your Merin account\n• Simulate withdrawals (3% Merin + $1 Binance fee)\n• View daily/monthly projections",
    icon: TrendingUp,
    type: 'page',
    path: '/profit-tracker',
    highlight: '[data-testid="balance-card"], [data-testid="add-deposit-btn"]',
    tip: "💡 Try clicking 'Add Deposit' to see the simulation",
  },
  {
    id: 'lot-formula',
    title: "The LOT Formula",
    content: "Your exit value is calculated as:\n\nLOT Size × Multiplier = Exit Value\n\n• LOT Size is auto-calculated from your balance ÷ 980\n• Multiplier comes from the daily signal (usually 15)\n\nExample: 14.71 LOT × 15 = $220.65 exit",
    icon: Calculator,
    type: 'modal',
    highlight: null,
    tip: "💡 Your LOT size automatically updates as your balance grows",
  },
  {
    id: 'trade-monitor',
    title: "Trade Monitor - Your Trading Hub",
    content: "This is where the action happens!\n\n1. Check the Active Signal (product, direction, time)\n2. See your calculated LOT size and projected exit value\n3. Click 'Enter the Trade Now!' when ready\n4. Wait for the countdown and enter your actual profit",
    icon: Activity,
    type: 'page',
    path: '/trade-monitor',
    highlight: '[data-testid="active-signal-card"], [data-testid="lot-size-card"]',
    tip: "💡 The Merin platform is embedded on the right for seamless trading",
  },
  {
    id: 'trade-flow',
    title: "The Trading Flow",
    content: "1. Admin posts daily signal (time, direction, multiplier)\n2. Check in and wait for countdown\n3. 5-second beep alert before trade time\n4. ENTER THE TRADE NOW! appears\n5. Enter your actual profit\n6. Celebrate and forward to Profit Tracker!",
    icon: Play,
    type: 'modal',
    highlight: null,
    tip: "💡 The Trade History table tracks all your trades with P/L",
  },
  {
    id: 'timezone',
    title: "Timezone Settings",
    content: "Trading signals are based on Philippine Time (GMT+8).\n\nSet your timezone in Profile Settings so you see the correct local trade time. The Trade Monitor shows both Philippine time and your local time!",
    icon: Globe,
    type: 'page',
    path: '/profile',
    highlight: null,
    tip: "💡 Update your timezone for accurate trade time conversion",
  },
  {
    id: 'ready',
    title: "You're Ready to Trade! 🚀",
    content: "Quick recap:\n\n✅ Check Trade Monitor for daily signals\n✅ Your LOT size × Multiplier = Exit Value\n✅ Forward profits to your Profit Tracker\n✅ Track your progress in the dashboard\n\nHappy trading with CrossCurrent!",
    icon: Rocket,
    type: 'modal',
    highlight: null,
    action: 'complete',
  },
];

export const OnboardingTour = ({ isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isNavigating, setIsNavigating] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const step = tourSteps[currentStep];
  const Icon = step.icon;
  const isLastStep = currentStep === tourSteps.length - 1;
  const isFirstStep = currentStep === 0;
  const progress = ((currentStep + 1) / tourSteps.length) * 100;

  // Navigate to the step's page if needed
  useEffect(() => {
    if (step.path && step.type === 'page' && location.pathname !== step.path) {
      setIsNavigating(true);
      navigate(step.path);
      // Wait for navigation and re-render
      setTimeout(() => {
        setIsNavigating(false);
        highlightElements();
      }, 500);
    } else if (step.type === 'page') {
      highlightElements();
    }
    
    return () => {
      // Clean up highlights when step changes
      removeHighlights();
    };
  }, [currentStep, step.path, location.pathname]);

  const highlightElements = useCallback(() => {
    if (step.highlight) {
      const selectors = step.highlight.split(',').map(s => s.trim());
      selectors.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
          element.classList.add('tour-highlight');
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }
  }, [step.highlight]);

  const removeHighlights = () => {
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight');
    });
  };

  const handleNext = () => {
    if (isLastStep) {
      removeHighlights();
      onClose();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    removeHighlights();
    onClose();
  };

  const handleStepClick = (index) => {
    setCurrentStep(index);
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) handleSkip(); }}>
      <DialogContent className="glass-card border-zinc-800 max-w-lg" data-testid="onboarding-dialog">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
              isLastStep 
                ? 'bg-gradient-to-br from-emerald-500 to-green-600' 
                : 'bg-gradient-to-br from-blue-500 to-cyan-500'
            }`}>
              <Icon className="w-7 h-7 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-xs text-zinc-500">Step {currentStep + 1} of {tourSteps.length}</p>
                {step.type === 'page' && (
                  <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full flex items-center gap-1">
                    <Eye className="w-3 h-3" /> Interactive
                  </span>
                )}
              </div>
              <DialogTitle className="text-white text-xl">{step.title}</DialogTitle>
            </div>
          </div>
          
          {/* Progress bar */}
          <Progress value={progress} className="h-1 mt-2" />
        </DialogHeader>

        <div className="mt-4">
          <div className="text-zinc-300 whitespace-pre-line text-sm leading-relaxed">
            {step.content}
          </div>
          
          {/* Tip box */}
          {step.tip && (
            <div className="mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <p className="text-sm text-blue-400">{step.tip}</p>
            </div>
          )}
        </div>

        {/* Step indicators - clickable */}
        <div className="flex justify-center gap-2 mt-6">
          {tourSteps.map((s, index) => (
            <button
              key={s.id}
              onClick={() => handleStepClick(index)}
              className={`h-2 rounded-full transition-all cursor-pointer hover:opacity-80 ${
                index === currentStep 
                  ? 'w-8 bg-gradient-to-r from-blue-500 to-cyan-500' 
                  : index < currentStep 
                    ? 'w-2 bg-emerald-500' 
                    : 'w-2 bg-zinc-700 hover:bg-zinc-600'
              }`}
              title={s.title}
            />
          ))}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-zinc-800">
          <Button
            variant="ghost"
            onClick={handleSkip}
            className="text-zinc-400 hover:text-white"
            data-testid="skip-tour-btn"
          >
            Skip Tour
          </Button>
          <div className="flex gap-2">
            {!isFirstStep && (
              <Button
                variant="outline"
                onClick={handlePrev}
                className="btn-secondary gap-1"
                data-testid="prev-step-btn"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </Button>
            )}
            <Button
              onClick={handleNext}
              className={`gap-2 ${isLastStep ? 'bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700' : 'btn-primary'}`}
              disabled={isNavigating}
              data-testid="next-step-btn"
            >
              {isNavigating ? (
                <>Loading...</>
              ) : isLastStep ? (
                <>
                  Start Trading <Rocket className="w-4 h-4" />
                </>
              ) : (
                <>
                  Next <ChevronRight className="w-4 h-4" />
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
      // Slight delay to ensure the page has loaded
      const timer = setTimeout(() => setShowTour(true), 500);
      return () => clearTimeout(timer);
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
