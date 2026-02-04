import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { format, addDays, isWeekend, isBefore, isAfter, startOfDay, eachDayOfInterval } from 'date-fns';
import { 
  ChevronRight, ChevronLeft, User, Calendar as CalendarIcon, 
  DollarSign, ArrowDownCircle, ArrowUpCircle, Check, Loader2,
  Sparkles, TrendingUp, Plus, Trash2, Save, X, RotateCcw, TreePine
} from 'lucide-react';
import { toast } from 'sonner';
import { profitAPI, tradeAPI } from '@/lib/api';

// Import mobile-optimized wizard
import { OnboardingWizardMobile } from './OnboardingWizardMobile';

// Import extracted step components
import { StepUserType } from './onboarding/StepUserType';
import { StepNewTraderBalance } from './onboarding/StepNewTraderBalance';
import { StepExperiencedStart } from './onboarding/StepExperiencedStart';

// Minimum start date for experienced traders (December 1, 2025)
const MIN_START_DATE = new Date(2025, 11, 1); // December 1, 2025
// Minimum deposit date (a week before December 1, 2025)
const MIN_DEPOSIT_DATE = new Date(2025, 10, 24); // November 24, 2025

// Note: Static holidays removed - all holidays are now managed via Admin Settings > Global Trading

// Format currency
const formatMoney = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(amount);
};

// Calculate LOT size and projected profit
const calculateLotSize = (balance) => Math.floor((balance / 980) * 100) / 100;
const calculateBalanceFromLot = (lotSize) => Math.round(lotSize * 980 * 100) / 100;
const calculateProjectedProfit = (lotSize) => Math.floor(lotSize * 15 * 100) / 100;

// Hook to detect mobile viewport
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false);
  
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  return isMobile;
};

