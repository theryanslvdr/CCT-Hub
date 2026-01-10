import React, { useState, useEffect } from 'react';
import { profitAPI, currencyAPI } from '@/lib/api';
import { formatNumber, calculateWithdrawalFees } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Plus, ArrowDownToLine, ArrowUpFromLine, Calculator, DollarSign, 
  TrendingUp, TrendingDown, Wallet, RotateCcw, Rocket, Calendar,
  Clock, CheckCircle2, AlertTriangle, Eye, Sparkles
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';

// Finance number formatting
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

// Generate projection data based on daily compounding
const generateProjectionData = (accountBalance) => {
  const projections = [];
  let balance = accountBalance || 0;
  
  // Time periods in days (trading days)
  const periods = [
    { label: '1 Month', days: 22 },
    { label: '3 Months', days: 66 },
    { label: '6 Months', days: 132 },
    { label: '1 Year', days: 264 },
    { label: '2 Years', days: 528 },
    { label: '3 Years', days: 792 },
    { label: '4 Years', days: 1056 },
    { label: '5 Years', days: 1320 },
  ];
  
  // Current state
  const currentLotSize = balance / 980;
  const currentDailyProfit = currentLotSize * 15;
  
  projections.push({
    period: 'Today',
    balance: balance,
    lotSize: currentLotSize,
    dailyProfit: currentDailyProfit,
  });
  
  let runningBalance = balance;
  for (const period of periods) {
    // Simulate daily compounding
    for (let day = projections.length === 1 ? 0 : projections[projections.length - 2]?.totalDays || 0; day < period.days; day++) {
      const lotSize = runningBalance / 980;
      const dailyProfit = lotSize * 15;
      runningBalance += dailyProfit;
    }
    
    const lotSize = runningBalance / 980;
    const dailyProfit = lotSize * 15;
    
    projections.push({
      period: period.label,
      balance: runningBalance,
      lotSize: lotSize,
      dailyProfit: dailyProfit,
      totalDays: period.days,
    });
  }
  
  return projections;
};

// Generate daily projection table (like Excel)
const generateDailyProjection = (accountBalance, days = 30, userTimezone = 'Asia/Manila') => {
  const data = [];
  let balance = accountBalance || 0;
  const today = new Date();
  
  for (let i = 0; i <= days; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    
    // Skip weekends
    const dayOfWeek = date.getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) continue;
    
    const lotSize = balance / 980;
    const dailyProfit = lotSize * 15;
    
    data.push({
      date: date.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric',
        timeZone: userTimezone 
      }),
      projectedBal: balance,
      lotSize: lotSize,
      targetProfit: dailyProfit,
      fundsBeforeTrade: balance,
    });
    
    balance += dailyProfit;
  }
  
  return data;
};

