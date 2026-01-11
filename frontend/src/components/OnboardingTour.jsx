import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, Activity, Target, CreditCard, Calculator, 
  Globe, Play, ChevronLeft, ChevronRight, Eye, Sparkles, Rocket, X
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
    content: "This is your home base. See your total balance, recent trades, and quick stats at a glance.",
    icon: TrendingUp,
    type: 'page',
    path: '/dashboard',
    highlight: '[data-testid="balance-card"]',
    tip: "💡 Click on the highlighted card to continue",
    clickToAdvance: true,
  },
  {
    id: 'profit-tracker',
    title: "Profit Tracker",
    content: "Track deposits, withdrawals, and watch your account grow! Click on 'Profit Tracker' in the sidebar to explore.",
    icon: TrendingUp,
    type: 'page',
    path: '/profit-tracker',
    highlight: '[data-testid="account-value-card"]',
    tip: "💡 Click the highlighted card to continue",
    clickToAdvance: true,
  },
  {
    id: 'lot-formula',
    title: "The LOT Formula",
    content: "Your exit value is calculated as:\n\nLOT Size × Multiplier = Exit Value\n\n• LOT Size = Balance ÷ 980\n• Multiplier comes from the daily signal (usually 15)\n\nExample: 14.71 LOT × 15 = $220.65 exit",
    icon: Calculator,
    type: 'modal',
    highlight: null,
    tip: "💡 Your LOT size automatically updates as your balance grows",
  },
  {
    id: 'trade-monitor',
    title: "Trade Monitor - Your Trading Hub",
    content: "This is where you execute trades!\n\n1. Check the Active Signal\n2. See your LOT size and projected exit\n3. Click 'Enter the Trade Now!' when ready",
    icon: Activity,
    type: 'page',
    path: '/trade-monitor',
    highlight: '[data-testid="active-signal-card"], [data-testid="lot-size-card"]',
    tip: "💡 Click the highlighted area to continue",
    clickToAdvance: true,
  },
  {
    id: 'trade-flow',
    title: "The Trading Flow",
    content: "1. Admin posts daily signal\n2. Check in and wait for countdown\n3. 5-second beep alert before trade\n4. ENTER THE TRADE NOW! appears\n5. Enter your actual profit\n6. Forward to Profit Tracker!",
    icon: Play,
    type: 'modal',
    highlight: null,
    tip: "💡 The Trade History tracks all your trades",
  },
  {
    id: 'timezone',
    title: "Timezone Settings",
    content: "Trading signals are based on Philippine Time (GMT+8). Set your timezone in Profile Settings so you see the correct local trade time.",
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

// Tooltip component that floats near highlighted elements
const TourTooltip = ({ step, currentStep, totalSteps, onNext, onPrev, onSkip, position }) => {
  const Icon = step.icon;
  const isLastStep = currentStep === totalSteps - 1;
  const isFirstStep = currentStep === 0;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  return (
    <div 
      className="fixed z-[10001] max-w-md animate-in fade-in slide-in-from-bottom-2 duration-300"
      style={{
        top: position.top,
        left: position.left,
        transform: position.transform || 'none',
      }}
    >
      <div className="bg-zinc-900/95 backdrop-blur-xl border border-zinc-700 rounded-xl shadow-2xl p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
            isLastStep 
              ? 'bg-gradient-to-br from-emerald-500 to-green-600' 
              : 'bg-gradient-to-br from-blue-500 to-cyan-500'
          }`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-zinc-500">Step {currentStep + 1} of {totalSteps}</p>
              <button 
                onClick={onSkip}
                className="text-zinc-500 hover:text-white p-1 rounded hover:bg-zinc-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <h3 className="text-white font-semibold text-base">{step.title}</h3>
          </div>
        </div>

        {/* Progress bar */}
        <Progress value={progress} className="h-1 mb-3" />

        {/* Content */}
        <div className="text-zinc-300 text-sm whitespace-pre-line leading-relaxed mb-3">
          {step.content}
        </div>

        {/* Tip box */}
        {step.tip && (
          <div className="mb-3 p-2 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <p className="text-xs text-blue-400">{step.tip}</p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between pt-2 border-t border-zinc-800">
          <Button
            variant="ghost"
            size="sm"
            onClick={onSkip}
            className="text-zinc-400 hover:text-white text-xs h-8"
          >
            Skip Tour
          </Button>
          <div className="flex gap-2">
            {!isFirstStep && (
              <Button
                variant="outline"
                size="sm"
                onClick={onPrev}
                className="h-8 text-xs border-zinc-700 text-zinc-300 hover:text-white"
              >
                <ChevronLeft className="w-3 h-3 mr-1" /> Back
              </Button>
            )}
            {!step.clickToAdvance && (
              <Button
                size="sm"
                onClick={onNext}
                className={`h-8 text-xs ${isLastStep ? 'bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700' : 'bg-blue-600 hover:bg-blue-700'}`}
              >
                {isLastStep ? (
                  <>Start Trading <Rocket className="w-3 h-3 ml-1" /></>
                ) : (
                  <>Next <ChevronRight className="w-3 h-3 ml-1" /></>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
      
      {/* Arrow pointer */}
      <div 
        className="absolute w-3 h-3 bg-zinc-900 border-l border-t border-zinc-700 transform rotate-45"
        style={{
          top: '-6px',
          left: '50%',
          marginLeft: '-6px',
        }}
      />
    </div>
  );
};

export const OnboardingTour = ({ isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isNavigating, setIsNavigating] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' });
  const navigate = useNavigate();
  const location = useLocation();
  const clickHandlerRef = useRef(null);

  const step = tourSteps[currentStep];
  const Icon = step.icon;
  const isLastStep = currentStep === tourSteps.length - 1;
  const isFirstStep = currentStep === 0;

  // Clean up click handlers
  const cleanupClickHandler = useCallback(() => {
    if (clickHandlerRef.current) {
      document.removeEventListener('click', clickHandlerRef.current, true);
      clickHandlerRef.current = null;
    }
  }, []);

  // Setup click handler for highlighted elements
  const setupClickHandler = useCallback(() => {
    cleanupClickHandler();
    
    if (step.clickToAdvance && step.highlight) {
      const handler = (e) => {
        const selectors = step.highlight.split(',').map(s => s.trim());
        for (const selector of selectors) {
          const element = document.querySelector(selector);
          if (element && (element.contains(e.target) || element === e.target)) {
            e.preventDefault();
            e.stopPropagation();
            handleNext();
            return;
          }
        }
      };
      
      clickHandlerRef.current = handler;
      // Use setTimeout to ensure it's added after React's event handlers
      setTimeout(() => {
        document.addEventListener('click', handler, true);
      }, 100);
    }
  }, [step, currentStep]);

  // Navigate to the step's page if needed
  useEffect(() => {
    if (!isOpen) return;
    
    if (step.path && step.type === 'page' && location.pathname !== step.path) {
      setIsNavigating(true);
      navigate(step.path);
      setTimeout(() => {
        setIsNavigating(false);
        highlightElements();
        setupClickHandler();
      }, 500);
    } else if (step.type === 'page') {
      highlightElements();
      setupClickHandler();
    }
    
    return () => {
      removeHighlights();
      cleanupClickHandler();
    };
  }, [currentStep, step.path, location.pathname, isOpen]);

  const highlightElements = useCallback(() => {
    if (step.highlight) {
      const selectors = step.highlight.split(',').map(s => s.trim());
      let firstElement = null;
      
      selectors.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
          element.classList.add('tour-highlight');
          if (!firstElement) {
            firstElement = element;
          }
        }
      });
      
      // Position tooltip near the first highlighted element
      if (firstElement) {
        const rect = firstElement.getBoundingClientRect();
        const tooltipTop = Math.min(rect.bottom + 20, window.innerHeight - 350);
        const tooltipLeft = Math.max(20, Math.min(rect.left + rect.width / 2, window.innerWidth - 250));
        
        setTooltipPosition({
          top: `${tooltipTop}px`,
          left: `${tooltipLeft}px`,
          transform: 'translateX(-50%)',
        });
        
        firstElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } else {
      // Center the tooltip for modal steps
      setTooltipPosition({ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' });
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
      cleanupClickHandler();
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
    cleanupClickHandler();
    onClose();
  };

  if (!isOpen) return null;

  // Show modal dialog for modal-type steps or when navigating
  if (step.type === 'modal' || isNavigating) {
    return (
      <>
        {/* Overlay */}
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[10000]" onClick={handleSkip} />
        
        {/* Modal */}
        <div className="fixed inset-0 flex items-center justify-center z-[10001] p-4">
          <div className="bg-zinc-900/95 backdrop-blur-xl border border-zinc-700 rounded-2xl shadow-2xl max-w-lg w-full p-6 animate-in fade-in zoom-in-95 duration-300">
            {/* Header */}
            <div className="flex items-start gap-4 mb-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center shrink-0 ${
                isLastStep 
                  ? 'bg-gradient-to-br from-emerald-500 to-green-600' 
                  : 'bg-gradient-to-br from-blue-500 to-cyan-500'
              }`}>
                <Icon className="w-7 h-7 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-zinc-500">Step {currentStep + 1} of {tourSteps.length}</p>
                  {step.type === 'page' && (
                    <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full flex items-center gap-1">
                      <Eye className="w-3 h-3" /> Interactive
                    </span>
                  )}
                </div>
                <h2 className="text-white text-xl font-semibold">{step.title}</h2>
              </div>
              <button 
                onClick={handleSkip}
                className="text-zinc-500 hover:text-white p-1 rounded hover:bg-zinc-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Progress bar */}
            <Progress value={((currentStep + 1) / tourSteps.length) * 100} className="h-1 mb-4" />

            {/* Content */}
            <div className="text-zinc-300 whitespace-pre-line text-sm leading-relaxed mb-4">
              {isNavigating ? 'Navigating to the next page...' : step.content}
            </div>

            {/* Tip box */}
            {step.tip && !isNavigating && (
              <div className="mb-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <p className="text-sm text-blue-400">{step.tip}</p>
              </div>
            )}

            {/* Step indicators */}
            <div className="flex justify-center gap-2 mb-4">
              {tourSteps.map((s, index) => (
                <button
                  key={s.id}
                  onClick={() => setCurrentStep(index)}
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
            <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
              <Button
                variant="ghost"
                onClick={handleSkip}
                className="text-zinc-400 hover:text-white"
              >
                Skip Tour
              </Button>
              <div className="flex gap-2">
                {!isFirstStep && (
                  <Button
                    variant="outline"
                    onClick={handlePrev}
                    className="border-zinc-700 text-zinc-300 hover:text-white"
                    disabled={isNavigating}
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" /> Previous
                  </Button>
                )}
                <Button
                  onClick={handleNext}
                  className={isLastStep ? 'bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700' : 'bg-blue-600 hover:bg-blue-700'}
                  disabled={isNavigating}
                >
                  {isNavigating ? (
                    'Loading...'
                  ) : isLastStep ? (
                    <>Start Trading <Rocket className="w-4 h-4 ml-1" /></>
                  ) : (
                    <>Next <ChevronRight className="w-4 h-4 ml-1" /></>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  // For page-type steps, show floating tooltip near highlighted elements
  return (
    <>
      {/* Semi-transparent overlay that allows clicking on highlighted elements */}
      <div 
        className="fixed inset-0 z-[9999] pointer-events-none"
        style={{
          background: 'radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.7) 100%)',
        }}
      />
      
      {/* Tooltip */}
      <TourTooltip
        step={step}
        currentStep={currentStep}
        totalSteps={tourSteps.length}
        onNext={handleNext}
        onPrev={handlePrev}
        onSkip={handleSkip}
        position={tooltipPosition}
      />
    </>
  );
};

// Hook to manage onboarding state
export const useOnboarding = () => {
  const [showTour, setShowTour] = useState(false);

  useEffect(() => {
    const hasSeenTour = localStorage.getItem('crosscurrent_tour_completed');
    if (!hasSeenTour) {
      // Slight delay to ensure the page has loaded
      const timer = setTimeout(() => setShowTour(true), 1000);
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