export const OnboardingWizard = ({ isOpen, onClose, onComplete, isReset = false }) => {
  const isMobile = useIsMobile();
  
  // Render mobile-optimized wizard on mobile devices
  if (isMobile) {
    return (
      <OnboardingWizardMobile 
        isOpen={isOpen} 
        onClose={onClose} 
        onComplete={onComplete} 
        isReset={isReset} 
      />
    );
  }
  
  // Desktop wizard state
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // User type
  const [userType, setUserType] = useState(null); // 'new' or 'experienced'
  
  // Common fields
  const [startingBalance, setStartingBalance] = useState('');
  
  // Experienced trader fields
  const [startDate, setStartDate] = useState(null);
  const [transactions, setTransactions] = useState([]); // { id, type: 'deposit'|'withdrawal', amount, date }
  const [newTransactionType, setNewTransactionType] = useState('deposit');
  const [newTransactionAmount, setNewTransactionAmount] = useState('');
  const [newTransactionDate, setNewTransactionDate] = useState(null);
  
  // Trade profits entry
  const [tradingDays, setTradingDays] = useState([]);
  const [currentTradeIndex, setCurrentTradeIndex] = useState(0);
  const [tradeEntries, setTradeEntries] = useState({}); // { dateKey: { balance: number, actualProfit: number, missed: boolean, product: string, direction: string } }
  
  // Commission (entered at final step)
  const [totalCommission, setTotalCommission] = useState('');
  
  // Global trading settings from backend
  const [globalHolidays, setGlobalHolidays] = useState([]);
  const [tradingProducts, setTradingProducts] = useState([]);
  
  // Default products and directions (fallback)
  const defaultProducts = ['MOIL10', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY'];
  const DIRECTIONS = ['BUY', 'SELL'];
  
  // Get active products (from backend or fallback)
  const PRODUCTS = useMemo(() => 
    tradingProducts.length > 0 
      ? tradingProducts.filter(p => p.is_active).map(p => p.name) 
      : defaultProducts,
    [tradingProducts]
  );
  
  // Holidays from backend (global trading holidays set by admin)
  // Only use global holidays - no static fallback. Admin controls all holidays via Settings.
  const allHolidays = useMemo(() => new Set(
    globalHolidays.map(h => h.date)
  ), [globalHolidays]);
  
  // Check if a date is a holiday (including global holidays)
  const isHolidayDate = useCallback((date) => {
    const dateKey = format(date, 'yyyy-MM-dd');
    return allHolidays.has(dateKey);
  }, [allHolidays]);
  
  // Check if a date is a trading day
  const isTradingDayCheck = useCallback((date) => {
    const day = date.getDay();
    if (day === 0 || day === 6) return false; // Weekend
    return !isHolidayDate(date);
  }, [isHolidayDate]);
  
  // Get trading days between two dates (using global holidays)
  const getTradingDays = useCallback((startDate, endDate) => {
    const days = eachDayOfInterval({ start: startDate, end: endDate });
    return days.filter(isTradingDayCheck);
  }, [isTradingDayCheck]);
  
  // Load global holidays and trading products
  useEffect(() => {
    const loadGlobalSettings = async () => {
      try {
        const [holidaysRes, productsRes] = await Promise.all([
          tradeAPI.getGlobalHolidays(),
          tradeAPI.getTradingProducts()
        ]);
        setGlobalHolidays(holidaysRes.data.holidays || []);
        setTradingProducts(productsRes.data.products || []);
      } catch (error) {
        console.error('Failed to load global trading settings:', error);
      }
    };
    
    if (isOpen) {
      loadGlobalSettings();
    }
  }, [isOpen]);
  
  // Load saved progress on mount
  useEffect(() => {
    if (isOpen) {
      const savedProgress = localStorage.getItem('onboarding_wizard_progress');
      if (savedProgress) {
        try {
          const data = JSON.parse(savedProgress);
          setUserType(data.userType || null);
          setStartingBalance(data.startingBalance || '');
          setStartDate(data.startDate ? new Date(data.startDate) : null);
          setTransactions(data.transactions || []);
          setTradeEntries(data.tradeEntries || {});
          setCurrentStep(data.currentStep || 1);
          setCurrentTradeIndex(data.currentTradeIndex || 0);
        } catch (e) {
          console.error('Failed to restore onboarding progress:', e);
        }
      }
    }
  }, [isOpen]);
  
  // Save progress whenever state changes
  const saveProgress = useCallback(() => {
    const data = {
      userType,
      startingBalance,
      startDate: startDate?.toISOString(),
      transactions,
      tradeEntries,
      currentStep,
      currentTradeIndex
    };
    localStorage.setItem('onboarding_wizard_progress', JSON.stringify(data));
  }, [userType, startingBalance, startDate, transactions, tradeEntries, currentStep, currentTradeIndex]);
  
  useEffect(() => {
    if (isOpen && (userType || startingBalance || startDate)) {
      saveProgress();
    }
  }, [isOpen, userType, startingBalance, startDate, transactions, tradeEntries, currentStep, currentTradeIndex, saveProgress]);
  
  // Calculate trading days when start date changes (using dynamic holidays)
  useEffect(() => {
    if (startDate && userType === 'experienced') {
      const today = startOfDay(new Date());
      const allDays = eachDayOfInterval({ start: startDate, end: today });
      const filteredDays = allDays.filter(day => {
        const dayOfWeek = day.getDay();
        if (dayOfWeek === 0 || dayOfWeek === 6) return false; // Weekend
        const dateKey = format(day, 'yyyy-MM-dd');
        return !allHolidays.has(dateKey);
      });
      setTradingDays(filteredDays);
    }
  }, [startDate, userType, allHolidays]);
  
  // Calculate running balance for a specific day
  // Truncate to 2 decimals without rounding
  const truncateTo2Decimals = (num) => Math.trunc(num * 100) / 100;
  
  const getBalanceForDay = (dayIndex) => {
    // Balance-first approach: if user has entered a balance for this day, use it
    const dayDate = tradingDays[dayIndex];
    if (!dayDate) return truncateTo2Decimals(parseFloat(startingBalance) || 0);
    
    const dateKey = format(dayDate, 'yyyy-MM-dd');
    const entry = tradeEntries[dateKey];
    
    // If user has entered a balance for this day, use it directly
    if (entry?.balance) {
      return truncateTo2Decimals(parseFloat(entry.balance));
    }
    
    // Calculate balance step by step:
    // Start with starting balance, then apply transactions and profits chronologically
    
    let balance = parseFloat(startingBalance) || 0;
    let lastProcessedDate = startDate ? format(startDate, 'yyyy-MM-dd') : '1970-01-01';
    
    // Process each trading day up to (but not including) the current day
    for (let i = 0; i < dayIndex; i++) {
      const day = tradingDays[i];
      const dayKey = format(day, 'yyyy-MM-dd');
      const prevEntry = tradeEntries[dayKey];
      
      // Apply any transactions between last processed date and this day (inclusive)
      for (const tx of transactions) {
        const txDateKey = tx.date.split('T')[0];
        // Transaction applies if it's after lastProcessedDate and on or before this day
        if (txDateKey > lastProcessedDate && txDateKey <= dayKey) {
          if (tx.type === 'deposit') {
            balance += parseFloat(tx.amount) || 0;
          } else {
            balance -= parseFloat(tx.amount) || 0;
          }
        }
      }
      
      // If this day has a user-entered balance, use it as the new base
      if (prevEntry?.balance) {
        balance = parseFloat(prevEntry.balance);
      }
      
      // ALWAYS add profit from this day (even if user entered a custom balance)
      // The user-entered balance is the "Balance Before" trade, so profit adds on top
      if (prevEntry && !prevEntry.missed && prevEntry.actualProfit !== undefined) {
        balance += parseFloat(prevEntry.actualProfit) || 0;
      }
      
      lastProcessedDate = dayKey;
    }
    
    // Apply any transactions between last trading day and current day
    const currentDayKey = format(dayDate, 'yyyy-MM-dd');
    for (const tx of transactions) {
      const txDateKey = tx.date.split('T')[0];
      if (txDateKey > lastProcessedDate && txDateKey <= currentDayKey) {
        if (tx.type === 'deposit') {
          balance += parseFloat(tx.amount) || 0;
        } else {
          balance -= parseFloat(tx.amount) || 0;
        }
      }
    }
    
    return truncateTo2Decimals(balance);
  };
  
  // Get total steps based on user type
  const getTotalSteps = () => {
    if (!userType) return 2;
    if (userType === 'new') return 2;
    return 4; // experienced: type, start date+balance (combined), transactions, trade profits
  };
  
  // Handle adding a transaction
  const handleAddTransaction = () => {
    if (!newTransactionAmount || parseFloat(newTransactionAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    if (!newTransactionDate) {
      toast.error('Please select a date');
      return;
    }
    
    const tx = {
      id: Date.now().toString(),
      type: newTransactionType,
      amount: parseFloat(newTransactionAmount),
      date: newTransactionDate.toISOString()
    };
    
    setTransactions([...transactions, tx]);
    setNewTransactionAmount('');
    setNewTransactionDate(null);
    toast.success(`${newTransactionType === 'deposit' ? 'Deposit' : 'Withdrawal'} added`);
  };
  
  // Handle removing a transaction
  const handleRemoveTransaction = (id) => {
    setTransactions(transactions.filter(tx => tx.id !== id));
  };
  
  // Handle trade entry for current day
  const handleTradeEntry = (field, value) => {
    const day = tradingDays[currentTradeIndex];
    if (!day) return;
    
    const dateKey = format(day, 'yyyy-MM-dd');
    const currentData = tradeEntries[dateKey] || { 
      product: 'MOIL10', 
      direction: 'BUY', 
      actualProfit: undefined, 
      missed: false,
      balance: null
    };
    
    // Get current balance for this day to store with the entry
    const currentBalance = getBalanceForDay(currentTradeIndex);
    
    // Process the value based on field type
    let processedValue = value;
    if (field === 'actualProfit') {
      processedValue = truncateTo2Decimals(parseFloat(value) || 0);
    } else if (field === 'balance') {
      // Truncate balance to 2 decimals, no rounding
      processedValue = truncateTo2Decimals(parseFloat(value) || 0);
    }
    
    setTradeEntries({
      ...tradeEntries,
      [dateKey]: { 
        ...currentData,
        [field]: processedValue,
        missed: false,
        // Always store the balance (use user-entered if field is 'balance', otherwise use calculated)
        balance: field === 'balance' ? processedValue : (currentData.balance || truncateTo2Decimals(currentBalance))
      }
    });
  };
  
  // Handle missed trade
  const handleMissedTrade = () => {
    const day = tradingDays[currentTradeIndex];
    if (!day) return;
    
    const dateKey = format(day, 'yyyy-MM-dd');
    setTradeEntries({
      ...tradeEntries,
      [dateKey]: { missed: true, actualProfit: 0, product: 'MOIL10', direction: 'BUY' }
    });
    
    // Move to next day
    if (currentTradeIndex < tradingDays.length - 1) {
      setCurrentTradeIndex(currentTradeIndex + 1);
    }
  };
  
  // Handle undo missed trade (clear the entry)
  const handleUndoMissedTrade = () => {
    const day = tradingDays[currentTradeIndex];
    if (!day) return;
    
    const dateKey = format(day, 'yyyy-MM-dd');
    const newEntries = { ...tradeEntries };
    delete newEntries[dateKey];
    setTradeEntries(newEntries);
    toast.success('Entry cleared - you can now re-enter this trade');
  };
  
  // Handle next trade entry - IMPORTANT: Save balance before moving to next day
  const handleNextTrade = () => {
    const day = tradingDays[currentTradeIndex];
    const dateKey = format(day, 'yyyy-MM-dd');
    const entry = tradeEntries[dateKey];
    
    if (!entry || (!entry.missed && entry.actualProfit === undefined)) {
      toast.error('Please enter your actual profit or mark as missed');
      return;
    }
    
    // CRITICAL: Always save the balance for this day before moving to next
    // This ensures the lot_size is calculated correctly when submitted
    if (!entry.missed && !entry.balance) {
      const currentBalance = getBalanceForDay(currentTradeIndex);
      setTradeEntries(prev => ({
        ...prev,
        [dateKey]: {
          ...prev[dateKey],
          balance: truncateTo2Decimals(currentBalance)
        }
      }));
    }
    
    if (currentTradeIndex < tradingDays.length - 1) {
      setCurrentTradeIndex(currentTradeIndex + 1);
    }
  };
  
  // Handle previous trade entry
  const handlePrevTrade = () => {
    if (currentTradeIndex > 0) {
      setCurrentTradeIndex(currentTradeIndex - 1);
    }
  };
  
  // Handle restart - clear all wizard data and start fresh
  const handleRestart = () => {
    // Clear all state
    setCurrentStep(1);
    setUserType(null);
    setStartDate(null);
    setStartingBalance('');
    setTransactions([]);
    setTradeEntries({});
    setTradingDays([]);
    setCurrentTradeIndex(0);
    setNewTransactionAmount('');
    setNewTransactionDate(null);
    setNewTransactionType('deposit');
    setTotalCommission('');
    
    // Clear saved progress
    localStorage.removeItem('onboarding_wizard_progress');
    
    toast.success('Wizard restarted. Enter your data again.');
  };
  
  // Handle next step
  const handleNext = () => {
    if (currentStep === 1) {
      // Validate user type selected
      if (!userType) {
        toast.error('Please select your trading experience');
        return;
      }
    }
    
    if (currentStep === 2 && userType === 'new') {
      // Validate starting balance for new trader
      if (!startingBalance || parseFloat(startingBalance) <= 0) {
        toast.error('Please enter a valid starting balance');
        return;
      }
      // New trader is done - submit
      handleSubmit();
      return;
    }
    
    if (currentStep === 2 && userType === 'experienced') {
      // Validate start date AND starting balance for experienced trader (combined step)
      if (!startDate) {
        toast.error('Please select your start date');
        return;
      }
      if (!startingBalance || parseFloat(startingBalance) <= 0) {
        toast.error('Please enter your starting balance');
        return;
      }
    }
    
    if (currentStep === 3 && userType === 'experienced') {
      // Transactions step - can proceed without any
    }
    
    if (currentStep === 4 && userType === 'experienced') {
      // Check if all trading days have entries
      const allEntered = tradingDays.every(day => {
        const dateKey = format(day, 'yyyy-MM-dd');
        const entry = tradeEntries[dateKey];
        return entry && (entry.missed || entry.actualProfit !== undefined);
      });
      
      if (!allEntered) {
        toast.error('Please enter all trade profits or mark missed days');
        return;
      }
      
      // Experienced trader is done - submit
      handleSubmit();
      return;
    }
    
    setCurrentStep(currentStep + 1);
  };
  
  // Handle back
  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  // Handle submit
  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      // Save onboarding data to backend
      const onboardingData = {
        user_type: userType,
        starting_balance: parseFloat(startingBalance),
        start_date: startDate?.toISOString(),
        transactions: transactions.map(tx => ({
          type: tx.type,
          amount: tx.amount,
          date: tx.date
        })),
        trade_entries: Object.entries(tradeEntries).map(([dateKey, entry]) => ({
          date: dateKey,
          actual_profit: entry.actualProfit ? parseFloat(entry.actualProfit) : null,
          missed: entry.missed || false,
          balance: entry.balance ? parseFloat(entry.balance) : null,  // Include user-entered balance
          product: entry.product || 'MOIL10',
          direction: entry.direction || 'BUY'
        })),
        total_commission: totalCommission ? parseFloat(totalCommission) : 0  // Total commission from final step
      };
      
      // Call backend to save onboarding data
      await profitAPI.completeOnboarding(onboardingData);
      
      // Clear saved progress
      localStorage.removeItem('onboarding_wizard_progress');
      
      // Save user type for future reference
      localStorage.setItem('user_trading_type', userType);
      
      toast.success('Welcome to CrossCurrent! Your profile is set up.');
      onComplete(onboardingData);
    } catch (error) {
      console.error('Onboarding failed:', error);
      toast.error(error.response?.data?.detail || 'Failed to complete onboarding');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle save and continue later
  const handleSaveForLater = () => {
    saveProgress();
    toast.success('Progress saved! You can continue later.');
    onClose();
  };
  
  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <StepUserType 
            userType={userType} 
            setUserType={setUserType} 
            isReset={isReset} 
          />
        );
      
      case 2:
        if (userType === 'new') {
          return (
            <StepNewTraderBalance 
              startingBalance={startingBalance} 
              setStartingBalance={setStartingBalance} 
            />
          );
        }
        // Experienced trader - start date and balance
        return (
          <StepExperiencedStart 
            startDate={startDate}
            setStartDate={setStartDate}
            startingBalance={startingBalance}
            setStartingBalance={setStartingBalance}
            minDate={MIN_START_DATE}
          />
        );
      
      case 3:
        // Deposits and withdrawals (was case 4)
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-500/20 flex items-center justify-center">
                <ArrowDownCircle className="w-8 h-8 text-amber-400" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Any deposits or withdrawals?</h2>
              <p className="text-zinc-400 text-sm">
                Enter any deposits or withdrawals between {startDate ? format(startDate, 'MMM d') : 'start'} and today
              </p>
            </div>
            
            <div className="max-w-lg mx-auto">
              {/* Add transaction form */}
              <div className="p-3 sm:p-4 rounded-lg bg-zinc-900/50 mb-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
                  <div>
                    <Label className="text-xs text-zinc-400">Type</Label>
                    <Select value={newTransactionType} onValueChange={setNewTransactionType}>
                      <SelectTrigger className="mt-1 bg-zinc-800 border-zinc-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-zinc-700">
                        <SelectItem value="deposit">Deposit</SelectItem>
                        <SelectItem value="withdrawal">Withdrawal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs text-zinc-400">Amount</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={newTransactionAmount}
                      onChange={(e) => setNewTransactionAmount(e.target.value)}
                      placeholder="0.00"
                      className="mt-1 input-dark"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-zinc-400">Date</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className={`w-full justify-start text-left font-normal mt-1 h-9 ${!newTransactionDate ? 'text-zinc-500' : 'text-white'}`}
                        >
                          {newTransactionDate ? format(newTransactionDate, 'MMM d') : 'Select'}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0 bg-zinc-900 border-zinc-700" align="start">
                        <Calendar
                          mode="single"
                          selected={newTransactionDate}
                          onSelect={setNewTransactionDate}
                          disabled={(date) => 
                            isBefore(date, MIN_DEPOSIT_DATE) || 
                            isAfter(date, new Date())
                          }
                          initialFocus
                          className="bg-zinc-900"
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
                <Button 
                  onClick={handleAddTransaction} 
                  className="w-full btn-primary"
                  disabled={!newTransactionAmount || !newTransactionDate}
                >
                  <Plus className="w-4 h-4 mr-2" /> Add Transaction
                </Button>
              </div>
              
              {/* Transaction list */}
              {transactions.length > 0 ? (
                <div className="space-y-2">
                  {transactions.map((tx) => (
                    <div key={tx.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                      <div className="flex items-center gap-3">
                        {tx.type === 'deposit' ? (
                          <ArrowDownCircle className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <ArrowUpCircle className="w-5 h-5 text-red-400" />
                        )}
                        <div>
                          <p className="text-sm font-medium text-white">
                            {tx.type === 'deposit' ? '+' : '-'}{formatMoney(tx.amount)}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {format(new Date(tx.date), 'MMM d, yyyy')}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemoveTransaction(tx.id)}
                        className="text-zinc-400 hover:text-red-400"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-zinc-500">
                  <p>No transactions added yet</p>
                  <p className="text-xs mt-1">You can skip this step if you had no deposits/withdrawals</p>
                </div>
              )}
            </div>
          </div>
        );
      
      case 4:
        // Enter actual profits for each trading day - Balance is source of truth (was case 5)
        const currentDay = tradingDays[currentTradeIndex];
        const currentDateKey = currentDay ? format(currentDay, 'yyyy-MM-dd') : '';
        const currentEntry = tradeEntries[currentDateKey];
        const defaultBalance = getBalanceForDay(currentTradeIndex);
        // Use entered balance if set, otherwise use calculated default
        const currentBalance = currentEntry?.balance ? parseFloat(currentEntry.balance) : defaultBalance;
        const currentLotSize = calculateLotSize(currentBalance);
        const currentProjected = calculateProjectedProfit(currentLotSize);
        
        // Calculate progress
        const completedDays = Object.keys(tradeEntries).length;
        const totalDays = tradingDays.length;
        const progressPercent = totalDays > 0 ? (completedDays / totalDays) * 100 : 0;
        
        return (
          <div className="space-y-4">
            {/* Header with disclaimer */}
            <div className="text-center">
              <h2 className="text-lg font-bold text-white">Enter Your Daily Trades</h2>
              <p className="text-[11px] text-zinc-500 mt-1 max-w-sm mx-auto">
                The goal is to catch up to your current account value with granular daily trade estimates. Commissions are totaled at the end.
              </p>
              <div className="flex items-center justify-center gap-2 mt-2">
                <Progress value={progressPercent} className="h-1.5 w-32" />
                <span className="text-xs text-zinc-500">{completedDays}/{totalDays}</span>
              </div>
            </div>
            
            {currentDay && (
              <Card className="max-w-md mx-auto glass-card">
                {/* Compact Header */}
                <div className="px-4 py-2 border-b border-zinc-800 flex items-center justify-between">
                  <span className="text-white font-medium text-sm">{format(currentDay, 'EEE, MMM d, yyyy')}</span>
                  <span className="text-xs text-zinc-500">Day {currentTradeIndex + 1}/{totalDays}</span>
                  {currentEntry?.missed && (
                    <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">Missed</span>
                  )}
                </div>
                
                <CardContent className="p-3 space-y-3">
                  {/* Row 1: Balance (primary), LOT (derived), Projected */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-zinc-900/50 rounded p-2">
                      <p className="text-[10px] text-zinc-500 uppercase">Balance</p>
                      <div className="relative mt-0.5">
                        <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-zinc-500 text-xs">$</span>
                        <Input
                          type="number"
                          step="0.01"
                          value={currentEntry?.balance ?? defaultBalance.toFixed(2)}
                          onChange={(e) => handleTradeEntry('balance', e.target.value)}
                          className="h-7 pl-5 pr-1 input-dark font-mono text-white text-sm"
                          disabled={currentEntry?.missed}
                        />
                      </div>
                    </div>
                    <div className="bg-zinc-900/50 rounded p-2">
                      <p className="text-[10px] text-zinc-500 uppercase">LOT Size</p>
                      <p className="font-mono text-purple-400 text-sm mt-1">{currentLotSize.toFixed(2)}</p>
                    </div>
                    <div className="bg-zinc-900/50 rounded p-2">
                      <p className="text-[10px] text-zinc-500 uppercase">Projected</p>
                      <p className="font-mono text-blue-400 text-sm mt-1">{formatMoney(currentProjected)}</p>
                    </div>
                  </div>
                  
                  {!currentEntry?.missed && (
                    <>
                      {/* Row 2: Product, Direction, Actual Profit */}
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <p className="text-[10px] text-zinc-500 uppercase mb-1">Product</p>
                          <Select
                            value={currentEntry?.product || 'MOIL10'}
                            onValueChange={(value) => handleTradeEntry('product', value)}
                          >
                            <SelectTrigger className="h-8 input-dark text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-900 border-zinc-700">
                              {PRODUCTS.map(p => (
                                <SelectItem key={p} value={p} className="text-white text-xs">{p}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <p className="text-[10px] text-zinc-500 uppercase mb-1">Direction</p>
                          <Select
                            value={currentEntry?.direction || 'BUY'}
                            onValueChange={(value) => handleTradeEntry('direction', value)}
                          >
                            <SelectTrigger className="h-8 input-dark text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-900 border-zinc-700">
                              {DIRECTIONS.map(d => (
                                <SelectItem key={d} value={d} className={`text-xs ${d === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                                  {d}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <p className="text-[10px] text-zinc-500 uppercase mb-1">Actual Profit</p>
                          <div className="relative">
                            <span className="absolute left-2 top-1/2 -translate-y-1/2 text-zinc-500 text-xs">$</span>
                            <Input
                              type="number"
                              step="0.01"
                              value={currentEntry?.actualProfit ?? ''}
                              onChange={(e) => handleTradeEntry('actualProfit', e.target.value)}
                              placeholder="0.00"
                              className="h-8 pl-5 input-dark font-mono text-sm"
                            />
                          </div>
                        </div>
                      </div>
                      
                      {/* Row 3: P/L Difference */}
                      {currentEntry?.actualProfit !== undefined && (
                        <div className="bg-zinc-900/50 rounded p-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-zinc-500">P/L Difference:</span>
                            <span className={`font-mono ${(parseFloat(currentEntry.actualProfit) - currentProjected) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {(parseFloat(currentEntry.actualProfit) - currentProjected) >= 0 ? '+' : ''}
                              {formatMoney(parseFloat(currentEntry.actualProfit) - currentProjected)}
                            </span>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
                
                {/* Compact Footer */}
                <div className="px-3 py-2 border-t border-zinc-800 flex items-center justify-between">
                  {currentEntry?.missed ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleUndoMissedTrade}
                      className="h-7 text-xs text-red-400 hover:bg-red-500/10"
                    >
                      <RotateCcw className="w-3 h-3 mr-1" /> Undo
                    </Button>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleMissedTrade}
                      className="h-7 text-xs"
                      disabled={currentEntry?.actualProfit !== undefined}
                    >
                      <X className="w-3 h-3 mr-1" /> Missed
                    </Button>
                  )}
                  
                  <div className="flex gap-1">
                    {currentTradeIndex > 0 && (
                      <Button variant="outline" size="sm" onClick={handlePrevTrade} className="h-7 w-7 p-0">
                        <ChevronLeft className="w-4 h-4" />
                      </Button>
                    )}
                    {currentTradeIndex < tradingDays.length - 1 && (
                      <Button 
                        size="sm"
                        onClick={handleNextTrade}
                        className="h-7 px-3 btn-primary"
                        disabled={!currentEntry || (!currentEntry.missed && currentEntry.actualProfit === undefined)}
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}
            
            {/* Commission Entry Card - shown when all days are complete or on last day */}
            {currentTradeIndex === tradingDays.length - 1 && (
              <Card className="max-w-md mx-auto glass-card mt-4 border-emerald-500/30">
                <div className="px-4 py-2 border-b border-zinc-800 bg-emerald-500/10">
                  <span className="text-emerald-400 font-medium text-sm flex items-center gap-2">
                    <DollarSign className="w-4 h-4" />
                    Total Commission (Optional)
                  </span>
                </div>
                <CardContent className="p-3">
                  <p className="text-xs text-zinc-400 mb-2">
                    Enter the total referral commission you&apos;ve received during this trading period. This will be added to your account balance.
                  </p>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      value={totalCommission}
                      onChange={(e) => setTotalCommission(e.target.value)}
                      placeholder="0.00"
                      className="pl-7 input-dark font-mono text-lg"
                      data-testid="total-commission-input"
                    />
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        );
      
      default:
        return null;
    }
  };
  
  const progress = (currentStep / getTotalSteps()) * 100;
  
  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-2xl bg-zinc-900 border-zinc-700 max-h-[90vh] overflow-y-auto p-4 sm:p-6">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center justify-between">
            <span className="text-base sm:text-lg">
              {isReset ? 'Reset Profit Tracker' : 'Setup Profit Tracker'}
            </span>
            <span className="text-xs sm:text-sm font-normal text-zinc-400">
              Step {currentStep} of {getTotalSteps()}
            </span>
          </DialogTitle>
          <Progress value={progress} className="h-1 mt-2" />
        </DialogHeader>
        
        <div className="py-2 sm:py-4">
          {renderStepContent()}
        </div>
        
        {/* Mobile-friendly footer buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-4 border-t border-zinc-800">
          {/* Secondary actions - stacked on mobile */}
          <div className="flex flex-wrap gap-2 order-2 sm:order-1">
            {currentStep > 1 && (
              <Button variant="outline" onClick={handleBack} className="flex-1 sm:flex-initial">
                <ChevronLeft className="w-4 h-4 mr-1 sm:mr-2" /> Back
              </Button>
            )}
            {currentStep > 1 && (
              <Button 
                variant="ghost" 
                onClick={handleRestart} 
                className="text-red-400 hover:text-red-300 hover:bg-red-500/10 flex-1 sm:flex-initial"
              >
                <RotateCcw className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Restart</span><span className="sm:hidden">Reset</span>
              </Button>
            )}
            <Button variant="ghost" onClick={handleSaveForLater} className="text-zinc-400 flex-1 sm:flex-initial">
              <Save className="w-4 h-4 mr-1 sm:mr-2" /> <span className="hidden sm:inline">Save & Continue Later</span><span className="sm:hidden">Save</span>
            </Button>
          </div>
          
          {/* Primary action - full width on mobile */}
          <Button 
            onClick={handleNext} 
            className="btn-primary w-full sm:w-auto order-1 sm:order-2"
            disabled={isLoading || (currentStep === 1 && !userType)}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <>
                {(currentStep === 2 && userType === 'new') || 
                 (currentStep === 4 && userType === 'experienced') ? 'Complete Setup' : 'Next'}
                <ChevronRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default OnboardingWizard;