export const ProfitTrackerPage = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Dialog states
  const [depositDialogOpen, setDepositDialogOpen] = useState(false);
  const [depositStep, setDepositStep] = useState('input'); // 'input', 'simulate', 'confirm'
  const [withdrawalDialogOpen, setWithdrawalDialogOpen] = useState(false);
  const [withdrawalStep, setWithdrawalStep] = useState('input'); // 'input', 'result', 'confirm'
  const [initialBalanceDialogOpen, setInitialBalanceDialogOpen] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  
  // Form states
  const [depositAmount, setDepositAmount] = useState('');
  const [depositNotes, setDepositNotes] = useState('');
  const [depositSimulation, setDepositSimulation] = useState(null);
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [withdrawalResult, setWithdrawalResult] = useState(null);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [initialBalance, setInitialBalance] = useState('');
  const [isFirstTime, setIsFirstTime] = useState(false);
  
  // Projection state
  const [projectionView, setProjectionView] = useState('summary'); // 'summary' or 'table'
  
  const userTimezone = user?.timezone || 'Asia/Manila';

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, depositsRes, ratesRes] = await Promise.all([
        profitAPI.getSummary(),
        profitAPI.getDeposits(),
        currencyAPI.getRates('USDT'),
      ]);
      setSummary(summaryRes.data);
      setDeposits(depositsRes.data);
      setRates(ratesRes.data.rates || {});
      
      if (depositsRes.data.length === 0) {
        setIsFirstTime(true);
        setInitialBalanceDialogOpen(true);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Deposit flow handlers
  const handleSimulateDeposit = () => {
    if (!depositAmount || parseFloat(depositAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    
    const amount = parseFloat(depositAmount);
    const depositFee = amount * 0.01; // 1% deposit fee
    const receiveAmount = amount - depositFee;
    
    setDepositSimulation({
      binanceAmount: amount,
      depositFee: depositFee,
      receiveAmount: receiveAmount,
    });
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
    });
    setWithdrawalStep('result');
  };

  const handleCompleteWithdrawal = async () => {
    try {
      // In a real app, this would trigger actual withdrawal
      // For now, we'll just record it as a negative deposit/withdrawal
      await api.post('/profit/withdrawal', {
        amount: parseFloat(withdrawalAmount),
      });
      toast.success('Withdrawal initiated! Check your Binance account in 1-2 business days.');
      resetWithdrawalDialog();
      loadData();
    } catch (error) {
      // If endpoint doesn't exist, show simulation message
      toast.info('Withdrawal simulation complete. In production, funds would be transferred to your Binance account.');
      resetWithdrawalDialog();
    }
  };

  const resetWithdrawalDialog = () => {
    setWithdrawalDialogOpen(false);
    setWithdrawalStep('input');
    setWithdrawalAmount('');
    setWithdrawalResult(null);
  };

  // Initial balance handler
  const handleInitialBalance = async () => {
    if (!initialBalance || parseFloat(initialBalance) < 0) {
      toast.error('Please enter a valid initial balance');
      return;
    }

    try {
      const amount = parseFloat(initialBalance);
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

  // Reset handler
  const handleResetTracker = async () => {
    try {
      await api.delete('/profit/reset');
      toast.success('Profit tracker has been reset. Start fresh!');
      setResetDialogOpen(false);
      loadData();
    } catch (error) {
      toast.error('Reset feature requires backend support. Contact admin.');
    }
  };

  const convertAmount = (amount, toCurrency) => {
    const rate = rates[toCurrency] || 1;
    return amount * rate;
  };

  // Projection data
  const projectionData = generateProjectionData(summary?.account_value || 0);
  const dailyProjection = generateDailyProjection(summary?.account_value || 0, 30, userTimezone);

  // Chart data for projection
  const projectionChartData = projectionData.slice(1).map(p => ({
    name: p.period,
    balance: p.balance,
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-card" data-testid="account-value-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Account Value</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">
                  {formatMoney(summary?.account_value || 0)}
                </p>
                <p className="text-sm text-zinc-500 mt-1">
                  ≈ {selectedCurrency === 'PHP' ? '₱' : selectedCurrency} {formatNumber(convertAmount(summary?.account_value || 0, selectedCurrency))}
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
              <div>
                <p className="text-sm text-zinc-400">Total Deposits</p>
                <p className="text-3xl font-bold font-mono text-white mt-2">
                  {formatMoney(summary?.total_deposits || 0)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 flex items-center justify-center">
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
                <p className={`text-3xl font-bold font-mono mt-2 ${(summary?.total_actual_profit || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {(summary?.total_actual_profit || 0) >= 0 ? '+' : ''}{formatMoney(summary?.total_actual_profit || 0)}
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
                  {((summary?.account_value || 0) / 980).toFixed(4)}
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

      {/* Actions */}
      <div className="flex flex-wrap gap-4">
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
                  <p className="text-2xl font-bold font-mono text-white">{formatMoney(summary?.account_value || 0)}</p>
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
                  <div className="flex justify-between text-amber-400">
                    <span>Binance Fee</span>
                    <span className="font-mono">-$1.00</span>
                  </div>
                  <div className="border-t border-zinc-700 pt-3 flex justify-between">
                    <span className="text-zinc-300 font-medium">Net Amount (to Binance)</span>
                    <span className="font-mono font-bold text-emerald-400">{formatMoney(withdrawalResult.netAmount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Merin Balance After</span>
                    <span className="font-mono text-white">{formatMoney(withdrawalResult.balanceAfter)}</span>
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

        <Select value={selectedCurrency} onValueChange={setSelectedCurrency}>
          <SelectTrigger className="w-32 input-dark">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="USD">USD</SelectItem>
            <SelectItem value="PHP">PHP</SelectItem>
            <SelectItem value="EUR">EUR</SelectItem>
            <SelectItem value="GBP">GBP</SelectItem>
          </SelectContent>
        </Select>

        {/* Reset Button */}
        <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="btn-secondary gap-2 text-amber-400 hover:text-amber-300" data-testid="reset-tracker-button">
              <RotateCcw className="w-4 h-4" /> Reset Tracker
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2 text-red-400">
                <RotateCcw className="w-5 h-5" /> Reset Profit Tracker
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
                <p className="font-medium mb-2">Warning: This action cannot be undone!</p>
                <p className="text-sm">Resetting will delete all your:</p>
                <ul className="list-disc list-inside text-sm mt-2">
                  <li>Deposit records</li>
                  <li>Trade logs</li>
                  <li>Profit calculations</li>
                </ul>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => setResetDialogOpen(false)}>
                  Cancel
                </Button>
                <Button className="flex-1 bg-red-500 hover:bg-red-600 text-white" onClick={handleResetTracker} data-testid="confirm-reset-button">
                  Reset Everything
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

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
              <Eye className="w-4 h-4 mr-1" /> Daily Table
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
                  <p className="font-mono text-lg text-white">{formatMoney(summary?.account_value || 0)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">LOT Size</p>
                  <p className="font-mono text-lg text-purple-400">{((summary?.account_value || 0) / 980).toFixed(4)}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Daily Profit (×15)</p>
                  <p className="font-mono text-lg text-emerald-400">{formatMoney(((summary?.account_value || 0) / 980) * 15)}</p>
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
                      tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                      formatter={(value) => [formatMoney(value), 'Projected Balance']}
                    />
                    <Line type="monotone" dataKey="balance" stroke="#3B82F6" strokeWidth={2} dot={{ fill: '#3B82F6' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Projection Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {projectionData.slice(1).map((p, i) => (
                  <div key={p.period} className={`p-4 rounded-lg border ${i === 0 ? 'bg-blue-500/10 border-blue-500/30' : 'bg-zinc-900/50 border-zinc-800'}`}>
                    <p className={`text-xs ${i === 0 ? 'text-blue-400' : 'text-zinc-500'}`}>{p.period}</p>
                    <p className={`font-mono text-lg ${i === 0 ? 'text-blue-400' : 'text-white'} mt-1`}>
                      {formatMoney(p.balance)}
                    </p>
                    <p className="text-xs text-zinc-500 mt-1">
                      LOT: {p.lotSize.toFixed(2)} | Daily: {formatMoney(p.dailyProfit)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-zinc-400">
                Daily projection based on compounding (Balance ÷ 980 × 15 per trading day). Weekends excluded.
              </p>
              <div className="overflow-x-auto max-h-[400px]">
                <table className="w-full data-table text-sm">
                  <thead className="sticky top-0 bg-zinc-900">
                    <tr>
                      <th>Date</th>
                      <th>Projected Balance</th>
                      <th>LOT Size</th>
                      <th>Target Profit</th>
                      <th>Funds Before Trade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dailyProjection.map((row, i) => (
                      <tr key={i} className={i === 0 ? 'bg-blue-500/10' : ''}>
                        <td className="font-medium">{row.date}</td>
                        <td className="font-mono text-white">{formatMoney(row.projectedBal)}</td>
                        <td className="font-mono text-purple-400">{row.lotSize.toFixed(4)}</td>
                        <td className="font-mono text-emerald-400">{formatMoney(row.targetProfit)}</td>
                        <td className="font-mono text-zinc-400">{formatMoney(row.fundsBeforeTrade)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Deposits Table */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white">Deposit Records</CardTitle>
        </CardHeader>
        <CardContent>
          {deposits.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
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
                      <td className="text-zinc-500">{deposit.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No deposits recorded yet. Add your first deposit to get started!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
