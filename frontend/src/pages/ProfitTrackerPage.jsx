import React, { useState, useEffect, useMemo } from 'react';
import api, { profitAPI, currencyAPI, adminAPI, tradeAPI } from '@/lib/api';
import BalanceAuditTrail, { BalanceAuditModal } from '@/components/BalanceAuditTrail';
import MyTransactionEdit from '@/components/MyTransactionEdit';
import { DailyProjectionDialog } from '@/components/profit/DailyProjectionDialog';
import { StatsCards } from '@/components/profit/StatsCards';
import { AdminActionsPanel } from '@/components/profit/AdminActionsPanel';
import { formatNumber, calculateWithdrawalFees, calculateDepositFees } from '@/lib/utils';
import {
  truncateTo2Decimals, formatFullCurrency, formatLargeNumber, formatCompact,
  MASKED_VALUE, maskAmount, formatMoney, addBusinessDays, isHoliday, isTradingDay,
  generateDailyProjectionForMonth, generateMonthlyProjection, groupMonthsByYear,
  generateProjectionData
} from '@/utils/profitCalculations';
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
import { Tooltip as ShadcnTooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { LicenseeWelcomeScreen } from '@/components/LicenseeWelcomeScreen';
import { AIFinancialSummary, AIBalanceForecast, AICommissionInsights } from '@/components/AIFeatures';
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
import { PreSyncWizard } from '@/components/PreSyncWizard';
import { DataHealthBadge } from '@/components/DataHealthBadge';
import { DepositRecordsDialog, WithdrawalRecordsDialog, CommissionRecordsDialog } from '@/components/TransactionRecords';
import { TransactionStepper } from '@/components/TransactionStepper';

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


export const ProfitTrackerPage = () => {
  const { 
    user, 
    simulatedView, 
    getSimulatedAccountValue, 
    getSimulatedLotSize, 
    getSimulatedTotalDeposits,
    getSimulatedTotalProfit,
    getSimulatedMemberName,
    isMasterAdmin,
    refreshUser
  } = useAuth();
  const [summary, setSummary] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [withdrawals, setWithdrawals] = useState([]);
  const [tradeLogs, setTradeLogs] = useState({});
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeSignal, setActiveSignal] = useState(null);
  
  // Hide/Show financial amounts toggle - per-card control
  const [hiddenCards, setHiddenCards] = useState({
    accountValue: false,
    deposits: false,
    profit: false,
    lotSize: false,
    growth: false
  });
  
  const toggleCardVisibility = (cardKey) => {
    setHiddenCards(prev => ({ ...prev, [cardKey]: !prev[cardKey] }));
  };
  
  // Simulation values
  const simulatedAccountValue = getSimulatedAccountValue();
  const simulatedLotSize = getSimulatedLotSize();
  const simulatedTotalDeposits = getSimulatedTotalDeposits();
  const simulatedTotalProfit = getSimulatedTotalProfit();
  const simulatedMemberName = getSimulatedMemberName();
  
  // Effective values - always prefer fetched summary (API-sourced, dynamic) over stale simulation context
  const effectiveAccountValue = summary?.account_value 
    ? summary.account_value 
    : (simulatedAccountValue !== null ? simulatedAccountValue : 0);
  const effectiveLotSize = truncateTo2Decimals(effectiveAccountValue / 980);
  const effectiveTotalDeposits = summary?.total_deposits 
    ? summary.total_deposits
    : (simulatedTotalDeposits !== null ? simulatedTotalDeposits : 0);
  const effectiveTotalProfit = summary?.total_actual_profit != null
    ? summary.total_actual_profit
    : (simulatedTotalProfit !== null ? simulatedTotalProfit : 0);
  
  // Mobile detection for responsive dialogs
  const isMobile = useIsMobile();
  
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
  
  // Balance Override states
  const [balanceVerificationOpen, setBalanceVerificationOpen] = useState(false);
  const [calculatedBalance, setCalculatedBalance] = useState(0);
  const [actualBalanceInput, setActualBalanceInput] = useState('');
  const [balanceOverrideLoading, setBalanceOverrideLoading] = useState(false);
  
  // Pre-Sync Validation Wizard states
  const [syncWizardOpen, setSyncWizardOpen] = useState(false);
  const [syncWizardStep, setSyncWizardStep] = useState(1); // 1: Start Date, 2: Missing Days, 3: Pre-Start Warning, 4: Sync
  const [syncValidation, setSyncValidation] = useState(null);
  const [syncValidationLoading, setSyncValidationLoading] = useState(false);
  const [newStartDate, setNewStartDate] = useState('');
  const [preStartAcknowledged, setPreStartAcknowledged] = useState(false);
  
  // Data Health Score
  const [dataHealth, setDataHealth] = useState(null);
  
  // Backend-calculated daily balances (authoritative source for historical months)
  const [backendDailyBalances, setBackendDailyBalances] = useState({});
  const [backendBalancesLoading, setBackendBalancesLoading] = useState(false);
  
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
  const [enterAPCommission, setEnterAPCommission] = useState(''); // Commission for the day
  const [enterAPLoading, setEnterAPLoading] = useState(false);
  
  // Adjustment options for past trades
  const [adjustmentType, setAdjustmentType] = useState('profit_only'); // 'profit_only', 'with_deposit', 'with_withdrawal'
  const [adjustmentAmount, setAdjustmentAmount] = useState(''); // deposit/withdrawal amount
  const [adjustedBalance, setAdjustedBalance] = useState(''); // manually adjusted balance before trade
  
  // Adjust Commission Dialog states
  const [adjustCommissionOpen, setAdjustCommissionOpen] = useState(false);
  const [adjustCommissionDate, setAdjustCommissionDate] = useState(null);
  const [adjustCommissionAmount, setAdjustCommissionAmount] = useState('');
  const [adjustCommissionLoading, setAdjustCommissionLoading] = useState(false);
  const [adjustCommissionSkipDeposit, setAdjustCommissionSkipDeposit] = useState(false);
  
  // Access Records Dialog (combined deposit, withdrawal, commission records)
  const [accessRecordsOpen, setAccessRecordsOpen] = useState(false);
  const [activeRecordTab, setActiveRecordTab] = useState('deposits');
  
  // Commission Dialog states
  const [commissionDialogOpen, setCommissionDialogOpen] = useState(false);
  const [commissionStep, setCommissionStep] = useState('input');
  const [commissionAmount, setCommissionAmount] = useState('');
  const [commissionTradersCount, setCommissionTradersCount] = useState('');
  const [commissionNotes, setCommissionNotes] = useState('');
  const [commissionDate, setCommissionDate] = useState(new Date().toISOString().split('T')[0]);
  const [commissions, setCommissions] = useState([]);
  
  // Dream Daily Profit Dialog states
  const [dreamProfitDialogOpen, setDreamProfitDialogOpen] = useState(false);
  const [dreamDailyProfit, setDreamDailyProfit] = useState('');
  
  // Simulate Actions Dialog (combined simulate deposit, withdrawal, commission)
  const [simulateActionsOpen, setSimulateActionsOpen] = useState(false);
  const [auditTrailModalOpen, setAuditTrailModalOpen] = useState(false);
  
  // Simulate Error Dialog
  const [errorDialogOpen, setErrorDialogOpen] = useState(false);
  const [errorType, setErrorType] = useState('');
  const [errorExplanation, setErrorExplanation] = useState('');
  const [errorProfit, setErrorProfit] = useState('');
  const [errorProduct, setErrorProduct] = useState('MOIL10');
  const [errorDirection, setErrorDirection] = useState('BUY');
  const [errorDate, setErrorDate] = useState(new Date().toISOString().split('T')[0]);
  const [submittingError, setSubmittingError] = useState(false);
  
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
  const [resetNewBalance, setResetNewBalance] = useState('');
  
  // Manual deposit override
  const [manualDepositMode, setManualDepositMode] = useState(false);
  const [manualDepositAmount, setManualDepositAmount] = useState('');
  
  // Check if user is a licensee (hide simulation/record buttons)
  const isLicensee = simulatedView?.license_type || user?.license_type;
  const isExtendedLicensee = (simulatedView?.license_type || user?.license_type) === 'extended';
  const isHonoraryLicensee = ['honorary', 'honorary_fa'].includes(simulatedView?.license_type || user?.license_type);
  
  // Master admin trades for extended licensees (profit credited tracking)
  const [masterAdminTrades, setMasterAdminTrades] = useState({});
  
  // License projections for extended licensees (fixed lot size and daily profit per quarter)
  const [licenseProjections, setLicenseProjections] = useState([]);
  
  // Trade overrides for licensees (per-licensee, per-date manual toggles by Master Admin)
  const [tradeOverrides, setTradeOverrides] = useState({});
  const [togglingTrade, setTogglingTrade] = useState(null); // Track which date is being toggled
  
  // Get effective start date for filtering past dates
  // Priority: 1) Simulated view's effective_start_date (for licensee simulation)
  //           2) Simulated view's trading_start_date (for simulating "new trader" members)
  //           3) Welcome info start date (for direct licensee login)
  //           4) First licensee projection date (for direct licensee login fallback)
  //           5) User's trading_start_date (for users who reset as "new trader")
  // This ensures users who reset as "new trader" don't see dates before their reset
  const licenseeStartFromProjections = licenseeProjections.length > 0 ? licenseeProjections[0]?.date : null;
  const effectiveStartDate = simulatedView?.effective_start_date 
    || (simulatedView?.trading_type === 'new' ? simulatedView?.trading_start_date : null)
    || (licenseeWelcomeInfo?.effective_start_date)
    || licenseeStartFromProjections
    || (user?.trading_type === 'new' ? user?.trading_start_date : null)
    || null;
  
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
    // Clear backend balance cache when simulation changes (to fetch fresh data)
    setBackendDailyBalances({});
    // Fetch data health in background (non-licensee, non-simulated)
    if (!simulatedView && !user?.license_type) {
      api.get('/profit/sync-validation').then(r => setDataHealth(r.data)).catch(() => {});
    }
  }, [simulatedView]);

  const checkLicenseeWelcome = async () => {
    // Only check for actual licensees (not simulated views)
    if (simulatedView || !user?.license_type) return;
    
    try {
      const response = await profitAPI.getLicenseeWelcomeInfo();
      // Always store the welcome info (needed for effective_start_date)
      if (response.data.is_licensee) {
        setLicenseeWelcomeInfo(response.data);
        if (!response.data.has_seen_welcome) {
          setShowLicenseeWelcome(true);
        }
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
        const isLicenseeSimulation = simulatedView.licenseId && simulatedView.license_type;
        
        // Build API calls - add licensee projections if simulating a licensee
        const apiCalls = [
          adminAPI.getMemberDetails(memberId),
          currencyAPI.getRates('USDT'),
          api.get('/trade/active-signal').catch(() => ({ data: null })),
          api.get(`/trade/logs?user_id=${memberId}`).catch(() => ({ data: [] })),
          api.get(`/admin/members/${memberId}/deposits`).catch(() => ({ data: [] })),
          api.get(`/admin/members/${memberId}/withdrawals`).catch(() => ({ data: [] })),
        ];
        
        // If simulating a licensee, also load their projections and Master Admin trades
        if (isLicenseeSimulation) {
          apiCalls.push(
            profitAPI.getLicenseeProjectionsForLicense(simulatedView.licenseId).catch(() => ({ data: { projections: [] } })),
            profitAPI.getMasterAdminTrades().catch(() => ({ data: [] }))
          );
        }
        
        const results = await Promise.all(apiCalls);
        const [memberRes, ratesRes, signalRes, memberTradeLogsRes, memberDepositsRes, memberWithdrawalsRes] = results;
        
        const stats = memberRes.data.stats || {};
        setSummary({
          account_value: stats.account_value || 0,
          total_deposits: stats.total_deposits || 0,
          total_profit: stats.total_profit || 0,
          total_actual_profit: stats.total_actual_profit || 0,
          current_lot_size: memberRes.data.user?.lot_size || 0.01
        });
        setDeposits((memberDepositsRes.data || memberRes.data.recent_deposits || []).filter(d => d.type !== 'profit'));
        setWithdrawals(memberWithdrawalsRes.data || []);
        
        // For licensees, use the projections from the dedicated endpoint
        if (isLicenseeSimulation && results[6]?.data?.projections) {
          setLicenseeProjections(results[6].data.projections);
          
          // Also set Master Admin trades for the Manager Traded column
          const masterTrades = results[7]?.data || [];
          const masterTradesMap = {};
          masterTrades.forEach(trade => {
            const dateKey = trade.trade_date || trade.created_at?.split('T')[0] || '';
            if (dateKey) {
              masterTradesMap[dateKey] = {
                traded: trade.has_traded !== false,
                actual_profit: trade.actual_profit,
                commission: trade.commission || 0
              };
            }
          });
          setMasterAdminTrades(masterTradesMap);
        }
        
        // Process trade logs to get the date-keyed format (for non-licensees)
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
              commission: trade.commission || 0,
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
      
      const [summaryRes, depositsRes, ratesRes, withdrawalsRes, signalRes, tradeLogsRes, commissionsRes, holidaysRes] = await Promise.all([
        profitAPI.getSummary(),
        profitAPI.getDeposits(),
        currencyAPI.getRates('USDT'),
        api.get('/profit/withdrawals').catch(() => ({ data: [] })),
        api.get('/trade/active-signal').catch(() => ({ data: null })),
        api.get('/trade/logs').catch(() => ({ data: [] })),
        api.get('/profit/commissions').catch(() => ({ data: [] })),
        tradeAPI.getGlobalHolidays().catch(() => ({ data: { holidays: [] } })),
      ]);
      // Update global holidays state from the same load cycle
      const loadedHolidays = holidaysRes.data?.holidays || [];
      setGlobalHolidays(loadedHolidays);
      const holidayDateSet = new Set(loadedHolidays.map(h => h.date));
      
      setSummary(summaryRes.data);
      
      // Separate deposits and withdrawals
      // CRITICAL FIX: Exclude type=profit entries to prevent double-counting
      // (profits are already tracked in trade_logs)
      const allDeposits = depositsRes.data || [];
      const onlyDeposits = allDeposits.filter(d => d.amount >= 0 && d.type !== 'profit');
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
      
      // Merge standalone commissions into tradeLogs so they appear in the daily projection table
      const commissionsData = commissionsRes.data || [];
      commissionsData.forEach(c => {
        let dateKey = c.commission_date || c.created_at?.split('T')[0];
        if (dateKey) {
          // Shift non-trading day commissions to the nearest previous trading day
          const d = new Date(dateKey + 'T12:00:00');
          let maxShifts = 7; // Safety limit
          while (maxShifts > 0) {
            const dow = d.getDay();
            const dk = d.toISOString().split('T')[0];
            if (dow !== 0 && dow !== 6 && !holidayDateSet.has(dk)) break;
            d.setDate(d.getDate() - 1);
            maxShifts--;
          }
          dateKey = d.toISOString().split('T')[0];
          const isHistorical = c.skip_deposit === true;
          
          if (logsMap[dateKey]) {
            logsMap[dateKey].commission = (logsMap[dateKey].commission || 0) + (c.amount || 0);
            if (!isHistorical) {
              logsMap[dateKey].balance_commission = (logsMap[dateKey].balance_commission || 0) + (c.amount || 0);
            }
          } else {
            logsMap[dateKey] = {
              actual_profit: 0,
              has_traded: false,
              commission: c.amount || 0,
              balance_commission: isHistorical ? 0 : (c.amount || 0),
            };
          }
        }
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

  // Open daily projection for a month and fetch backend balances
  const handleOpenDailyProjection = async (month) => {
    setSelectedMonth(month);
    setDailyProjectionOpen(true);
    
    // Fetch authoritative daily balances from backend for historical accuracy
    const year = month.monthDate.getFullYear();
    const monthNum = month.monthDate.getMonth() + 1;
    const startDate = `${year}-${String(monthNum).padStart(2, '0')}-01`;
    const lastDay = new Date(year, monthNum, 0).getDate();
    const endDate = `${year}-${String(monthNum).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
    
    // Cache key for this month
    const cacheKey = `${year}-${monthNum}`;
    
    // Skip if already cached
    if (backendDailyBalances[cacheKey]) return;
    
    try {
      setBackendBalancesLoading(true);
      // CRITICAL FIX: Use memberId, not userId, for simulated members
      const userId = simulatedView?.memberId || null;
      const response = await profitAPI.getDailyBalances(startDate, endDate, userId);
      
      if (response.data?.daily_balances) {
        // Convert array to date-keyed map for quick lookup
        const balanceMap = {};
        response.data.daily_balances.forEach(b => {
          balanceMap[b.date] = b;
        });
        
        setBackendDailyBalances(prev => ({
          ...prev,
          [cacheKey]: balanceMap
        }));
      }
    } catch (error) {
      console.error('Failed to fetch backend daily balances:', error);
    } finally {
      setBackendBalancesLoading(false);
    }
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
    // Note: licenseeProjections (from simulation) takes precedence over licenseProjections (from user profile)
    const activeProjections = licenseeProjections.length > 0 ? licenseeProjections : licenseProjections;
    if (isLicensee && activeProjections.length > 0) {
      // Filter projections for selected month
      const monthKey = `${selectedMonth.monthDate.getFullYear()}-${String(selectedMonth.monthDate.getMonth() + 1).padStart(2, '0')}`;
      let monthProjections = activeProjections.filter(p => p.date.startsWith(monthKey));
      
      // Filter by effective start date if set
      if (effectiveStartDate) {
        monthProjections = monthProjections.filter(p => p.date >= effectiveStartDate);
      }
      
      if (monthProjections.length === 0) return [];
      
      // For licensees: Use backend's quarterly compounding values as the base,
      // BUT recalculate when there are local overrides that differ from backend
      
      // First, check if any overrides differ from backend's manager_traded
      const hasOverrideDifferences = monthProjections.some(p => {
        const override = tradeOverrides[p.date];
        if (override !== undefined) {
          return override.traded !== p.manager_traded;
        }
        return false;
      });
      
      // Track running balance (starting from first projection's start_value)
      let runningBalance = monthProjections[0]?.start_value || effectiveAccountValue;
      
      // Track accumulated profit for this month (for Current Profit display)
      let accumulatedProfit = 0;
      
      return monthProjections.map((p, idx) => {
        const projDate = new Date(p.date + 'T00:00:00'); // Ensure local date parsing
        const isToday = projDate.toDateString() === today.toDateString();
        const isFuture = projDate > today;
        const isPast = projDate < today;
        
        // Check trade override first, then fall back to backend's manager_traded
        const hasOverride = tradeOverrides[p.date] !== undefined;
        let masterTraded;
        if (hasOverride) {
          masterTraded = tradeOverrides[p.date].traded;
        } else if (isLicensee && p.manager_traded !== undefined) {
          masterTraded = p.manager_traded;
        } else {
          masterTraded = masterAdminTrades[p.date]?.traded;
        }
        
        // Determine status based on masterTraded (including overrides)
        let status = 'pending';
        if (isPast && masterTraded) {
          status = 'completed';
        } else if (isPast && !masterTraded) {
          status = 'missed';
        } else if (isToday) {
          status = masterTraded ? 'completed' : 'pending';
        } else if (isFuture) {
          status = 'future';
        }
        
        // Determine balance before for this day
        // If no override differences, use backend's pre-calculated start_value
        // If there are override differences, recalculate from running balance
        let balanceBefore;
        if (hasOverrideDifferences) {
          // Recalculate: use running balance which accounts for overrides
          balanceBefore = runningBalance;
        } else {
          // No overrides differ: use backend's pre-calculated value (most accurate)
          balanceBefore = p.start_value;
          // Also sync runningBalance for consistency
          runningBalance = p.start_value;
        }
        
        // Daily profit from backend
        const dailyProfit = p.daily_profit;
        
        // Track accumulated profit from trading days
        if ((isPast || isToday) && masterTraded) {
          accumulatedProfit += dailyProfit;
        }
        
        // Update running balance for next day's calculation
        // Add profit only if manager traded (or if today and traded, or future for projection)
        if (hasOverrideDifferences) {
          if ((isPast || (isToday && masterTraded)) && masterTraded) {
            runningBalance = balanceBefore + dailyProfit;
          } else if (isFuture) {
            // For future: assume trading will happen (optimistic projection)
            runningBalance = balanceBefore + dailyProfit;
          }
          // If didn't trade on past day, balance stays same (carry forward)
        } else {
          // When using backend values, let the next iteration pick up from backend's start_value
          // But we still need to track running balance for the case when next day has override
          if (idx < monthProjections.length - 1) {
            runningBalance = monthProjections[idx + 1]?.start_value || (balanceBefore + (masterTraded ? dailyProfit : 0));
          }
        }
        
        return {
          date: projDate,
          dateStr: projDate.toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
          }),
          dateKey: p.date,
          balanceBefore: balanceBefore,
          lotSize: p.lot_size,
          targetProfit: masterTraded || isFuture ? dailyProfit : 0,
          actualProfit: (isPast || isToday) && masterTraded ? dailyProfit : undefined,
          status: status,
          isToday: isToday,
          managerTraded: masterTraded,
          hasOverride: hasOverride,
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
      // For past months, calculate starting balance by working backwards from current balance
      // The inner generateDailyProjectionForMonth will handle the day-by-day calculations
      const monthKey = `${selectedMonth.monthDate.getFullYear()}-${String(selectedMonth.monthDate.getMonth() + 1).padStart(2, '0')}`;
      const monthStart = new Date(selectedMonth.monthDate.getFullYear(), selectedMonth.monthDate.getMonth(), 1);
      
      // Sum all profits from AFTER this month (not including this month)
      // This gives us the balance at the END of this month
      const nextMonthPrefix = selectedMonth.monthDate.getMonth() === 11
        ? `${selectedMonth.monthDate.getFullYear() + 1}-01`
        : `${selectedMonth.monthDate.getFullYear()}-${String(selectedMonth.monthDate.getMonth() + 2).padStart(2, '0')}`;
      
      let totalProfitAfterMonth = 0;
      Object.entries(tradeLogs).forEach(([dateKey, log]) => {
        if (dateKey >= nextMonthPrefix) {  // From NEXT month onwards (not including this month)
          totalProfitAfterMonth += (log?.actual_profit || 0) + (log?.commission || 0);
        }
      });
      
      // Sum all deposits/withdrawals from AFTER this month
      let totalTxAfterMonth = 0;
      [...deposits, ...withdrawals].forEach(tx => {
        const txDate = tx.created_at?.split('T')[0];
        if (txDate && txDate >= `${nextMonthPrefix}-01`) {
          totalTxAfterMonth += (tx.amount || 0);  // Withdrawals already negative
        }
      });
      
      // Balance at END of selected month = current balance - profits after - transactions after
      // The inner function will then work backwards from this to get daily balances
      startBalance = effectiveAccountValue - totalProfitAfterMonth - totalTxAfterMonth;
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
    const frontendProjection = generateDailyProjectionForMonth(
      startBalance,
      selectedMonth.monthDate,
      tradeLogs,
      activeSignal,
      allTransactions,
      isCurrentMonth ? effectiveAccountValue : null,  // Only pass live value for current month
      globalHolidayDates,
      effectiveStartDate  // Pass effective start date for licensees
    );
    
    // CRITICAL FIX: Use backend-calculated balances as the authoritative source for ALL months
    // This fixes the balance calculation bug where frontend-calculated balances diverge
    // especially after a tracker reset
    const year = selectedMonth.monthDate.getFullYear();
    const monthNum = selectedMonth.monthDate.getMonth() + 1;
    const cacheKey = `${year}-${monthNum}`;
    const backendBalanceMap = backendDailyBalances[cacheKey];
    
    // Apply backend balances for ALL months (including current) to ensure accuracy
    // The only exception: for "today" we use the live effectiveAccountValue
    if (backendBalanceMap && Object.keys(backendBalanceMap).length > 0) {
      // Override frontend-calculated balances with authoritative backend values
      return frontendProjection.map(day => {
        // For today, use live account value (from effectiveAccountValue) instead of cached backend data
        // because backend data might be stale if user just made a trade
        if (day.isToday) {
          return day; // Keep frontend calculation for today
        }
        
        const backendData = backendBalanceMap[day.dateKey];
        if (backendData) {
          // Use backend's authoritative balance calculation
          const correctedBalance = backendData.balance_before;
          const correctedLotSize = truncateTo2Decimals(correctedBalance / 980);
          const correctedTarget = truncateTo2Decimals(correctedLotSize * 15);
          
          // Recalculate P/L diff with corrected target
          const correctedPlDiff = day.actualProfit !== undefined && day.actualProfit !== null
            ? truncateTo2Decimals(day.actualProfit - correctedTarget)
            : null;
          
          return {
            ...day,
            balanceBefore: correctedBalance,
            lotSize: correctedLotSize,
            targetProfit: correctedTarget,
            plDiff: correctedPlDiff,
            // Keep original actual profit, commission, and status
          };
        }
        return day;
      });
    }
    
    return frontendProjection;
  }, [selectedMonth, tradeLogs, activeSignal, effectiveAccountValue, isExtendedLicensee, licenseProjections, licenseeProjections, masterAdminTrades, tradeOverrides, deposits, withdrawals, globalHolidays, effectiveStartDate, backendDailyBalances]);

  // For licensees: Calculate Account Value from daily projections
  // This shows the balance AFTER the most recent day where Manager Traded = true
  const licenseeAccountValueFromProjections = useMemo(() => {
    if (!isLicensee) return null;
    
    // Use the same projection source as the daily table
    const activeProjections = licenseeProjections.length > 0 ? licenseeProjections : licenseProjections;
    if (activeProjections.length === 0) return null;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Get all projections up to and including today
    const projectionsUpToToday = activeProjections.filter(p => {
      const projDate = new Date(p.date + 'T00:00:00');
      return projDate <= today;
    });
    
    if (projectionsUpToToday.length === 0) return null;
    
    // Find the most recent day where manager traded (including overrides)
    let lastTradedProjection = null;
    for (let i = projectionsUpToToday.length - 1; i >= 0; i--) {
      const p = projectionsUpToToday[i];
      const override = tradeOverrides[p.date];
      const managerTraded = override !== undefined ? override.traded : p.manager_traded;
      
      if (managerTraded) {
        lastTradedProjection = p;
        break;
      }
    }
    
    if (!lastTradedProjection) {
      // No trades yet, return starting balance
      return projectionsUpToToday[0]?.start_value || null;
    }
    
    // Return balance AFTER the last traded day (start_value + daily_profit)
    return lastTradedProjection.start_value + lastTradedProjection.daily_profit;
  }, [isLicensee, licenseeProjections, licenseProjections, tradeOverrides]);

  // For licensees: Calculate Account Growth percentage
  // Formula: ((Current Account Value - Starting Amount) / Starting Amount) × 100
  const licenseeAccountGrowth = useMemo(() => {
    if (!isLicensee) return null;
    
    // Get starting amount from simulation context
    const startingAmount = simulatedView?.starting_amount || simulatedView?.startingAmount;
    if (!startingAmount || startingAmount === 0) return null;
    
    // Use the calculated account value from projections, or fall back to effectiveAccountValue
    const currentValue = licenseeAccountValueFromProjections || effectiveAccountValue;
    if (!currentValue) return null;
    
    const growth = ((currentValue - startingAmount) / startingAmount) * 100;
    return growth;
  }, [isLicensee, simulatedView, licenseeAccountValueFromProjections, effectiveAccountValue]);

  // Effective account value for display - for licensees, use projection-based value
  const displayAccountValue = isLicensee && licenseeAccountValueFromProjections !== null
    ? licenseeAccountValueFromProjections
    : effectiveAccountValue;

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
    if (enterAPValue === '' || enterAPValue === undefined || enterAPValue === null || isNaN(parseFloat(enterAPValue))) {
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
      
      // Parse commission (default to 0 if empty)
      const commissionValue = enterAPCommission ? parseFloat(enterAPCommission) : 0;

      // Log the trade with commission
      await tradeAPI.logMissedTrade({
        date: enterAPDate.dateKey,
        actual_profit: parseFloat(enterAPValue),
        commission: commissionValue,
        lot_size: calculatedLotSize,
        direction: activeSignal?.direction || 'BUY',
        balance_before: balanceForCalculation,
        notes: adjustmentType === 'profit_only' 
          ? 'Retroactively logged via Adjust Trade'
          : `Adjusted trade with ${adjustmentType === 'with_deposit' ? 'deposit' : 'withdrawal'} of $${adjustmentAmount}`
      });
      
      toast.success('Trade adjusted successfully!');
      
      // Check if we came from the sync wizard
      const fromWizard = enterAPDate?.fromWizard;
      
      setEnterAPDialogOpen(false);
      setEnterAPValue('');
      setEnterAPCommission('');
      setEnterAPDate(null);
      setAdjustmentType('profit_only');
      setAdjustmentAmount('');
      setAdjustedBalance('');
      
      // Reload data to reflect the new trade
      await loadData();
      
      // Reopen the sync wizard if we came from there
      if (fromWizard) {
        startSyncWizard();
      }
    } catch (error) {
      console.error('Failed to adjust trade:', error);
      toast.error(error.response?.data?.detail || 'Failed to adjust trade');
    } finally {
      setEnterAPLoading(false);
    }
  };

  // Handle "Did not trade" action
  const handleDidNotTrade = async (day) => {
    if (!window.confirm(
      `Mark ${day.dateStr} as "Did not trade"?\n\n` +
      `This will:\n` +
      `• Set profit/commission for this day to $0\n` +
      `• Reset your trading streak to 0\n\n` +
      `This action cannot be undone.`
    )) {
      return;
    }

    try {
      await api.post('/trade/did-not-trade', null, {
        params: { date: day.dateKey }
      });
      toast.success('Marked as "Did not trade". Your streak has been reset.');
      loadData();
    } catch (error) {
      console.error('Failed to mark as did not trade:', error);
      toast.error(error.response?.data?.detail || 'Failed to mark as "did not trade"');
    }
  };

  // Adjust Commission handlers
  const handleOpenAdjustCommission = (day) => {
    setAdjustCommissionDate(day);
    setAdjustCommissionAmount(day.commission?.toString() || '');
    setAdjustCommissionSkipDeposit(false);
    setAdjustCommissionOpen(true);
  };

  const handleSubmitAdjustCommission = async () => {
    if (!adjustCommissionAmount || parseFloat(adjustCommissionAmount) < 0) {
      toast.error('Please enter a valid commission amount');
      return;
    }

    if (!adjustCommissionDate) {
      toast.error('No date selected');
      return;
    }

    setAdjustCommissionLoading(true);
    try {
      // Use the commission endpoint with the specific date
      await api.post('/profit/commission', {
        amount: parseFloat(adjustCommissionAmount),
        traders_count: 1,
        notes: `Commission for ${adjustCommissionDate.dateStr}`,
        commission_date: adjustCommissionDate.dateKey,
        skip_deposit: adjustCommissionSkipDeposit
      });
      
      toast.success('Commission adjusted successfully!');
      setAdjustCommissionOpen(false);
      setAdjustCommissionAmount('');
      setAdjustCommissionDate(null);
      loadData();
    } catch (error) {
      console.error('Failed to adjust commission:', error);
      toast.error(error.response?.data?.detail || 'Failed to adjust commission');
    } finally {
      setAdjustCommissionLoading(false);
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

  // Balance Override handler - syncs calculated balance with actual Merin balance
  const handleBalanceOverride = async () => {
    const actualBalance = parseFloat(actualBalanceInput);
    if (isNaN(actualBalance) || actualBalance < 0) {
      toast.error('Please enter a valid balance amount');
      return;
    }
    
    setBalanceOverrideLoading(true);
    try {
      const response = await api.post('/profit/balance-override', {
        actual_balance: actualBalance,
        reason: 'Manual balance sync with Merin after onboarding'
      });
      
      toast.success(`Balance synced! Adjustment of $${response.data.override.adjustment_amount.toFixed(2)} applied.`);
      setBalanceVerificationOpen(false);
      setSyncWizardOpen(false);
      setActualBalanceInput('');
      
      // Clear cached balances and reload
      setBackendDailyBalances({});
      await loadData();
      // Refresh health score
      api.get('/profit/sync-validation').then(r => setDataHealth(r.data)).catch(() => {});
    } catch (error) {
      console.error('Failed to create balance override:', error);
      toast.error('Failed to sync balance: ' + (error.response?.data?.detail || error.message));
    } finally {
      setBalanceOverrideLoading(false);
    }
  };

  // Start the Pre-Sync Validation Wizard
  const startSyncWizard = async () => {
    setSyncWizardOpen(true);
    setSyncWizardStep(1);
    setSyncValidationLoading(true);
    setPreStartAcknowledged(false);
    
    try {
      const response = await api.get('/profit/sync-validation');
      setSyncValidation(response.data);
      
      // Determine which step to start at
      if (!response.data.trading_start_date) {
        setSyncWizardStep(1); // Need to set start date
        setNewStartDate(response.data.suggested_start_date || '');
      } else if (response.data.missing_trade_days?.length > 0) {
        setSyncWizardStep(2); // Missing trade days
      } else if (response.data.pre_start_trades?.length > 0) {
        setSyncWizardStep(3); // Pre-start trades warning
      } else {
        setSyncWizardStep(4); // Ready to sync
        setCalculatedBalance(displayAccountValue);
        setActualBalanceInput(displayAccountValue.toFixed(2));
      }
    } catch (error) {
      console.error('Failed to get sync validation:', error);
      toast.error('Failed to validate: ' + (error.response?.data?.detail || error.message));
      setSyncWizardOpen(false);
    } finally {
      setSyncValidationLoading(false);
    }
  };

  // Set trading start date
  const handleSetStartDate = async () => {
    if (!newStartDate) {
      toast.error('Please select a start date');
      return;
    }
    
    try {
      await api.post('/profit/set-trading-start-date', { trading_start_date: newStartDate });
      toast.success('Trading start date set!');
      
      // Refresh validation
      setSyncValidationLoading(true);
      const response = await api.get('/profit/sync-validation');
      setSyncValidation(response.data);
      
      // Move to next step
      if (response.data.missing_trade_days?.length > 0) {
        setSyncWizardStep(2);
      } else if (response.data.pre_start_trades?.length > 0) {
        setSyncWizardStep(3);
      } else {
        setSyncWizardStep(4);
        setCalculatedBalance(displayAccountValue);
        setActualBalanceInput(displayAccountValue.toFixed(2));
      }
    } catch (error) {
      toast.error('Failed to set start date: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSyncValidationLoading(false);
    }
  };

  // Quick mark as "Did Not Trade" from wizard
  const handleQuickDidNotTrade = async (date) => {
    try {
      await api.post('/trade/did-not-trade', null, { params: { date: date } });
      toast.success(`Marked ${date} as "Did Not Trade"`);
      
      // Refresh validation
      const response = await api.get('/profit/sync-validation');
      setSyncValidation(response.data);
      setDataHealth(response.data);
      
      // Check if we can move to next step
      if (response.data.missing_trade_days?.length === 0) {
        if (response.data.pre_start_trades?.length > 0) {
          setSyncWizardStep(3);
        } else {
          setSyncWizardStep(4);
          setCalculatedBalance(displayAccountValue);
          setActualBalanceInput(displayAccountValue.toFixed(2));
        }
      }
    } catch (error) {
      const detail = error.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail.map(d => d.msg || JSON.stringify(d)).join(', ') : error.message);
      toast.error('Failed: ' + msg);
    }
  };

  // Mark all missing days as "Did Not Trade"
  const handleMarkAllDidNotTrade = async () => {
    if (!syncValidation?.missing_trade_days?.length) return;
    
    setSyncValidationLoading(true);
    try {
      for (const day of syncValidation.missing_trade_days) {
        await api.post('/trade/did-not-trade', null, { params: { date: day.date } });
      }
      toast.success(`Marked ${syncValidation.missing_trade_days.length} days as "Did Not Trade"`);
      
      // Refresh validation
      const response = await api.get('/profit/sync-validation');
      setSyncValidation(response.data);
      setDataHealth(response.data);
      
      // Move to next step
      if (response.data.pre_start_trades?.length > 0) {
        setSyncWizardStep(3);
      } else {
        setSyncWizardStep(4);
        setCalculatedBalance(displayAccountValue);
        setActualBalanceInput(displayAccountValue.toFixed(2));
      }
    } catch (error) {
      toast.error('Failed to mark days: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSyncValidationLoading(false);
    }
  };

  // Proceed after acknowledging pre-start trades warning
  const handleAcknowledgePreStartTrades = () => {
    setPreStartAcknowledged(true);
    setSyncWizardStep(4);
    setCalculatedBalance(displayAccountValue);
    setActualBalanceInput(displayAccountValue.toFixed(2));
  };

  // Open adjust trade dialog for a specific date from wizard
  const openAdjustTradeFromWizard = (date) => {
    // Close wizard temporarily
    setSyncWizardOpen(false);
    // Open the existing Enter AP dialog for the specific date
    setEnterAPDate({
      date: date,
      dateKey: date,
      dateStr: date,
      fromWizard: true,
      balanceBefore: displayAccountValue
    });
    setEnterAPValue('');
    setEnterAPCommission('');
    setAdjustmentType('profit_only');
    setAdjustmentAmount('');
    setAdjustedBalance('');
    setEnterAPDialogOpen(true);
  };

  // Legacy openBalanceVerification - now opens wizard instead
  const openBalanceVerification = (calcBalance) => {
    startSyncWizard();
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

    // CRITICAL SAFETY CHECK: If simulating, we MUST have a valid memberId
    // Otherwise we would accidentally reset the Master Admin's account!
    if (simulatedView && !simulatedView.memberId) {
      toast.error('Cannot reset: Simulated member ID is missing. Please exit simulation and try again.');
      console.error('Reset blocked: simulatedView exists but memberId is missing', simulatedView);
      return;
    }

    try {
      // Verify password first (always Master Admin's password when simulating)
      const verifyRes = await api.post('/auth/verify-password', {
        password: resetPassword,
      });
      
      if (!verifyRes.data.valid) {
        toast.error('Invalid password');
        return;
      }
      
      // Reset tracker - pass user_id if simulating a member
      // IMPORTANT: Only pass user_id if we have a valid memberId from simulation
      const targetUserId = simulatedView?.memberId || null;
      
      if (simulatedView && targetUserId) {
        // Simulating a member - reset THEIR data
        await api.delete(`/profit/reset?user_id=${targetUserId}`);
        toast.success(`${simulatedView.displayName || 'Member'}'s profit tracker has been reset!`);
      } else {
        // Not simulating - reset current user's data
        await api.delete('/profit/reset');
        toast.success('Profit tracker has been reset!');
      }
      
      // CRITICAL: Clear cached backend daily balances to force fresh fetch after reset
      setBackendDailyBalances({});
      
      resetResetDialog();
      
      // Open the onboarding wizard for reset flow
      setIsResetOnboarding(true);
      setOnboardingWizardOpen(true);
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Invalid password. Please try again.');
      } else {
        toast.error('Failed to reset tracker');
        console.error('Reset error:', error);
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
        notes: commissionNotes || `Commission from ${commissionTradersCount} referral trades`,
        commission_date: commissionDate
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
    setCommissionDate(new Date().toISOString().split('T')[0]);
  };

  // Handle Error Trade Submission
  const handleSubmitErrorTrade = async () => {
    if (!errorType) {
      toast.error('Please select an error type');
      return;
    }
    if (errorType === 'other' && !errorExplanation) {
      toast.error('Please provide an explanation for the error');
      return;
    }
    if (!errorProfit && errorProfit !== '0') {
      toast.error('Please enter the profit/loss amount');
      return;
    }
    if (!errorDate) {
      toast.error('Please select a date');
      return;
    }
    
    setSubmittingError(true);
    try {
      await api.post('/trade/log-error', {
        error_type: errorType,
        error_explanation: errorExplanation || null,
        actual_profit: parseFloat(errorProfit),
        product: errorProduct,
        direction: errorDirection,
        date: errorDate
      });
      toast.success('Error trade logged successfully! Admins have been notified.');
      resetErrorDialog();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to log error trade');
    } finally {
      setSubmittingError(false);
    }
  };

  const resetErrorDialog = () => {
    setErrorDialogOpen(false);
    setErrorType('');
    setErrorExplanation('');
    setErrorProfit('');
    setErrorProduct('MOIL10');
    setErrorDirection('BUY');
    setErrorDate(new Date().toISOString().split('T')[0]);
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
    return generateMonthlyProjection(effectiveAccountValue, tradeLogs, globalHolidayDates, deposits, effectiveStartDate);
  }, [effectiveAccountValue, tradeLogs, globalHolidays, deposits, effectiveStartDate]);
  
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
        <div className="w-8 h-8 border-4 border-orange-500/20 border-t-orange-500 rounded-full animate-spin" />
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
                <p className="text-xs text-amber-400/70">
                  Account Value: {formatLargeNumber(effectiveAccountValue)}
                  {/* Hide LOT Size for licensees */}
                  {!isLicensee && ` • LOT Size: ${effectiveLotSize.toFixed(2)}`}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trading Signal Banner - Desktop Only - Hidden for licensees (they don't trade) */}
      {activeSignal && !isLicensee && (
        <Card className="hidden md:block glass-highlight bg-gradient-to-r from-orange-500/10 to-amber-500/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Radio className="w-5 h-5 text-orange-400 animate-pulse" />
                <div>
                  <p className="text-xs text-zinc-400">Today&apos;s Trading Signal</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-white font-bold">{activeSignal.product}</span>
                    <span className={`px-3 py-1 rounded-lg font-bold text-sm ${activeSignal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                      {activeSignal.direction}
                    </span>
                    <span className="text-zinc-400">at</span>
                    <span className="font-mono text-orange-400 font-bold">{activeSignal.trade_time}</span>
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

      {/* Mobile Signal Card - Compact "Trade Now" button that navigates to Trade Monitor - Hidden for licensees */}
      {activeSignal && !isLicensee && (
        <Card className="md:hidden glass-card border-orange-500/20 bg-orange-500/5" data-testid="mobile-signal-card">
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

      {/* Summary Cards */}
      <StatsCards
        isLicensee={isLicensee}
        simulatedView={simulatedView}
        displayAccountValue={displayAccountValue}
        effectiveTotalDeposits={effectiveTotalDeposits}
        effectiveTotalProfit={effectiveTotalProfit}
        effectiveLotSize={effectiveLotSize}
        licenseeAccountGrowth={licenseeAccountGrowth}
        hiddenCards={hiddenCards}
        toggleCardVisibility={toggleCardVisibility}
        selectedCurrency={selectedCurrency}
        setSelectedCurrency={setSelectedCurrency}
        getCurrencySymbol={getCurrencySymbol}
        convertAmount={convertAmount}
        openBalanceVerification={openBalanceVerification}
      />

      {/* Compact Active Signal Card for Profit Tracker - Mobile Only (desktop version is in summary cards) - Hidden for licensees */}
      {activeSignal && !isLicensee && (
        <Card className="md:hidden glass-card border-orange-500/20 bg-orange-500/5">
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
        {/* Desktop: Dialog, Mobile: Full-screen overlay */}
        {!isMobile && (
          <div className="hidden md:flex gap-2">
          <Dialog open={simulateActionsOpen} onOpenChange={setSimulateActionsOpen}>
            <DialogTrigger asChild>
              <Button className="btn-primary gap-2" data-testid="simulate-actions-button">
                <Calculator className="w-4 h-4" /> Simulate Actions
              </Button>
            </DialogTrigger>
            <DialogContent className="glass-card border-white/[0.06] max-w-sm">
              <DialogHeader>
                <DialogTitle className="text-white flex items-center gap-2">
                  <Calculator className="w-5 h-5 text-orange-400" /> Simulate Actions
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
                {/* Simulate Error Button - Master Admin Only */}
                {isMasterAdmin() && (
                <Button 
                  variant="outline"
                  className="w-full btn-secondary gap-2 justify-start border-red-500/50 hover:bg-red-500/10" 
                  onClick={() => { setSimulateActionsOpen(false); setErrorDialogOpen(true); }}
                  data-testid="simulate-error-button"
                >
                  <AlertTriangle className="w-4 h-4 text-red-400" /> Simulate Error
                </Button>
                )}
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
                {/* Export Debug Data - Master Admin Only */}
                {isMasterAdmin() && (
                  <Button 
                    variant="outline"
                    className="w-full btn-secondary gap-2 justify-start border-yellow-500/50 hover:bg-yellow-500/10" 
                    onClick={async () => {
                      try {
                        setSimulateActionsOpen(false);
                        const targetId = simulatedView?.memberId || user?.id;
                        const res = await api.get(`/admin/export-debug-data/${targetId}`);
                        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `debug-data-${new Date().toISOString().slice(0,10)}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                        toast.success('Debug data exported! Share this file with your developer.');
                      } catch (e) {
                        toast.error('Failed to export debug data');
                      }
                    }}
                    data-testid="export-debug-data-button"
                  >
                    <FileText className="w-4 h-4 text-yellow-400" /> Export Debug Data
                  </Button>
                )}
              </div>
            </DialogContent>
          </Dialog>
          <Button
            variant="outline"
            className="btn-secondary gap-2"
            onClick={() => setAuditTrailModalOpen(true)}
            data-testid="balance-trail-button"
          >
            <TrendingUp className="w-4 h-4 text-orange-400" /> Balance Trail
          </Button>
          </div>
        )}

        {/* Mobile Simulate Actions Button */}
        <div className="md:hidden w-full flex gap-2">
          <Button 
            className="btn-primary gap-2 flex-1" 
            onClick={() => setSimulateActionsOpen(true)}
            data-testid="simulate-actions-button-mobile"
          >
            <Calculator className="w-4 h-4" /> Simulate Actions
          </Button>
          <Button
            variant="outline"
            className="btn-secondary gap-2"
            onClick={() => setAuditTrailModalOpen(true)}
            data-testid="balance-trail-button-mobile"
          >
            <TrendingUp className="w-4 h-4 text-orange-400" />
          </Button>
        </div>

        {/* Mobile Simulate Actions Full-Screen Overlay */}
        {simulateActionsOpen && (
          <div className="md:hidden fixed inset-0 z-[9999] bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="h-full w-full flex flex-col bg-gradient-to-b from-zinc-900 via-zinc-950 to-black overflow-hidden">
              
              {/* Header */}
              <div className="flex-shrink-0 p-6 pb-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-orange-500/10 flex items-center justify-center">
                      <Calculator className="w-6 h-6 text-orange-400" />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-white">Simulate Actions</h1>
                      <p className="text-sm text-zinc-500">Choose an action below</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setSimulateActionsOpen(false)}
                    className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-y-auto px-6 pb-32">
                <div className="space-y-4">
                  
                  {/* Deposit Card */}
                  <button
                    onClick={() => { setSimulateActionsOpen(false); setDepositDialogOpen(true); }}
                    className="relative w-full p-5 rounded-2xl border-2 border-emerald-500/30 bg-emerald-500/5 text-left transition-all duration-300 hover:border-emerald-500/50 hover:bg-emerald-500/10 group overflow-hidden"
                    data-testid="mobile-simulate-deposit"
                  >
                    <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-emerald-500/20 blur-3xl opacity-0 group-hover:opacity-50 transition-opacity" />
                    <div className="relative z-10 flex items-center gap-4">
                      <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 flex items-center justify-center">
                        <Plus className="w-7 h-7 text-emerald-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-white mb-1">Simulate Deposit</h3>
                        <p className="text-sm text-zinc-500">Add funds to your account</p>
                      </div>
                      <ChevronDown className="w-5 h-5 text-zinc-500 -rotate-90" />
                    </div>
                  </button>

                  {/* Withdrawal Card */}
                  <button
                    onClick={() => { setSimulateActionsOpen(false); setWithdrawalDialogOpen(true); }}
                    className="relative w-full p-5 rounded-2xl border-2 border-orange-500/30 bg-orange-500/5 text-left transition-all duration-300 hover:border-orange-500/50 hover:bg-orange-500/10 group overflow-hidden"
                    data-testid="mobile-simulate-withdrawal"
                  >
                    <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-orange-500/20 blur-3xl opacity-0 group-hover:opacity-50 transition-opacity" />
                    <div className="relative z-10 flex items-center gap-4">
                      <div className="w-14 h-14 rounded-2xl bg-orange-500/20 flex items-center justify-center">
                        <ArrowUpFromLine className="w-7 h-7 text-orange-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-white mb-1">Simulate Withdrawal</h3>
                        <p className="text-sm text-zinc-500">Withdraw funds from account</p>
                      </div>
                      <ChevronDown className="w-5 h-5 text-zinc-500 -rotate-90" />
                    </div>
                  </button>

                  {/* Commission Card */}
                  <button
                    onClick={() => { setSimulateActionsOpen(false); setCommissionDialogOpen(true); }}
                    className="relative w-full p-5 rounded-2xl border-2 border-purple-500/30 bg-purple-500/5 text-left transition-all duration-300 hover:border-purple-500/50 hover:bg-purple-500/10 group overflow-hidden"
                    data-testid="mobile-simulate-commission"
                  >
                    <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-purple-500/20 blur-3xl opacity-0 group-hover:opacity-50 transition-opacity" />
                    <div className="relative z-10 flex items-center gap-4">
                      <div className="w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center">
                        <Award className="w-7 h-7 text-purple-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-white mb-1">Simulate Commission</h3>
                        <p className="text-sm text-zinc-500">Add referral commission</p>
                      </div>
                      <ChevronDown className="w-5 h-5 text-zinc-500 -rotate-90" />
                    </div>
                  </button>

                  {/* Error Trade Card - Master Admin Only */}
                  {isMasterAdmin() && (
                  <button
                    onClick={() => { setSimulateActionsOpen(false); setErrorDialogOpen(true); }}
                    className="relative w-full p-5 rounded-2xl border-2 border-red-500/30 bg-red-500/5 text-left transition-all duration-300 hover:border-red-500/50 hover:bg-red-500/10 group overflow-hidden"
                    data-testid="mobile-simulate-error"
                  >
                    <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-red-500/20 blur-3xl opacity-0 group-hover:opacity-50 transition-opacity" />
                    <div className="relative z-10 flex items-center gap-4">
                      <div className="w-14 h-14 rounded-2xl bg-red-500/20 flex items-center justify-center">
                        <AlertTriangle className="w-7 h-7 text-red-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-white mb-1">Simulate Error</h3>
                        <p className="text-sm text-zinc-500">Report a trading error</p>
                      </div>
                      <ChevronDown className="w-5 h-5 text-zinc-500 -rotate-90" />
                    </div>
                  </button>
                  )}

                  {/* VSD Card - Master Admin Only */}
                  {isMasterAdmin() && (
                    <button
                      onClick={() => { setSimulateActionsOpen(false); loadVSDData(); setVsdDialogOpen(true); }}
                      className="relative w-full p-5 rounded-2xl border-2 border-cyan-500/30 bg-cyan-500/5 text-left transition-all duration-300 hover:border-cyan-500/50 hover:bg-cyan-500/10 group overflow-hidden"
                      data-testid="mobile-licensee-vsd"
                    >
                      <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-cyan-500/20 blur-3xl opacity-0 group-hover:opacity-50 transition-opacity" />
                      <div className="relative z-10 flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-cyan-500/20 flex items-center justify-center">
                          <Users className="w-7 h-7 text-cyan-400" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-bold text-white mb-1">Licensee VSD</h3>
                          <p className="text-sm text-zinc-500">Virtual Share Distribution</p>
                        </div>
                        <ChevronDown className="w-5 h-5 text-zinc-500 -rotate-90" />
                      </div>
                    </button>
                  )}

                  {/* Export Debug Data - Mobile Master Admin */}
                  {isMasterAdmin() && (
                    <button
                      className="group relative w-full text-left p-5 rounded-2xl bg-[#0d0d0d]/50 border border-yellow-500/20 hover:border-yellow-500/40 transition-all overflow-hidden"
                      onClick={async () => {
                        try {
                          setSimulateActionsOpen(false);
                          const targetId = simulatedView?.memberId || user?.id;
                          const res = await api.get(`/admin/export-debug-data/${targetId}`);
                          const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `debug-data-${new Date().toISOString().slice(0,10)}.json`;
                          a.click();
                          URL.revokeObjectURL(url);
                          toast.success('Debug data exported!');
                        } catch (e) {
                          toast.error('Failed to export debug data');
                        }
                      }}
                      data-testid="export-debug-data-button-mobile"
                    >
                      <div className="relative z-10 flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-yellow-500/20 flex items-center justify-center">
                          <FileText className="w-7 h-7 text-yellow-400" />
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-bold text-white mb-1">Export Debug Data</h3>
                          <p className="text-sm text-zinc-500">Download JSON for developer</p>
                        </div>
                        <ChevronDown className="w-5 h-5 text-zinc-500 -rotate-90" />
                      </div>
                    </button>
                  )}

                </div>
              </div>

              {/* Bottom safe area with close button */}
              <div className="flex-shrink-0 p-6 pt-0 pb-8 bg-gradient-to-t from-black to-transparent">
                <button
                  onClick={() => setSimulateActionsOpen(false)}
                  className="w-full py-4 rounded-xl bg-[#1a1a1a] text-zinc-300 font-medium hover:bg-white/[0.08] transition-colors"
                >
                  Close
                </button>
              </div>

            </div>
          </div>
        )}
        
        {/* VSD (Virtual Share Distribution) Dialog - Master Admin Only */}
        {isMasterAdmin() && (
          <VSDDialog 
            open={vsdDialogOpen} 
            onOpenChange={setVsdDialogOpen} 
            vsdData={vsdData} 
            loading={vsdLoading} 
          />
        )}
        
        {/* Simulate Error Dialog - Desktop */}
        <Dialog open={errorDialogOpen} onOpenChange={(open) => { if (!open) resetErrorDialog(); else setErrorDialogOpen(true); }}>
          <DialogContent className="glass-card border-white/[0.06] max-w-md hidden md:block">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-400" /> Report Error Trade
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                <p className="text-sm text-red-400">
                  Report a trading error (wrong product, wrong time, etc.). 
                  This will be logged and affect your account value. Admins will be notified.
                </p>
              </div>
              
              {/* Error Type Selection */}
              <div>
                <Label className="text-zinc-300">Error Type</Label>
                <Select value={errorType} onValueChange={setErrorType}>
                  <SelectTrigger className="mt-1 bg-[#0d0d0d] border-white/[0.08] text-white">
                    <SelectValue placeholder="Select error type..." />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0d0d0d] border-white/[0.08]">
                    <SelectItem value="wrong_product" className="text-white">Wrong Product Selection</SelectItem>
                    <SelectItem value="wrong_time" className="text-white">Wrong Trade Time</SelectItem>
                    <SelectItem value="wrong_direction" className="text-white">Wrong Direction (BUY/SELL)</SelectItem>
                    <SelectItem value="other" className="text-white">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {/* Product Selection */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-zinc-300">Product</Label>
                  <Select value={errorProduct} onValueChange={setErrorProduct}>
                    <SelectTrigger className="mt-1 bg-[#0d0d0d] border-white/[0.08] text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0d0d0d] border-white/[0.08]">
                      <SelectItem value="MOIL10" className="text-white">MOIL10</SelectItem>
                      <SelectItem value="XAUUSD" className="text-white">XAUUSD</SelectItem>
                      <SelectItem value="BTCUSD" className="text-white">BTCUSD</SelectItem>
                      <SelectItem value="ETHUSD" className="text-white">ETHUSD</SelectItem>
                      <SelectItem value="OTHER" className="text-amber-400">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-zinc-300">Direction</Label>
                  <Select value={errorDirection} onValueChange={setErrorDirection}>
                    <SelectTrigger className="mt-1 bg-[#0d0d0d] border-white/[0.08] text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0d0d0d] border-white/[0.08]">
                      <SelectItem value="BUY" className="text-emerald-400">BUY</SelectItem>
                      <SelectItem value="SELL" className="text-red-400">SELL</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {/* Date Selection */}
              <div>
                <Label className="text-zinc-300">Date of Error Trade</Label>
                <Input
                  type="date"
                  value={errorDate}
                  onChange={(e) => setErrorDate(e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                  className="input-dark mt-1"
                  data-testid="error-date-input"
                />
              </div>
              
              {/* Profit/Loss Amount */}
              <div>
                <Label className="text-zinc-300">Profit/Loss Amount (USDT)</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={errorProfit}
                    onChange={(e) => setErrorProfit(e.target.value)}
                    placeholder="Enter negative for loss (e.g., -50)"
                    className="input-dark pl-7"
                    data-testid="error-profit-input"
                  />
                </div>
                <p className="text-xs text-zinc-500 mt-1">Enter negative value for losses (e.g., -50 for $50 loss)</p>
              </div>
              
              {/* Explanation - Required for "Other" type */}
              <div>
                <Label className="text-zinc-300">
                  Explanation {errorType === 'other' ? <span className="text-red-400">*</span> : '(optional)'}
                </Label>
                <Input
                  value={errorExplanation}
                  onChange={(e) => setErrorExplanation(e.target.value)}
                  placeholder="Describe what happened..."
                  className="input-dark mt-1"
                  data-testid="error-explanation-input"
                />
              </div>
              
              {/* Preview */}
              {errorProfit && (
                <div className={`p-3 rounded-lg ${parseFloat(errorProfit) >= 0 ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'} border`}>
                  <p className="text-sm text-zinc-300">
                    This will {parseFloat(errorProfit) >= 0 ? 'add' : 'subtract'}{' '}
                    <span className={`font-mono font-bold ${parseFloat(errorProfit) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      ${Math.abs(parseFloat(errorProfit)).toFixed(2)}
                    </span>{' '}
                    {parseFloat(errorProfit) >= 0 ? 'to' : 'from'} your account value.
                  </p>
                </div>
              )}
              
              <Button 
                onClick={handleSubmitErrorTrade} 
                disabled={submittingError}
                className="w-full bg-red-600 hover:bg-red-700 text-white"
                data-testid="submit-error-button"
              >
                {submittingError ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 mr-2" /> Log Error Trade
                  </>
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Mobile Error Dialog - Full Screen Overlay */}
        {errorDialogOpen && (
          <div className="md:hidden fixed inset-0 z-[9999] bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="h-full w-full flex flex-col bg-gradient-to-b from-zinc-900 via-zinc-950 to-black overflow-hidden">
              
              {/* Header */}
              <div className="flex-shrink-0 p-6 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-red-500/20 flex items-center justify-center">
                      <AlertTriangle className="w-6 h-6 text-red-400" />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-white">Report Error Trade</h1>
                      <p className="text-sm text-zinc-500">This will affect your account</p>
                    </div>
                  </div>
                  <button 
                    onClick={resetErrorDialog}
                    className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-y-auto px-6 pb-32">
                <div className="space-y-6">
                  
                  {/* Warning Banner */}
                  <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30">
                    <p className="text-sm text-red-400 leading-relaxed">
                      Report a trading error (wrong product, wrong time, etc.). 
                      This will be logged and affect your account value. Admins will be notified.
                    </p>
                  </div>
                  
                  {/* Error Type Selection */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Error Type
                    </label>
                    <Select value={errorType} onValueChange={setErrorType}>
                      <SelectTrigger className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-lg py-5 focus:border-red-500 focus:ring-2 focus:ring-red-500/20">
                        <SelectValue placeholder="Select error type..." />
                      </SelectTrigger>
                      <SelectContent className="bg-[#0d0d0d] border-white/[0.08] z-[99999]">
                        <SelectItem value="wrong_product" className="text-white py-3">Wrong Product Selection</SelectItem>
                        <SelectItem value="wrong_time" className="text-white py-3">Wrong Trade Time</SelectItem>
                        <SelectItem value="wrong_direction" className="text-white py-3">Wrong Direction (BUY/SELL)</SelectItem>
                        <SelectItem value="other" className="text-white py-3">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Product & Direction */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                        Product
                      </label>
                      <Select value={errorProduct} onValueChange={setErrorProduct}>
                        <SelectTrigger className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white py-4 focus:border-cyan-500">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[#0d0d0d] border-white/[0.08] z-[99999]">
                          <SelectItem value="MOIL10" className="text-white">MOIL10</SelectItem>
                          <SelectItem value="XAUUSD" className="text-white">XAUUSD</SelectItem>
                          <SelectItem value="BTCUSD" className="text-white">BTCUSD</SelectItem>
                          <SelectItem value="ETHUSD" className="text-white">ETHUSD</SelectItem>
                          <SelectItem value="OTHER" className="text-amber-400">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                        Direction
                      </label>
                      <Select value={errorDirection} onValueChange={setErrorDirection}>
                        <SelectTrigger className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white py-4 focus:border-cyan-500">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-[#0d0d0d] border-white/[0.08] z-[99999]">
                          <SelectItem value="BUY" className="text-emerald-400">BUY</SelectItem>
                          <SelectItem value="SELL" className="text-red-400">SELL</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  {/* Date Selection */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Date of Error Trade
                    </label>
                    <input
                      type="date"
                      value={errorDate}
                      onChange={(e) => setErrorDate(e.target.value)}
                      max={new Date().toISOString().split('T')[0]}
                      className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-base focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 transition-all duration-300 px-4 py-5"
                      data-testid="mobile-error-date-input"
                    />
                  </div>
                  
                  {/* Profit/Loss Amount */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Profit/Loss Amount (USDT)
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                      <input
                        type="number"
                        step="0.01"
                        value={errorProfit}
                        onChange={(e) => setErrorProfit(e.target.value)}
                        placeholder="-50.00"
                        className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-lg font-mono placeholder:text-zinc-600 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all duration-300 pl-10 pr-4 py-5"
                        data-testid="mobile-error-profit-input"
                      />
                    </div>
                    <p className="text-xs text-zinc-500">Enter negative for losses (e.g., -50 for $50 loss)</p>
                  </div>
                  
                  {/* Explanation */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Explanation {errorType === 'other' && <span className="text-red-400">*</span>}
                    </label>
                    <input
                      value={errorExplanation}
                      onChange={(e) => setErrorExplanation(e.target.value)}
                      placeholder="Describe what happened..."
                      className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-base placeholder:text-zinc-600 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-300 px-4 py-5"
                      data-testid="mobile-error-explanation-input"
                    />
                  </div>
                  
                  {/* Preview Card */}
                  {errorProfit && (
                    <div className={`p-5 rounded-2xl border-2 ${
                      parseFloat(errorProfit) >= 0 
                        ? 'bg-emerald-500/10 border-emerald-500/30' 
                        : 'bg-red-500/10 border-red-500/30'
                    }`}>
                      <p className="text-zinc-300 text-center">
                        This will {parseFloat(errorProfit) >= 0 ? 'add' : 'subtract'}{' '}
                        <span className={`text-2xl font-mono font-bold block mt-2 ${
                          parseFloat(errorProfit) >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                          ${Math.abs(parseFloat(errorProfit || 0)).toFixed(2)}
                        </span>
                        <span className="text-sm text-zinc-500 mt-1 block">
                          {parseFloat(errorProfit) >= 0 ? 'to' : 'from'} your account value
                        </span>
                      </p>
                    </div>
                  )}

                </div>
              </div>

              {/* Bottom Action Area */}
              <div className="flex-shrink-0 p-6 pt-0 pb-8 bg-gradient-to-t from-black to-transparent space-y-3">
                <button
                  onClick={handleSubmitErrorTrade}
                  disabled={submittingError}
                  className="w-full py-4 rounded-xl bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                  data-testid="mobile-submit-error-button"
                >
                  {submittingError ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" /> Submitting...
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-5 h-5" /> Log Error Trade
                    </>
                  )}
                </button>
                <button
                  onClick={resetErrorDialog}
                  className="w-full py-4 rounded-xl bg-[#1a1a1a] text-zinc-300 font-medium hover:bg-white/[0.08] transition-colors"
                >
                  Cancel
                </button>
              </div>

            </div>
          </div>
        )}

        {/* Mobile Full-Screen Overlay for Deposit Dialog */}
        {isMobile && depositDialogOpen && (
          <div className="md:hidden fixed inset-0 z-[9999] bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="h-full w-full flex flex-col bg-gradient-to-b from-zinc-900 via-zinc-950 to-black">
              {/* Header */}
              <div className="flex-shrink-0 p-6 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 flex items-center justify-center">
                      <Plus className="w-6 h-6 text-emerald-400" />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-white">
                        {depositStep === 'input' && 'Simulate Deposit'}
                        {depositStep === 'simulate' && 'Deposit Calculation'}
                        {depositStep === 'confirm' && 'Confirm Deposit'}
                      </h1>
                      <p className="text-sm text-zinc-500">Add funds to your account</p>
                    </div>
                  </div>
                  <button 
                    onClick={resetDepositDialog}
                    className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Content Area - Scrollable */}
              <div className="flex-1 overflow-y-auto px-6 pb-8">
                <div className="space-y-6">
                  <TransactionStepper
                    steps={[
                      { id: 'amount', label: 'Amount' },
                      { id: 'calculate', label: 'Calculate' },
                      { id: 'confirm', label: 'Confirm' },
                    ]}
                    activeStep={depositStep === 'input' ? 1 : depositStep === 'simulate' ? 2 : 3}
                  />
                  {depositStep === 'input' && (
                    <>
                      {!manualDepositMode ? (
                        <>
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                              Binance USDT Amount
                            </label>
                            <div className="relative">
                              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                              <input
                                type="number"
                                value={depositAmount}
                                onChange={(e) => setDepositAmount(e.target.value)}
                                placeholder="0.00"
                                className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-lg font-mono pl-10 pr-4 py-5 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                                data-testid="mobile-deposit-amount-input"
                              />
                            </div>
                            <p className="text-xs text-zinc-500">Amount you're sending from Binance</p>
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                              Notes (optional)
                            </label>
                            <input
                              value={depositNotes}
                              onChange={(e) => setDepositNotes(e.target.value)}
                              placeholder="Add notes..."
                              className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white px-4 py-4 focus:outline-none focus:border-emerald-500"
                            />
                          </div>
                          <button 
                            onClick={handleSimulateDeposit} 
                            className="w-full py-4 rounded-xl bg-emerald-500 text-white font-bold hover:bg-emerald-600 transition-colors flex items-center justify-center gap-2"
                            data-testid="mobile-calculate-deposit"
                          >
                            <Calculator className="w-5 h-5" /> Calculate Deposit
                          </button>
                          <button 
                            onClick={() => setManualDepositMode(true)}
                            className="w-full text-center text-sm text-zinc-500 hover:text-orange-400 underline transition-colors"
                          >
                            Wrong Calculations? Enter your total deposit manually
                          </button>
                        </>
                      ) : (
                        <>
                          <div className="p-4 rounded-2xl bg-orange-500/10 border border-orange-500/20">
                            <p className="text-orange-400 font-medium">Manual Override Mode</p>
                            <p className="text-xs text-zinc-400 mt-1">Enter the exact amount that will be added to your Merin balance.</p>
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                              Total Deposit Amount (USDT)
                            </label>
                            <div className="relative">
                              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                              <input
                                type="number"
                                value={manualDepositAmount}
                                onChange={(e) => setManualDepositAmount(e.target.value)}
                                placeholder="0.00"
                                className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-lg font-mono pl-10 pr-4 py-5 focus:outline-none focus:border-orange-500"
                              />
                            </div>
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                              Notes (optional)
                            </label>
                            <input
                              value={depositNotes}
                              onChange={(e) => setDepositNotes(e.target.value)}
                              placeholder="Add notes..."
                              className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white px-4 py-4 focus:outline-none focus:border-orange-500"
                            />
                          </div>
                          <button 
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
                            className="w-full py-4 rounded-xl bg-orange-500 text-white font-bold hover:bg-orange-600 transition-colors"
                          >
                            Continue
                          </button>
                          <button 
                            onClick={() => setManualDepositMode(false)}
                            className="w-full text-center text-sm text-zinc-500 hover:text-emerald-400 underline"
                          >
                            Back to automatic calculation
                          </button>
                        </>
                      )}
                    </>
                  )}

                  {depositStep === 'simulate' && depositSimulation && (
                    <>
                      <div className="p-4 rounded-2xl bg-[#0d0d0d]/50 border border-white/[0.06] space-y-4">
                        {!depositSimulation.isManualOverride ? (
                          <>
                            <div className="flex justify-between items-center">
                              <span className="text-zinc-400">Binance Amount</span>
                              <span className="font-mono text-white text-lg">{formatMoney(depositSimulation.binanceAmount)}</span>
                            </div>
                            <div className="flex justify-between items-center text-red-400">
                              <span>Deposit Fee ({(depositSimulation.depositFee / depositSimulation.binanceAmount * 100).toFixed(1)}%)</span>
                              <span className="font-mono">-{formatMoney(depositSimulation.depositFee)}</span>
                            </div>
                            <div className="border-t border-white/[0.08] pt-4 flex justify-between items-center">
                              <span className="text-emerald-400 font-medium">You'll Receive</span>
                              <span className="font-mono text-emerald-400 text-xl font-bold">{formatMoney(depositSimulation.receiveAmount)}</span>
                            </div>
                          </>
                        ) : (
                          <div className="flex justify-between items-center">
                            <span className="text-emerald-400 font-medium">Manual Override Amount</span>
                            <span className="font-mono text-emerald-400 text-xl font-bold">{formatMoney(depositSimulation.receiveAmount)}</span>
                          </div>
                        )}
                      </div>
                      <p className="text-sm text-zinc-500 text-center">
                        This amount will be added to your Merin balance.
                      </p>
                      <div className="space-y-3">
                        <button 
                          onClick={() => setDepositStep('confirm')}
                          className="w-full py-4 rounded-xl bg-emerald-500 text-white font-bold hover:bg-emerald-600 transition-colors"
                        >
                          Proceed to Confirm
                        </button>
                        <button 
                          onClick={() => { setDepositStep('input'); setDepositSimulation(null); }}
                          className="w-full py-4 rounded-xl bg-[#1a1a1a] text-zinc-300 font-medium hover:bg-white/[0.08] transition-colors"
                        >
                          Back
                        </button>
                      </div>
                    </>
                  )}

                  {depositStep === 'confirm' && depositSimulation && (
                    <>
                      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30">
                        <p className="text-amber-400 font-medium text-center mb-2">Confirm Your Deposit</p>
                        <p className="text-sm text-zinc-400 text-center">
                          Have you already made this deposit of {formatMoney(depositSimulation.receiveAmount)} in your Merin account?
                        </p>
                      </div>
                      <div className="space-y-3">
                        <button 
                          onClick={handleConfirmDeposit}
                          className="w-full py-4 rounded-xl bg-emerald-500 text-white font-bold hover:bg-emerald-600 transition-colors flex items-center justify-center gap-2"
                          data-testid="mobile-confirm-deposit"
                        >
                          <CheckCircle2 className="w-5 h-5" /> Yes, I confirm
                        </button>
                        <button 
                          onClick={() => setDepositStep('simulate')}
                          className="w-full py-4 rounded-xl bg-[#1a1a1a] text-zinc-300 font-medium hover:bg-white/[0.08] transition-colors"
                        >
                          No, I'm just thinking
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mobile Full-Screen Overlay for Withdrawal Dialog */}
        {isMobile && withdrawalDialogOpen && (
          <div className="md:hidden fixed inset-0 z-[9999] bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="h-full w-full flex flex-col bg-gradient-to-b from-zinc-900 via-zinc-950 to-black">
              {/* Header */}
              <div className="flex-shrink-0 p-6 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-orange-500/20 flex items-center justify-center">
                      <ArrowUpFromLine className="w-6 h-6 text-orange-400" />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-white">
                        {withdrawalStep === 'input' && 'Simulate Withdrawal'}
                        {withdrawalStep === 'result' && 'Withdrawal Calculation'}
                        {withdrawalStep === 'confirm' && 'Confirm Withdrawal'}
                      </h1>
                      <p className="text-sm text-zinc-500">Withdraw funds from account</p>
                    </div>
                  </div>
                  <button 
                    onClick={resetWithdrawalDialog}
                    className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Content Area - Scrollable */}
              <div className="flex-1 overflow-y-auto px-6 pb-8">
                <div className="space-y-6">
                  <TransactionStepper
                    steps={[
                      { id: 'amount', label: 'Amount' },
                      { id: 'fees', label: 'Fees' },
                      { id: 'confirm', label: 'Confirm' },
                    ]}
                    activeStep={withdrawalStep === 'input' ? 1 : withdrawalStep === 'result' ? 2 : 3}
                  />
                  {withdrawalStep === 'input' && (
                    <>
                      <div className="p-4 rounded-2xl bg-[#0d0d0d]/50 border border-white/[0.06]">
                        <p className="text-sm text-zinc-400">Current Merin Balance</p>
                        <p className="text-2xl font-bold font-mono text-white">{formatLargeNumber(summary?.account_value || 0)}</p>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                          Withdrawal Amount (USDT)
                        </label>
                        <div className="relative">
                          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                          <input
                            type="number"
                            value={withdrawalAmount}
                            onChange={(e) => setWithdrawalAmount(e.target.value)}
                            placeholder="0.00"
                            className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-lg font-mono pl-10 pr-4 py-5 focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-500/20"
                            data-testid="mobile-withdrawal-amount-input"
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                          Notes (optional)
                        </label>
                        <input
                          value={withdrawalNotes}
                          onChange={(e) => setWithdrawalNotes(e.target.value)}
                          placeholder="Withdrawal reason..."
                          className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white px-4 py-4 focus:outline-none focus:border-orange-500"
                        />
                      </div>
                      <button 
                        onClick={handleSimulateWithdrawal}
                        className="w-full py-4 rounded-xl bg-orange-500 text-white font-bold hover:bg-orange-600 transition-colors flex items-center justify-center gap-2"
                        data-testid="mobile-calculate-withdrawal"
                      >
                        <Calculator className="w-5 h-5" /> Calculate Fees
                      </button>
                    </>
                  )}

                  {withdrawalStep === 'result' && withdrawalResult && (
                    <>
                      <div className="p-4 rounded-2xl bg-[#0d0d0d]/50 border border-white/[0.06] space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-zinc-400">Gross Amount</span>
                          <span className="font-mono text-white">{formatMoney(withdrawalResult.grossAmount)}</span>
                        </div>
                        <div className="flex justify-between items-center text-amber-400">
                          <span>Withdrawal Fee ({(withdrawalResult.withdrawalFee / withdrawalResult.grossAmount * 100).toFixed(1)}%)</span>
                          <span className="font-mono">-{formatMoney(withdrawalResult.withdrawalFee)}</span>
                        </div>
                        <div className="border-t border-white/[0.08] pt-4 flex justify-between items-center">
                          <span className="text-orange-400 font-medium">Net Withdrawal</span>
                          <span className="font-mono text-orange-400 text-xl font-bold">{formatMoney(withdrawalResult.netAmount)}</span>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <button 
                          onClick={() => setWithdrawalStep('confirm')}
                          className="w-full py-4 rounded-xl bg-orange-500 text-white font-bold hover:bg-orange-600 transition-colors"
                        >
                          Proceed to Confirm
                        </button>
                        <button 
                          onClick={() => { setWithdrawalStep('input'); setWithdrawalResult(null); }}
                          className="w-full py-4 rounded-xl bg-[#1a1a1a] text-zinc-300 font-medium hover:bg-white/[0.08] transition-colors"
                        >
                          Back
                        </button>
                      </div>
                    </>
                  )}

                  {withdrawalStep === 'confirm' && withdrawalResult && (
                    <>
                      <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30">
                        <p className="text-red-400 font-medium text-center mb-2">Confirm Your Withdrawal</p>
                        <p className="text-sm text-zinc-400 text-center">
                          {formatMoney(withdrawalResult.grossAmount)} will be deducted from your account.
                          You'll receive {formatMoney(withdrawalResult.netAmount)} in your Binance.
                        </p>
                      </div>
                      <div className="space-y-3">
                        <button 
                          onClick={handleCompleteWithdrawal}
                          className="w-full py-4 rounded-xl bg-red-500 text-white font-bold hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
                          data-testid="mobile-confirm-withdrawal"
                        >
                          <CheckCircle2 className="w-5 h-5" /> Yes, confirm withdrawal
                        </button>
                        <button 
                          onClick={() => setWithdrawalStep('result')}
                          className="w-full py-4 rounded-xl bg-[#1a1a1a] text-zinc-300 font-medium hover:bg-white/[0.08] transition-colors"
                        >
                          Go back
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mobile Full-Screen Overlay for Commission Dialog */}
        {isMobile && commissionDialogOpen && (
          <div className="md:hidden fixed inset-0 z-[9999] bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="h-full w-full flex flex-col bg-gradient-to-b from-zinc-900 via-zinc-950 to-black">
              {/* Header */}
              <div className="flex-shrink-0 p-6 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-purple-500/20 flex items-center justify-center">
                      <Award className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-white">Simulate Commission</h1>
                      <p className="text-sm text-zinc-500">Add referral commission</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setCommissionDialogOpen(false)}
                    className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Content Area - Scrollable */}
              <div className="flex-1 overflow-y-auto px-6 pb-8">
                <div className="space-y-6">
                  <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/30">
                    <p className="text-sm text-purple-400 leading-relaxed">
                      Commission is recorded separately and added to your total profit, but not to your account balance.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Commission Amount (USDT)
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                      <input
                        type="number"
                        step="0.01"
                        value={commissionAmount}
                        onChange={(e) => setCommissionAmount(e.target.value)}
                        placeholder="0.00"
                        className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-lg font-mono pl-10 pr-4 py-5 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
                        data-testid="mobile-commission-amount-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Notes (optional)
                    </label>
                    <input
                      value={commissionNotes}
                      onChange={(e) => setCommissionNotes(e.target.value)}
                      placeholder="Commission details..."
                      className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white px-4 py-4 focus:outline-none focus:border-purple-500"
                    />
                  </div>
                  <button 
                    onClick={handleSimulateCommission}
                    className="w-full py-4 rounded-xl bg-purple-500 text-white font-bold hover:bg-purple-600 transition-colors flex items-center justify-center gap-2"
                    data-testid="mobile-confirm-commission"
                  >
                    <Award className="w-5 h-5" /> Add Commission
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mobile Full-Screen Overlay for Adjust Trade Dialog */}
        {isMobile && enterAPDialogOpen && enterAPDate && (
          <div className="md:hidden fixed inset-0 z-[9999] bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="h-full w-full flex flex-col bg-gradient-to-b from-zinc-900 via-zinc-950 to-black">
              {/* Header */}
              <div className="flex-shrink-0 p-6 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-amber-500/20 flex items-center justify-center">
                      <Edit3 className="w-6 h-6 text-amber-400" />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-white">Adjust Trade</h1>
                      <p className="text-sm text-zinc-500">{enterAPDate.dateStr}</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setEnterAPDialogOpen(false)}
                    className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Content Area - Scrollable */}
              <div className="flex-1 overflow-y-auto px-6 pb-8">
                <div className="space-y-5">
                  {/* Current calculated values */}
                  <div className="p-4 rounded-2xl bg-[#0d0d0d]/50 border border-white/[0.06] space-y-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">Calculated Balance Before</span>
                      <span className="font-mono text-white">{formatLargeNumber(enterAPDate.balanceBefore || 0)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">Calculated Lot Size</span>
                      <span className="font-mono text-purple-400">{truncateTo2Decimals(enterAPDate.lotSize || (enterAPDate.balanceBefore || 0) / 980).toFixed(2)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">Target Profit</span>
                      <span className="font-mono text-zinc-400">{formatMoney(enterAPDate.targetProfit || truncateTo2Decimals((enterAPDate.lotSize || (enterAPDate.balanceBefore || 0) / 980) * 15))}</span>
                    </div>
                  </div>

                  {/* Adjustment type selection */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Did you deposit or withdraw on this day?
                    </label>
                    <Select value={adjustmentType} onValueChange={setAdjustmentType}>
                      <SelectTrigger className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white py-4 focus:border-amber-500">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#0d0d0d] border-white/[0.08] z-[99999]">
                        <SelectItem value="profit_only" className="text-white py-3">No, just enter profit</SelectItem>
                        <SelectItem value="with_deposit" className="text-white py-3">Yes, I made a deposit</SelectItem>
                        <SelectItem value="with_withdrawal" className="text-white py-3">Yes, I made a withdrawal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Deposit/Withdrawal amount */}
                  {adjustmentType !== 'profit_only' && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                        {adjustmentType === 'with_deposit' ? 'Deposit' : 'Withdrawal'} Amount (USD)
                      </label>
                      <div className="relative">
                        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                        <input
                          type="number"
                          step="0.01"
                          value={adjustmentAmount}
                          onChange={(e) => setAdjustmentAmount(e.target.value)}
                          placeholder="0.00"
                          className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white font-mono pl-10 pr-4 py-4 focus:outline-none focus:border-amber-500"
                          data-testid="mobile-adjustment-amount"
                        />
                      </div>
                    </div>
                  )}

                  {/* Manual balance adjustment */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Adjusted Balance Before Trade (optional)
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                      <input
                        type="number"
                        step="0.01"
                        value={adjustedBalance}
                        onChange={(e) => setAdjustedBalance(e.target.value)}
                        placeholder={enterAPDate.balanceBefore?.toString() || '0'}
                        className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white font-mono pl-10 pr-4 py-4 focus:outline-none focus:border-amber-500"
                        data-testid="mobile-adjusted-balance"
                      />
                    </div>
                    <p className="text-xs text-zinc-500">
                      If the calculated balance is incorrect, enter the actual balance you had before this trade
                    </p>
                  </div>

                  {/* Actual profit input */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Actual Profit (USD)
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                      <input
                        type="number"
                        step="0.01"
                        value={enterAPValue}
                        onChange={(e) => setEnterAPValue(e.target.value)}
                        placeholder="Enter your actual profit"
                        className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white text-lg font-mono pl-10 pr-4 py-5 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20"
                        data-testid="mobile-enter-ap-input"
                      />
                    </div>
                    <p className="text-xs text-zinc-500">
                      Enter positive for profit, negative for loss
                    </p>
                  </div>
                  
                  {/* Commission input */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                      Commission for the Day (USD) - Optional
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 text-lg font-mono">$</span>
                      <input
                        type="number"
                        step="0.01"
                        value={enterAPCommission}
                        onChange={(e) => setEnterAPCommission(e.target.value)}
                        placeholder="0.00"
                        className="w-full bg-[#0a0a0a]/80 border border-white/[0.06] rounded-xl text-white font-mono pl-10 pr-4 py-4 focus:outline-none focus:border-cyan-500"
                        data-testid="mobile-enter-ap-commission"
                      />
                    </div>
                  </div>

                  {/* Summary of adjustments */}
                  {(enterAPValue || adjustmentAmount || adjustedBalance || enterAPCommission) && (
                    <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-2 text-sm">
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
                      {enterAPCommission && parseFloat(enterAPCommission) > 0 && (
                        <div className="flex items-center justify-between">
                          <span className="text-zinc-400">Commission</span>
                          <span className="font-mono text-cyan-400">
                            +${parseFloat(enterAPCommission).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="space-y-3 pt-2">
                    <button 
                      onClick={handleSubmitEnterAP}
                      disabled={enterAPLoading || !enterAPValue}
                      className="w-full py-4 rounded-xl bg-amber-500 text-white font-bold hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      data-testid="mobile-submit-enter-ap"
                    >
                      {enterAPLoading ? 'Saving...' : 'Save Adjustment'}
                    </button>
                    <button 
                      onClick={() => setEnterAPDialogOpen(false)}
                      className="w-full py-4 rounded-xl bg-[#1a1a1a] text-zinc-300 font-medium hover:bg-white/[0.08] transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Simulate Deposit Dialog - Desktop Only */}
        <Dialog open={depositDialogOpen && !isMobile} onOpenChange={(open) => { if (!open) resetDepositDialog(); else setDepositDialogOpen(true); }}>
          <DialogContent className="glass-card border-white/[0.06] max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white">
                {depositStep === 'input' && 'Simulate Deposit'}
                {depositStep === 'simulate' && 'Deposit Calculation'}
                {depositStep === 'confirm' && 'Confirm Deposit'}
              </DialogTitle>
            </DialogHeader>
            
            <TransactionStepper
              steps={[
                { id: 'amount', label: 'Amount' },
                { id: 'calculate', label: 'Calculate' },
                { id: 'confirm', label: 'Confirm' },
              ]}
              activeStep={depositStep === 'input' ? 1 : depositStep === 'simulate' ? 2 : 3}
              className="mt-2"
            />

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
                      className="w-full text-center text-sm text-zinc-500 hover:text-orange-400 underline transition-colors"
                      data-testid="manual-deposit-link"
                    >
                      Wrong Calculations? Enter your total deposit manually
                    </button>
                  </>
                ) : (
                  <>
                    <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
                      <p className="text-sm text-orange-400">Manual Override Mode</p>
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
                      className="w-full text-center text-sm text-zinc-500 hover:text-orange-400 underline transition-colors"
                    >
                      Back to automatic calculation
                    </button>
                  </>
                )}
              </div>
            )}

            {depositStep === 'simulate' && depositSimulation && (
              <div className="space-y-4 mt-4">
                <div className="space-y-3 p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
                  {depositSimulation.isManualOverride ? (
                    <>
                      <div className="p-2 rounded bg-orange-500/10 border border-orange-500/20 mb-3">
                        <p className="text-xs text-orange-400 text-center">Manual Override - No fees applied</p>
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
                      <div className="border-t border-white/[0.08] pt-3 flex justify-between">
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
                <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-orange-400 mt-0.5" />
                    <div>
                      <p className="text-orange-400 font-medium">Confirm Your Action</p>
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

        {/* Withdrawal Dialog - Desktop Only */}
        <Dialog open={withdrawalDialogOpen && !isMobile} onOpenChange={(open) => { if (!open) resetWithdrawalDialog(); else setWithdrawalDialogOpen(true); }}>
          <DialogContent className="glass-card border-white/[0.06] max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white">
                {withdrawalStep === 'input' && 'Simulate Withdrawal'}
                {withdrawalStep === 'result' && 'Withdrawal Calculation'}
                {withdrawalStep === 'confirm' && 'Confirm Withdrawal'}
              </DialogTitle>
            </DialogHeader>

            <TransactionStepper
              steps={[
                { id: 'amount', label: 'Amount' },
                { id: 'fees', label: 'Fees' },
                { id: 'confirm', label: 'Confirm' },
              ]}
              activeStep={withdrawalStep === 'input' ? 1 : withdrawalStep === 'result' ? 2 : 3}
              className="mt-2"
            />

            {withdrawalStep === 'input' && (
              <div className="space-y-4 mt-4">
                <div className="p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
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
                <div className="space-y-3 p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Gross Amount</span>
                    <span className="font-mono text-white">{formatMoney(withdrawalResult.grossAmount)}</span>
                  </div>
                  <div className="flex justify-between text-amber-400">
                    <span>Merin Fee (3%)</span>
                    <span className="font-mono">-{formatMoney(withdrawalResult.merinFee)}</span>
                  </div>
                  <div className="border-t border-white/[0.08] pt-3 flex justify-between">
                    <span className="text-zinc-300 font-medium">Net Amount (to Binance)</span>
                    <span className="font-mono font-bold text-emerald-400">{formatMoney(withdrawalResult.netAmount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Merin Balance After</span>
                    <span className="font-mono text-white">{formatLargeNumber(withdrawalResult.balanceAfter)}</span>
                  </div>
                </div>
                
                <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/15">
                  <div className="flex items-center gap-2 text-orange-400 mb-1">
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

        {/* Commission Dialog - Desktop Only */}
        <Dialog open={commissionDialogOpen && !isMobile} onOpenChange={(open) => { if (!open) resetCommissionDialog(); else setCommissionDialogOpen(true); }}>
          <DialogContent className="glass-card border-white/[0.06] max-w-md">
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
                <Label className="text-zinc-300">Commission Date</Label>
                <Input
                  type="date"
                  value={commissionDate}
                  onChange={(e) => setCommissionDate(e.target.value)}
                  className="input-dark mt-1"
                  data-testid="commission-date-input"
                />
                <p className="text-xs text-zinc-500 mt-1">The date the commission should be applied to</p>
              </div>
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

        {/* Access Records and Reset Buttons */}
          <AdminActionsPanel
            accessRecordsOpen={accessRecordsOpen}
            setAccessRecordsOpen={setAccessRecordsOpen}
            setDepositRecordsOpen={setDepositRecordsOpen}
            setWithdrawalRecordsOpen={setWithdrawalRecordsOpen}
            setCommissionRecordsOpen={setCommissionRecordsOpen}
            resetDialogOpen={resetDialogOpen}
            setResetDialogOpen={setResetDialogOpen}
            resetStep={resetStep}
            setResetStep={setResetStep}
            resetPassword={resetPassword}
            setResetPassword={setResetPassword}
            resetNewBalance={resetNewBalance}
            setResetNewBalance={setResetNewBalance}
            handleResetConfirm={handleResetConfirm}
            handleResetWithPassword={handleResetWithPassword}
            resetResetDialog={resetResetDialog}
            summary={summary}
          />
      </div>
      )}

      {/* Onboarding Wizard */}
      <OnboardingWizard
        isOpen={onboardingWizardOpen}
        onClose={() => setOnboardingWizardOpen(false)}
        onComplete={async (data) => {
          setOnboardingWizardOpen(false);
          setIsFirstTime(false);
          // Wait a moment for backend to process
          await new Promise(resolve => setTimeout(resolve, 500));
          // Refresh user data from server to get updated trading_type and trading_start_date
          await refreshUser();
          // Reload all profit tracker data
          await loadData();
          
          // Calculate the expected balance from onboarding data
          const startingBalance = data?.starting_balance || 0;
          const tradeProfits = (data?.trade_entries || [])
            .filter(t => !t.missed)
            .reduce((sum, t) => sum + (t.actual_profit || 0), 0);
          const deposits = (data?.transactions || [])
            .filter(t => t.type === 'deposit')
            .reduce((sum, t) => sum + (t.amount || 0), 0);
          const withdrawals = (data?.transactions || [])
            .filter(t => t.type === 'withdrawal')
            .reduce((sum, t) => sum + (t.amount || 0), 0);
          const totalCommission = data?.total_commission || 0;
          
          const calculatedTotal = startingBalance + tradeProfits + deposits - withdrawals + totalCommission;
          
          // Show balance verification popup
          toast.success('Your profit tracker is ready!');
          openBalanceVerification(calculatedTotal);
        }}
        isReset={isResetOnboarding}
      />

      {/* Pre-Sync Validation Wizard */}
      <PreSyncWizard
        open={syncWizardOpen}
        onOpenChange={setSyncWizardOpen}
        step={syncWizardStep}
        validation={syncValidation}
        validationLoading={syncValidationLoading}
        newStartDate={newStartDate}
        onStartDateChange={setNewStartDate}
        onSetStartDate={handleSetStartDate}
        onMarkDidNotTrade={handleQuickDidNotTrade}
        onMarkAllDidNotTrade={handleMarkAllDidNotTrade}
        onAdjustTrade={openAdjustTradeFromWizard}
        preStartAcknowledged={preStartAcknowledged}
        onToggleAcknowledgePreStart={setPreStartAcknowledged}
        onContinuePastPreStart={handleAcknowledgePreStartTrades}
        calculatedBalance={calculatedBalance}
        actualBalanceInput={actualBalanceInput}
        onActualBalanceChange={setActualBalanceInput}
        onSync={handleBalanceOverride}
        syncLoading={balanceOverrideLoading}
        isMobile={isMobile}
      />

      {/* Balance Verification Dialog - shown after onboarding to sync with Merin */}
      <Dialog open={balanceVerificationOpen} onOpenChange={setBalanceVerificationOpen}>
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" /> Verify Your Balance
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
              <p className="text-sm text-zinc-400 mb-1">Your reported balance:</p>
              <p className="text-3xl font-bold text-emerald-400">
                ${calculatedBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            
            <div className="border-t border-white/[0.06] pt-4">
              <p className="text-sm text-zinc-400 mb-3">
                <span className="text-amber-400">Merin showing a different balance?</span><br/>
                Enter your actual Merin balance below to sync. This will not affect your past trading history.
              </p>
              
              <div>
                <Label className="text-zinc-300">Actual Merin Balance (USDT)</Label>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    value={actualBalanceInput}
                    onChange={(e) => setActualBalanceInput(e.target.value)}
                    placeholder="0.00"
                    className="input-dark pl-7 text-lg"
                    data-testid="actual-balance-input"
                  />
                </div>
                {actualBalanceInput && parseFloat(actualBalanceInput) !== calculatedBalance && (
                  <p className="text-xs mt-2 text-amber-400">
                    Adjustment: {parseFloat(actualBalanceInput) > calculatedBalance ? '+' : ''}
                    ${(parseFloat(actualBalanceInput) - calculatedBalance).toFixed(2)}
                  </p>
                )}
              </div>
            </div>
            
            <div className="flex gap-3 pt-2">
              <Button 
                variant="outline" 
                className="flex-1 btn-secondary" 
                onClick={() => setBalanceVerificationOpen(false)}
              >
                Skip
              </Button>
              <Button 
                onClick={handleBalanceOverride} 
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                disabled={balanceOverrideLoading}
                data-testid="sync-balance-button"
              >
                {balanceOverrideLoading ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Syncing...</>
                ) : (
                  <><CheckCircle2 className="w-4 h-4 mr-2" /> Sync Balance</>
                )}
              </Button>
            </div>
            
            <p className="text-xs text-zinc-500 text-center">
              Future trade days will use this synced balance as the starting point.
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Legacy Initial Balance Dialog - kept for backwards compatibility */}
      <Dialog open={initialBalanceDialogOpen} onOpenChange={setInitialBalanceDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Rocket className="w-5 h-5 text-orange-400" /> Welcome to Profit Tracker!
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
      <DepositRecordsDialog
        open={depositRecordsOpen}
        onOpenChange={setDepositRecordsOpen}
        deposits={deposits}
      />

      {/* Withdrawal Records Dialog */}
      <WithdrawalRecordsDialog
        open={withdrawalRecordsOpen}
        onOpenChange={setWithdrawalRecordsOpen}
        withdrawals={withdrawals}
        onConfirmReceipt={handleConfirmReceipt}
      />

      {/* Commission Records Dialog */}
      <CommissionRecordsDialog
        open={commissionRecordsOpen}
        onOpenChange={setCommissionRecordsOpen}
        commissions={commissions}
      />

      {/* Adjust Commission Dialog */}
      <Dialog open={adjustCommissionOpen} onOpenChange={setAdjustCommissionOpen}>
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-cyan-400" /> Adjust Commission
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-sm text-zinc-400">
              Record commission earnings for <span className="text-white font-medium">{adjustCommissionDate?.dateStr}</span>
            </p>
            <div>
              <Label className="text-zinc-300">Commission Amount (USDT)</Label>
              <div className="relative mt-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                <Input
                  type="number"
                  step="0.01"
                  value={adjustCommissionAmount}
                  onChange={(e) => setAdjustCommissionAmount(e.target.value)}
                  placeholder="0.00"
                  className="input-dark pl-7"
                  data-testid="adjust-commission-amount"
                />
              </div>
            </div>
            <label className="flex items-start gap-2 p-3 rounded-lg bg-white/[0.04] border border-white/[0.08]/50 cursor-pointer">
              <input
                type="checkbox"
                checked={adjustCommissionSkipDeposit}
                onChange={(e) => setAdjustCommissionSkipDeposit(e.target.checked)}
                className="mt-0.5 accent-amber-500"
                data-testid="skip-deposit-checkbox"
              />
              <div>
                <p className="text-sm text-zinc-300">Historical correction only</p>
                <p className="text-xs text-zinc-500 mt-0.5">Check this to record past commissions without adding to your account balance</p>
              </div>
            </label>
            <Button 
              onClick={handleSubmitAdjustCommission} 
              className="w-full btn-primary"
              disabled={adjustCommissionLoading}
              data-testid="confirm-adjust-commission"
            >
              {adjustCommissionLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Award className="w-4 h-4 mr-2" /> Save Commission
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Balance Audit Modal (triggered by Balance Trail button) */}
      {!isLicensee && (
        <BalanceAuditModal
          open={auditTrailModalOpen}
          onClose={() => setAuditTrailModalOpen(false)}
          userId={simulatedView?.memberId}
        />
      )}

      {/* AI Insights Section */}
      {!isLicensee && !simulatedView && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <AIFinancialSummary />
          <AIBalanceForecast />
          <AICommissionInsights />
        </div>
      )}

      {/* Projection Vision Card */}
      <Card className="glass-highlight">
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3">
          <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
            <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-orange-400" /> Projection Vision
            {!isLicensee && !simulatedView && dataHealth && (
              <DataHealthBadge healthData={dataHealth} onClick={() => openBalanceVerification(displayAccountValue)} />
            )}
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
              {/* Current Stats - Mobile optimized, hide LOT Size and Daily Profit for licensees */}
              <div className={`grid ${isLicensee ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4'} gap-2 sm:gap-4 p-3 sm:p-4 rounded-lg bg-[#0d0d0d]/50`}>
                <div>
                  <p className="text-[10px] sm:text-xs text-zinc-500">Current Balance</p>
                  <p className="font-mono text-sm sm:text-lg text-white truncate">{formatLargeNumber(effectiveAccountValue)}</p>
                </div>
                {/* Hide LOT Size and Daily Profit for licensees - they don't trade */}
                {!isLicensee && (
                  <>
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
                  </>
                )}
                {/* For licensees, show Total Profit instead */}
                {isLicensee && (
                  <div>
                    <p className="text-[10px] sm:text-xs text-zinc-500">Total Profit</p>
                    <p className={`font-mono text-sm sm:text-lg ${effectiveTotalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {effectiveTotalProfit >= 0 ? '+' : ''}{formatLargeNumber(effectiveTotalProfit)}
                    </p>
                  </div>
                )}
              </div>

              {/* Projection Chart - Mobile optimized height */}
              <div className="h-[180px] sm:h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={projectionChartData}>
                    <defs>
                      <linearGradient id="colorProjection" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F97316" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#F97316" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="name" stroke="#404040" fontSize={10} tickMargin={5} />
                    <YAxis 
                      stroke="#404040" 
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
                    <Line type="monotone" dataKey="balance" stroke="#F97316" strokeWidth={2} dot={{ fill: '#F97316', r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Projection Grid - Mobile optimized */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4">
                {projectionData.slice(1, 4).map((p, i) => (
                  <div key={p.period} className={`p-2 sm:p-4 rounded-lg border ${i === 0 ? 'bg-orange-500/10 border-orange-500/20' : 'bg-[#0d0d0d]/50 border-white/[0.06]'}`}>
                    <p className={`text-[10px] sm:text-xs ${i === 0 ? 'text-orange-400' : 'text-zinc-500'}`}>{p.period}</p>
                    <p className={`font-mono text-sm sm:text-lg ${i === 0 ? 'text-orange-400' : 'text-white'} mt-0.5 sm:mt-1 truncate`}>
                      {formatLargeNumber(p.balance)}
                    </p>
                    <p className="text-[9px] sm:text-xs text-zinc-500 mt-0.5 sm:mt-1 truncate">
                      LOT: {truncateTo2Decimals(p.lotSize).toFixed(2)}
                    </p>
                  </div>
                ))}
                
                {/* Year selector card */}
                <div className="p-2 sm:p-4 rounded-lg border bg-gradient-to-br from-orange-500/10 to-amber-500/10 border-orange-500/20">
                  <div className="flex items-center justify-between mb-1 sm:mb-2">
                    <p className="text-[10px] sm:text-xs text-purple-400">Year</p>
                    <Select value={selectedYears.toString()} onValueChange={(v) => setSelectedYears(parseInt(v))}>
                      <SelectTrigger className="w-14 sm:w-20 h-5 sm:h-6 text-[10px] sm:text-xs bg-[#0d0d0d]/50 border-white/[0.08]">
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
                      className="border border-white/[0.06] rounded-lg overflow-hidden"
                    >
                      <AccordionTrigger className="px-4 py-3 bg-[#0d0d0d]/50 hover:bg-[#0d0d0d] text-white">
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
                      <AccordionContent className="bg-[#0a0a0a]/50">
                        <table className="w-full data-table text-sm">
                          <thead>
                            <tr>
                              <th>Month</th>
                              <th>{months[0]?.isPastMonth ? 'Trades' : 'Trading Days'}</th>
                              <th>{months[0]?.isPastMonth ? 'Total Profit' : 'Final Balance'}</th>
                              {months[0]?.isPastMonth && <th>Commission</th>}
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {months.map((m) => (
                              <tr key={m.monthKey} className={m.isCurrentMonth ? 'bg-orange-500/10' : ''}>
                                <td className="font-medium">
                                  {m.monthName}
                                  {m.isCurrentMonth && (
                                    <span className="ml-2 text-xs text-orange-400">(Current)</span>
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
                                {m.isPastMonth && (
                                  <td className="font-mono text-purple-400">
                                    {(m.totalCommission || 0) > 0 ? `+${formatLargeNumber(m.totalCommission)}` : '-'}
                                  </td>
                                )}
                                <td>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="h-7 text-xs text-orange-400 border-orange-400/30 hover:bg-orange-400/10"
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

      {/* Recent Activity */}
      {!isLicensee && (
        <BalanceAuditTrail userId={simulatedView?.memberId} />
      )}

      {/* My Recent Transactions (member self-edit) */}
      {!isLicensee && !simulatedView?.memberId && (
        <MyTransactionEdit />
      )}

      {/* Daily Projection Dialog */}
      <DailyProjectionDialog
        open={dailyProjectionOpen}
        onOpenChange={setDailyProjectionOpen}
        selectedMonth={selectedMonth}
        dailyData={getDailyProjectionForSelectedMonth}
        isLicensee={isLicensee}
        isMasterAdmin={isMasterAdmin()}
        simulatedView={simulatedView}
        globalHolidays={globalHolidays}
        tradeLogs={tradeLogs}
        togglingTrade={togglingTrade}
        onToggleTradeOverride={handleToggleTradeOverride}
        onOpenEnterAP={handleOpenEnterAP}
        onDidNotTrade={handleDidNotTrade}
        onOpenAdjustCommission={handleOpenAdjustCommission}
      />

      {/* Adjust Trade Dialog - Desktop Only */}
      <Dialog open={enterAPDialogOpen && !isMobile} onOpenChange={setEnterAPDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06] max-w-md">
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
              <div className="p-3 rounded-lg bg-[#0d0d0d]/50 space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Calculated Balance Before</span>
                  <span className="font-mono text-white">{formatLargeNumber(enterAPDate.balanceBefore || 0)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Calculated Lot Size</span>
                  <span className="font-mono text-purple-400">{truncateTo2Decimals(enterAPDate.lotSize || (enterAPDate.balanceBefore || 0) / 980).toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">Target Profit</span>
                  <span className="font-mono text-zinc-400">{formatMoney(enterAPDate.targetProfit || truncateTo2Decimals((enterAPDate.lotSize || (enterAPDate.balanceBefore || 0) / 980) * 15))}</span>
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
              
              {/* Commission input */}
              <div className="space-y-2">
                <Label className="text-zinc-300">Commission for the Day (USD) - Optional</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                  <Input
                    type="number"
                    step="0.01"
                    value={enterAPCommission}
                    onChange={(e) => setEnterAPCommission(e.target.value)}
                    placeholder="0.00"
                    className="input-dark pl-7 font-mono"
                    data-testid="enter-ap-commission-input"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  Enter any referral commission you earned on this day
                </p>
              </div>

              {/* Summary of adjustments */}
              {(enterAPValue || adjustmentAmount || adjustedBalance || enterAPCommission) && (
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
                  {enterAPCommission && parseFloat(enterAPCommission) > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-zinc-400">Commission</span>
                      <span className="font-mono text-cyan-400">
                        +${parseFloat(enterAPCommission).toLocaleString()}
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
