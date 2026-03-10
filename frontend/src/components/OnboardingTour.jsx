import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, Activity, Target, CreditCard, Calculator, 
  Globe, Play, ChevronLeft, ChevronRight, Eye, Sparkles, Rocket, X,
  Award, Wallet, ArrowUpFromLine, ArrowDownToLine
} from 'lucide-react';

// Interactive tour steps for REGULAR MEMBERS
const memberTourSteps = [
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
    content: "This is your home base. See your total balance, recent trades, and quick stats at a glance. The KPI cards show your account value, today's profit, and trading statistics.",
    icon: TrendingUp,
    type: 'page',
    path: '/dashboard',
    highlight: null,
    tip: "💡 Your dashboard updates in real-time as you trade",
  },
  {
    id: 'profit-tracker',
    title: "Profit Tracker",
    content: "Track deposits, withdrawals, and watch your account grow! This is where you manage your trading capital and see your profit projections.",
    icon: TrendingUp,
    type: 'page',
    path: '/profit-tracker',
    highlight: null,
    tip: "💡 Add deposits here and watch your projected growth over time",
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
    content: "This is where you execute trades!\n\n1. Check the Active Signal card\n2. See your LOT size and projected exit value\n3. Click 'Enter the Trade Now!' when the countdown ends",
    icon: Activity,
    type: 'page',
    path: '/trade-monitor',
    highlight: null,
    tip: "💡 The Merin Trading Platform is embedded on the right side for seamless trading",
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

// Simplified tour steps for LICENSEES
const licenseeTourSteps = [
  {
    id: 'welcome',
    title: "Welcome, Licensee! 🌟",
    content: "You're part of the CrossCurrent Licensed Trader Program. Your account is managed by our team - here's a quick overview of what you need to know.",
    icon: Award,
    type: 'modal',
    highlight: null,
    action: null,
  },
  {
    id: 'dashboard',
    title: "Your Dashboard",
    content: "This is your home base. View your current account value, total profit, and account statistics. Your balance is updated automatically as trades are made on your behalf.",
    icon: TrendingUp,
    type: 'page',
    path: '/dashboard',
    highlight: null,
    tip: "💡 Your account value reflects your license balance",
  },
  {
    id: 'profit-tracker',
    title: "Profit Tracker",
    content: "Track your profit growth over time. As a licensee, your profits are calculated daily based on your license amount.\n\nDaily Profit = (Balance ÷ 980) × 15",
    icon: TrendingUp,
    type: 'page',
    path: '/profit-tracker',
    highlight: null,
    tip: "💡 Watch your account grow with daily trading profits",
  },
  {
    id: 'deposit-withdrawal',
    title: "Deposit & Withdrawal",
    content: "Request deposits and withdrawals here:\n\n📥 Deposit: Submit a request with proof of payment\n📤 Withdraw: Request to withdraw from your balance\n\nAll requests are reviewed by the admin team.",
    icon: Wallet,
    type: 'page',
    path: '/licensee-account',
    highlight: null,
    tip: "💡 Withdrawals are processed within 5 business days",
  },
  {
    id: 'ready',
    title: "You're All Set! 🎉",
    content: "Quick recap:\n\n✅ Check Dashboard for your current balance\n✅ View Profit Tracker for growth projection\n✅ Use Deposit/Withdrawal for fund requests\n\nYour trading is managed by our team - sit back and watch your account grow!",
    icon: Rocket,
    type: 'modal',
    highlight: null,
    action: 'complete',
  },
];

export const OnboardingTour = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [isNavigating, setIsNavigating] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Determine which tour steps to use based on user type
  const isLicensee = user?.license_type;
  const tourSteps = isLicensee ? licenseeTourSteps : memberTourSteps;

  const step = tourSteps[currentStep];
  const Icon = step.icon;
  const isLastStep = currentStep === tourSteps.length - 1;
  const isFirstStep = currentStep === 0;

  // Handle next step
  const handleNext = useCallback(() => {
    if (isLastStep) {
      onClose();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  }, [isLastStep, onClose]);

  // Handle previous step
  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  // Handle skip
  const handleSkip = useCallback(() => {
    onClose();
  }, [onClose]);

  // Navigate to the step's page if needed
  useEffect(() => {
    if (!isOpen) return;
    
    if (step.path && step.type === 'page' && location.pathname !== step.path) {
      setIsNavigating(true);
      navigate(step.path);
      const timer = setTimeout(() => {
        setIsNavigating(false);
      }, 600);
      return () => clearTimeout(timer);
    } else if (step.type === 'page') {
      setIsNavigating(false);
    }
  }, [currentStep, step.path, step.type, location.pathname, isOpen, navigate]);

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay - Click to dismiss and save tour state */}
      <div 
        className="fixed inset-0 bg-black/40 z-[10000]" 
        onClick={handleSkip}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-[10001] p-4 pointer-events-none">
        <div 
          className="bg-zinc-900/95 backdrop-blur-xl border border-zinc-700 rounded-2xl shadow-2xl max-w-lg w-full p-6 animate-in fade-in zoom-in-95 duration-300 pointer-events-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-start gap-4 mb-4">
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center shrink-0 ${
              isLastStep 
                ? 'bg-gradient-to-br from-emerald-500 to-green-600' 
                : 'bg-gradient-to-br from-orange-500 to-amber-500'
            }`}>
              <Icon className="w-7 h-7 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-zinc-500">Step {currentStep + 1} of {tourSteps.length}</p>
                {step.type === 'page' && (
                  <span className="text-xs px-2 py-0.5 bg-orange-500/10 text-orange-400 rounded-full flex items-center gap-1">
                    <Eye className="w-3 h-3" /> {step.path}
                  </span>
                )}
              </div>
              <h2 className="text-white text-xl font-semibold">{step.title}</h2>
            </div>
            <button 
              onClick={handleSkip}
              className="text-zinc-500 hover:text-white p-1 rounded hover:bg-zinc-800 transition-colors"
              data-testid="tour-close-btn"
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
            <div className="mb-4 p-3 rounded-lg bg-orange-500/10 border border-orange-500/15">
              <p className="text-sm text-orange-400">{step.tip}</p>
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
                    ? 'w-8 bg-gradient-to-r from-orange-500 to-amber-500' 
                    : index < currentStep 
                      ? 'w-2 bg-emerald-500' 
                      : 'w-2 bg-zinc-700 hover:bg-zinc-600'
                }`}
                title={s.title}
                data-testid={`tour-step-${index}`}
              />
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
            <Button
              variant="ghost"
              onClick={handleSkip}
              className="text-zinc-400 hover:text-white"
              data-testid="tour-skip-btn"
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
                  data-testid="tour-prev-btn"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Previous
                </Button>
              )}
              <Button
                onClick={handleNext}
                className={isLastStep ? 'bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700' : 'bg-orange-600 hover:bg-orange-700'}
                disabled={isNavigating}
                data-testid="tour-next-btn"
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
