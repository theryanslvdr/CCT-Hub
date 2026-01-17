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

export const OnboardingWizard = ({ isOpen, onClose, onComplete, isReset = false }) => {
  // Wizard state
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
  const [tradeEntries, setTradeEntries] = useState({}); // { dateKey: { actualProfit: number, commission: number, lotSize: number, missed: boolean, product: string, direction: string } }
  
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
  const getBalanceForDay = (dayIndex) => {
    // For experienced traders, LOT size is the source of truth
    // Balance = LOT × 980
    // If LOT is set for this day, use it; otherwise calculate from running balance
    
    const dayDate = tradingDays[dayIndex];
    if (!dayDate) return parseFloat(startingBalance) || 0;
    
    const dateKey = format(dayDate, 'yyyy-MM-dd');
    const entry = tradeEntries[dateKey];
    
    // If user has entered a LOT size for this day, derive balance from it
    if (entry?.lotSize) {
      return calculateBalanceFromLot(parseFloat(entry.lotSize));
    }
    
    // Otherwise, calculate running balance from start
    let balance = parseFloat(startingBalance) || 0;
    
    // Add deposits/withdrawals up to this day
    for (const tx of transactions) {
      const txDate = new Date(tx.date);
      if (isBefore(txDate, dayDate) || txDate.toDateString() === dayDate.toDateString()) {
        if (tx.type === 'deposit') {
          balance += parseFloat(tx.amount) || 0;
        } else {
          balance -= parseFloat(tx.amount) || 0;
        }
      }
    }
    
    // For days without LOT entry, use previous day's LOT balance + profit
    // This gives a reasonable default before user enters their actual LOT
    for (let i = 0; i < dayIndex; i++) {
      const prevDay = tradingDays[i];
      const prevDateKey = format(prevDay, 'yyyy-MM-dd');
      const prevEntry = tradeEntries[prevDateKey];
      if (prevEntry && !prevEntry.missed) {
        if (prevEntry.lotSize) {
          // Previous day had a LOT, so use that as base
          balance = calculateBalanceFromLot(parseFloat(prevEntry.lotSize));
        }
        // Add actual profit (commission is captured in next day's LOT balance)
        balance += parseFloat(prevEntry.actualProfit) || 0;
      }
    }
    
    return balance;
  };
  
  // Get total steps based on user type
  const getTotalSteps = () => {
    if (!userType) return 2;
    if (userType === 'new') return 2;
    return 5; // experienced: type, start date, balance, transactions, trade profits
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
      missed: false 
    };
    
    setTradeEntries({
      ...tradeEntries,
      [dateKey]: { 
        ...currentData,
        [field]: field === 'actualProfit' ? (parseFloat(value) || 0) : value,
        missed: false 
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
  
  // Handle next trade entry
  const handleNextTrade = () => {
    const day = tradingDays[currentTradeIndex];
    const dateKey = format(day, 'yyyy-MM-dd');
    const entry = tradeEntries[dateKey];
    
    if (!entry || (!entry.missed && entry.actualProfit === undefined)) {
      toast.error('Please enter your actual profit or mark as missed');
      return;
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
      // Validate start date for experienced trader
      if (!startDate) {
        toast.error('Please select your start date');
        return;
      }
    }
    
    if (currentStep === 3 && userType === 'experienced') {
      // Validate starting balance
      if (!startingBalance || parseFloat(startingBalance) <= 0) {
        toast.error('Please enter your starting balance');
        return;
      }
    }
    
    if (currentStep === 4 && userType === 'experienced') {
      // Transactions step - can proceed without any
    }
    
    if (currentStep === 5 && userType === 'experienced') {
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
          actual_profit: entry.actualProfit,
          missed: entry.missed
        }))
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
          <div className="space-y-6">
            <div className="text-center mb-8">
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">
                {isReset ? 'Reset Your Tracker' : 'Welcome to CrossCurrent!'}
              </h2>
              <p className="text-zinc-400">
                Let&apos;s set up your profit tracker. Are you new to Merin trading?
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card 
                className={`cursor-pointer transition-all hover:border-blue-500/50 ${userType === 'new' ? 'border-blue-500 bg-blue-500/10' : 'glass-card'}`}
                onClick={() => setUserType('new')}
              >
                <CardContent className="p-6 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <User className="w-8 h-8 text-emerald-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">New Trader / Start Fresh</h3>
                  <p className="text-sm text-zinc-400">
                    {isReset ? 'Start over with a clean slate.' : 'Just starting my trading journey.'} Set up a fresh tracker.
                  </p>
                  {userType === 'new' && (
                    <div className="mt-4">
                      <Check className="w-6 h-6 text-emerald-400 mx-auto" />
                    </div>
                  )}
                </CardContent>
              </Card>
              
              <Card 
                className={`cursor-pointer transition-all hover:border-blue-500/50 ${userType === 'experienced' ? 'border-blue-500 bg-blue-500/10' : 'glass-card'}`}
                onClick={() => setUserType('experienced')}
              >
                <CardContent className="p-6 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <TrendingUp className="w-8 h-8 text-purple-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Experienced Trader</h3>
                  <p className="text-sm text-zinc-400">
                    Already trading on Merin. Import my trading history.
                  </p>
                  {userType === 'experienced' && (
                    <div className="mt-4">
                      <Check className="w-6 h-6 text-purple-400 mx-auto" />
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        );
      
      case 2:
        if (userType === 'new') {
          return (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <DollarSign className="w-8 h-8 text-emerald-400" />
                </div>
                <h2 className="text-xl font-bold text-white mb-2">What&apos;s your starting balance?</h2>
                <p className="text-zinc-400 text-sm">
                  Enter the amount you&apos;re starting with on Merin
                </p>
              </div>
              
              <div className="max-w-md mx-auto">
                <Label className="text-zinc-300">Starting Balance (USDT)</Label>
                <div className="relative mt-2">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400">$</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={startingBalance}
                    onChange={(e) => setStartingBalance(e.target.value)}
                    placeholder="0.00"
                    className="pl-8 input-dark text-2xl font-mono h-14 text-center"
                  />
                </div>
                
                {startingBalance && parseFloat(startingBalance) > 0 && (
                  <div className="mt-6 p-4 rounded-lg bg-zinc-900/50 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">Your LOT Size:</span>
                      <span className="font-mono text-purple-400">{calculateLotSize(parseFloat(startingBalance))}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-zinc-400">Daily Projected Profit:</span>
                      <span className="font-mono text-emerald-400">
                        {formatMoney(calculateProjectedProfit(calculateLotSize(parseFloat(startingBalance))))}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        } else {
          // Experienced trader - start date
          return (
            <div className="space-y-6">
              <div className="text-center mb-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <CalendarIcon className="w-8 h-8 text-purple-400" />
                </div>
                <h2 className="text-xl font-bold text-white mb-2">When did you start tracking?</h2>
                <p className="text-zinc-400 text-sm">
                  Select the date you want to start tracking your Merin profits
                </p>
              </div>
              
              <div className="max-w-md mx-auto">
                <Label className="text-zinc-300">Start Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={`w-full justify-start text-left font-normal mt-2 h-14 ${!startDate ? 'text-zinc-500' : 'text-white'}`}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {startDate ? format(startDate, 'MMMM d, yyyy') : 'Select your start date'}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0 bg-zinc-900 border-zinc-700" align="start">
                    <Calendar
                      mode="single"
                      selected={startDate}
                      onSelect={setStartDate}
                      disabled={(date) => 
                        isBefore(date, MIN_START_DATE) || 
                        isAfter(date, new Date()) ||
                        isWeekend(date)
                      }
                      initialFocus
                      className="bg-zinc-900"
                    />
                  </PopoverContent>
                </Popover>
                <p className="text-xs text-zinc-500 mt-2">
                  * Trading started on December 1, 2025. Only trading days (Mon-Fri) are selectable.
                </p>
                
                {startDate && (
                  <div className="mt-4 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                    <p className="text-sm text-blue-300">
                      You&apos;ll enter your actual profits for {getTradingDays(startDate, new Date()).length} trading days
                    </p>
                  </div>
                )}
              </div>
            </div>
          );
        }
      
      case 3:
        // Starting balance for experienced trader
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <DollarSign className="w-8 h-8 text-emerald-400" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">What was your starting balance?</h2>
              <p className="text-zinc-400 text-sm">
                Enter your balance on {startDate ? format(startDate, 'MMMM d, yyyy') : 'your start date'}
              </p>
            </div>
            
            <div className="max-w-md mx-auto">
              <Label className="text-zinc-300">Starting Balance (USDT)</Label>
              <div className="relative mt-2">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400">$</span>
                <Input
                  type="number"
                  step="0.01"
                  value={startingBalance}
                  onChange={(e) => setStartingBalance(e.target.value)}
                  placeholder="0.00"
                  className="pl-8 input-dark text-2xl font-mono h-14 text-center"
                />
              </div>
              
              {startingBalance && parseFloat(startingBalance) > 0 && (
                <div className="mt-6 p-4 rounded-lg bg-zinc-900/50 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">Starting LOT Size:</span>
                    <span className="font-mono text-purple-400">{calculateLotSize(parseFloat(startingBalance))}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">Starting Daily Projected:</span>
                    <span className="font-mono text-emerald-400">
                      {formatMoney(calculateProjectedProfit(calculateLotSize(parseFloat(startingBalance))))}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      
      case 4:
        // Deposits and withdrawals
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
              <div className="p-4 rounded-lg bg-zinc-900/50 mb-4">
                <div className="grid grid-cols-3 gap-3 mb-3">
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
      
      case 5:
        // Enter actual profits for each trading day
        const currentDay = tradingDays[currentTradeIndex];
        const currentDateKey = currentDay ? format(currentDay, 'yyyy-MM-dd') : '';
        const currentEntry = tradeEntries[currentDateKey];
        const currentBalance = getBalanceForDay(currentTradeIndex);
        const defaultLotSize = calculateLotSize(currentBalance);
        // Use custom LOT if set, otherwise use calculated
        const currentLotSize = currentEntry?.lotSize ? parseFloat(currentEntry.lotSize) : defaultLotSize;
        const currentLotBalance = currentEntry?.lotSize ? calculateBalanceFromLot(parseFloat(currentEntry.lotSize)) : currentBalance;
        const currentProjected = calculateProjectedProfit(currentLotSize);
        
        // Calculate commission: (Next Day Balance - Current Day Balance) - Current Day Actual Profit
        // Commission is auto-calculated based on next day's LOT entry
        const nextDay = tradingDays[currentTradeIndex + 1];
        const nextDateKey = nextDay ? format(nextDay, 'yyyy-MM-dd') : '';
        const nextEntry = tradeEntries[nextDateKey];
        let calculatedCommission = null;
        if (nextEntry?.lotSize && currentEntry?.actualProfit !== undefined) {
          const nextDayBalance = calculateBalanceFromLot(parseFloat(nextEntry.lotSize));
          const balanceDiff = nextDayBalance - currentLotBalance;
          calculatedCommission = balanceDiff - (parseFloat(currentEntry.actualProfit) || 0);
        }
        
        // Calculate progress
        const completedDays = Object.keys(tradeEntries).length;
        const totalDays = tradingDays.length;
        const progressPercent = totalDays > 0 ? (completedDays / totalDays) * 100 : 0;
        
        return (
          <div className="space-y-4">
            {/* Header */}
            <div className="text-center">
              <h2 className="text-lg font-bold text-white">Enter Your Trade Profits</h2>
              <div className="flex items-center justify-center gap-2 mt-1">
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
                  {/* Row 1: LOT, Balance, Projected */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-zinc-900/50 rounded p-2">
                      <p className="text-[10px] text-zinc-500 uppercase">LOT Size</p>
                      <Input
                        type="number"
                        step="0.01"
                        value={currentEntry?.lotSize ?? defaultLotSize.toFixed(2)}
                        onChange={(e) => handleTradeEntry('lotSize', e.target.value)}
                        className="h-7 px-2 mt-0.5 input-dark font-mono text-purple-400 text-sm text-center"
                        disabled={currentEntry?.missed}
                      />
                    </div>
                    <div className="bg-zinc-900/50 rounded p-2">
                      <p className="text-[10px] text-zinc-500 uppercase">Balance</p>
                      <p className="font-mono text-white text-sm mt-1">{formatMoney(currentLotBalance)}</p>
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
                      
                      {/* Row 3: Summary - P/L Diff and Commission */}
                      {currentEntry?.actualProfit !== undefined && (
                        <div className="bg-zinc-900/50 rounded p-2 grid grid-cols-2 gap-2 text-xs">
                          <div className="flex justify-between">
                            <span className="text-zinc-500">P/L Diff:</span>
                            <span className={`font-mono ${(parseFloat(currentEntry.actualProfit) - currentProjected) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {(parseFloat(currentEntry.actualProfit) - currentProjected) >= 0 ? '+' : ''}
                              {formatMoney(parseFloat(currentEntry.actualProfit) - currentProjected)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-zinc-500">Commission:</span>
                            {calculatedCommission !== null ? (
                              <span className="font-mono text-amber-400">{formatMoney(calculatedCommission)}</span>
                            ) : (
                              <span className="text-zinc-600 italic">Enter next LOT</span>
                            )}
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
          </div>
        );
      
      default:
        return null;
    }
  };
  
  const progress = (currentStep / getTotalSteps()) * 100;
  
  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-2xl bg-zinc-900 border-zinc-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center justify-between">
            <span>
              {isReset ? 'Reset Profit Tracker' : 'Setup Profit Tracker'}
            </span>
            <span className="text-sm font-normal text-zinc-400">
              Step {currentStep} of {getTotalSteps()}
            </span>
          </DialogTitle>
          <Progress value={progress} className="h-1 mt-2" />
        </DialogHeader>
        
        <div className="py-4">
          {renderStepContent()}
        </div>
        
        <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
          <div className="flex gap-2">
            {currentStep > 1 && (
              <Button variant="outline" onClick={handleBack}>
                <ChevronLeft className="w-4 h-4 mr-2" /> Back
              </Button>
            )}
            <Button variant="ghost" onClick={handleSaveForLater} className="text-zinc-400">
              <Save className="w-4 h-4 mr-2" /> Save & Continue Later
            </Button>
          </div>
          
          <Button 
            onClick={handleNext} 
            className="btn-primary"
            disabled={isLoading || (currentStep === 1 && !userType)}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <>
                {(currentStep === 2 && userType === 'new') || 
                 (currentStep === 5 && userType === 'experienced') ? 'Complete Setup' : 'Next'}
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
