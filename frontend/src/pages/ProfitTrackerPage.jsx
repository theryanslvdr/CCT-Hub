import React, { useState, useEffect, useMemo } from 'react';
import api, { profitAPI, currencyAPI, adminAPI } from '@/lib/api';
import { formatNumber, calculateWithdrawalFees, calculateDepositFees } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { toast } from 'sonner';
import { 
  Plus, ArrowDownToLine, ArrowUpFromLine, Calculator, 
  TrendingUp, Wallet, RotateCcw, Rocket, Calendar,
  Clock, CheckCircle2, AlertTriangle, Eye, Sparkles,
  ChevronDown, FileText, Receipt, Lock, Check, ExternalLink,
  Radio, EyeOff, Award
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '@/contexts/AuthContext';

// Truncate to 2 decimal places without rounding
const truncateTo2Decimals = (num) => {
  return Math.trunc(num * 100) / 100;
};

// Format large numbers (millions, billions, trillions)
const formatLargeNumber = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  
  if (absAmount >= 1e12) {
    return `${sign}$${(absAmount / 1e12).toFixed(2)} Trillion`;
  } else if (absAmount >= 1e9) {
    return `${sign}$${(absAmount / 1e9).toFixed(2)} Billion`;
  } else if (absAmount >= 1e6) {
    return `${sign}$${(absAmount / 1e6).toFixed(2)} Million`;
  } else {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  }
};

// Standard money formatting
const formatMoney = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Calculate business days from now
const addBusinessDays = (date, days) => {
  const result = new Date(date);
  let added = 0;
  while (added < days) {
    result.setDate(result.getDate() + 1);
    const dayOfWeek = result.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      added++;
    }
  }
  return result;
};

// Common holidays (can be expanded)
const isHoliday = (date) => {
  const holidays = [
    // US Holidays
    { month: 0, day: 1 },   // New Year's Day
    { month: 0, day: 2 },   // New Year's Day observed
    { month: 6, day: 4 },   // Independence Day
    { month: 11, day: 25 }, // Christmas
    { month: 11, day: 26 }, // Christmas observed
    // Add more as needed
  ];
  
  return holidays.some(h => h.month === date.getMonth() && h.day === date.getDate());
};

// Check if date is a trading day (weekday and not holiday)
const isTradingDay = (date) => {
  const dayOfWeek = date.getDay();
  return dayOfWeek !== 0 && dayOfWeek !== 6 && !isHoliday(date);
};

