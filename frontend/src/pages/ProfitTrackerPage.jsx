import React, { useState, useEffect } from 'react';
import { profitAPI, currencyAPI } from '@/lib/api';
import { formatCurrency, formatNumber, calculateWithdrawalFees } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, ArrowDownToLine, ArrowUpFromLine, Calculator, DollarSign, TrendingUp, TrendingDown, Wallet } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export const ProfitTrackerPage = () => {
  const [summary, setSummary] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  const [depositDialogOpen, setDepositDialogOpen] = useState(false);
  const [withdrawalDialogOpen, setWithdrawalDialogOpen] = useState(false);
  const [newDeposit, setNewDeposit] = useState({ amount: '', product: 'MOIL10', currency: 'USDT', notes: '' });
  const [withdrawalAmount, setWithdrawalAmount] = useState('');
  const [withdrawalResult, setWithdrawalResult] = useState(null);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');

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
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeposit = async () => {
    if (!newDeposit.amount || parseFloat(newDeposit.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      await profitAPI.createDeposit({
        amount: parseFloat(newDeposit.amount),
        product: newDeposit.product,
        currency: newDeposit.currency,
        notes: newDeposit.notes,
      });
      toast.success('Deposit recorded successfully!');
      setDepositDialogOpen(false);
      setNewDeposit({ amount: '', product: 'MOIL10', currency: 'USDT', notes: '' });
      loadData();
    } catch (error) {
      toast.error('Failed to record deposit');
    }
  };

  const handleWithdrawalSimulation = () => {
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
    setWithdrawalResult({
      ...fees,
      currentBalance: summary?.account_value || 0,
      balanceAfter: (summary?.account_value || 0) - amount,
    });
  };

  const convertAmount = (amount, toCurrency) => {
    const rate = rates[toCurrency] || 1;
    return amount * rate;
  };

  // Chart data for deposits over time
  const depositChartData = deposits.map((d, i) => ({
    name: `Deposit ${i + 1}`,
    amount: d.amount,
    cumulative: deposits.slice(0, i + 1).reduce((sum, dep) => sum + dep.amount, 0),
  }));

  // Pie chart data
  const pieData = [
    { name: 'Deposits', value: summary?.total_deposits || 0, color: '#3B82F6' },
    { name: 'Profit', value: summary?.total_actual_profit || 0, color: '#10B981' },
  ];

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div>;
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
                  ${formatNumber(summary?.account_value || 0)}
                </p>
                <p className="text-sm text-zinc-500 mt-1">
                  ≈ {formatCurrency(convertAmount(summary?.account_value || 0, selectedCurrency), selectedCurrency)}
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
                  ${formatNumber(summary?.total_deposits || 0)}
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
                  {(summary?.total_actual_profit || 0) >= 0 ? '+' : ''}${formatNumber(summary?.total_actual_profit || 0)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="profit-difference-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Projected vs Actual</p>
                <p className={`text-3xl font-bold font-mono mt-2 ${(summary?.profit_difference || 0) >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {(summary?.profit_difference || 0) >= 0 ? '+' : ''}${formatNumber(summary?.profit_difference || 0)}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${(summary?.profit_difference || 0) >= 0 ? 'bg-gradient-to-br from-emerald-500 to-emerald-600' : 'bg-gradient-to-br from-amber-500 to-amber-600'}`}>
                {(summary?.profit_difference || 0) >= 0 ? <TrendingUp className="w-6 h-6 text-white" /> : <TrendingDown className="w-6 h-6 text-white" />}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-4">
        <Dialog open={depositDialogOpen} onOpenChange={setDepositDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-primary gap-2" data-testid="add-deposit-button">
              <Plus className="w-4 h-4" /> Add Deposit
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white">Record New Deposit</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label className="text-zinc-300">Amount (USDT)</Label>
                <Input
                  type="number"
                  value={newDeposit.amount}
                  onChange={(e) => setNewDeposit({ ...newDeposit, amount: e.target.value })}
                  placeholder="Enter amount"
                  className="input-dark mt-1"
                  data-testid="deposit-amount-input"
                />
              </div>
              <div>
                <Label className="text-zinc-300">Product</Label>
                <Select value={newDeposit.product} onValueChange={(v) => setNewDeposit({ ...newDeposit, product: v })}>
                  <SelectTrigger className="input-dark mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MOIL10">MOIL10</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-zinc-300">Notes (optional)</Label>
                <Input
                  value={newDeposit.notes}
                  onChange={(e) => setNewDeposit({ ...newDeposit, notes: e.target.value })}
                  placeholder="Add notes..."
                  className="input-dark mt-1"
                />
              </div>
              <Button onClick={handleDeposit} className="w-full btn-primary" data-testid="confirm-deposit-button">
                Record Deposit
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={withdrawalDialogOpen} onOpenChange={setWithdrawalDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-secondary gap-2" data-testid="simulate-withdrawal-button">
              <ArrowUpFromLine className="w-4 h-4" /> Simulate Withdrawal
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-card border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-white">Withdrawal Simulation</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                <p className="text-sm text-zinc-400">Current Balance</p>
                <p className="text-2xl font-bold font-mono text-white">${formatNumber(summary?.account_value || 0)}</p>
              </div>
              <div>
                <Label className="text-zinc-300">Withdrawal Amount (USDT)</Label>
                <Input
                  type="number"
                  value={withdrawalAmount}
                  onChange={(e) => { setWithdrawalAmount(e.target.value); setWithdrawalResult(null); }}
                  placeholder="Enter amount"
                  className="input-dark mt-1"
                  data-testid="withdrawal-amount-input"
                />
              </div>
              <Button onClick={handleWithdrawalSimulation} className="w-full btn-secondary" data-testid="calculate-withdrawal-button">
                <Calculator className="w-4 h-4 mr-2" /> Calculate Fees
              </Button>

              {withdrawalResult && (
                <div className="space-y-3 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Gross Amount</span>
                    <span className="font-mono text-white">${formatNumber(withdrawalResult.grossAmount)}</span>
                  </div>
                  <div className="flex justify-between text-amber-400">
                    <span>Merin Fee (3%)</span>
                    <span className="font-mono">-${formatNumber(withdrawalResult.merinFee)}</span>
                  </div>
                  <div className="flex justify-between text-amber-400">
                    <span>Binance Fee</span>
                    <span className="font-mono">-$1.00</span>
                  </div>
                  <div className="border-t border-zinc-700 pt-3 flex justify-between">
                    <span className="text-zinc-400">Net Amount</span>
                    <span className="font-mono font-bold text-emerald-400">${formatNumber(withdrawalResult.netAmount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Balance After</span>
                    <span className="font-mono text-white">${formatNumber(withdrawalResult.balanceAfter)}</span>
                  </div>
                  <div className="mt-2 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                    <p className="text-xs text-blue-400">Processing Time: 1-2 business days</p>
                  </div>
                </div>
              )}
            </div>
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
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="glass-card lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-white">Deposit History</CardTitle>
          </CardHeader>
          <CardContent>
            {depositChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={depositChartData}>
                  <defs>
                    <linearGradient id="colorDeposit" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                  <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                  <YAxis stroke="#71717A" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }} />
                  <Area type="monotone" dataKey="cumulative" stroke="#3B82F6" fillOpacity={1} fill="url(#colorDeposit)" name="Cumulative" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-zinc-500">
                No deposits yet. Add your first deposit to see the chart!
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white">Account Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {(summary?.total_deposits || 0) > 0 || (summary?.total_actual_profit || 0) > 0 ? (
              <div className="flex flex-col items-center">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex gap-6 mt-4">
                  {pieData.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                      <span className="text-zinc-400 text-sm">{entry.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-[200px] flex items-center justify-center text-zinc-500">
                No data to display yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>

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
                    <th>Product</th>
                    <th>Currency</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {deposits.map((deposit) => (
                    <tr key={deposit.id}>
                      <td className="font-mono">{new Date(deposit.created_at).toLocaleDateString()}</td>
                      <td className="font-mono text-emerald-400">+${formatNumber(deposit.amount)}</td>
                      <td>{deposit.product}</td>
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
