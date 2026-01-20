import React, { useState, useEffect, useMemo } from 'react';
import api, { profitAPI, currencyAPI, adminAPI, tradeAPI } from '@/lib/api';
import { formatNumber, calculateWithdrawalFees, calculateDepositFees } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Switch } from '@/components/ui/switch';
import { ValueTooltip } from '@/components/ui/value-tooltip';
import { LicenseeWelcomeScreen } from '@/components/LicenseeWelcomeScreen';
import { toast } from 'sonner';
import { 
  Plus, ArrowDownToLine, ArrowUpFromLine, Calculator, 
  TrendingUp, TrendingDown, Wallet, RotateCcw, Rocket, Calendar,
  Clock, CheckCircle2, AlertTriangle, Eye, Sparkles,
  ChevronDown, FileText, Receipt, Lock, Check, ExternalLink,
  Radio, EyeOff, Award, FolderOpen, MoreHorizontal, Edit3, X, TreePine, Loader2, Users
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '@/contexts/AuthContext';
import { OnboardingWizard } from '@/components/OnboardingWizard';
import { VSDDialog } from '@/components/VSDDialog';

// Truncate to 2 decimal places without rounding
const truncateTo2Decimals = (num) => {
  return Math.trunc(num * 100) / 100;
};

// Format full currency amount (no abbreviation)
const formatFullCurrency = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Format large numbers - Desktop: Full amount unless 100K+, Mobile: Always abbreviated
const formatLargeNumber = (amount, forceCompact = false) => {
  if (amount === null || amount === undefined) return '$0.00';
  
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  
  // For mobile (forceCompact) or amounts >= 100K, use abbreviations
  const shouldAbbreviate = forceCompact || absAmount >= 1e5;
  
  if (shouldAbbreviate) {
    if (absAmount >= 1e12) {
      return `${sign}$${(absAmount / 1e12).toFixed(2)}T`;
    } else if (absAmount >= 1e9) {
      return `${sign}$${(absAmount / 1e9).toFixed(2)}B`;
    } else if (absAmount >= 1e6) {
      return `${sign}$${(absAmount / 1e6).toFixed(2)}M`;
    } else if (absAmount >= 1e5) {
      return `${sign}$${(absAmount / 1e3).toFixed(1)}K`;
    }
  }
  
  // For amounts under 100K on desktop, show full amount
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Compact number format for mobile (always uses abbreviations)
const formatCompact = (amount) => {
  if (amount === null || amount === undefined) return '$0';
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  
  if (absAmount >= 1e12) return `${sign}$${(absAmount / 1e12).toFixed(2)}T`;
  if (absAmount >= 1e9) return `${sign}$${(absAmount / 1e9).toFixed(2)}B`;
  if (absAmount >= 1e6) return `${sign}$${(absAmount / 1e6).toFixed(2)}M`;
  if (absAmount >= 1e3) return `${sign}$${(absAmount / 1e3).toFixed(2)}K`;
  return `${sign}$${absAmount.toFixed(2)}`;
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

// Common holidays (Merin non-trading days)
const isHoliday = (date) => {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();
  
  // Holiday list - add more as needed
  const holidays = [
    // 2025 holidays
    { year: 2025, month: 11, day: 25 },  // Christmas
    { year: 2025, month: 11, day: 26 },  // Boxing Day
    { year: 2025, month: 11, day: 31 },  // New Year's Eve
    // 2026 holidays
    { year: 2026, month: 0, day: 1 },    // New Year's Day
    { year: 2026, month: 0, day: 2 },    // New Year Holiday
    // Generic annual holidays (checked every year)
    // Note: These are fallback - prefer year-specific dates above
  ];
  
  // Check year-specific holidays first
  const isYearSpecificHoliday = holidays.some(h => 
    h.year === year && h.month === month && h.day === day
  );
  
  if (isYearSpecificHoliday) return true;
  
  // Generic annual holidays (applied to all years not covered above)
  const genericHolidays = [
    { month: 0, day: 1 },   // New Year's Day
    { month: 11, day: 25 }, // Christmas
    { month: 11, day: 26 }, // Boxing Day
  ];
  
  return genericHolidays.some(h => h.month === month && h.day === day);
};

// Check if date is a trading day (weekday and not holiday)
// Now accepts globalHolidays parameter to use dynamic holidays from backend
const isTradingDay = (date, globalHolidayDates = new Set()) => {
  const dayOfWeek = date.getDay();
  if (dayOfWeek === 0 || dayOfWeek === 6) return false; // Weekend
  
  // Check global holidays from backend
  // Use LOCAL date format (YYYY-MM-DD) to avoid timezone issues
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const dateKey = `${year}-${month}-${day}`;
  if (globalHolidayDates.has(dateKey)) return false;
  
  return true;
};

// Generate daily projection for a specific month
// Now accepts deposits array to properly calculate running balance
// Also accepts globalHolidayDates set to use dynamic holidays
const generateDailyProjectionForMonth = (startBalance, monthDate, tradeLogs = {}, activeSignal = null, allTransactions = [], liveAccountValue = null, globalHolidayDates = new Set(), effectiveStartDate = null) => {
  const days = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  let firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  
  // If effectiveStartDate is set and falls within or after this month, adjust firstDay
  if (effectiveStartDate) {
    const effStartParsed = new Date(effectiveStartDate + 'T00:00:00');
    if (!isNaN(effStartParsed.getTime())) {
      // Only show days on or after the effective start date
      if (effStartParsed > firstDay) {
        firstDay = effStartParsed;
      }
      // If effective start is after this month entirely, return empty
      if (effStartParsed > lastDay) {
        return [];
      }
    }
  }
  
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
  const isPastMonth = (year < today.getFullYear()) || (year === today.getFullYear() && month < today.getMonth());
  
  // Create a map of deposits/withdrawals by date for quick lookup
  // Note: Withdrawals already have NEGATIVE amounts in the database
  const transactionsByDate = {};
  if (allTransactions && allTransactions.length > 0) {
    allTransactions.forEach(tx => {
      const txDate = tx.created_at ? tx.created_at.split('T')[0] : null;
      if (txDate) {
        if (!transactionsByDate[txDate]) {
          transactionsByDate[txDate] = 0;
        }
        // The amount is already negative for withdrawals, so just add it
        transactionsByDate[txDate] += (tx.amount || 0);
      }
    });
  }
  
  // Calculate the starting balance for this month by working backwards
  let runningBalance = startBalance;
  
  if (isCurrentMonth || isPastMonth) {
    // Get all trades and transactions for this month
    const monthPrefix = `${year}-${String(month + 1).padStart(2, '0')}`;
    
    // Sum up all profits + commissions in this month
    const monthTrades = Object.entries(tradeLogs)
      .filter(([key, _]) => key.startsWith(monthPrefix))
      .sort(([a], [b]) => a.localeCompare(b));
    
    const totalMonthProfit = monthTrades.reduce((sum, [_, log]) => {
      return sum + (log?.actual_profit || 0) + (log?.commission || 0);
    }, 0);
    
    // Sum up all deposits/withdrawals in this month
    const totalMonthTransactions = Object.entries(transactionsByDate)
      .filter(([dateKey, _]) => dateKey.startsWith(monthPrefix))
      .reduce((sum, [_, amount]) => sum + amount, 0);
    
    // Starting balance for the month = current balance - total month profit - total month transactions
    runningBalance = startBalance - totalMonthProfit - totalMonthTransactions;
  }
  
  let currentDate = new Date(firstDay);
  
  while (currentDate <= lastDay) {
    if (isTradingDay(currentDate, globalHolidayDates)) {
      // Use LOCAL date format to avoid timezone issues
      const year = currentDate.getFullYear();
      const month = String(currentDate.getMonth() + 1).padStart(2, '0');
      const day = String(currentDate.getDate()).padStart(2, '0');
      const dateKey = `${year}-${month}-${day}`;
      
      const tradeLog = tradeLogs[dateKey];
      const hasTraded = tradeLog?.has_traded;
      const actualProfit = tradeLog?.actual_profit;
      const commission = tradeLog?.commission || 0;  // Daily commission from referrals
      
      // Apply any deposits/withdrawals for this date BEFORE calculating lot size
      // (deposits should affect the balance BEFORE the day's trade)
      const dayTransaction = transactionsByDate[dateKey] || 0;
      if (dayTransaction !== 0) {
        runningBalance += dayTransaction;
      }
      
      // For completed trades, use the STORED lot_size and projected_profit from trade logs
      // This ensures Trade History and Daily Projection show consistent values
      const hasStoredTradeData = tradeLog && tradeLog.lot_size && tradeLog.projected_profit;
      
      // Calculate lot size and target profit based on current running balance
      // But use stored values for completed trades to maintain consistency
      let lotSize, targetProfit;
      if (hasStoredTradeData) {
        // Use stored values from when the trade was logged
        lotSize = tradeLog.lot_size;
        targetProfit = tradeLog.projected_profit;
      } else {
        // Recalculate for days without trades
        lotSize = truncateTo2Decimals(runningBalance / 980);
        targetProfit = truncateTo2Decimals(lotSize * 15);
      }
      
      // Determine status
      let status = 'pending';
      const isToday = currentDate.toDateString() === today.toDateString();
      const isFuture = currentDate > today;
      const isPast = currentDate < today;
      
      if (hasTraded && actualProfit !== undefined) {
        status = 'completed';
      } else if (isPast) {
        status = 'missed'; // Past day without trade
      } else if (isToday && activeSignal) {
        status = 'active';
      } else if (isFuture) {
        status = 'future';
      }
      
      // Calculate P/L difference based on projected profit (stored or calculated)
      const plDiff = hasTraded && actualProfit !== undefined 
        ? truncateTo2Decimals(actualProfit - targetProfit)
        : null;
      
      // Determine performance based on values
      let performance = null;
      if (hasTraded && actualProfit !== undefined) {
        if (actualProfit >= targetProfit) {
          performance = actualProfit > targetProfit ? 'exceeded' : 'perfect';
        } else if (actualProfit > 0) {
          performance = 'below';
        } else {
          performance = 'below';
        }
      }
      
      // For today, recalculate lot size and target profit based on live account value
      // For past days with trades, use stored values; for future days, use calculated values
      let effectiveLotSize, effectiveTargetProfit, effectiveBalance;
      
      if (isToday && liveAccountValue !== null) {
        // CRITICAL FIX: "Balance Before" should show the balance BEFORE today's trade
        // If we traded today, the live account value already INCLUDES today's profit + commission
        // So we need to subtract them to get the true "Balance Before"
        if (hasTraded && actualProfit !== undefined) {
          // Calculate what the balance was BEFORE we traded
          effectiveBalance = truncateTo2Decimals(liveAccountValue - actualProfit - commission);
        } else {
          // No trade yet today, live value IS the balance before
          effectiveBalance = liveAccountValue;
        }
        effectiveLotSize = truncateTo2Decimals(effectiveBalance / 980);
        effectiveTargetProfit = truncateTo2Decimals(effectiveLotSize * 15);
      } else if (hasStoredTradeData) {
        // CRITICAL: For days with stored trade data, derive balance FROM the stored lot_size
        // This ensures Balance Before matches the LOT Size (Balance = LOT × 980)
        effectiveLotSize = lotSize;
        effectiveTargetProfit = targetProfit;
        effectiveBalance = truncateTo2Decimals(lotSize * 980);
      } else {
        effectiveLotSize = lotSize;
        effectiveTargetProfit = targetProfit;
        effectiveBalance = runningBalance;
      }
      
      days.push({
        date: new Date(currentDate),
        dateStr: currentDate.toLocaleDateString('en-US', { 
          weekday: 'short', 
          month: 'short', 
          day: 'numeric' 
        }),
        dateKey: dateKey,
        balanceBefore: effectiveBalance,
        lotSize: effectiveLotSize,
        targetProfit: effectiveTargetProfit,
        actualProfit: actualProfit,
        commission: commission,  // Daily commission from referrals
        plDiff: hasTraded && actualProfit !== undefined 
          ? truncateTo2Decimals(actualProfit - effectiveTargetProfit)
          : null,
        performance: performance,
        status: status,
        isToday: isToday,
        hasTransaction: dayTransaction !== 0,
        transactionAmount: dayTransaction,
      });
      
      // Add profit AND commission to running balance for next day's calculation
      // Balance formula: Next Day Balance = Today's Balance + Today's Profit + Today's Commission
      if (hasTraded && actualProfit !== undefined) {
        runningBalance += actualProfit + commission;
      } else {
        runningBalance += targetProfit;
      }
    }
    
    currentDate.setDate(currentDate.getDate() + 1);
  }
  
  return days;
};

// Generate monthly projection data for accordion (up to 5 years = 60 months)
// Now includes past months if user has trade data in those months
const generateMonthlyProjection = (accountBalance, tradeLogs = {}, globalHolidayDates = new Set(), deposits = []) => {
  const months = [];
  const today = new Date();
  
  // Find the earliest trade or deposit date to determine if we need to show past months
  const tradeKeys = Object.keys(tradeLogs).sort();
  const depositDates = deposits.map(d => d.created_at?.split('T')[0]).filter(Boolean).sort();
  const allDates = [...tradeKeys, ...depositDates].sort();
  
  let startMonthOffset = 0;
  
  if (allDates.length > 0) {
    const earliestDate = new Date(allDates[0]);
    const monthsDiff = (today.getFullYear() - earliestDate.getFullYear()) * 12 + 
                       (today.getMonth() - earliestDate.getMonth());
    startMonthOffset = -monthsDiff; // Negative to go back in time
  }
  
  // For past months, we need to calculate forward from the earliest data point
  // For future months, we project forward from current balance
  
  // First, gather all past months with data
  const pastMonths = [];
  for (let monthOffset = startMonthOffset; monthOffset < 0; monthOffset++) {
    const monthDate = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
    const monthKey = `${monthDate.getFullYear()}-${String(monthDate.getMonth() + 1).padStart(2, '0')}`;
    
    const hasTradesInMonth = tradeKeys.some(key => key.startsWith(monthKey));
    const hasDepositsInMonth = depositDates.some(d => d?.startsWith(monthKey));
    
    if (hasTradesInMonth || hasDepositsInMonth) {
      // Get trades for this month
      const monthTrades = Object.entries(tradeLogs)
        .filter(([key]) => key.startsWith(monthKey))
        .sort(([a], [b]) => a.localeCompare(b));
      
      // Count trading days and sum profits
      const lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
      let tradingDays = 0;
      let currentDate = new Date(monthDate);
      
      while (currentDate <= lastDay) {
        if (isTradingDay(currentDate, globalHolidayDates)) {
          tradingDays++;
        }
        currentDate.setDate(currentDate.getDate() + 1);
      }
      
      // For past months, we show actual data from trade logs
      const totalProfit = monthTrades.reduce((sum, [_, log]) => sum + (log?.actual_profit || 0), 0);
      
      pastMonths.push({
        monthOffset: monthOffset,
        year: 0, // Will be labeled as "History"
        monthDate: new Date(monthDate),
        monthKey: monthKey,
        monthName: monthDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        tradingDays: tradingDays,
        isCurrentMonth: false,
        isPastMonth: true,
        totalProfit: totalProfit,
        tradesCount: monthTrades.length,
      });
    }
  }
  
  // Add past months to the result (they'll appear first due to negative monthOffset)
  months.push(...pastMonths);
  
  // Now add current and future months with projections
  let balance = accountBalance || 0;
  
  for (let monthOffset = 0; monthOffset <= 60; monthOffset++) {
    const monthDate = new Date(today.getFullYear(), today.getMonth() + monthOffset, 1);
    const monthKey = `${monthDate.getFullYear()}-${String(monthDate.getMonth() + 1).padStart(2, '0')}`;
    
    const isCurrentMonth = monthOffset === 0;
    
    // Calculate trading days in this month
    let tradingDays = 0;
    let monthBalance = balance;
    const lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
    
    // For current month, start from today
    let currentDate = isCurrentMonth ? new Date(today) : new Date(monthDate);
    
    while (currentDate <= lastDay) {
      if (isTradingDay(currentDate, globalHolidayDates)) {
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
      isPastMonth: false,
    });
    
    balance = monthBalance;
  }
  
  return months;
};

// Group months by year for accordion
// Year 0 = "History" (past months with trade data) - should appear FIRST
const groupMonthsByYear = (monthlyData) => {
  const years = {};
  monthlyData.forEach(m => {
    const yearKey = m.year === 0 ? 'History' : `Year ${m.year}`;
    if (!years[yearKey]) {
      years[yearKey] = [];
    }
    years[yearKey].push(m);
  });
  
  // Return as array of [yearKey, months] sorted so History comes first
  const sortedYears = Object.entries(years).sort(([a], [b]) => {
    if (a === 'History') return -1;
    if (b === 'History') return 1;
    return parseInt(a.replace('Year ', '')) - parseInt(b.replace('Year ', ''));
  });
  
  // Convert back to object but maintain order
  const orderedYears = {};
  sortedYears.forEach(([key, value]) => {
    orderedYears[key] = value;
  });
  
  return orderedYears;
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
    getSimulatedMemberName,
    isMasterAdmin
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
  
  // Onboarding Wizard states
  const [onboardingWizardOpen, setOnboardingWizardOpen] = useState(false);
  const [isResetOnboarding, setIsResetOnboarding] = useState(false);
  
  // Licensee Welcome Screen states
  const [showLicenseeWelcome, setShowLicenseeWelcome] = useState(false);
  const [licenseeWelcomeInfo, setLicenseeWelcomeInfo] = useState(null);
  const [licenseeProjections, setLicenseeProjections] = useState([]);
  
  // Adjust Trade Dialog for past trades (renamed from Adjust Trade)
  const [enterAPDialogOpen, setEnterAPDialogOpen] = useState(false);
  const [enterAPDate, setEnterAPDate] = useState(null);
  const [enterAPValue, setEnterAPValue] = useState('');
  const [enterAPLoading, setEnterAPLoading] = useState(false);
  
  // Adjustment options for past trades
  const [adjustmentType, setAdjustmentType] = useState('profit_only'); // 'profit_only', 'with_deposit', 'with_withdrawal'
  const [adjustmentAmount, setAdjustmentAmount] = useState(''); // deposit/withdrawal amount
  const [adjustedBalance, setAdjustedBalance] = useState(''); // manually adjusted balance before trade
  
  // Access Records Dialog (combined deposit, withdrawal, commission records)
  const [accessRecordsOpen, setAccessRecordsOpen] = useState(false);
  const [activeRecordTab, setActiveRecordTab] = useState('deposits');
  
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
  
  // Simulate Actions Dialog (combined simulate deposit, withdrawal, commission)
  const [simulateActionsOpen, setSimulateActionsOpen] = useState(false);
  
  // VSD (Virtual Share Distribution) Dialog - Master Admin only
  const [vsdDialogOpen, setVsdDialogOpen] = useState(false);
  const [vsdData, setVsdData] = useState(null);
  const [vsdLoading, setVsdLoading] = useState(false);
  
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
  
  // Manual deposit override
  const [manualDepositMode, setManualDepositMode] = useState(false);
  const [manualDepositAmount, setManualDepositAmount] = useState('');
  
  // Check if user is a licensee (hide simulation/record buttons)
  const isLicensee = simulatedView?.license_type || user?.license_type;
  const isExtendedLicensee = (simulatedView?.license_type || user?.license_type) === 'extended';
  const isHonoraryLicensee = (simulatedView?.license_type || user?.license_type) === 'honorary';
  
  // Master admin trades for extended licensees (profit credited tracking)
  const [masterAdminTrades, setMasterAdminTrades] = useState({});
  
  // License projections for extended licensees (fixed lot size and daily profit per quarter)
  const [licenseProjections, setLicenseProjections] = useState([]);
  
  // Trade overrides for licensees (per-licensee, per-date manual toggles by Master Admin)
  const [tradeOverrides, setTradeOverrides] = useState({});
  const [togglingTrade, setTogglingTrade] = useState(null); // Track which date is being toggled
  
  // Get effective start date for licensees
  const effectiveStartDate = simulatedView?.effective_start_date || null;
  
  // Projection states
  const [selectedYears, setSelectedYears] = useState(1);
  const [projectionView, setProjectionView] = useState('summary');
  
  // Global holidays state (fetched from backend)
  const [globalHolidays, setGlobalHolidays] = useState([]);
  
  const userTimezone = user?.timezone || 'Asia/Manila';

  useEffect(() => {
    loadData();
    loadGlobalHolidays();
    // Check if licensee needs to see welcome screen
    checkLicenseeWelcome();
    // Load trade overrides if simulating a licensee
    if (simulatedView?.licenseId) {
      loadTradeOverrides(simulatedView.licenseId);
    }
  }, [simulatedView]);

  const checkLicenseeWelcome = async () => {
    // Only check for actual licensees (not simulated views)
    if (simulatedView || !user?.license_type) return;
    
    try {
      const response = await profitAPI.getLicenseeWelcomeInfo();
      if (response.data.is_licensee && !response.data.has_seen_welcome) {
        setLicenseeWelcomeInfo(response.data);
        setShowLicenseeWelcome(true);
      }
    } catch (error) {
      console.error('Failed to check licensee welcome:', error);
    }
  };

  const loadTradeOverrides = async (licenseId) => {
    try {
      const response = await adminAPI.getLicenseTradeOverrides(licenseId);
      setTradeOverrides(response.data.overrides || {});
    } catch (error) {
      console.error('Failed to load trade overrides:', error);
      setTradeOverrides({});
    }
  };

  const handleToggleTradeOverride = async (dateKey, currentTraded) => {
    if (!simulatedView?.licenseId) {
      toast.error('Cannot toggle trade status - no license selected');
      return;
    }
    
    setTogglingTrade(dateKey);
    try {
      await adminAPI.setLicenseTradeOverride(simulatedView.licenseId, {
        license_id: simulatedView.licenseId,
        date: dateKey,
        traded: !currentTraded,
        notes: `Toggled by Master Admin on ${new Date().toISOString()}`
      });
      
      // Update local state
      setTradeOverrides(prev => ({
        ...prev,
        [dateKey]: { ...prev[dateKey], traded: !currentTraded, date: dateKey }
      }));
      
      toast.success(`Trade status for ${dateKey} set to ${!currentTraded ? '✓ Traded' : '✗ Not Traded'}`);
    } catch (error) {
      console.error('Failed to toggle trade override:', error);
      toast.error('Failed to update trade status');
    } finally {
      setTogglingTrade(null);
    }
  };

  // Load VSD (Virtual Share Distribution) data for Master Admin
  const loadVSDData = async () => {
    if (!isMasterAdmin()) return;
    
    setVsdLoading(true);
    try {
      const response = await profitAPI.getVSD();
      setVsdData(response.data);
    } catch (error) {
      console.error('Failed to load VSD data:', error);
      toast.error('Failed to load Virtual Share Distribution');
    } finally {
      setVsdLoading(false);
    }
  };

  const loadLicenseeProjections = async () => {
    try {
      const response = await profitAPI.getLicenseeDailyProjection();
      setLicenseeProjections(response.data.projections || []);
    } catch (error) {
      console.error('Failed to load licensee projections:', error);
    }
  };

  const loadGlobalHolidays = async () => {
    try {
      const response = await tradeAPI.getGlobalHolidays();
      setGlobalHolidays(response.data.holidays || []);
    } catch (error) {
      console.error('Failed to load global holidays:', error);
    }
  };

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
        // For specific member simulation, fetch their complete data from API
        const memberId = simulatedView.memberId;
        const [memberRes, ratesRes, signalRes, memberTradeLogsRes, memberDepositsRes, memberWithdrawalsRes] = await Promise.all([
          adminAPI.getMemberDetails(memberId),
          currencyAPI.getRates('USDT'),
          api.get('/trade/active-signal').catch(() => ({ data: null })),
          api.get(`/trade/logs?user_id=${memberId}`).catch(() => ({ data: [] })),
          api.get(`/admin/members/${memberId}/deposits`).catch(() => ({ data: [] })),
          api.get(`/admin/members/${memberId}/withdrawals`).catch(() => ({ data: [] })),
        ]);
        
        const stats = memberRes.data.stats || {};
        setSummary({
          account_value: stats.account_value || 0,
          total_deposits: stats.total_deposits || 0,
          total_profit: stats.total_profit || 0,
          total_actual_profit: stats.total_actual_profit || 0,
          current_lot_size: memberRes.data.user?.lot_size || 0.01
        });
        setDeposits(memberDepositsRes.data || memberRes.data.recent_deposits || []);
        setWithdrawals(memberWithdrawalsRes.data || []);
        
        // Process trade logs to get the date-keyed format
        const tradeLogsData = memberTradeLogsRes.data || [];
        const logsMap = {};
        tradeLogsData.forEach(trade => {
          const dateKey = trade.created_at?.split('T')[0] || '';
          if (dateKey) {
            logsMap[dateKey] = {
              actual_profit: trade.actual_profit,
              has_traded: true,
              lot_size: trade.lot_size,
              projected_profit: trade.projected_profit,
              ...trade
            };
          }
        });
        setTradeLogs(logsMap);
        
        setIsFirstTime(false);
        setRates(ratesRes.data.rates || {});
        if (signalRes.data?.signal) {
          setActiveSignal(signalRes.data.signal);
        }
        setCommissions([]);
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
      
      // Check if first time user - but skip onboarding wizard for licensees
      const licenseType = simulatedView?.license_type || user?.license_type;
      if (allDeposits.length === 0 && !licenseType) {
        // Non-licensees: Show onboarding wizard
        setIsFirstTime(true);
        setIsResetOnboarding(false);
        setOnboardingWizardOpen(true);
      } else if (allDeposits.length === 0 && licenseType) {
        // Licensees: Skip onboarding, they get their balance from admin
        setIsFirstTime(false);
      }
      
      // Load master admin trades for ALL licensees (not just extended)
      if (licenseType) {
        try {
          const startDate = new Date();
          startDate.setMonth(0, 1); // January 1st of current year
          const endDate = new Date();
          endDate.setMonth(11, 31); // December 31st of current year
          
          const tradesRes = await profitAPI.getMasterAdminTrades(
            startDate.toISOString().split('T')[0],
            endDate.toISOString().split('T')[0]
          );
          setMasterAdminTrades(tradesRes.data?.trading_dates || {});
          
          // Load license projections for fixed lot size/daily profit (extended licensees)
          if (licenseType === 'extended') {
            const projectionsRes = await profitAPI.getLicenseProjections();
            if (projectionsRes.data?.monthly_projections) {
              setLicenseProjections(projectionsRes.data.monthly_projections);
            }
          }
          
          // Load licensee-specific daily projections
          await loadLicenseeProjections();
        } catch (error) {
          console.error('Failed to load master admin trades:', error);
        }
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
  // Note: For licensees, use backend projections with Manager Traded logic
  // For current month, always use the latest effectiveAccountValue to ensure
  // the projection reflects any newly logged trades
  const getDailyProjectionForSelectedMonth = useMemo(() => {
    if (!selectedMonth) return [];
    
    const today = new Date();
    const isCurrentMonth = selectedMonth.monthDate.getFullYear() === today.getFullYear() &&
                           selectedMonth.monthDate.getMonth() === today.getMonth();
    
    // For ALL licensees: Use backend projections with Manager Traded logic
    if (isLicensee && licenseProjections.length > 0) {
      // Filter projections for selected month
      const monthKey = `${selectedMonth.monthDate.getFullYear()}-${String(selectedMonth.monthDate.getMonth() + 1).padStart(2, '0')}`;
      let monthProjections = licenseProjections.filter(p => p.date.startsWith(monthKey));
      
      // Filter by effective start date if set
      if (effectiveStartDate) {
        monthProjections = monthProjections.filter(p => p.date >= effectiveStartDate);
      }
      
      if (monthProjections.length === 0) return [];
      
      // Build projections with carry-forward logic when manager didn't trade
      // Start with the first day's "start_value" (balance BEFORE first trade)
      let runningBalance = monthProjections[0]?.start_value || 
                           (monthProjections[0]?.account_value - monthProjections[0]?.daily_profit) || 
                           effectiveAccountValue;
      
      // Track accumulated profit for this month (for licensees)
      let accumulatedProfit = 0;
      
      return monthProjections.map((p, idx) => {
        const projDate = new Date(p.date + 'T00:00:00'); // Ensure local date parsing
        const isToday = projDate.toDateString() === today.toDateString();
        const isFuture = projDate > today;
        const isPast = projDate < today;
        
        // Check trade override first, then fall back to master admin trades
        const hasOverride = tradeOverrides[p.date] !== undefined;
        const masterTraded = hasOverride 
          ? tradeOverrides[p.date].traded 
          : masterAdminTrades[p.date]?.traded;
        
        // Determine status
        let status = 'pending';
        if (isPast && masterTraded) {
          status = 'completed';
        } else if (isPast && !masterTraded) {
          status = 'missed'; // Past day without master admin trade
        } else if (isToday) {
          status = masterTraded ? 'completed' : 'pending';
        } else if (isFuture) {
          status = 'future';
        }
        
        // Calculate balance - accumulate properly
        const balanceBefore = runningBalance;
        
        // For past days and today (if traded), add the actual profit
        // For future days, project based on accumulated balance
        let dailyProfit = p.daily_profit;
        
        // If master didn't trade on a past day, no profit for that day
        if (isPast && !masterTraded) {
          dailyProfit = 0;
        }
        
        // Track accumulated profit from trading days
        if ((isPast || (isToday && masterTraded)) && masterTraded) {
          accumulatedProfit += p.daily_profit;
        }
        
        // Update running balance for next day
        // Only add profit if manager actually traded (for past days) or for future projections
        if (isPast && masterTraded) {
          runningBalance = balanceBefore + p.daily_profit;
        } else if (isToday && masterTraded) {
          // For today, use the projected profit if manager traded
          runningBalance = balanceBefore + p.daily_profit;
        } else if (isFuture) {
          // For future days, project based on current running balance
          // Assume manager WILL trade (optimistic projection)
          runningBalance = balanceBefore + p.daily_profit;
        }
        // If manager didn't trade on past day, balance stays the same (carry forward)
        
        return {
          date: projDate,
          dateStr: projDate.toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
          }),
          dateKey: p.date,
          balanceBefore: balanceBefore,
          lotSize: p.lot_size,  // Will be hidden in UI for licensees
          targetProfit: masterTraded || isFuture ? p.daily_profit : 0, // Show "--" for missed past days
          actualProfit: (isPast || isToday) && masterTraded ? p.daily_profit : undefined,
          status: status,
          isToday: isToday,
          managerTraded: masterTraded, // Explicit flag for the "Manager Traded" column
          hasOverride: hasOverride, // Track if this is an override
        };
      });
    }
    
    // For regular users (non-licensees), use standard calculation
    // For past months, we need to calculate the correct starting balance by working
    // backwards from current account value using trade logs and transactions
    let startBalance;
    
    if (isCurrentMonth) {
      startBalance = effectiveAccountValue;
    } else if (selectedMonth.isPastMonth) {
      // For past months, calculate starting balance by:
      // Current balance - all profits after this month - all deposits/withdrawals after this month
      const monthKey = `${selectedMonth.monthDate.getFullYear()}-${String(selectedMonth.monthDate.getMonth() + 1).padStart(2, '0')}`;
      const monthStart = new Date(selectedMonth.monthDate.getFullYear(), selectedMonth.monthDate.getMonth(), 1);
      
      // Sum all profits from this month onwards
      let totalProfitAfter = 0;
      Object.entries(tradeLogs).forEach(([dateKey, log]) => {
        if (dateKey >= monthKey.slice(0, 7)) {  // From this month onwards
          totalProfitAfter += (log?.actual_profit || 0);
        }
      });
      
      // Sum all deposits/withdrawals from this month onwards
      let totalTxAfter = 0;
      [...deposits, ...withdrawals].forEach(tx => {
        const txDate = tx.created_at?.split('T')[0];
        if (txDate && txDate >= `${monthKey}-01`) {
          totalTxAfter += (tx.amount || 0);  // Withdrawals already negative
        }
      });
      
      // Starting balance for this month = current - profits after - transactions after
      // But we need the balance at the START of this month, so add back the month's profits
      const monthProfits = Object.entries(tradeLogs)
        .filter(([key]) => key.startsWith(monthKey))
        .reduce((sum, [_, log]) => sum + (log?.actual_profit || 0), 0);
      
      startBalance = effectiveAccountValue - totalProfitAfter - totalTxAfter + monthProfits;
    } else {
      // Future months - use the month's calculated start balance
      startBalance = selectedMonth.startBalance;
    }
    
    // Combine deposits and withdrawals for accurate balance tracking
    // Note: Withdrawals already have NEGATIVE amounts stored in the database
    const allTransactions = [...deposits, ...withdrawals];
    
    // Pass effectiveAccountValue as liveAccountValue to synchronize today's balance
    // with the live dashboard value
    const globalHolidayDates = new Set(globalHolidays.map(h => h.date));
    return generateDailyProjectionForMonth(
      startBalance,
      selectedMonth.monthDate,
      tradeLogs,
      activeSignal,
      allTransactions,
      isCurrentMonth ? effectiveAccountValue : null,  // Only pass live value for current month
      globalHolidayDates,
      effectiveStartDate  // Pass effective start date for licensees
    );
  }, [selectedMonth, tradeLogs, activeSignal, effectiveAccountValue, isExtendedLicensee, licenseProjections, masterAdminTrades, deposits, withdrawals, globalHolidays, effectiveStartDate]);

  // Handle opening Adjust Trade dialog for a specific date
  const handleOpenEnterAP = (day) => {
    setEnterAPDate(day);
    setEnterAPValue('');
    setAdjustmentType('profit_only');
    setAdjustmentAmount('');
    setAdjustedBalance(day.balanceBefore?.toString() || '');
    setEnterAPDialogOpen(true);
  };

  // Handle submitting the adjusted trade
  const handleSubmitEnterAP = async () => {
    if (!enterAPValue || parseFloat(enterAPValue) < 0) {
      toast.error('Please enter a valid actual profit value');
      return;
    }
    
    if (!enterAPDate) {
      toast.error('No date selected');
      return;
    }

    // Validate adjustment amount if deposit/withdrawal selected
    if (adjustmentType !== 'profit_only' && (!adjustmentAmount || parseFloat(adjustmentAmount) <= 0)) {
      toast.error('Please enter a valid deposit/withdrawal amount');
      return;
    }

    setEnterAPLoading(true);
    try {
      // First, if there's a deposit or withdrawal, record it
      if (adjustmentType === 'with_deposit' && adjustmentAmount) {
        await profitAPI.createDeposit({
          amount: parseFloat(adjustmentAmount),
          date: enterAPDate.dateKey,
          notes: `Retroactive deposit for ${enterAPDate.dateStr}`
        });
      } else if (adjustmentType === 'with_withdrawal') {
        // Record as negative deposit or withdrawal
        await profitAPI.recordWithdrawal({
          amount: parseFloat(adjustmentAmount),
          date: enterAPDate.dateKey,
          notes: `Retroactive withdrawal for ${enterAPDate.dateStr}`
        });
      }

      // Calculate the lot size based on adjusted balance if provided
      const balanceForCalculation = adjustedBalance ? parseFloat(adjustedBalance) : enterAPDate.balanceBefore;
      const calculatedLotSize = truncateTo2Decimals(balanceForCalculation / 980);

      // Log the trade
      await tradeAPI.logMissedTrade({
        date: enterAPDate.dateKey,
        actual_profit: parseFloat(enterAPValue),
        lot_size: calculatedLotSize,
        direction: activeSignal?.direction || 'BUY',
        balance_before: balanceForCalculation,
        notes: adjustmentType === 'profit_only' 
          ? 'Retroactively logged via Adjust Trade'
          : `Adjusted trade with ${adjustmentType === 'with_deposit' ? 'deposit' : 'withdrawal'} of $${adjustmentAmount}`
      });
      
      toast.success('Trade adjusted successfully!');
      setEnterAPDialogOpen(false);
      setEnterAPValue('');
      setEnterAPDate(null);
      setAdjustmentType('profit_only');
      setAdjustmentAmount('');
      setAdjustedBalance('');
      
      // Reload data to reflect the new trade
      loadData();
    } catch (error) {
      console.error('Failed to adjust trade:', error);
      toast.error(error.response?.data?.detail || 'Failed to adjust trade');
    } finally {
      setEnterAPLoading(false);
    }
  };


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
    setManualDepositMode(false);
    setManualDepositAmount('');
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
    setResetStep('password');
  };

  const handleResetNewBalance = () => {
    // This step is now handled by the onboarding wizard
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
      
      toast.success('Profit tracker has been reset!');
      resetResetDialog();
      
      // Open the onboarding wizard for reset flow
      setIsResetOnboarding(true);
      setOnboardingWizardOpen(true);
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
  
  const monthlyProjection = useMemo(() => {
    const globalHolidayDates = new Set(globalHolidays.map(h => h.date));
    return generateMonthlyProjection(effectiveAccountValue, tradeLogs, globalHolidayDates, deposits);
  }, [effectiveAccountValue, tradeLogs, globalHolidays, deposits]);
  
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

  // Show licensee welcome screen for first-time licensees
  if (showLicenseeWelcome && licenseeWelcomeInfo) {
    return (
      <LicenseeWelcomeScreen 
        welcomeInfo={licenseeWelcomeInfo}
        onContinue={() => {
          setShowLicenseeWelcome(false);
          loadData();
          loadLicenseeProjections();
        }}
      />
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

      {/* Trading Signal Banner - Desktop Only */}
      {activeSignal && (
        <Card className="hidden md:block glass-highlight border-blue-500/30 bg-gradient-to-r from-blue-500/10 to-cyan-500/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Radio className="w-5 h-5 text-blue-400 animate-pulse" />
                <div>
                  <p className="text-xs text-zinc-400">Today&apos;s Trading Signal</p>
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

      {/* Mobile Signal Card - Compact "Trade Now" button that navigates to Trade Monitor */}
      {activeSignal && (
        <Card className="md:hidden glass-card border-blue-500/30 bg-blue-500/5" data-testid="mobile-signal-card">
          <CardContent className="p-3">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                activeSignal.direction === 'BUY' ? 'bg-emerald-500' : 'bg-red-500'
              }`}>
                {activeSignal.direction === 'BUY' ? (
                  <TrendingUp className="w-5 h-5 text-white" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-white" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-bold ${activeSignal.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {activeSignal.direction}
                  </span>
                  <span className="text-xs text-zinc-400">{activeSignal.product || 'MOIL10'}</span>
                </div>
                <p className="text-xs text-zinc-500">
                  {activeSignal.trade_time} ({activeSignal.trade_timezone || 'Manila'})
                </p>
              </div>
              <Button
                onClick={() => window.location.href = '/trade-monitor'}
                className="btn-primary h-10 px-4 text-sm font-medium flex-shrink-0"
                data-testid="mobile-trade-now-btn"
              >
                Trade Now
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards - Single column on mobile for readability */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Card className="glass-card" data-testid="account-value-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-zinc-400">Account Value</p>
                <ValueTooltip exactValue={formatFullCurrency(effectiveAccountValue)}>
                  {/* Desktop: Full amount, Mobile: Compact */}
                  <p className="text-2xl font-bold font-mono text-white mt-1">
                    <span className="hidden md:inline">{formatLargeNumber(effectiveAccountValue)}</span>
                    <span className="md:hidden">{formatCompact(effectiveAccountValue)}</span>
                  </p>
                </ValueTooltip>
              </div>
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
                <Wallet className="w-5 h-5 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="total-deposits-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-xs text-zinc-400">Deposits</p>
                  <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
                    <SelectTrigger className="w-16 h-5 text-[10px] bg-zinc-900/50 border-zinc-700">
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
                <ValueTooltip exactValue={`${getCurrencySymbol(selectedCurrency)}${formatNumber(convertAmount(effectiveTotalDeposits, selectedCurrency))} (${formatFullCurrency(effectiveTotalDeposits)} USDT)`}>
                  <p className="text-2xl font-bold font-mono text-white mt-1">
                    <span className="hidden md:inline">{getCurrencySymbol(selectedCurrency)}{formatNumber(convertAmount(effectiveTotalDeposits, selectedCurrency))}</span>
                    <span className="md:hidden">{formatCompact(effectiveTotalDeposits)}</span>
                  </p>
                </ValueTooltip>
                <p className="text-[10px] text-zinc-500 hidden md:block">≈ {formatFullCurrency(effectiveTotalDeposits)} USDT</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center flex-shrink-0">
                <ArrowDownToLine className="w-5 h-5 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="total-profit-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-zinc-400">Total Profit</p>
                <ValueTooltip exactValue={formatFullCurrency(effectiveTotalProfit)}>
                  <p className={`text-2xl font-bold font-mono mt-1 ${effectiveTotalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    <span className="hidden md:inline">{effectiveTotalProfit >= 0 ? '+' : ''}{formatLargeNumber(effectiveTotalProfit)}</span>
                    <span className="md:hidden">{effectiveTotalProfit >= 0 ? '+' : ''}{formatCompact(effectiveTotalProfit)}</span>
                  </p>
                </ValueTooltip>
              </div>
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="current-lot-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-zinc-400">LOT Size</p>
                <p className="text-2xl font-bold font-mono text-purple-400 mt-1">
                  {effectiveLotSize.toFixed(2)}
                </p>
                <p className="text-[10px] text-zinc-500">Balance ÷ 980</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Calculator className="w-5 h-5 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Compact Active Signal Card for Profit Tracker - Mobile Only (desktop version is in summary cards) */}
      {activeSignal && (
        <Card className="md:hidden glass-card border-blue-500/30 bg-blue-500/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  activeSignal.direction === 'BUY' ? 'bg-emerald-500' : 'bg-red-500'
                }`}>
                  {activeSignal.direction === 'BUY' ? (
                    <TrendingUp className="w-5 h-5 text-white" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-white" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-bold ${activeSignal.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {activeSignal.direction}
                    </span>
                    <span className="text-xs text-zinc-400">{activeSignal.product || 'MOIL10'}</span>
                  </div>
                  <p className="text-xs text-zinc-500">
                    Trade at {activeSignal.trade_time} ({activeSignal.trade_timezone})
                  </p>
                </div>
              </div>
              <Button
                onClick={() => window.location.href = '/trade-monitor'}
                className="btn-primary h-10 px-4 text-sm font-medium flex-shrink-0"
                data-testid="trade-now-btn"
              >
                Trade Now
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions - Hidden for licensees who have their own Deposit/Withdrawal page */}
      {!isLicensee && (
      <div className="flex flex-col md:flex-row md:flex-wrap md:items-center gap-3 md:gap-4">
        {/* Simulate Actions - Full width on mobile */}
        <div className="w-full md:w-auto md:flex-1">
        
        {/* Simulate Actions Popup */}
        <Dialog open={simulateActionsOpen} onOpenChange={setSimulateActionsOpen}>
          <DialogTrigger asChild>
            <Button className="btn-primary gap-2 w-full md:w-auto" data-testid="simulate-actions-button">
              <Calculator className="w-4 h-4" /> Simulate Actions
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800 max-w-sm">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <Calculator className="w-5 h-5 text-blue-400" /> Simulate Actions
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-3 mt-4">
              <Button 
                className="w-full btn-primary gap-2 justify-start" 
                onClick={() => { setSimulateActionsOpen(false); setDepositDialogOpen(true); }}
                data-testid="simulate-deposit-button"
              >
                <Plus className="w-4 h-4" /> Simulate Deposit
              </Button>
              <Button 
                variant="outline"
                className="w-full btn-secondary gap-2 justify-start" 
                onClick={() => { setSimulateActionsOpen(false); setWithdrawalDialogOpen(true); }}
                data-testid="simulate-withdrawal-button"
              >
                <ArrowUpFromLine className="w-4 h-4" /> Simulate Withdrawal
              </Button>
              <Button 
                variant="outline"
                className="w-full btn-secondary gap-2 justify-start" 
                onClick={() => { setSimulateActionsOpen(false); setCommissionDialogOpen(true); }}
                data-testid="simulate-commission-button"
              >
                <Award className="w-4 h-4" /> Simulate Commission
              </Button>
              {/* VSD Button - Master Admin Only */}
              {isMasterAdmin() && (
                <Button 
                  variant="outline"
                  className="w-full btn-secondary gap-2 justify-start border-purple-500/50 hover:bg-purple-500/10" 
                  onClick={() => { setSimulateActionsOpen(false); loadVSDData(); setVsdDialogOpen(true); }}
                  data-testid="licensee-vsd-button"
                >
                  <Users className="w-4 h-4 text-purple-400" /> Licensee VSD
                </Button>
              )}
            </div>
          </DialogContent>
        </Dialog>
        
        {/* VSD (Virtual Share Distribution) Dialog - Master Admin Only */}
        {isMasterAdmin() && (
          <VSDDialog 
            open={vsdDialogOpen} 
            onOpenChange={setVsdDialogOpen} 
            vsdData={vsdData} 
            loading={vsdLoading} 
          />
        )}
        
        {/* Simulate Deposit Dialog - Now triggered from popup */}
        <Dialog open={depositDialogOpen} onOpenChange={(open) => { if (!open) resetDepositDialog(); else setDepositDialogOpen(true); }}>
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
                {!manualDepositMode ? (
                  <>
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
                      <p className="text-xs text-zinc-500 mt-1">Amount you&apos;re sending from Binance</p>
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
                    <button 
                      onClick={() => setManualDepositMode(true)}
                      className="w-full text-center text-sm text-zinc-500 hover:text-blue-400 underline transition-colors"
                      data-testid="manual-deposit-link"
                    >
                      Wrong Calculations? Enter your total deposit manually
                    </button>
                  </>
                ) : (
                  <>
                    <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                      <p className="text-sm text-blue-400">Manual Override Mode</p>
                      <p className="text-xs text-zinc-400 mt-1">Enter the exact amount that will be added to your Merin balance.</p>
                    </div>
                    <div>
                      <Label className="text-zinc-300">Total Deposit Amount (USDT)</Label>
                      <div className="relative mt-1">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                        <Input
                          type="number"
                          value={manualDepositAmount}
                          onChange={(e) => setManualDepositAmount(e.target.value)}
                          placeholder="0.00"
                          className="input-dark pl-7"
                          data-testid="manual-deposit-amount-input"
                        />
                      </div>
                      <p className="text-xs text-zinc-500 mt-1">This exact amount will be added to your balance (no fee calculations)</p>
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
                    <Button 
                      onClick={() => {
                        if (!manualDepositAmount || parseFloat(manualDepositAmount) <= 0) {
                          toast.error('Please enter a valid amount');
                          return;
                        }
                        setDepositSimulation({
                          binanceAmount: parseFloat(manualDepositAmount),
                          depositFee: 0,
                          receiveAmount: parseFloat(manualDepositAmount),
                          isManualOverride: true
                        });
                        setDepositStep('simulate');
                      }} 
                      className="w-full btn-primary" 
                      data-testid="manual-deposit-button"
                    >
                      <CheckCircle2 className="w-4 h-4 mr-2" /> Confirm Amount
                    </Button>
                    <button 
                      onClick={() => setManualDepositMode(false)}
                      className="w-full text-center text-sm text-zinc-500 hover:text-blue-400 underline transition-colors"
                    >
                      Back to automatic calculation
                    </button>
                  </>
                )}
              </div>
            )}

            {depositStep === 'simulate' && depositSimulation && (
              <div className="space-y-4 mt-4">
                <div className="space-y-3 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  {depositSimulation.isManualOverride ? (
                    <>
                      <div className="p-2 rounded bg-blue-500/10 border border-blue-500/30 mb-3">
                        <p className="text-xs text-blue-400 text-center">Manual Override - No fees applied</p>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-300 font-medium">Deposit Amount</span>
                        <span className="font-mono font-bold text-emerald-400">{formatMoney(depositSimulation.receiveAmount)}</span>
                      </div>
                    </>
                  ) : (
                    <>
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
                    </>
                  )}
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
                        By proceeding, you&apos;re confirming that you&apos;re adding <span className="text-white font-mono">{formatMoney(depositSimulation?.receiveAmount)}</span> to your Merin Account.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setDepositStep('simulate')}>
                    No, I&apos;m just thinking
                  </Button>
                  <Button onClick={handleConfirmDeposit} className="flex-1 btn-primary" data-testid="confirm-deposit-button">
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Yes, I confirm
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Withdrawal Dialog - Now triggered from popup */}
        <Dialog open={withdrawalDialogOpen} onOpenChange={(open) => { if (!open) resetWithdrawalDialog(); else setWithdrawalDialogOpen(true); }}>
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
                        By proceeding, you&apos;re confirming that you&apos;re withdrawing <span className="text-white font-mono">{formatMoney(parseFloat(withdrawalAmount))}</span> from your Merin Account.
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

        {/* Commission Dialog - Now triggered from popup */}
        <Dialog open={commissionDialogOpen} onOpenChange={(open) => { if (!open) resetCommissionDialog(); else setCommissionDialogOpen(true); }}>
          <DialogContent className="glass-card border-zinc-800 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <Award className="w-5 h-5 text-purple-400" /> Simulate Commission
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 mt-4">
              <p className="text-sm text-zinc-400">
                Record commission earnings from your referrals&apos; trades.
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

        {/* Access Records and Reset Buttons - Side by side on mobile, full width together */}
        <div className="flex gap-2 w-full md:w-auto md:ml-auto">
          {/* Access Records Button - Combined Popup */}
          <Dialog open={accessRecordsOpen} onOpenChange={setAccessRecordsOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="btn-secondary gap-2 flex-1 md:flex-none" data-testid="access-records-button">
                <FolderOpen className="w-4 h-4" /> <span className="hidden sm:inline">Access </span>Records
              </Button>
            </DialogTrigger>
            <DialogContent className="glass-card border-zinc-800 max-w-sm">
              <DialogHeader>
                <DialogTitle className="text-white flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-blue-400" /> Access Records
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-3 mt-4">
                <Button 
                  variant="outline" 
                  className="w-full btn-secondary gap-2 justify-start" 
                  onClick={() => { setAccessRecordsOpen(false); setDepositRecordsOpen(true); }}
                  data-testid="view-deposits-button"
                >
                  <FileText className="w-4 h-4 text-emerald-400" /> Deposit Records
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full btn-secondary gap-2 justify-start" 
                  onClick={() => { setAccessRecordsOpen(false); setWithdrawalRecordsOpen(true); }}
                  data-testid="view-withdrawals-button"
                >
                  <Receipt className="w-4 h-4 text-amber-400" /> Withdrawal Records
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full btn-secondary gap-2 justify-start" 
                  onClick={() => { setAccessRecordsOpen(false); setCommissionRecordsOpen(true); }}
                  data-testid="view-commissions-button"
                >
                  <Award className="w-4 h-4 text-purple-400" /> Commission Records
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          {/* Reset Button */}
          <Dialog open={resetDialogOpen} onOpenChange={(open) => { if (!open) resetResetDialog(); else setResetDialogOpen(true); }}>
            <DialogTrigger asChild>
              <Button variant="outline" className="btn-secondary gap-2 text-amber-400 hover:text-amber-300 flex-1 md:flex-none" data-testid="reset-tracker-button">
                <RotateCcw className="w-4 h-4" /> Reset<span className="hidden sm:inline"> Tracker</span>
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

            {resetStep === 'password' && (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                  <div className="flex items-start gap-3">
                    <Lock className="w-5 h-5 text-amber-400 mt-0.5" />
                    <div>
                      <p className="text-amber-400 font-medium">Security Verification Required</p>
                      <p className="text-sm text-zinc-400 mt-1">
                        Please enter your password to confirm the reset. You&apos;ll be guided through setting up your new tracker.
                      </p>
                    </div>
                  </div>
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
                  <Button variant="outline" className="flex-1" onClick={() => setResetStep('confirm')}>
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

      {/* Onboarding Wizard */}
      <OnboardingWizard
        isOpen={onboardingWizardOpen}
        onClose={() => setOnboardingWizardOpen(false)}
        onComplete={(data) => {
          setOnboardingWizardOpen(false);
          setIsFirstTime(false);
          loadData(); // Reload data after onboarding
          toast.success('Your profit tracker is ready!');
        }}
        isReset={isResetOnboarding}
      />

      {/* Legacy Initial Balance Dialog - kept for backwards compatibility */}
      <Dialog open={initialBalanceDialogOpen} onOpenChange={setInitialBalanceDialogOpen}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Rocket className="w-5 h-5 text-blue-400" /> Welcome to Profit Tracker!
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-zinc-400">
              Let&apos;s get started by setting your current Merin Trading Platform balance. 
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
              <p className="text-xs text-zinc-500 mt-1">Enter 0 if you haven&apos;t deposited yet</p>
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
                      <td className="font-mono text-emerald-400">{formatMoney(w.net_amount || (Math.abs(w.amount) * 0.97))}</td>
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

      {/* Commission Records Dialog */}
      <Dialog open={commissionRecordsOpen} onOpenChange={setCommissionRecordsOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-400" /> Commission Records
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4 max-h-[400px] overflow-y-auto">
            {commissions.length > 0 ? (
              <table className="w-full data-table text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr>
                    <th>Date</th>
                    <th>Amount (USDT)</th>
                    <th>Traders</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {commissions.map((c) => (
                    <tr key={c.id}>
                      <td className="font-mono">{new Date(c.created_at).toLocaleDateString()}</td>
                      <td className="font-mono text-purple-400">+{formatMoney(c.amount)}</td>
                      <td className="font-mono text-zinc-400">{c.traders_count}</td>
                      <td className="text-zinc-500 max-w-[200px] truncate">{c.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                No commissions recorded yet.
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Projection Vision Card */}
      <Card className="glass-highlight border-blue-500/30">
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3">
          <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
            <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400" /> Projection Vision
          </CardTitle>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              variant={projectionView === 'summary' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setProjectionView('summary')}
              className={`flex-1 sm:flex-none text-xs sm:text-sm ${projectionView === 'summary' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Summary
            </Button>
            <Button
              variant={projectionView === 'table' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setProjectionView('table')}
              className={`flex-1 sm:flex-none text-xs sm:text-sm ${projectionView === 'table' ? 'btn-primary' : 'btn-secondary'}`}
            >
              <Eye className="w-3 h-3 sm:w-4 sm:h-4 mr-1" /> Monthly Table
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-3 sm:p-6">
          {projectionView === 'summary' ? (
            <div className="space-y-4 sm:space-y-6">
              {/* Current Stats - Mobile optimized */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4 p-3 sm:p-4 rounded-lg bg-zinc-900/50">
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">Current Balance</p>
                  <p className="font-mono text-sm sm:text-lg text-white truncate">{formatLargeNumber(effectiveAccountValue)}</p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">LOT Size</p>
                  <p className="font-mono text-sm sm:text-lg text-purple-400">{effectiveLotSize.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">Daily Profit</p>
                  <p className="font-mono text-sm sm:text-lg text-emerald-400 truncate">{formatMoney(effectiveLotSize * 15)}</p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">Formula</p>
                  <p className="text-xs sm:text-sm text-zinc-400">Bal ÷ 980 × 15</p>
                </div>
              </div>

              {/* Projection Chart - Mobile optimized height */}
              <div className="h-[180px] sm:h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={projectionChartData}>
                    <defs>
                      <linearGradient id="colorProjection" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                    <XAxis dataKey="name" stroke="#71717A" fontSize={10} tickMargin={5} />
                    <YAxis 
                      stroke="#71717A" 
                      fontSize={10} 
                      width={45}
                      tickFormatter={(v) => {
                        if (v >= 1e12) return `$${(v/1e12).toFixed(1)}T`;
                        if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`;
                        if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
                        if (v >= 1e3) return `$${(v/1e3).toFixed(0)}k`;
                        return `$${v.toFixed(0)}`;
                      }}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px', fontSize: '12px' }}
                      formatter={(value) => [formatLargeNumber(value), 'Projected Balance']}
                    />
                    <Line type="monotone" dataKey="balance" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6', r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Projection Grid - Mobile optimized */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4">
                {projectionData.slice(1, 4).map((p, i) => (
                  <div key={p.period} className={`p-2 sm:p-4 rounded-lg border ${i === 0 ? 'bg-blue-500/10 border-blue-500/30' : 'bg-zinc-900/50 border-zinc-800'}`}>
                    <p className={`text-[10px] sm:text-xs ${i === 0 ? 'text-blue-400' : 'text-zinc-500'}`}>{p.period}</p>
                    <p className={`font-mono text-sm sm:text-lg ${i === 0 ? 'text-blue-400' : 'text-white'} mt-0.5 sm:mt-1 truncate`}>
                      {formatLargeNumber(p.balance)}
                    </p>
                    <p className="text-[9px] sm:text-xs text-zinc-500 mt-0.5 sm:mt-1 truncate">
                      LOT: {truncateTo2Decimals(p.lotSize).toFixed(2)}
                    </p>
                  </div>
                ))}
                
                {/* Year selector card */}
                <div className="p-2 sm:p-4 rounded-lg border bg-gradient-to-br from-purple-500/10 to-blue-500/10 border-purple-500/30">
                  <div className="flex items-center justify-between mb-1 sm:mb-2">
                    <p className="text-[10px] sm:text-xs text-purple-400">Year</p>
                    <Select value={selectedYears.toString()} onValueChange={(v) => setSelectedYears(parseInt(v))}>
                      <SelectTrigger className="w-14 sm:w-20 h-5 sm:h-6 text-[10px] sm:text-xs bg-zinc-900/50 border-zinc-700">
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
                  <p className="font-mono text-sm sm:text-lg text-purple-400 mt-0.5 sm:mt-1 truncate">
                    {formatLargeNumber(projectionData[4]?.balance || 0)}
                  </p>
                  <p className="text-[9px] sm:text-xs text-zinc-500 mt-0.5 sm:mt-1 truncate">
                    LOT: {truncateTo2Decimals(projectionData[4]?.lotSize || 0).toFixed(2)}
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
                  {Object.entries(yearlyGroupedProjection).map(([yearKey, months]) => (
                    <AccordionItem 
                      key={yearKey} 
                      value={`year-${yearKey}`}
                      className="border border-zinc-800 rounded-lg overflow-hidden"
                    >
                      <AccordionTrigger className="px-4 py-3 bg-zinc-900/50 hover:bg-zinc-900 text-white">
                        <div className="flex items-center justify-between w-full pr-4">
                          <span className="font-medium">
                            {yearKey === 'History' ? (
                              <span className="text-amber-400">📜 History</span>
                            ) : yearKey}
                          </span>
                          <span className="font-mono text-emerald-400">
                            {months[0]?.isPastMonth 
                              ? `${months.length} month${months.length > 1 ? 's' : ''} with data`
                              : formatLargeNumber(months[months.length - 1]?.endBalance || 0)
                            }
                          </span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="bg-zinc-950/50">
                        <table className="w-full data-table text-sm">
                          <thead>
                            <tr>
                              <th>Month</th>
                              <th>{months[0]?.isPastMonth ? 'Trades' : 'Trading Days'}</th>
                              <th>{months[0]?.isPastMonth ? 'Total Profit' : 'Final Balance'}</th>
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
                                <td className="font-mono text-zinc-400">
                                  {m.isPastMonth 
                                    ? `${m.tradesCount || 0} trades`
                                    : `${m.tradingDays} days`
                                  }
                                </td>
                                <td className="font-mono text-white">
                                  {m.isPastMonth 
                                    ? <span className={m.totalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}>{formatLargeNumber(m.totalProfit || 0)}</span>
                                    : formatLargeNumber(m.endBalance)
                                  }
                                </td>
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
                  {getDailyProjectionForSelectedMonth.filter(day => day.actualProfit === undefined && day.status !== 'completed').length} Remaining Days
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
                    {/* Hide LOT Size for licensees - they don't trade */}
                    {!isLicensee && <th>LOT Size</th>}
                    <th>Target Profit</th>
                    {/* For licensees: Show Manager Traded column, hide Actual/Commission/P/L */}
                    {isLicensee ? (
                      <th>Manager Traded</th>
                    ) : (
                      <>
                        <th>Actual Profit</th>
                        <th>Commission</th>
                        <th>P/L Diff</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {getDailyProjectionForSelectedMonth.map((day, idx) => {
                    const plDiff = day.status === 'completed' && day.actualProfit !== undefined 
                      ? day.actualProfit - day.targetProfit 
                      : null;
                    
                    // For licensees: check if master admin traded on this day
                    // First check trade overrides (manual overrides by Master Admin), then fall back to actual trades
                    const hasOverride = tradeOverrides[day.dateKey] !== undefined;
                    const masterTraded = hasOverride 
                      ? tradeOverrides[day.dateKey].traded 
                      : masterAdminTrades[day.dateKey]?.traded;
                    
                    // Check if this date is a global holiday
                    const isGlobalHoliday = globalHolidays.some(h => h.date === day.dateKey);
                    
                    // Determine row styling based on status
                    let rowClass = '';
                    if (isGlobalHoliday) {
                      rowClass = 'bg-emerald-500/10 border-l-2 border-l-emerald-500';
                    } else if (day.isToday) {
                      rowClass = 'bg-blue-500/20 border-l-2 border-l-blue-500';
                    } else if (day.status === 'completed') {
                      rowClass = 'bg-emerald-500/5';
                    } else if (day.status === 'missed') {
                      rowClass = 'bg-zinc-800/30 opacity-75';
                    }
                    
                    // If this is a global holiday, show special HOLIDAY row
                    if (isGlobalHoliday) {
                      return (
                        <tr key={day.dateKey} className={rowClass}>
                          <td className="font-medium">
                            <div className="flex items-center gap-2">
                              <TreePine className="w-4 h-4 text-emerald-400" />
                              {day.dateStr}
                            </div>
                          </td>
                          <td colSpan={isLicensee ? 4 : 6} className="text-center">
                            <span className="text-emerald-400 font-medium flex items-center justify-center gap-2">
                              <TreePine className="w-4 h-4" />
                              HOLIDAY
                              <TreePine className="w-4 h-4" />
                            </span>
                          </td>
                        </tr>
                      );
                    }
                    
                    return (
                      <tr 
                        key={day.dateKey} 
                        className={rowClass}
                      >
                        <td className="font-medium">
                          {day.dateStr}
                          {day.isToday && (
                            <span className="ml-2 text-xs bg-blue-500 text-white px-1.5 py-0.5 rounded">TODAY</span>
                          )}
                          {day.status === 'completed' && !day.isToday && (
                            <span className="ml-2 text-xs bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">✓</span>
                          )}
                          {/* Show indicator for manually adjusted trades */}
                          {!isLicensee && tradeLogs[day.dateKey]?.is_manual_adjustment && (
                            <span className="ml-1 text-xs bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded" title="Manually Adjusted">
                              ✎
                            </span>
                          )}
                        </td>
                        <td className="font-mono text-white">{formatLargeNumber(day.balanceBefore)}</td>
                        <td className="font-mono text-purple-400">{truncateTo2Decimals(day.lotSize).toFixed(2)}</td>
                        
                        {/* Target Profit - For licensees: show "--" if manager didn't trade */}
                        <td className="font-mono text-zinc-400">
                          {isLicensee && day.status !== 'future' && !masterTraded ? (
                            <span className="text-zinc-500">--</span>
                          ) : (
                            formatMoney(day.targetProfit)
                          )}
                        </td>
                        
                        {/* For licensees: Manager Traded column with toggle for Master Admin */}
                        {isLicensee && (
                          <td className="text-center">
                            {day.status === 'future' ? (
                              <span className="text-zinc-500 text-xs">-</span>
                            ) : isMasterAdmin() && simulatedView?.licenseId ? (
                              // Master Admin can toggle trade status when simulating a licensee
                              <div className="flex items-center justify-center gap-2">
                                <Switch
                                  checked={masterTraded || false}
                                  onCheckedChange={() => handleToggleTradeOverride(day.dateKey, masterTraded)}
                                  disabled={togglingTrade === day.dateKey}
                                  className="data-[state=checked]:bg-emerald-500 data-[state=unchecked]:bg-red-500"
                                  data-testid={`trade-toggle-${day.dateKey}`}
                                />
                                {togglingTrade === day.dateKey && (
                                  <Loader2 className="w-3 h-3 animate-spin text-zinc-400" />
                                )}
                              </div>
                            ) : masterTraded ? (
                              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/20" title="Manager traded - profit added">
                                <Check className="w-4 h-4 text-emerald-400" />
                              </span>
                            ) : (
                              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-500/20" title="Manager did not trade - balance carried forward">
                                <X className="w-4 h-4 text-red-400" />
                              </span>
                            )}
                          </td>
                        )}
                        
                        {/* For non-licensees: Actual Profit column */}
                        {!isLicensee && (
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
                            ) : day.status === 'missed' ? (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-6 text-xs border-amber-500/50 text-amber-400 hover:bg-amber-500/20"
                                onClick={() => handleOpenEnterAP(day)}
                                data-testid={`enter-ap-${day.dateKey}`}
                              >
                                <Edit3 className="w-3 h-3 mr-1" /> Adjust Trade
                              </Button>
                            ) : day.status === 'future' ? (
                              <span className="text-zinc-500 text-xs">-</span>
                            ) : day.isToday ? (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-6 text-xs border-amber-500/50 text-amber-400 hover:bg-amber-500/20"
                                onClick={() => handleOpenEnterAP(day)}
                                data-testid={`enter-ap-${day.dateKey}`}
                              >
                                <Edit3 className="w-3 h-3 mr-1" /> Adjust Trade
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-6 text-xs border-amber-500/50 text-amber-400 hover:bg-amber-500/20"
                                onClick={() => handleOpenEnterAP(day)}
                                data-testid={`enter-ap-${day.dateKey}`}
                              >
                                <Edit3 className="w-3 h-3 mr-1" /> Adjust Trade
                              </Button>
                            )}
                          </td>
                        )}
                        
                        {/* Commission column - hidden for licensees */}
                        {!isLicensee && (
                          <td>
                            {day.status === 'completed' && day.commission > 0 ? (
                              <span className="font-mono text-cyan-400">
                                +{formatMoney(day.commission)}
                              </span>
                            ) : day.status === 'completed' ? (
                              <span className="text-zinc-500 text-xs">-</span>
                            ) : (
                              <span className="text-zinc-500 text-xs">-</span>
                            )}
                          </td>
                        )}
                        
                        {/* P/L Diff column - hidden for licensees */}
                        {!isLicensee && (
                          <td>
                            {plDiff !== null ? (
                              <span className={`font-mono ${plDiff >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                {plDiff >= 0 ? '+' : ''}{formatMoney(plDiff)}
                              </span>
                            ) : (
                              <span className="text-zinc-500 text-xs">-</span>
                            )}
                          </td>
                        )}
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
            {isLicensee ? (
              <>
                <p>• <span className="text-emerald-400"><Check className="w-3 h-3 inline" /></span> = Manager traded - profit added to your balance</p>
                <p>• <span className="text-red-400"><X className="w-3 h-3 inline" /></span> = Manager did not trade - balance carried forward (no profit)</p>
                <p>• &quot;--&quot; in Target Profit means no trade was made that day</p>
                {isMasterAdmin() && simulatedView?.licenseId && (
                  <p className="mt-1 text-amber-400">• Toggle switch to override &quot;Manager Traded&quot; status for any day</p>
                )}
              </>
            ) : (
              <>
                <p>• <span className="text-amber-400">Adjust Trade</span> = Click to enter your actual profit for missed trades</p>
                <p>• <span className="text-blue-400">Trade Now</span> = Active signal available</p>
                <p>• Actual profits update your Account Value when recorded</p>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Adjust Trade Dialog - For logging missed trades with deposit/withdrawal options */}
      <Dialog open={enterAPDialogOpen} onOpenChange={setEnterAPDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-amber-400" /> Adjust Trade
            </DialogTitle>
          </DialogHeader>
          {enterAPDate && (
            <div className="space-y-5 py-4">
              <p className="text-zinc-400 text-sm">
                Adjust your trade data for <span className="text-white font-medium">{enterAPDate.dateStr}</span>
              </p>
              
              {/* Current calculated values */}
              <div className="p-3 rounded-lg bg-zinc-900/50 space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Calculated Balance Before</span>
                  <span className="font-mono text-white">{formatLargeNumber(enterAPDate.balanceBefore)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Calculated Lot Size</span>
                  <span className="font-mono text-purple-400">{truncateTo2Decimals(enterAPDate.lotSize).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Target Profit</span>
                  <span className="font-mono text-zinc-400">{formatMoney(enterAPDate.targetProfit)}</span>
                </div>
              </div>

              {/* Adjustment type selection */}
              <div className="space-y-2">
                <Label className="text-zinc-300">Did you deposit or withdraw on this day?</Label>
                <Select value={adjustmentType} onValueChange={setAdjustmentType}>
                  <SelectTrigger className="input-dark">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="profit_only">No, just enter profit</SelectItem>
                    <SelectItem value="with_deposit">Yes, I made a deposit</SelectItem>
                    <SelectItem value="with_withdrawal">Yes, I made a withdrawal</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Deposit/Withdrawal amount */}
              {adjustmentType !== 'profit_only' && (
                <div className="space-y-2">
                  <Label className="text-zinc-300">
                    {adjustmentType === 'with_deposit' ? 'Deposit' : 'Withdrawal'} Amount (USD)
                  </Label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                    <Input
                      type="number"
                      step="0.01"
                      value={adjustmentAmount}
                      onChange={(e) => setAdjustmentAmount(e.target.value)}
                      placeholder="0.00"
                      className="input-dark pl-7 font-mono"
                      data-testid="adjustment-amount-input"
                    />
                  </div>
                </div>
              )}

              {/* Manual balance adjustment */}
              <div className="space-y-2">
                <Label className="text-zinc-300">Adjusted Balance Before Trade (optional)</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={adjustedBalance}
                    onChange={(e) => setAdjustedBalance(e.target.value)}
                    placeholder={enterAPDate.balanceBefore?.toString() || '0'}
                    className="input-dark pl-7 font-mono"
                    data-testid="adjusted-balance-input"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  If the calculated balance is incorrect, enter the actual balance you had before this trade
                </p>
              </div>

              {/* Actual profit input */}
              <div className="space-y-2">
                <Label className="text-zinc-300">Actual Profit (USD)</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={enterAPValue}
                    onChange={(e) => setEnterAPValue(e.target.value)}
                    placeholder="Enter your actual profit"
                    className="input-dark pl-7 text-lg font-mono"
                    data-testid="enter-ap-input"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  Enter positive for profit, negative for loss
                </p>
              </div>

              {/* Summary of adjustments */}
              {(enterAPValue || adjustmentAmount || adjustedBalance) && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-2 text-sm">
                  <p className="text-amber-400 font-medium">Adjustment Summary:</p>
                  {adjustedBalance && adjustedBalance !== enterAPDate.balanceBefore?.toString() && (
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">New Balance Before</span>
                      <span className="font-mono text-white">${parseFloat(adjustedBalance).toLocaleString()}</span>
                    </div>
                  )}
                  {adjustmentType !== 'profit_only' && adjustmentAmount && (
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">{adjustmentType === 'with_deposit' ? 'Deposit' : 'Withdrawal'}</span>
                      <span className={`font-mono ${adjustmentType === 'with_deposit' ? 'text-emerald-400' : 'text-red-400'}`}>
                        {adjustmentType === 'with_deposit' ? '+' : '-'}${parseFloat(adjustmentAmount).toLocaleString()}
                      </span>
                    </div>
                  )}
                  {enterAPValue && (
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">Actual Profit</span>
                      <span className={`font-mono ${parseFloat(enterAPValue) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {parseFloat(enterAPValue) >= 0 ? '+' : ''}${parseFloat(enterAPValue).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <Button 
                  variant="outline" 
                  className="flex-1 btn-secondary"
                  onClick={() => setEnterAPDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button 
                  className="flex-1 btn-primary"
                  onClick={handleSubmitEnterAP}
                  disabled={enterAPLoading || !enterAPValue}
                  data-testid="submit-enter-ap"
                >
                  {enterAPLoading ? 'Saving...' : 'Save Adjustment'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