// Generate daily projection for a specific month
const generateDailyProjectionForMonth = (startBalance, monthDate, tradeLogs = {}, activeSignal = null) => {
  const days = [];
  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  // Get first day of month
  const firstDay = new Date(year, month, 1);
  // Get last day of month
  const lastDay = new Date(year, month + 1, 0);
  
  let runningBalance = startBalance;
  let currentDate = new Date(firstDay);
  
  // For current month, start from today if we're past the 1st
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
  if (isCurrentMonth && today.getDate() > 1) {
    currentDate = new Date(today);
  }
  
  while (currentDate <= lastDay) {
    if (isTradingDay(currentDate)) {
      const dateKey = currentDate.toISOString().split('T')[0];
      const lotSize = runningBalance / 980;
      const targetProfit = lotSize * 15;
      
      // Check for actual profit from trade logs
      const actualProfit = tradeLogs[dateKey]?.actual_profit;
      const hasTraded = tradeLogs[dateKey]?.has_traded;
      
      // Determine status
      let status = 'pending'; // Default: Pending Trade
      const isToday = currentDate.toDateString() === today.toDateString();
      const isFuture = currentDate > today;
      
      if (hasTraded && actualProfit !== undefined) {
        status = 'completed';
      } else if (isToday && activeSignal) {
        status = 'active'; // Trade Now
      } else if (isFuture) {
        status = 'future';
      }
      
      days.push({
        date: new Date(currentDate),
        dateStr: currentDate.toLocaleDateString('en-US', { 
          weekday: 'short', 
          month: 'short', 
          day: 'numeric' 
        }),
        dateKey: dateKey,
        balanceBefore: runningBalance,
        lotSize: lotSize,
        targetProfit: targetProfit,
        actualProfit: actualProfit,
        status: status,
        isToday: isToday,
      });
      
      // Add actual profit if completed, otherwise target
      if (hasTraded && actualProfit !== undefined) {
        runningBalance += actualProfit;
      } else {
        runningBalance += targetProfit;
      }
    }
    
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  return days;
};

// Generate monthly projection data for accordion (up to 5 years = 60 months)
const generateMonthlyProjection = (accountBalance, tradeLogs = {}) => {
  const months = [];
  let balance = accountBalance || 0;
  const today = new Date();
  
  for (let monthOffset = 0; monthOffset <= 60; monthOffset++) {
    const monthDate = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
    const monthKey = `${monthDate.getFullYear()}-${String(monthDate.getMonth() + 1).padStart(2, '0')}`;
    
    // Calculate trading days in this month
    let tradingDays = 0;
    let monthBalance = balance;
    const lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
    
    // For current month, only count remaining days
    const isCurrentMonth = monthDate.getFullYear() === today.getFullYear() && 
                          monthDate.getMonth() === today.getMonth();
    
    let currentDate = isCurrentMonth ? new Date(today) : new Date(monthDate);
    
    while (currentDate <= lastDay) {
      if (isTradingDay(currentDate)) {
        tradingDays++;
        const lotSize = monthBalance / 980;
        const dailyProfit = lotSize * 15;
        monthBalance += dailyProfit;
      }
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Include current month (offset 0) in Year 1
    const yearNumber = Math.max(1, Math.ceil((monthOffset + 1) / 12));
    
    months.push({
      monthOffset: monthOffset,
      year: yearNumber,
      monthDate: new Date(monthDate),
      monthKey: monthKey,
      monthName: monthDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
      startBalance: balance,
      endBalance: monthBalance,
      lotSize: monthBalance / 980,
      dailyProfit: (monthBalance / 980) * 15,
      tradingDays: tradingDays,
      isCurrentMonth: isCurrentMonth,
    });
    
    balance = monthBalance;
  }
  
  return months;
};

// Group months by year for accordion
const groupMonthsByYear = (monthlyData) => {
  const years = {};
  monthlyData.forEach(m => {
    const yearKey = m.year;
    if (!years[yearKey]) {
      years[yearKey] = [];
    }
    years[yearKey].push(m);
  });
  return years;
};

// Generate projection for specific periods
const generateProjectionData = (accountBalance, selectedYears = 1) => {
  const projections = [];
  let balance = accountBalance || 0;
  
  const periods = [
    { label: '1 Month', days: 22 },
    { label: '3 Months', days: 66 },
    { label: '6 Months', days: 132 },
  ];
  
  // Add selected years
  const yearDays = selectedYears * 264;
  periods.push({ label: `${selectedYears} Year${selectedYears > 1 ? 's' : ''}`, days: yearDays });
  
  const currentLotSize = balance / 980;
  const currentDailyProfit = currentLotSize * 15;
  
  projections.push({
    period: 'Today',
    balance: balance,
    lotSize: currentLotSize,
    dailyProfit: currentDailyProfit,
  });
  
  let runningBalance = balance;
  let lastDays = 0;
  
  for (const period of periods) {
    for (let day = lastDays; day < period.days; day++) {
      const lotSize = runningBalance / 980;
      const dailyProfit = lotSize * 15;
      runningBalance += dailyProfit;
    }
    lastDays = period.days;
    
    const lotSize = runningBalance / 980;
    const dailyProfit = lotSize * 15;
    
    projections.push({
      period: period.label,
      balance: runningBalance,
      lotSize: lotSize,
      dailyProfit: dailyProfit,
    });
  }
  
  return projections;
};

export const ProfitTrackerPage = () => {
  const { 
    user, 
    simulatedView, 
    getSimulatedAccountValue, 
    getSimulatedLotSize, 
    getSimulatedTotalDeposits,
    getSimulatedTotalProfit,
    getSimulatedMemberName 
  } = useAuth();
  const [summary, setSummary] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [withdrawals, setWithdrawals] = useState([]);
  const [tradeLogs, setTradeLogs] = useState({});
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeSignal, setActiveSignal] = useState(null);
  
  // Simulation values
  const simulatedAccountValue = getSimulatedAccountValue();
  const simulatedLotSize = getSimulatedLotSize();
  const simulatedTotalDeposits = getSimulatedTotalDeposits();
  const simulatedTotalProfit = getSimulatedTotalProfit();
  const simulatedMemberName = getSimulatedMemberName();
  
  // Effective values - use simulated if in simulation mode
  const effectiveAccountValue = simulatedAccountValue !== null 
    ? simulatedAccountValue 
    : (summary?.account_value || 0);
  const effectiveLotSize = simulatedLotSize !== null 
    ? truncateTo2Decimals(simulatedLotSize) 
    : truncateTo2Decimals(effectiveAccountValue / 980);
  const effectiveTotalDeposits = simulatedTotalDeposits !== null
    ? simulatedTotalDeposits
    : (summary?.total_deposits || 0);
  const effectiveTotalProfit = simulatedTotalProfit !== null
    ? simulatedTotalProfit
    : (summary?.total_actual_profit || 0);
  
  // Dialog states
  const [depositDialogOpen, setDepositDialogOpen] = useState(false);
  const [depositStep, setDepositStep] = useState('input');
  const [withdrawalDialogOpen, setWithdrawalDialogOpen] = useState(false);
  const [withdrawalStep, setWithdrawalStep] = useState('input');
  const [initialBalanceDialogOpen, setInitialBalanceDialogOpen] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetStep, setResetStep] = useState('confirm');
  const [depositRecordsOpen, setDepositRecordsOpen] = useState(false);
  const [withdrawalRecordsOpen, setWithdrawalRecordsOpen] = useState(false);
  const [commissionRecordsOpen, setCommissionRecordsOpen] = useState(false);
  const [dailyProjectionOpen, setDailyProjectionOpen] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(null);
  
  // Commission Dialog states
  const [commissionDialogOpen, setCommissionDialogOpen] = useState(false);
  const [commissionStep, setCommissionStep] = useState('input');
  const [commissionAmount, setCommissionAmount] = useState('');
  const [commissionTradersCount, setCommissionTradersCount] = useState('');
  const [commissionNotes, setCommissionNotes] = useState('');
  const [commissions, setCommissions] = useState([]);
  
  // Dream Daily Profit Dialog states
  const [dreamProfitDialogOpen, setDreamProfitDialogOpen] = useState(false);
  const [dreamDailyProfit, setDreamDailyProfit] = useState('');
  
  // Form states
  const [depositAmount, setDepositAmount] = useState('');
  const [depositNotes, setDepositNotes] = useState('');
  const [depositSimulation, setDepositSimulation] = useState(null);
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [withdrawalNotes, setWithdrawalNotes] = useState('');
  const [withdrawalResult, setWithdrawalResult] = useState(null);
  const [selectedCurrency, setSelectedCurrency] = useState('PHP');
  const [initialBalance, setInitialBalance] = useState('');
  const [isFirstTime, setIsFirstTime] = useState(false);
  
  // Reset form states
  const [newAccountValue, setNewAccountValue] = useState('');
  const [resetReason, setResetReason] = useState('');
  const [resetPassword, setResetPassword] = useState('');
  
  // Check if user is a licensee (hide simulation/record buttons)
  const isLicensee = simulatedView?.license_type || user?.license_type;
  
  // Projection states
  const [selectedYears, setSelectedYears] = useState(1);
  const [projectionView, setProjectionView] = useState('summary');
  
  const userTimezone = user?.timezone || 'Asia/Manila';

  useEffect(() => {
    loadData();
  }, [simulatedView]);

  const loadData = async () => {
    try {
      // For demo/role-based simulation (no memberId), use simulated values
      const isDemoSimulation = simulatedView && !simulatedView.memberId;
      const isSpecificMemberSimulation = simulatedView && simulatedView.memberId;
      
      if (isDemoSimulation) {
        // Use demo values for role-based simulation
        setSummary({
          account_value: simulatedView.accountValue || 5000,
          total_deposits: simulatedView.totalDeposits || 5000,
          total_profit: simulatedView.totalProfit || 0,
          current_lot_size: simulatedView.lotSize || 0.05
        });
        setDeposits([{
          id: 'demo-deposit',
          amount: simulatedView.totalDeposits || 5000,
          type: 'initial',
          notes: 'Demo initial balance',
          created_at: new Date().toISOString()
        }]);
        setWithdrawals([]);
        setTradeLogs({});
        setIsFirstTime(false);
        
        // Still load rates and signals
        const [ratesRes, signalRes] = await Promise.all([
          currencyAPI.getRates('USDT'),
          api.get('/trade/active-signal').catch(() => ({ data: null })),
        ]);
        setRates(ratesRes.data.rates || {});
        if (signalRes.data?.signal) {
          setActiveSignal(signalRes.data.signal);
        }
        setLoading(false);
        return;
      }
      
      if (isSpecificMemberSimulation) {
        // For specific member simulation, fetch their data from API
        // The API returns license.current_amount for licensees
        const [memberRes, ratesRes, signalRes] = await Promise.all([
          adminAPI.getMemberDetails(simulatedView.memberId),
          currencyAPI.getRates('USDT'),
          api.get('/trade/active-signal').catch(() => ({ data: null })),
        ]);
        
        const stats = memberRes.data.stats || {};
        setSummary({
          account_value: stats.account_value || 0,  // Authoritative value from license.current_amount
          total_deposits: stats.total_deposits || 0,
          total_profit: stats.total_profit || 0,
          current_lot_size: memberRes.data.user?.lot_size || 0.01
        });
        setDeposits(memberRes.data.recent_deposits || []);
        setWithdrawals([]);
        setTradeLogs({});
        setIsFirstTime(false);
        setRates(ratesRes.data.rates || {});
        if (signalRes.data?.signal) {
          setActiveSignal(signalRes.data.signal);
        }
        setLoading(false);
        return;
      }
      
      const [summaryRes, depositsRes, ratesRes, withdrawalsRes, signalRes, tradeLogsRes, commissionsRes] = await Promise.all([
        profitAPI.getSummary(),
        profitAPI.getDeposits(),
        currencyAPI.getRates('USDT'),
        api.get('/profit/withdrawals').catch(() => ({ data: [] })),
        api.get('/trade/active-signal').catch(() => ({ data: null })),
        api.get('/trade/logs').catch(() => ({ data: [] })),
        api.get('/profit/commissions').catch(() => ({ data: [] })),
      ]);
      setSummary(summaryRes.data);
      
      // Separate deposits and withdrawals
      const allDeposits = depositsRes.data || [];
      const onlyDeposits = allDeposits.filter(d => d.amount >= 0);
      setDeposits(onlyDeposits);
      
      // Get withdrawals from dedicated endpoint or filter
      const withdrawalData = withdrawalsRes.data || allDeposits.filter(d => d.amount < 0 || d.is_withdrawal);
      setWithdrawals(withdrawalData);
      
      // Set commissions
      setCommissions(commissionsRes.data || []);
      
      setRates(ratesRes.data.rates || {});
      
      // Set active signal
      if (signalRes.data?.signal) {
        setActiveSignal(signalRes.data.signal);
      } else if (signalRes.data && !signalRes.data.message) {
        setActiveSignal(signalRes.data);
      }
      
      // Process trade logs into a date-keyed object
      const logs = tradeLogsRes.data || [];
      const logsMap = {};
      logs.forEach(log => {
        const dateKey = new Date(log.created_at).toISOString().split('T')[0];
        logsMap[dateKey] = {
          actual_profit: log.actual_profit,
          has_traded: true,
          ...log
        };
      });
      setTradeLogs(logsMap);
      
      if (allDeposits.length === 0) {
        setIsFirstTime(true);
        setInitialBalanceDialogOpen(true);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Open daily projection for a month
  const handleOpenDailyProjection = (month) => {
    setSelectedMonth(month);
    setDailyProjectionOpen(true);
  };

  // Get daily projection data for selected month
  const getDailyProjectionForSelectedMonth = useMemo(() => {
    if (!selectedMonth) return [];
    return generateDailyProjectionForMonth(
      selectedMonth.startBalance,
      selectedMonth.monthDate,
      tradeLogs,
      activeSignal
    );
  }, [selectedMonth, tradeLogs, activeSignal]);

  // Deposit flow handlers
  const handleSimulateDeposit = () => {
    if (!depositAmount || parseFloat(depositAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    
    const amount = parseFloat(depositAmount);
    const fees = calculateDepositFees(amount);
    
    setDepositSimulation(fees);
    setDepositStep('simulate');
  };

  const handleConfirmDeposit = async () => {
    try {
      await profitAPI.createDeposit({
        amount: depositSimulation.receiveAmount,
        currency: 'USDT',
        notes: depositNotes || `Deposit from Binance (${formatMoney(depositSimulation.binanceAmount)} - 1% fee)`,
      });
      toast.success('Deposit confirmed and added to your Merin account!');
      resetDepositDialog();
      loadData();
    } catch (error) {
      toast.error('Failed to record deposit');
    }
  };

  const resetDepositDialog = () => {
    setDepositDialogOpen(false);
    setDepositStep('input');
    setDepositAmount('');
    setDepositNotes('');
    setDepositSimulation(null);
  };

  // Withdrawal flow handlers
  const handleSimulateWithdrawal = () => {
    if (!withdrawalAmount || parseFloat(withdrawalAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    const amount = parseFloat(withdrawalAmount);
    if (amount > (summary?.account_value || 0)) {
      toast.error('Insufficient balance');
      return;
    }

    const fees = calculateWithdrawalFees(amount);
    const estimatedDate = addBusinessDays(new Date(), 2);
    
    setWithdrawalResult({
      ...fees,
      currentBalance: summary?.account_value || 0,
      balanceAfter: (summary?.account_value || 0) - amount,
      estimatedReceiveDate: estimatedDate.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timeZone: userTimezone,
      }),
      estimatedDateISO: estimatedDate.toISOString(),
    });
    setWithdrawalStep('result');
  };

  const handleCompleteWithdrawal = async () => {
    try {
      await api.post('/profit/withdrawal', {
        amount: parseFloat(withdrawalAmount),
        notes: withdrawalNotes || '',
      });
      toast.success('Withdrawal initiated! Your balance has been updated. Check your Binance account in 1-2 business days.');
      resetWithdrawalDialog();
      loadData();
    } catch (error) {
      toast.error('Failed to process withdrawal');
    }
  };

  const resetWithdrawalDialog = () => {
    setWithdrawalDialogOpen(false);
    setWithdrawalStep('input');
    setWithdrawalAmount('');
    setWithdrawalNotes('');
    setWithdrawalResult(null);
  };

  // Confirm receipt of withdrawal
  const handleConfirmReceipt = async (withdrawalId) => {
    try {
      const confirmedAt = new Date().toLocaleString('en-US', {
        timeZone: userTimezone,
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
      
      await api.put(`/profit/withdrawals/${withdrawalId}/confirm`, {
        confirmed_at: confirmedAt,
      });
      toast.success('Receipt confirmed!');
      loadData();
    } catch (error) {
      toast.error('Failed to confirm receipt');
    }
  };

  // Initial balance handler
  const handleInitialBalance = async () => {
    if (!initialBalance || parseFloat(initialBalance) < 0) {
      toast.error('Please enter a valid initial balance');
      return;
    }

    try {
      // Limit to 2 decimal places
      const amount = truncateTo2Decimals(parseFloat(initialBalance));
      if (amount > 0) {
        await profitAPI.createDeposit({
          amount: amount,
          currency: 'USDT',
          notes: 'Initial Merin account balance',
        });
      }
      toast.success('Welcome to Profit Tracker! Your journey starts now!');
      setInitialBalanceDialogOpen(false);
      setInitialBalance('');
      setIsFirstTime(false);
      loadData();
    } catch (error) {
      toast.error('Failed to set initial balance');
    }
  };

  // Reset handlers
  const handleResetConfirm = () => {
    setResetStep('newBalance');
  };

  const handleResetNewBalance = () => {
    if (!newAccountValue || parseFloat(newAccountValue) < 0) {
      toast.error('Please enter a valid account value');
      return;
    }
    if (!resetReason.trim()) {
      toast.error('Please provide a reason for the reset');
      return;
    }
    setResetStep('password');
  };

  const handleResetWithPassword = async () => {
    if (!resetPassword) {
      toast.error('Please enter your password');
      return;
    }

    try {
      // Verify password first
      const verifyRes = await api.post('/auth/verify-password', {
        password: resetPassword,
      });
      
      if (!verifyRes.data.valid) {
        toast.error('Invalid password');
        return;
      }
      
      // Reset tracker
      await api.delete('/profit/reset');
      
      // Add new initial balance if > 0 (limited to 2 decimals)
      const amount = truncateTo2Decimals(parseFloat(newAccountValue));
      if (amount > 0) {
        await profitAPI.createDeposit({
          amount: amount,
          currency: 'USDT',
          notes: `Reset: ${resetReason}`,
        });
      }
      
      toast.success('Profit tracker has been reset with new balance!');
      resetResetDialog();
      loadData();
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Invalid password. Please try again.');
      } else {
        toast.error('Failed to reset tracker');
      }
    }
  };

  const resetResetDialog = () => {
    setResetDialogOpen(false);
    setResetStep('confirm');
    setNewAccountValue('');
    setResetReason('');
    setResetPassword('');
  };

  // Commission handlers
  const handleSimulateCommission = async () => {
    if (!commissionAmount || parseFloat(commissionAmount) <= 0) {
      toast.error('Please enter a valid commission amount');
      return;
    }
    if (!commissionTradersCount || parseInt(commissionTradersCount) <= 0) {
      toast.error('Please enter the number of traders');
      return;
    }
    
    try {
      await api.post('/profit/commission', {
        amount: parseFloat(commissionAmount),
        traders_count: parseInt(commissionTradersCount),
        notes: commissionNotes || `Commission from ${commissionTradersCount} referral trades`
      });
      toast.success('Commission recorded successfully!');
      resetCommissionDialog();
      loadData();
    } catch (error) {
      toast.error('Failed to record commission');
    }
  };

  const resetCommissionDialog = () => {
    setCommissionDialogOpen(false);
    setCommissionStep('input');
    setCommissionAmount('');
    setCommissionTradersCount('');
    setCommissionNotes('');
  };

  // Dream Daily Profit Calculator
  const calculateRequiredBalance = (targetDailyProfit) => {
    if (!targetDailyProfit || parseFloat(targetDailyProfit) <= 0) return 0;
    // Formula: Target Daily Profit = (Balance / 980) * 15
    // So: Balance = Target Daily Profit * 980 / 15
    const requiredBalance = (parseFloat(targetDailyProfit) * 980) / 15;
    return requiredBalance;
  };

  const dreamProfitRequired = calculateRequiredBalance(dreamDailyProfit);
  const dreamProfitAmountToAdd = Math.max(0, dreamProfitRequired - effectiveAccountValue);

  const convertAmount = (amount, toCurrency) => {
    const rate = rates[toCurrency] || 1;
    return amount * rate;
  };

  // Projection data - use effective account value for simulations
  const projectionData = useMemo(() => 
    generateProjectionData(effectiveAccountValue, selectedYears),
    [effectiveAccountValue, selectedYears]
  );
  
  const monthlyProjection = useMemo(() => 
    generateMonthlyProjection(effectiveAccountValue, tradeLogs),
    [effectiveAccountValue, tradeLogs]
  );
  
  const yearlyGroupedProjection = useMemo(() => 
    groupMonthsByYear(monthlyProjection),
    [monthlyProjection]
  );

  // Chart data
  const projectionChartData = projectionData.slice(1).map(p => ({
    name: p.period,
    balance: p.balance,
  }));

  // Currency symbols
  const getCurrencySymbol = (currency) => {
    switch(currency) {
      case 'PHP': return '₱';
      case 'EUR': return '€';
      case 'GBP': return '£';
      default: return '$';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Simulation Banner */}
      {simulatedView && simulatedMemberName && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30" data-testid="simulation-banner">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Eye className="w-5 h-5 text-amber-400" />
              <div>
                <p className="text-amber-400 font-medium">Simulating: {simulatedMemberName}</p>
                <p className="text-xs text-amber-400/70">Account Value: {formatLargeNumber(effectiveAccountValue)} • LOT Size: {effectiveLotSize.toFixed(2)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trading Signal Banner */}
      {activeSignal && (
        <Card className="glass-highlight border-blue-500/30 bg-gradient-to-r from-blue-500/10 to-cyan-500/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Radio className="w-5 h-5 text-blue-400 animate-pulse" />
                <div>
                  <p className="text-xs text-zinc-400">Today's Trading Signal</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-white font-bold">{activeSignal.product}</span>
                    <span className={`px-3 py-1 rounded-lg font-bold text-sm ${activeSignal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                      {activeSignal.direction}
                    </span>
                    <span className="text-zinc-400">at</span>
                    <span className="font-mono text-blue-400 font-bold">{activeSignal.trade_time}</span>
                    <span className="text-zinc-500 text-sm">({activeSignal.trade_timezone || 'Asia/Manila'})</span>
                  </div>
                </div>
              </div>
              <Button 
                className="btn-primary gap-2"
                onClick={() => window.open('https://www.meringlobaltrading.com/', '_blank')}
                data-testid="trade-now-button"
              >
                Trade Now <ExternalLink className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-card" data-testid="account-value-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Account Value (USDT)</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">
                  {formatLargeNumber(effectiveAccountValue)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <Wallet className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="total-deposits-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-zinc-400">Total Deposits</p>
                  <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
                    <SelectTrigger className="w-20 h-6 text-xs bg-zinc-900/50 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="PHP">PHP</SelectItem>
                      <SelectItem value="EUR">EUR</SelectItem>
                      <SelectItem value="GBP">GBP</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <p className="text-3xl font-bold font-mono text-white mt-2">
                  {getCurrencySymbol(selectedCurrency)}{formatNumber(convertAmount(effectiveTotalDeposits, selectedCurrency))}
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  ≈ {formatMoney(effectiveTotalDeposits)} USDT
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center ml-3">
                <ArrowDownToLine className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="total-profit-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Profit</p>
                <p className={`text-3xl font-bold font-mono mt-2 ${effectiveTotalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {effectiveTotalProfit >= 0 ? '+' : ''}{formatLargeNumber(effectiveTotalProfit)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="current-lot-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Current LOT Size</p>
                <p className="text-3xl font-bold font-mono text-purple-400 mt-2">
                  {effectiveLotSize.toFixed(2)}
                </p>
                <p className="text-xs text-zinc-500 mt-1">Balance ÷ 980</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                <Calculator className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions - Hidden for licensees who have their own Deposit/Withdrawal page */}
      {!isLicensee && (
      <div className="flex flex-wrap items-center gap-4">
        {/* Left side - Simulate buttons */}
        <div className="flex flex-wrap gap-4 flex-1">
        {/* Simulate Deposit Dialog */}
        <Dialog open={depositDialogOpen} onOpenChange={(open) => { if (!open) resetDepositDialog(); else setDepositDialogOpen(true); }}>
          <DialogTrigger asChild>
            <Button className="btn-primary gap-2" data-testid="simulate-deposit-button">
              <Plus className="w-4 h-4" /> Simulate Deposit
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white">
                {depositStep === 'input' && 'Simulate Deposit'}
                {depositStep === 'simulate' && 'Deposit Calculation'}
                {depositStep === 'confirm' && 'Confirm Deposit'}
              </DialogTitle>
            </DialogHeader>
            
            {depositStep === 'input' && (
              <div className="space-y-4 mt-4">
                <div>
                  <Label className="text-zinc-300">Binance USDT Amount</Label>
                  <div className="relative mt-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                    <Input
                      type="number"
                      value={depositAmount}
                      onChange={(e) => setDepositAmount(e.target.value)}
                      placeholder="0.00"
                      className="input-dark pl-7"
                      data-testid="deposit-amount-input"
                    />
                  </div>
                  <p className="text-xs text-zinc-500 mt-1">Amount you're sending from Binance</p>
                </div>
                <div>
                  <Label className="text-zinc-300">Notes (optional)</Label>
                  <Input
                    value={depositNotes}
                    onChange={(e) => setDepositNotes(e.target.value)}
                    placeholder="Add notes..."
                    className="input-dark mt-1"
                  />
                </div>
                <Button onClick={handleSimulateDeposit} className="w-full btn-primary" data-testid="calculate-deposit-button">
                  <Calculator className="w-4 h-4 mr-2" /> Calculate Deposit
                </Button>
              </div>
            )}

            {depositStep === 'simulate' && depositSimulation && (
              <div className="space-y-4 mt-4">
                <div className="space-y-3 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Binance USDT</span>
                    <span className="font-mono text-white">{formatMoney(depositSimulation.binanceAmount)}</span>
                  </div>
                  <div className="flex justify-between text-amber-400">
                    <span>Deposit Fee (1%)</span>
                    <span className="font-mono">-{formatMoney(depositSimulation.depositFee)}</span>
                  </div>
                  <div className="flex justify-between text-amber-400">
                    <span>Binance Fee</span>
                    <span className="font-mono">-$1.00</span>
                  </div>
                  <div className="border-t border-zinc-700 pt-3 flex justify-between">
                    <span className="text-zinc-300 font-medium">Receive Amount</span>
                    <span className="font-mono font-bold text-emerald-400">{formatMoney(depositSimulation.receiveAmount)}</span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setDepositStep('input')}>
                    Back
                  </Button>
                  <Button onClick={() => setDepositStep('confirm')} className="flex-1 btn-primary" data-testid="proceed-deposit-button">
                    Deposit Now
                  </Button>
                </div>
              </div>
            )}

            {depositStep === 'confirm' && (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-blue-400 mt-0.5" />
                    <div>
                      <p className="text-blue-400 font-medium">Confirm Your Action</p>
                      <p className="text-sm text-zinc-400 mt-1">
                        By proceeding, you're confirming that you're adding <span className="text-white font-mono">{formatMoney(depositSimulation?.receiveAmount)}</span> to your Merin Account.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setDepositStep('simulate')}>
                    No, I'm just thinking
                  </Button>
                  <Button onClick={handleConfirmDeposit} className="flex-1 btn-primary" data-testid="confirm-deposit-button">
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Yes, I confirm
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Withdrawal Dialog */}
        <Dialog open={withdrawalDialogOpen} onOpenChange={(open) => { if (!open) resetWithdrawalDialog(); else setWithdrawalDialogOpen(true); }}>
          <DialogTrigger asChild>
            <Button className="btn-secondary gap-2" data-testid="simulate-withdrawal-button">
              <ArrowUpFromLine className="w-4 h-4" /> Simulate Withdrawal
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white">
                {withdrawalStep === 'input' && 'Simulate Withdrawal'}
                {withdrawalStep === 'result' && 'Withdrawal Calculation'}
                {withdrawalStep === 'confirm' && 'Confirm Withdrawal'}
              </DialogTitle>
            </DialogHeader>

            {withdrawalStep === 'input' && (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  <p className="text-sm text-zinc-400">Current Merin Balance</p>
                  <p className="text-2xl font-bold font-mono text-white">{formatLargeNumber(summary?.account_value || 0)}</p>
                </div>
                <div>
                  <Label className="text-zinc-300">Withdrawal Amount (USDT)</Label>
                  <div className="relative mt-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                    <Input
                      type="number"
                      value={withdrawalAmount}
                      onChange={(e) => setWithdrawalAmount(e.target.value)}
                      placeholder="0.00"
                      className="input-dark pl-7"
                      data-testid="withdrawal-amount-input"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-300">Notes (optional)</Label>
                  <Input
                    value={withdrawalNotes}
                    onChange={(e) => setWithdrawalNotes(e.target.value)}
                    placeholder="Withdrawal reason..."
                    className="input-dark mt-1"
                  />
                </div>
                <Button onClick={handleSimulateWithdrawal} className="w-full btn-secondary" data-testid="calculate-withdrawal-button">
                  <Calculator className="w-4 h-4 mr-2" /> Calculate Fees
                </Button>
              </div>
            )}

            {withdrawalStep === 'result' && withdrawalResult && (
              <div className="space-y-4 mt-4">
                <div className="space-y-3 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Gross Amount</span>
                    <span className="font-mono text-white">{formatMoney(withdrawalResult.grossAmount)}</span>
                  </div>
                  <div className="flex justify-between text-amber-400">
                    <span>Merin Fee (3%)</span>
                    <span className="font-mono">-{formatMoney(withdrawalResult.merinFee)}</span>
                  </div>
                  <div className="border-t border-zinc-700 pt-3 flex justify-between">
                    <span className="text-zinc-300 font-medium">Net Amount (to Binance)</span>
                    <span className="font-mono font-bold text-emerald-400">{formatMoney(withdrawalResult.netAmount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Merin Balance After</span>
                    <span className="font-mono text-white">{formatLargeNumber(withdrawalResult.balanceAfter)}</span>
                  </div>
                </div>
                
                <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <div className="flex items-center gap-2 text-blue-400 mb-1">
                    <Clock className="w-4 h-4" />
                    <span className="text-sm font-medium">Processing Time</span>
                  </div>
                  <p className="text-xs text-zinc-400">1-2 business days</p>
                  <p className="text-sm text-white mt-1">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    Estimated: <span className="font-medium">{withdrawalResult.estimatedReceiveDate}</span>
                  </p>
                </div>

                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setWithdrawalStep('input')}>
                    Back
                  </Button>
                  <Button onClick={() => setWithdrawalStep('confirm')} className="flex-1 btn-primary" data-testid="complete-withdrawal-button">
                    Complete Withdrawal
                  </Button>
                </div>
              </div>
            )}

            {withdrawalStep === 'confirm' && (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
                    <div>
                      <p className="text-amber-400 font-medium">Confirm Withdrawal</p>
                      <p className="text-sm text-zinc-400 mt-1">
                        By proceeding, you're confirming that you're withdrawing <span className="text-white font-mono">{formatMoney(parseFloat(withdrawalAmount))}</span> from your Merin Account.
                      </p>
                      <p className="text-sm text-zinc-400 mt-2">
                        You will receive <span className="text-emerald-400 font-mono">{formatMoney(withdrawalResult?.netAmount)}</span> in your Binance account.
                      </p>
                      <p className="text-sm text-amber-400 mt-2 font-medium">
                        Your Merin balance will be updated immediately.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setWithdrawalStep('result')}>
                    No, go back
                  </Button>
                  <Button onClick={handleCompleteWithdrawal} className="flex-1 bg-amber-500 hover:bg-amber-600 text-black" data-testid="confirm-withdrawal-button">
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Yes, withdraw now
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Commission Dialog */}
        <Dialog open={commissionDialogOpen} onOpenChange={(open) => { if (!open) resetCommissionDialog(); else setCommissionDialogOpen(true); }}>
          <DialogTrigger asChild>
            <Button className="btn-secondary gap-2" data-testid="simulate-commission-button">
              <Award className="w-4 h-4" /> Simulate Commission
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <Award className="w-5 h-5 text-purple-400" /> Simulate Commission
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              <p className="text-sm text-zinc-400">
                Record commission earnings from your referrals' trades.
              </p>
              <div>
                <Label className="text-zinc-300">Commission Amount (USDT)</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={commissionAmount}
                    onChange={(e) => setCommissionAmount(e.target.value)}
                    placeholder="0.00"
                    className="input-dark pl-7"
                    data-testid="commission-amount-input"
                  />
                </div>
              </div>
              <div>
                <Label className="text-zinc-300">Number of Traders</Label>
                <Input
                  type="number"
                  value={commissionTradersCount}
                  onChange={(e) => setCommissionTradersCount(e.target.value)}
                  placeholder="How many referrals traded?"
                  className="input-dark mt-1"
                  data-testid="commission-traders-input"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Notes (optional)</Label>
                <Input
                  value={commissionNotes}
                  onChange={(e) => setCommissionNotes(e.target.value)}
                  placeholder="Add notes..."
                  className="input-dark mt-1"
                />
              </div>
              <Button onClick={handleSimulateCommission} className="w-full btn-primary" data-testid="confirm-commission-button">
                <Award className="w-4 h-4 mr-2" /> Record Commission
              </Button>
            </div>
          </DialogContent>
        </Dialog>
        </div>

        {/* Right side - Records and Reset Buttons */}
        <div className="flex flex-wrap gap-2 ml-auto">
          <Button variant="outline" className="btn-secondary gap-2" onClick={() => setDepositRecordsOpen(true)} data-testid="view-deposits-button">
            <FileText className="w-4 h-4" /> Deposit Records
          </Button>
          
          <Button variant="outline" className="btn-secondary gap-2" onClick={() => setWithdrawalRecordsOpen(true)} data-testid="view-withdrawals-button">
            <Receipt className="w-4 h-4" /> Withdrawal Records
          </Button>
          
          <Button variant="outline" className="btn-secondary gap-2" onClick={() => setCommissionRecordsOpen(true)} data-testid="view-commissions-button">
            <Award className="w-4 h-4" /> Commission Records
          </Button>

          {/* Reset Button */}
          <Dialog open={resetDialogOpen} onOpenChange={(open) => { if (!open) resetResetDialog(); else setResetDialogOpen(true); }}>
            <DialogTrigger asChild>
              <Button variant="outline" className="btn-secondary gap-2 text-amber-400 hover:text-amber-300" data-testid="reset-tracker-button">
                <RotateCcw className="w-4 h-4" /> Reset Tracker
              </Button>
            </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                {resetStep === 'confirm' && <><RotateCcw className="w-5 h-5 text-red-400" /> Reset Profit Tracker</>}
                {resetStep === 'newBalance' && <><Wallet className="w-5 h-5 text-blue-400" /> Set New Account Value</>}
                {resetStep === 'password' && <><Lock className="w-5 h-5 text-amber-400" /> Security Verification</>}
              </DialogTitle>
            </DialogHeader>
            
            {resetStep === 'confirm' && (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                  <p className="font-medium mb-2">Warning: This action cannot be undone!</p>
                  <p className="text-sm">Resetting will delete all your:</p>
                  <ul className="list-disc list-inside text-sm mt-2">
                    <li>Deposit records</li>
                    <li>Withdrawal records</li>
                    <li>Trade logs</li>
                    <li>Profit calculations</li>
                  </ul>
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setResetDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button className="flex-1 bg-red-500 hover:bg-red-600 text-white" onClick={handleResetConfirm}>
                    Continue
                  </Button>
                </div>
              </div>
            )}

            {resetStep === 'newBalance' && (
              <div className="space-y-4 mt-4">
                <p className="text-zinc-400 text-sm">Enter your new account value and the reason for this reset.</p>
                <div>
                  <Label className="text-zinc-300">New Account Value (USDT)</Label>
                  <div className="relative mt-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                    <Input
                      type="number"
                      value={newAccountValue}
                      onChange={(e) => setNewAccountValue(e.target.value)}
                      placeholder="0.00"
                      className="input-dark pl-7"
                      data-testid="new-account-value-input"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-300">Reason for Reset</Label>
                  <Input
                    value={resetReason}
                    onChange={(e) => setResetReason(e.target.value)}
                    placeholder="e.g., Starting fresh, Account correction..."
                    className="input-dark mt-1"
                    data-testid="reset-reason-input"
                  />
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setResetStep('confirm')}>
                    Back
                  </Button>
                  <Button className="flex-1 btn-primary" onClick={handleResetNewBalance}>
                    Continue
                  </Button>
                </div>
              </div>
            )}

            {resetStep === 'password' && (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                  <div className="flex items-start gap-3">
                    <Lock className="w-5 h-5 text-amber-400 mt-0.5" />
                    <div>
                      <p className="text-amber-400 font-medium">Security Verification Required</p>
                      <p className="text-sm text-zinc-400 mt-1">
                        Please enter your password to confirm this action.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-zinc-900/50">
                  <p className="text-xs text-zinc-500">New Balance</p>
                  <p className="font-mono text-white">{formatMoney(truncateTo2Decimals(parseFloat(newAccountValue) || 0))}</p>
                  <p className="text-xs text-zinc-500 mt-2">Reason</p>
                  <p className="text-zinc-300 text-sm">{resetReason}</p>
                </div>
                <div>
                  <Label className="text-zinc-300">Password</Label>
                  <Input
                    type="password"
                    value={resetPassword}
                    onChange={(e) => setResetPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="input-dark mt-1"
                    data-testid="reset-password-input"
                  />
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setResetStep('newBalance')}>
                    Back
                  </Button>
                  <Button className="flex-1 bg-red-500 hover:bg-red-600 text-white" onClick={handleResetWithPassword} data-testid="confirm-reset-button">
                    <Lock className="w-4 h-4 mr-2" /> Confirm Reset
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
        </div>
      </div>
      )}

      {/* Initial Balance Setup Dialog */}
      <Dialog open={initialBalanceDialogOpen} onOpenChange={setInitialBalanceDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Rocket className="w-5 h-5 text-blue-400" /> Welcome to Profit Tracker!
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-zinc-400">
              Let's get started by setting your current Merin Trading Platform balance. 
              This is the amount you currently have in your trading account.
            </p>
            <div>
              <Label className="text-zinc-300">Your Current Merin Balance (USDT)</Label>
              <div className="relative mt-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                <Input
                  type="number"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(e.target.value)}
                  placeholder="0.00"
                  className="input-dark pl-7"
                  data-testid="initial-balance-input"
                />
              </div>
              <p className="text-xs text-zinc-500 mt-1">Enter 0 if you haven't deposited yet</p>
            </div>
            <Button onClick={handleInitialBalance} className="w-full btn-primary" data-testid="set-initial-balance-button">
              <Rocket className="w-4 h-4 mr-2" /> Start Tracking My Profits
            </Button>
            <Button variant="ghost" className="w-full text-zinc-500" onClick={() => setInitialBalanceDialogOpen(false)}>
              Skip for now
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Deposit Records Dialog */}
      <Dialog open={depositRecordsOpen} onOpenChange={setDepositRecordsOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-cyan-400" /> Deposit Records
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4 max-h-[400px] overflow-y-auto">
            {deposits.length > 0 ? (
              <table className="w-full data-table text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Currency</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {deposits.map((deposit) => (
                    <tr key={deposit.id}>
                      <td className="font-mono">{new Date(deposit.created_at).toLocaleDateString()}</td>
                      <td className="font-mono text-emerald-400">+{formatMoney(deposit.amount)}</td>
                      <td>{deposit.currency}</td>
                      <td className="text-zinc-500 max-w-[200px] truncate">{deposit.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                No deposits recorded yet.
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Withdrawal Records Dialog */}
      <Dialog open={withdrawalRecordsOpen} onOpenChange={setWithdrawalRecordsOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-3xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Receipt className="w-5 h-5 text-amber-400" /> Withdrawal Records
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4 max-h-[400px] overflow-y-auto">
            {withdrawals.length > 0 ? (
              <table className="w-full data-table text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr>
                    <th>Date Initiated</th>
                    <th>Amount (USDT)</th>
                    <th>Final Binance (USDT)</th>
                    <th>Est. Arrival</th>
                    <th>Notes</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {withdrawals.map((w) => (
                    <tr key={w.id}>
                      <td className="font-mono">{new Date(w.created_at).toLocaleDateString()}</td>
                      <td className="font-mono text-red-400">{formatMoney(Math.abs(w.gross_amount || w.amount))}</td>
                      <td className="font-mono text-emerald-400">{formatMoney(w.net_amount || (Math.abs(w.amount) * 0.97 - 1))}</td>
                      <td className="font-mono text-zinc-400">
                        {w.estimated_arrival || addBusinessDays(new Date(w.created_at), 2).toLocaleDateString()}
                      </td>
                      <td className="text-zinc-500 max-w-[150px] truncate">{w.notes || '-'}</td>
                      <td>
                        {w.confirmed_at ? (
                          <span className="text-emerald-400 text-xs flex items-center gap-1">
                            <Check className="w-3 h-3" /> {w.confirmed_at}
                          </span>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs h-7 text-blue-400 border-blue-400/30 hover:bg-blue-400/10"
                            onClick={() => handleConfirmReceipt(w.id)}
                            data-testid={`confirm-receipt-${w.id}`}
                          >
                            Confirm Receipt
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                No withdrawals recorded yet.
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Projection Vision Card */}
      <Card className="glass-highlight border-blue-500/30">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-400" /> Projection Vision
          </CardTitle>
          <div className="flex gap-2">
            <Button
              variant={projectionView === 'summary' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setProjectionView('summary')}
              className={projectionView === 'summary' ? 'btn-primary' : 'btn-secondary'}
            >
              Summary
            </Button>
            <Button
              variant={projectionView === 'table' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setProjectionView('table')}
              className={projectionView === 'table' ? 'btn-primary' : 'btn-secondary'}
            >
              <Eye className="w-4 h-4 mr-1" /> Monthly Table
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {projectionView === 'summary' ? (
            <div className="space-y-6">
              {/* Current Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-lg bg-zinc-900/50">
                <div>
                  <p className="text-xs text-zinc-500">Current Balance</p>
                  <p className="font-mono text-lg text-white">{formatLargeNumber(effectiveAccountValue)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">LOT Size</p>
                  <p className="font-mono text-lg text-purple-400">{effectiveLotSize.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Daily Profit (×15)</p>
                  <p className="font-mono text-lg text-emerald-400">{formatMoney(effectiveLotSize * 15)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Formula</p>
                  <p className="text-sm text-zinc-400">Balance ÷ 980 × 15</p>
                </div>
              </div>

              {/* Projection Chart */}
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={projectionChartData}>
                    <defs>
                      <linearGradient id="colorProjection" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                    <XAxis dataKey="name" stroke="#71717A" fontSize={11} />
                    <YAxis 
                      stroke="#71717A" 
                      fontSize={11} 
                      tickFormatter={(v) => {
                        if (v >= 1e12) return `$${(v/1e12).toFixed(1)}T`;
                        if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`;
                        if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
                        if (v >= 1e3) return `$${(v/1e3).toFixed(0)}k`;
                        return `$${v.toFixed(0)}`;
                      }}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                      formatter={(value) => [formatLargeNumber(value), 'Projected Balance']}
                    />
                    <Line type="monotone" dataKey="balance" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Projection Grid - 1mo, 3mo, 6mo, then dropdown for years */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {projectionData.slice(1, 4).map((p, i) => (
                  <div key={p.period} className={`p-4 rounded-lg border ${i === 0 ? 'bg-blue-500/10 border-blue-500/30' : 'bg-zinc-900/50 border-zinc-800'}`}>
                    <p className={`text-xs ${i === 0 ? 'text-blue-400' : 'text-zinc-500'}`}>{p.period}</p>
                    <p className={`font-mono text-lg ${i === 0 ? 'text-blue-400' : 'text-white'} mt-1`}>
                      {formatLargeNumber(p.balance)}
                    </p>
                    <p className="text-xs text-zinc-500 mt-1">
                      LOT: {truncateTo2Decimals(p.lotSize).toFixed(2)} | Daily: {formatLargeNumber(p.dailyProfit)}
                    </p>
                  </div>
                ))}
                
                {/* Year selector card */}
                <div className="p-4 rounded-lg border bg-gradient-to-br from-purple-500/10 to-blue-500/10 border-purple-500/30">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-purple-400">Year Projection</p>
                    <Select value={selectedYears.toString()} onValueChange={(v) => setSelectedYears(parseInt(v))}>
                      <SelectTrigger className="w-20 h-6 text-xs bg-zinc-900/50 border-zinc-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 Year</SelectItem>
                        <SelectItem value="2">2 Years</SelectItem>
                        <SelectItem value="3">3 Years</SelectItem>
                        <SelectItem value="4">4 Years</SelectItem>
                        <SelectItem value="5">5 Years</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <p className="font-mono text-lg text-purple-400 mt-1">
                    {formatLargeNumber(projectionData[4]?.balance || 0)}
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">
                    LOT: {truncateTo2Decimals(projectionData[4]?.lotSize || 0).toFixed(2)} | Daily: {formatLargeNumber(projectionData[4]?.dailyProfit || 0)}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-zinc-400">
                Monthly projection based on compounding (Balance ÷ 980 × 15 per trading day). Weekends excluded.
              </p>
              <div className="max-h-[500px] overflow-y-auto">
                <Accordion type="multiple" className="space-y-2">
                  {Object.entries(yearlyGroupedProjection).map(([year, months]) => (
                    <AccordionItem 
                      key={year} 
                      value={`year-${year}`}
                      className="border border-zinc-800 rounded-lg overflow-hidden"
                    >
                      <AccordionTrigger className="px-4 py-3 bg-zinc-900/50 hover:bg-zinc-900 text-white">
                        <div className="flex items-center justify-between w-full pr-4">
                          <span className="font-medium">Year {year}</span>
                          <span className="font-mono text-emerald-400">
                            {formatLargeNumber(months[months.length - 1]?.endBalance || 0)}
                          </span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="bg-zinc-950/50">
                        <table className="w-full data-table text-sm">
                          <thead>
                            <tr>
                              <th>Month</th>
                              <th>Trading Days</th>
                              <th>Final Balance</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {months.map((m) => (
                              <tr key={m.monthKey} className={m.isCurrentMonth ? 'bg-blue-500/10' : ''}>
                                <td className="font-medium">
                                  {m.monthName}
                                  {m.isCurrentMonth && (
                                    <span className="ml-2 text-xs text-blue-400">(Current)</span>
                                  )}
                                </td>
                                <td className="font-mono text-zinc-400">{m.tradingDays} days</td>
                                <td className="font-mono text-white">{formatLargeNumber(m.endBalance)}</td>
                                <td>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="h-7 text-xs text-blue-400 border-blue-400/30 hover:bg-blue-400/10"
                                    onClick={() => handleOpenDailyProjection(m)}
                                    data-testid={`daily-projection-${m.monthKey}`}
                                  >
                                    <Eye className="w-3 h-3 mr-1" /> Daily View
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Daily Projection Dialog */}
      <Dialog open={dailyProjectionOpen} onOpenChange={setDailyProjectionOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-5xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-400" />
              Daily Projection - {selectedMonth?.monthName}
              {selectedMonth?.isCurrentMonth && (
                <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full ml-2">
                  {getDailyProjectionForSelectedMonth.length} Remaining Days
                </span>
              )}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4 max-h-[60vh] overflow-y-auto">
            {getDailyProjectionForSelectedMonth.length > 0 ? (
              <table className="w-full data-table text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr>
                    <th>Date</th>
                    <th>Balance Before</th>
                    <th>LOT Size</th>
                    <th>Target Profit</th>
                    <th>Actual Profit</th>
                    <th>P/L Diff</th>
                  </tr>
                </thead>
                <tbody>
                  {getDailyProjectionForSelectedMonth.map((day, idx) => {
                    const plDiff = day.status === 'completed' && day.actualProfit !== undefined 
                      ? day.actualProfit - day.targetProfit 
                      : null;
                    
                    return (
                      <tr 
                        key={day.dateKey} 
                        className={day.isToday ? 'bg-blue-500/20 border-l-2 border-l-blue-500' : ''}
                      >
                        <td className="font-medium">
                          {day.dateStr}
                          {day.isToday && (
                            <span className="ml-2 text-xs bg-blue-500 text-white px-1.5 py-0.5 rounded">TODAY</span>
                          )}
                        </td>
                        <td className="font-mono text-white">{formatLargeNumber(day.balanceBefore)}</td>
                        <td className="font-mono text-purple-400">{truncateTo2Decimals(day.lotSize).toFixed(2)}</td>
                        <td className="font-mono text-zinc-400">{formatMoney(day.targetProfit)}</td>
                        <td>
                          {day.status === 'completed' ? (
                            <span className={`font-mono ${day.actualProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {day.actualProfit >= 0 ? '+' : ''}{formatMoney(day.actualProfit)}
                            </span>
                          ) : day.status === 'active' ? (
                            <Button
                              size="sm"
                              className="h-6 text-xs btn-primary"
                              onClick={() => window.location.href = '/trade-monitor'}
                              data-testid="trade-now-daily"
                            >
                              Trade Now
                            </Button>
                          ) : day.status === 'future' ? (
                            <span className="text-zinc-500 text-xs">-</span>
                          ) : (
                            <span className="text-amber-400 text-xs">Pending Trade</span>
                          )}
                        </td>
                        <td>
                          {plDiff !== null ? (
                            <span className={`font-mono ${plDiff >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {plDiff >= 0 ? '+' : ''}{formatMoney(plDiff)}
                            </span>
                          ) : (
                            <span className="text-zinc-500 text-xs">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                No trading days in this period.
              </div>
            )}
          </div>
          <div className="mt-4 p-3 rounded-lg bg-zinc-900/50 text-xs text-zinc-400">
            <p>• Weekends and holidays are excluded from projections</p>
            <p>• <span className="text-amber-400">Pending Trade</span> = No trade recorded yet</p>
            <p>• <span className="text-blue-400">Trade Now</span> = Active signal available</p>
            <p>• Actual profits update your Account Value when recorded</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
