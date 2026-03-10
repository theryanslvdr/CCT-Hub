import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { format, isWeekend, startOfDay, eachDayOfInterval } from 'date-fns';
import { 
  ChevronRight, ChevronLeft, Calendar as CalendarIcon, 
  DollarSign, ArrowDownCircle, ArrowUpCircle, Check, Loader2,
  Wallet, History, TrendingUp, Plus, Trash2, X, RotateCcw, Save
} from 'lucide-react';
import { toast } from 'sonner';
import { profitAPI, tradeAPI } from '@/lib/api';

// Constants
const MIN_START_DATE = new Date(2025, 11, 1);
const MIN_DEPOSIT_DATE = new Date(2025, 10, 24);

// Format currency
const formatMoney = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(amount);
};

// Calculations
const calculateLotSize = (balance) => Math.floor((balance / 980) * 100) / 100;
const calculateProjectedProfit = (lotSize) => Math.floor(lotSize * 15 * 100) / 100;

// Step Progress Indicator
const StepIndicator = ({ current, total }) => {
  return (
    <div className="flex gap-2 w-full px-2">
      {Array.from({ length: total }, (_, i) => (
        <div 
          key={i}
          className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
            i < current 
              ? 'bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]' 
              : i === current 
                ? 'bg-cyan-500/50' 
                : 'bg-zinc-800'
          }`}
        />
      ))}
    </div>
  );
};

// Selection Card Component
const SelectionCard = ({ 
  selected, 
  onClick, 
  icon: Icon, 
  title, 
  description, 
  accentColor = 'cyan',
  testId 
}) => {
  return (
    <button
      onClick={onClick}
      data-testid={testId}
      className={`
        relative w-full p-6 rounded-2xl border-2 text-left
        transition-all duration-300 overflow-hidden group
        ${selected 
          ? `border-${accentColor}-500 bg-${accentColor}-500/10 shadow-[0_0_30px_rgba(6,182,212,0.2)]` 
          : 'border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 hover:bg-zinc-800/50'
        }
      `}
    >
      {/* Background Glow Effect */}
      <div className={`
        absolute -top-20 -right-20 w-40 h-40 rounded-full blur-3xl transition-opacity duration-500
        ${selected ? 'opacity-30' : 'opacity-0 group-hover:opacity-10'}
        ${accentColor === 'cyan' ? 'bg-cyan-500' : 'bg-teal-500'}
      `} />
      
      {/* Content */}
      <div className="relative z-10">
        <div className={`
          w-14 h-14 rounded-2xl flex items-center justify-center mb-4
          transition-all duration-300
          ${selected 
            ? `bg-${accentColor}-500/20 text-${accentColor}-400` 
            : 'bg-zinc-800 text-zinc-400 group-hover:bg-zinc-700'
          }
        `}>
          <Icon className="w-7 h-7" />
        </div>
        
        <h3 className={`
          text-lg font-bold mb-2 transition-colors
          ${selected ? 'text-white' : 'text-zinc-300 group-hover:text-white'}
        `}>
          {title}
        </h3>
        
        <p className="text-sm text-zinc-500 leading-relaxed">
          {description}
        </p>
        
        {/* Check indicator */}
        {selected && (
          <div className="absolute top-4 right-4 w-8 h-8 rounded-full bg-cyan-500 flex items-center justify-center">
            <Check className="w-5 h-5 text-white" />
          </div>
        )}
      </div>
    </button>
  );
};

// Glass Input Component
const GlassInput = ({ label, icon: Icon, value, onChange, placeholder, type = 'text', testId, prefix }) => {
  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
          {label}
        </label>
      )}
      <div className="relative">
        {prefix && (
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">
            {prefix}
          </span>
        )}
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          data-testid={testId}
          className={`
            w-full bg-zinc-950/80 border border-zinc-800 rounded-xl
            text-white text-lg font-mono placeholder:text-zinc-600
            focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20
            transition-all duration-300
            ${prefix ? 'pl-10 pr-4 py-5' : 'px-4 py-5'}
          `}
        />
        {Icon && !prefix && (
          <Icon className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
        )}
      </div>
    </div>
  );
};

// Stats Card Component
const StatsCard = ({ label, value, color = 'cyan' }) => {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
      <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-mono font-bold ${
        color === 'cyan' ? 'text-cyan-400' : color === 'teal' ? 'text-teal-400' : 'text-white'
      }`}>
        {value}
      </p>
    </div>
  );
};

// Main Wizard Component
export const OnboardingWizardMobile = ({ isOpen, onClose, onComplete, isReset = false }) => {
  // Wizard state
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  
  // User type
  const [userType, setUserType] = useState(null);
  
  // Common fields
  const [startingBalance, setStartingBalance] = useState('');
  
  // Experienced trader fields
  const [startDate, setStartDate] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [newTransactionType, setNewTransactionType] = useState('deposit');
  const [newTransactionAmount, setNewTransactionAmount] = useState('');
  const [newTransactionDate, setNewTransactionDate] = useState(null);
  
  // Trade profits entry
  const [tradingDays, setTradingDays] = useState([]);
  const [currentTradeIndex, setCurrentTradeIndex] = useState(0);
  const [tradeEntries, setTradeEntries] = useState({});
  
  // Commission
  const [totalCommission, setTotalCommission] = useState('');
  
  // Global trading settings
  const [globalHolidays, setGlobalHolidays] = useState([]);
  const [tradingProducts, setTradingProducts] = useState([]);
  
  const defaultProducts = ['MOIL10', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY'];
  const DIRECTIONS = ['BUY', 'SELL'];
  
  const PRODUCTS = useMemo(() => 
    tradingProducts.length > 0 
      ? tradingProducts.filter(p => p.is_active).map(p => p.name) 
      : defaultProducts,
    [tradingProducts]
  );
  
  const allHolidays = useMemo(() => new Set(
    globalHolidays.map(h => h.date)
  ), [globalHolidays]);
  
  const isHolidayDate = useCallback((date) => {
    const dateKey = format(date, 'yyyy-MM-dd');
    return allHolidays.has(dateKey);
  }, [allHolidays]);

  // Save progress to localStorage
  const saveProgress = useCallback(() => {
    const data = {
      userType,
      startingBalance,
      startDate: startDate?.toISOString(),
      transactions,
      tradeEntries,
      currentStep,
      currentTradeIndex,
      totalCommission
    };
    localStorage.setItem('onboarding_wizard_progress', JSON.stringify(data));
  }, [userType, startingBalance, startDate, transactions, tradeEntries, currentStep, currentTradeIndex, totalCommission]);

  // Auto-save progress when state changes
  useEffect(() => {
    if (isOpen && (userType || startingBalance || startDate)) {
      saveProgress();
    }
  }, [isOpen, userType, startingBalance, startDate, transactions, tradeEntries, currentStep, currentTradeIndex, totalCommission, saveProgress]);

  // Load saved progress on mount
  useEffect(() => {
    if (isOpen) {
      const saved = localStorage.getItem('onboarding_wizard_progress');
      if (saved) {
        try {
          const data = JSON.parse(saved);
          if (data.userType) setUserType(data.userType);
          if (data.startingBalance) setStartingBalance(data.startingBalance);
          if (data.startDate) setStartDate(new Date(data.startDate));
          if (data.transactions) setTransactions(data.transactions);
          if (data.tradeEntries) setTradeEntries(data.tradeEntries);
          if (data.currentStep) setCurrentStep(data.currentStep);
          if (data.currentTradeIndex) setCurrentTradeIndex(data.currentTradeIndex);
          if (data.totalCommission) setTotalCommission(data.totalCommission);
        } catch (e) {
          console.error('Failed to load saved progress:', e);
        }
      }
    }
  }, [isOpen]);

  // Handle save and continue later
  const handleSaveForLater = () => {
    saveProgress();
    toast.success('Progress saved! You can continue later.');
    onClose();
  };

  // Fetch global settings
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const [holidaysRes, productsRes] = await Promise.all([
          tradeAPI.getGlobalHolidays(),
          tradeAPI.getTradingProducts()
        ]);
        setGlobalHolidays(holidaysRes.data?.holidays || []);
        setTradingProducts(productsRes.data?.products || []);
      } catch (error) {
        console.error('Failed to fetch global settings:', error);
      }
    };
    if (isOpen) fetchSettings();
  }, [isOpen]);

  // Generate trading days
  const generateTradingDays = useCallback(() => {
    if (!startDate) return [];
    const today = startOfDay(new Date());
    const start = startOfDay(startDate);
    if (start >= today) return [];
    
    const allDays = eachDayOfInterval({ start, end: today });
    return allDays.filter(date => {
      if (isWeekend(date)) return false;
      if (isHolidayDate(date)) return false;
      const dateKey = format(date, 'yyyy-MM-dd');
      const todayKey = format(today, 'yyyy-MM-dd');
      return dateKey !== todayKey;
    });
  }, [startDate, isHolidayDate]);

  useEffect(() => {
    if (userType === 'experienced' && startDate) {
      const days = generateTradingDays();
      setTradingDays(days);
    }
  }, [userType, startDate, generateTradingDays]);

  // Calculate totals
  const getTotalSteps = () => {
    if (!userType) return 2;
    if (userType === 'new') return 2;
    return 4;
  };

  const currentTradingDay = tradingDays[currentTradeIndex];
  const currentDateKey = currentTradingDay ? format(currentTradingDay, 'yyyy-MM-dd') : null;
  const currentEntry = currentDateKey ? tradeEntries[currentDateKey] : null;

  // Calculate running balance
  const calculateRunningBalance = useCallback((upToIndex) => {
    let balance = parseFloat(startingBalance) || 0;
    
    transactions.forEach(tx => {
      if (tx.type === 'deposit') balance += tx.amount;
      else balance -= tx.amount;
    });
    
    for (let i = 0; i < upToIndex && i < tradingDays.length; i++) {
      const day = tradingDays[i];
      const dateKey = format(day, 'yyyy-MM-dd');
      const entry = tradeEntries[dateKey];
      if (entry?.actualProfit !== undefined && !entry?.missed) {
        balance += parseFloat(entry.actualProfit) || 0;
      }
    }
    return balance;
  }, [startingBalance, transactions, tradingDays, tradeEntries]);

  const currentBalance = calculateRunningBalance(currentTradeIndex);
  const currentLotSize = calculateLotSize(currentBalance);
  const currentProjected = calculateProjectedProfit(currentLotSize);

  // Handlers
  const handleTradeEntry = (field, value) => {
    if (!currentDateKey) return;
    // For actualProfit, treat empty string as clearing the field
    const processedValue = (field === 'actualProfit' && value === '') ? undefined : value;
    setTradeEntries(prev => ({
      ...prev,
      [currentDateKey]: {
        ...prev[currentDateKey],
        [field]: processedValue,
        balance: currentBalance,
        lotSize: currentLotSize,
        projectedProfit: currentProjected
      }
    }));
  };

  const handleClearEntry = () => {
    if (!currentDateKey) return;
    setTradeEntries(prev => {
      const next = { ...prev };
      delete next[currentDateKey];
      return next;
    });
  };

  const handleMissedTrade = () => {
    if (!currentDateKey) return;
    setTradeEntries(prev => ({
      ...prev,
      [currentDateKey]: {
        missed: true,
        balance: currentBalance,
        lotSize: currentLotSize,
        projectedProfit: currentProjected
      }
    }));
  };

  const handleAddTransaction = () => {
    if (!newTransactionAmount || !newTransactionDate) {
      toast.error('Please enter amount and date');
      return;
    }
    setTransactions(prev => [...prev, {
      id: Date.now(),
      type: newTransactionType,
      amount: parseFloat(newTransactionAmount),
      date: newTransactionDate
    }]);
    setNewTransactionAmount('');
    setNewTransactionDate(null);
  };

  const handleRemoveTransaction = (id) => {
    setTransactions(prev => prev.filter(t => t.id !== id));
  };

  const handleNext = async () => {
    if (currentStep === 1 && !userType) {
      toast.error('Please select your trader type');
      return;
    }
    
    if (currentStep === 2) {
      if (!startingBalance || parseFloat(startingBalance) < 10) {
        toast.error('Please enter a valid starting balance (min $10)');
        return;
      }
      if (userType === 'experienced' && !startDate) {
        toast.error('Please select your start date');
        return;
      }
      if (userType === 'new') {
        await handleComplete();
        return;
      }
    }
    
    if (currentStep === 4) {
      await handleComplete();
      return;
    }
    
    setCurrentStep(prev => prev + 1);
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      const tradeHistory = Object.entries(tradeEntries)
        .filter(([_, entry]) => entry)
        .map(([dateKey, entry]) => ({
          date: dateKey,
          actual_profit: (!entry.missed && entry.actualProfit !== undefined) ? parseFloat(entry.actualProfit) || 0 : null,
          missed: entry.missed || false,
          balance: entry.balance || null,
          product: entry.product || 'MOIL10',
          direction: entry.direction || 'BUY'
        }));

      const onboardingData = {
        starting_balance: parseFloat(startingBalance),
        start_date: startDate ? format(startDate, 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd'),
        transactions: transactions.map(t => ({
          type: t.type,
          amount: t.amount,
          date: format(t.date, 'yyyy-MM-dd')
        })),
        trade_entries: tradeHistory,
        total_commission: parseFloat(totalCommission) || 0,
        is_reset: isReset,
        user_type: userType
      };

      await profitAPI.completeOnboarding(onboardingData);
      localStorage.setItem('user_trading_type', userType);
      toast.success('Setup complete! Welcome to CrossCurrent');
      onComplete(onboardingData);
    } catch (error) {
      console.error('Onboarding failed:', error);
      toast.error(error.response?.data?.detail || 'Setup failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const progress = (currentStep / getTotalSteps()) * 100;
  const lotSize = calculateLotSize(parseFloat(startingBalance) || 0);
  const dailyTarget = calculateProjectedProfit(lotSize);

  return (
    <div className="fixed inset-0 z-[9999] bg-black/90 backdrop-blur-sm">
      {/* Main Container */}
      <div className="h-full w-full flex flex-col bg-gradient-to-b from-zinc-900 via-zinc-950 to-black overflow-hidden">
        
        {/* Header */}
        <div className="flex-shrink-0 p-6 pb-4 space-y-4">
          <StepIndicator current={currentStep - 1} total={getTotalSteps()} />
          <div className="text-xs text-zinc-500 text-center font-medium tracking-widest uppercase">
            Step {currentStep} of {getTotalSteps()}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto px-6 pb-6">
          
          {/* STEP 1: User Type Selection */}
          {currentStep === 1 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="text-center space-y-3 py-4">
                <h1 className="text-3xl font-extrabold text-white tracking-tight">
                  {isReset ? 'RESET TRACKER' : 'WELCOME'}
                </h1>
                <p className="text-zinc-400 text-base">
                  {isReset ? 'Start fresh with your trading journey' : "Let's set up your profit tracker"}
                </p>
              </div>
              
              <div className="space-y-4 pt-4">
                <SelectionCard
                  selected={userType === 'new'}
                  onClick={() => setUserType('new')}
                  icon={Wallet}
                  title="New Trader"
                  description="Just starting out? Set up a fresh tracker with your current balance."
                  accentColor="cyan"
                  testId="user-type-new"
                />
                
                <SelectionCard
                  selected={userType === 'experienced'}
                  onClick={() => setUserType('experienced')}
                  icon={History}
                  title="Experienced Trader"
                  description="Already trading? Import your history and pick up where you left off."
                  accentColor="teal"
                  testId="user-type-experienced"
                />
              </div>
            </div>
          )}

          {/* STEP 2: Balance Entry */}
          {currentStep === 2 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="text-center space-y-3 py-2">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500/20 to-teal-500/20 flex items-center justify-center mb-4">
                  <DollarSign className="w-8 h-8 text-cyan-400" />
                </div>
                <h1 className="text-2xl font-bold text-white">
                  {userType === 'new' ? 'Starting Balance' : 'When Did You Start?'}
                </h1>
                <p className="text-zinc-400 text-sm">
                  {userType === 'new' 
                    ? 'Enter your current Merin account balance'
                    : 'Select your first trade date and initial balance'
                  }
                </p>
              </div>

              <div className="space-y-5">
                {/* Date picker for experienced traders */}
                {userType === 'experienced' && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Start Date
                    </label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <button
                          data-testid="start-date-picker"
                          className="w-full flex items-center justify-between bg-zinc-950/80 border border-zinc-800 rounded-xl px-4 py-5 text-left hover:border-zinc-700 transition-colors"
                        >
                          <span className={startDate ? 'text-white font-mono' : 'text-zinc-500'}>
                            {startDate ? format(startDate, 'MMMM d, yyyy') : 'Select a date'}
                          </span>
                          <CalendarIcon className="w-5 h-5 text-zinc-500" />
                        </button>
                      </PopoverTrigger>
                      <PopoverContent 
                        className="w-auto p-0 bg-zinc-900 border-zinc-800 z-[99999]" 
                        align="center"
                        side="bottom"
                        sideOffset={5}
                        collisionPadding={20}
                        avoidCollisions={true}
                      >
                        <Calendar
                          mode="single"
                          selected={startDate}
                          onSelect={setStartDate}
                          disabled={(date) => date > new Date() || date < MIN_START_DATE}
                          initialFocus
                          className="bg-zinc-900 rounded-xl"
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                )}

                {/* Balance input */}
                <GlassInput
                  label="Account Balance (USDT)"
                  value={startingBalance}
                  onChange={(e) => setStartingBalance(e.target.value)}
                  placeholder="10,000"
                  type="number"
                  prefix="$"
                  testId="starting-balance-input"
                />

                {/* Stats preview */}
                {startingBalance && parseFloat(startingBalance) > 0 && (
                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <StatsCard 
                      label="LOT Size" 
                      value={lotSize.toFixed(2)} 
                      color="cyan" 
                    />
                    <StatsCard 
                      label="Daily Target" 
                      value={formatMoney(dailyTarget)} 
                      color="teal" 
                    />
                  </div>
                )}

                {/* Info box */}
                <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <TrendingUp className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-cyan-400 font-medium">How it works</p>
                      <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                        LOT Size = Balance ÷ 980<br />
                        Daily Target = LOT × $15
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Deposits & Withdrawals */}
          {currentStep === 3 && userType === 'experienced' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="text-center space-y-3 py-2">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center mb-4">
                  <ArrowDownCircle className="w-8 h-8 text-amber-400" />
                </div>
                <h1 className="text-2xl font-bold text-white">Transactions</h1>
                <p className="text-zinc-400 text-sm">
                  Any deposits or withdrawals since {startDate ? format(startDate, 'MMM d') : 'start'}?
                </p>
              </div>

              <div className="space-y-4">
                {/* Add transaction form */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-zinc-500 uppercase tracking-wider">Type</label>
                      <Select value={newTransactionType} onValueChange={setNewTransactionType}>
                        <SelectTrigger className="mt-1 bg-zinc-950 border-zinc-800 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-900 border-zinc-800">
                          <SelectItem value="deposit" className="text-emerald-400">Deposit</SelectItem>
                          <SelectItem value="withdrawal" className="text-red-400">Withdrawal</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-xs text-zinc-500 uppercase tracking-wider">Amount</label>
                      <Input
                        type="number"
                        value={newTransactionAmount}
                        onChange={(e) => setNewTransactionAmount(e.target.value)}
                        placeholder="0.00"
                        className="mt-1 bg-zinc-950 border-zinc-800 text-white font-mono"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs text-zinc-500 uppercase tracking-wider">Date</label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <button className="w-full mt-1 flex items-center justify-between bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-left hover:border-zinc-700 transition-colors">
                          <span className={newTransactionDate ? 'text-white text-sm font-mono' : 'text-zinc-500 text-sm'}>
                            {newTransactionDate ? format(newTransactionDate, 'MMM d, yyyy') : 'Select date'}
                          </span>
                          <CalendarIcon className="w-4 h-4 text-zinc-500" />
                        </button>
                      </PopoverTrigger>
                      <PopoverContent 
                        className="w-auto p-0 bg-zinc-900 border-zinc-800 z-[99999]" 
                        align="center"
                        side="bottom"
                        sideOffset={5}
                        collisionPadding={20}
                        avoidCollisions={true}
                      >
                        <Calendar
                          mode="single"
                          selected={newTransactionDate}
                          onSelect={setNewTransactionDate}
                          disabled={(date) => date > new Date() || date < MIN_DEPOSIT_DATE}
                          initialFocus
                          className="bg-zinc-900"
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  
                  <Button
                    onClick={handleAddTransaction}
                    className="w-full bg-zinc-800 hover:bg-zinc-700 text-white"
                  >
                    <Plus className="w-4 h-4 mr-2" /> Add Transaction
                  </Button>
                </div>

                {/* Transaction list */}
                {transactions.length > 0 && (
                  <div className="space-y-2">
                    {transactions.map((tx) => (
                      <div 
                        key={tx.id} 
                        className="flex items-center justify-between bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3"
                      >
                        <div className="flex items-center gap-3">
                          {tx.type === 'deposit' ? (
                            <ArrowDownCircle className="w-5 h-5 text-emerald-400" />
                          ) : (
                            <ArrowUpCircle className="w-5 h-5 text-red-400" />
                          )}
                          <div>
                            <p className={`font-mono font-medium ${tx.type === 'deposit' ? 'text-emerald-400' : 'text-red-400'}`}>
                              {tx.type === 'deposit' ? '+' : '-'}{formatMoney(tx.amount)}
                            </p>
                            <p className="text-xs text-zinc-500">{format(tx.date, 'MMM d, yyyy')}</p>
                          </div>
                        </div>
                        <button 
                          onClick={() => handleRemoveTransaction(tx.id)}
                          className="p-2 text-zinc-500 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {transactions.length === 0 && (
                  <p className="text-center text-zinc-500 text-sm py-4">
                    No transactions added. Tap &quot;Next&quot; to continue.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* STEP 4: Trade History Entry */}
          {currentStep === 4 && userType === 'experienced' && (
            <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="text-center space-y-2">
                <h1 className="text-xl font-bold text-white">Trade History</h1>
                <p className="text-zinc-400 text-sm">
                  {tradingDays.length > 0 
                    ? `Enter profits for ${tradingDays.length} trading days`
                    : 'No trading days to enter'
                  }
                </p>
              </div>

              {tradingDays.length > 0 && currentTradingDay && (
                <div className="space-y-4">
                  {/* Day navigation */}
                  <div className="flex items-center justify-between bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3">
                    <button
                      onClick={() => setCurrentTradeIndex(Math.max(0, currentTradeIndex - 1))}
                      disabled={currentTradeIndex === 0}
                      className="p-2 text-zinc-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="text-center">
                      <p className="text-lg font-bold text-white">{format(currentTradingDay, 'EEE, MMM d')}</p>
                      <p className="text-xs text-zinc-500">Day {currentTradeIndex + 1} of {tradingDays.length}</p>
                    </div>
                    <button
                      onClick={() => setCurrentTradeIndex(Math.min(tradingDays.length - 1, currentTradeIndex + 1))}
                      disabled={currentTradeIndex === tradingDays.length - 1}
                      className="p-2 text-zinc-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Trade entry card */}
                  <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl overflow-hidden">
                    {/* Header stats */}
                    <div className="grid grid-cols-2 divide-x divide-zinc-800 border-b border-zinc-800">
                      <div className="p-4 text-center">
                        <p className="text-xs text-zinc-500 uppercase">Balance</p>
                        <p className="text-lg font-mono text-white mt-1">{formatMoney(currentBalance)}</p>
                      </div>
                      <div className="p-4 text-center">
                        <p className="text-xs text-zinc-500 uppercase">Target</p>
                        <p className="text-lg font-mono text-cyan-400 mt-1">{formatMoney(currentProjected)}</p>
                      </div>
                    </div>

                    {/* Entry form */}
                    {!currentEntry?.missed ? (
                      <div className="p-4 space-y-4">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-xs text-zinc-500 uppercase">Product</label>
                            <Select
                              value={currentEntry?.product || 'MOIL10'}
                              onValueChange={(v) => handleTradeEntry('product', v)}
                            >
                              <SelectTrigger className="mt-1 bg-zinc-950 border-zinc-800 text-white text-sm">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="bg-zinc-900 border-zinc-800 z-[99999]">
                                {PRODUCTS.map(p => (
                                  <SelectItem key={p} value={p} className="text-white text-sm">{p}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <label className="text-xs text-zinc-500 uppercase">Direction</label>
                            <Select
                              value={currentEntry?.direction || 'BUY'}
                              onValueChange={(v) => handleTradeEntry('direction', v)}
                            >
                              <SelectTrigger className="mt-1 bg-zinc-950 border-zinc-800 text-white text-sm">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="bg-zinc-900 border-zinc-800 z-[99999]">
                                {DIRECTIONS.map(d => (
                                  <SelectItem key={d} value={d} className={`text-sm ${d === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                                    {d}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        <div>
                          <label className="text-xs text-zinc-500 uppercase">Actual Profit</label>
                          <div className="relative mt-1">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 font-mono">$</span>
                            <Input
                              type="number"
                              step="0.01"
                              value={currentEntry?.actualProfit ?? ''}
                              onChange={(e) => handleTradeEntry('actualProfit', e.target.value)}
                              placeholder="0.00"
                              className="pl-8 bg-zinc-950 border-zinc-800 text-white font-mono text-lg"
                            />
                          </div>
                        </div>

                        {currentEntry?.actualProfit !== undefined && (
                          <div className="flex justify-between items-center bg-zinc-950/50 rounded-lg px-4 py-3">
                            <span className="text-sm text-zinc-400">P/L Difference</span>
                            <span className={`font-mono font-bold ${
                              (parseFloat(currentEntry.actualProfit) - currentProjected) >= 0 
                                ? 'text-emerald-400' 
                                : 'text-red-400'
                            }`}>
                              {(parseFloat(currentEntry.actualProfit) - currentProjected) >= 0 ? '+' : ''}
                              {formatMoney(parseFloat(currentEntry.actualProfit) - currentProjected)}
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="p-8 text-center">
                        <X className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                        <p className="text-zinc-400 font-medium">Marked as missed</p>
                        <button
                          onClick={() => setTradeEntries(prev => ({ ...prev, [currentDateKey]: undefined }))}
                          className="mt-3 text-sm text-cyan-400 hover:text-cyan-300"
                        >
                          Undo
                        </button>
                      </div>
                    )}

                    {/* Footer actions */}
                    {!currentEntry?.missed && (
                      <div className="border-t border-zinc-800 px-4 py-3 flex justify-between items-center">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={handleMissedTrade}
                            disabled={currentEntry?.actualProfit !== undefined && currentEntry?.actualProfit !== ''}
                            className="text-sm text-zinc-500 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1"
                          >
                            <X className="w-4 h-4" /> Missed Trade
                          </button>
                          {currentEntry?.actualProfit !== undefined && (
                            <button
                              onClick={handleClearEntry}
                              className="text-sm text-amber-500 hover:text-amber-400 flex items-center gap-1"
                            >
                              <RotateCcw className="w-3.5 h-3.5" /> Clear
                            </button>
                          )}
                        </div>
                        <span className="text-xs text-zinc-600">
                          LOT: {currentLotSize.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Commission input */}
                  {currentTradeIndex === tradingDays.length - 1 && (
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                      <label className="text-xs text-zinc-500 uppercase">Total Commission Earned</label>
                      <div className="relative mt-2">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 font-mono">$</span>
                        <Input
                          type="number"
                          value={totalCommission}
                          onChange={(e) => setTotalCommission(e.target.value)}
                          placeholder="0.00"
                          className="pl-8 bg-zinc-950 border-zinc-800 text-white font-mono"
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {tradingDays.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-zinc-500">No trading days between your start date and today.</p>
                  <p className="text-zinc-600 text-sm mt-2">This can happen if you just started or it&apos;s a weekend.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-6 pt-4 border-t border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm space-y-3">
          {/* Save & Continue Later button */}
          <button
            onClick={handleSaveForLater}
            className="w-full flex items-center justify-center gap-2 py-3 text-zinc-400 hover:text-white transition-colors"
            data-testid="wizard-save-later-btn"
          >
            <Save className="w-4 h-4" />
            <span className="text-sm font-medium">Save & Continue Later</span>
          </button>
          
          {/* Navigation buttons */}
          <div className="flex gap-3">
            {currentStep > 1 && (
              <Button
                variant="outline"
                onClick={handleBack}
                className="flex-1 bg-zinc-900 border-zinc-700 text-white hover:bg-zinc-800 py-6 rounded-xl"
              >
                <ChevronLeft className="w-5 h-5 mr-2" /> Back
              </Button>
            )}
            <Button
              onClick={handleNext}
              disabled={isLoading || (currentStep === 1 && !userType)}
              className={`
                flex-1 py-6 rounded-xl font-bold text-white
                bg-gradient-to-r from-cyan-600 to-amber-600 
                hover:from-cyan-500 hover:to-amber-500
                shadow-[0_0_20px_rgba(6,182,212,0.3)]
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-300 active:scale-95
              `}
              data-testid="wizard-next-btn"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  {(currentStep === 2 && userType === 'new') || currentStep === 4 
                    ? 'Complete Setup' 
                    : 'Continue'
                  }
                  <ChevronRight className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingWizardMobile;
