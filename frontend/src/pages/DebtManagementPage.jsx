import React, { useState, useEffect } from 'react';
import { debtAPI } from '@/lib/api';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { toast } from 'sonner';
import { Plus, CreditCard, Calendar, AlertCircle, CheckCircle, DollarSign, HelpCircle, Info, Trash2, Wallet } from 'lucide-react';

// Tooltip helper component
const InfoTooltip = ({ content }) => (
  <Tooltip>
    <TooltipTrigger asChild>
      <button className="ml-1.5 text-zinc-500 hover:text-zinc-300 transition-colors">
        <HelpCircle className="w-4 h-4" />
      </button>
    </TooltipTrigger>
    <TooltipContent className="max-w-xs bg-[#1a1a1a] text-zinc-200 border-white/[0.08]">
      <p>{content}</p>
    </TooltipContent>
  </Tooltip>
);

export const DebtManagementPage = () => {
  const [debts, setDebts] = useState([]);
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedDebt, setSelectedDebt] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [newDebt, setNewDebt] = useState({
    name: '',
    total_amount: '',
    minimum_payment: '',
    due_day: '1',
    interest_rate: '0',
    currency: 'USD',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [debtsRes, planRes] = await Promise.all([
        debtAPI.getAll(),
        debtAPI.getPlan(),
      ]);
      setDebts(debtsRes.data);
      setPlan(planRes.data);
    } catch (error) {
      console.error('Failed to load debts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDebt = async () => {
    if (!newDebt.name || !newDebt.total_amount || !newDebt.minimum_payment) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await debtAPI.create({
        name: newDebt.name,
        total_amount: parseFloat(newDebt.total_amount),
        minimum_payment: parseFloat(newDebt.minimum_payment),
        due_day: parseInt(newDebt.due_day),
        interest_rate: parseFloat(newDebt.interest_rate) || 0,
        currency: newDebt.currency,
      });
      toast.success('Debt added successfully!');
      setDialogOpen(false);
      setNewDebt({ name: '', total_amount: '', minimum_payment: '', due_day: '1', interest_rate: '0', currency: 'USD' });
      loadData();
    } catch (error) {
      toast.error('Failed to add debt');
    }
  };

  const handlePayment = async () => {
    if (!paymentAmount || parseFloat(paymentAmount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    try {
      await debtAPI.makePayment(selectedDebt.id, parseFloat(paymentAmount));
      toast.success('Payment recorded!');
      setPaymentDialogOpen(false);
      setPaymentAmount('');
      setSelectedDebt(null);
      loadData();
    } catch (error) {
      toast.error('Failed to record payment');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-orange-500/20 border-t-orange-500 rounded-full animate-spin" /></div>;
  }

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Overview Cards with Tooltips */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="glass-card" data-testid="total-debt-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400 flex items-center">
                    Total Debt
                    <InfoTooltip content="The sum of all remaining balances across all your debts. Pay this down to become debt-free!" />
                  </p>
                  <p className="text-3xl font-bold font-mono text-white mt-2">
                    ${formatNumber(plan?.total_debt || 0)}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center">
                  <CreditCard className="w-6 h-6 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card" data-testid="monthly-commitment-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400 flex items-center">
                    Monthly Commitment
                    <InfoTooltip content="Total of all minimum payments due each month. This is the minimum you should pay to stay current on all debts." />
                  </p>
                  <p className="text-3xl font-bold font-mono text-white mt-2">
                    ${formatNumber(plan?.monthly_commitment || 0)}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card" data-testid="account-balance-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400 flex items-center">
                    Account Balance
                    <InfoTooltip content="Your current trading account balance. Use profits from trading to pay down your debts faster!" />
                  </p>
                  <p className="text-3xl font-bold font-mono text-white mt-2">
                    ${formatNumber(plan?.account_value || 0)}
                  </p>
                </div>
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card" data-testid="status-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400 flex items-center">
                    Status
                    <InfoTooltip content={plan?.can_cover_this_month 
                      ? "Great! Your current balance can cover this month's minimum payments." 
                      : "Your current balance is not enough to cover minimum payments. Consider making additional trades or deposits."} />
                  </p>
                  <p className={`text-xl font-bold mt-2 ${plan?.can_cover_this_month ? 'text-emerald-400' : 'text-red-400'}`}>
                    {plan?.can_cover_this_month ? 'Can Cover' : 'Need More'}
                  </p>
                </div>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${plan?.can_cover_this_month ? 'bg-gradient-to-br from-emerald-500 to-emerald-600' : 'bg-gradient-to-br from-red-500 to-red-600'}`}>
                  {plan?.can_cover_this_month ? <CheckCircle className="w-6 h-6 text-white" /> : <AlertCircle className="w-6 h-6 text-white" />}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Add Debt Button */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogTrigger asChild>
          <Button className="btn-primary gap-2" data-testid="add-debt-button">
            <Plus className="w-4 h-4" /> Add Debt
          </Button>
        </DialogTrigger>
        <DialogContent className="glass-card border-white/[0.06]">
          <DialogHeader>
            <DialogTitle className="text-white">Add New Debt</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300 flex items-center">
                Debt Name
                <InfoTooltip content="Give your debt a recognizable name like 'Chase Credit Card' or 'Car Loan'" />
              </Label>
              <Input
                value={newDebt.name}
                onChange={(e) => setNewDebt({ ...newDebt, name: e.target.value })}
                placeholder="e.g., Credit Card, Personal Loan"
                className="input-dark mt-1"
                data-testid="debt-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300 flex items-center">
                  Total Amount
                  <InfoTooltip content="The total remaining balance you owe on this debt" />
                </Label>
                <Input
                  type="number"
                  value={newDebt.total_amount}
                  onChange={(e) => setNewDebt({ ...newDebt, total_amount: e.target.value })}
                  placeholder="0.00"
                  className="input-dark mt-1"
                  data-testid="debt-amount-input"
                />
              </div>
              <div>
                <Label className="text-zinc-300 flex items-center">
                  Minimum Payment
                  <InfoTooltip content="The minimum amount due each month to stay current" />
                </Label>
                <Input
                  type="number"
                  value={newDebt.minimum_payment}
                  onChange={(e) => setNewDebt({ ...newDebt, minimum_payment: e.target.value })}
                  placeholder="0.00"
                  className="input-dark mt-1"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-zinc-300 flex items-center">
                  Due Day (1-31)
                  <InfoTooltip content="The day of the month when your payment is due" />
                </Label>
                <Input
                  type="number"
                  min="1"
                  max="31"
                  value={newDebt.due_day}
                  onChange={(e) => setNewDebt({ ...newDebt, due_day: e.target.value })}
                  className="input-dark mt-1"
                />
              </div>
              <div>
                <Label className="text-zinc-300 flex items-center">
                  Interest Rate (%)
                  <InfoTooltip content="Annual interest rate (APR). Used to calculate how much extra you'll pay over time" />
                </Label>
                <Input
                  type="number"
                  step="0.1"
                  value={newDebt.interest_rate}
                  onChange={(e) => setNewDebt({ ...newDebt, interest_rate: e.target.value })}
                  placeholder="0.0"
                  className="input-dark mt-1"
                />
              </div>
            </div>
            <Button onClick={handleCreateDebt} className="w-full btn-primary" data-testid="confirm-add-debt">
              Add Debt
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Upcoming Payments */}
      {plan?.upcoming_payments?.length > 0 && (
        <Card className="glass-highlight">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-400" /> Upcoming Payments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {plan.upcoming_payments.map((payment, index) => (
                <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06]">
                  <div>
                    <p className="font-medium text-white">{payment.debt_name}</p>
                    <p className="text-sm text-zinc-400">
                      Due: {new Date(payment.due_date).toLocaleDateString()} ({payment.days_until} days)
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-mono font-bold text-white">${formatNumber(payment.amount)}</p>
                    <p className="text-xs text-amber-400">
                      Withdraw by: {new Date(payment.withdrawal_deadline).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Debts List */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white">Your Debts</CardTitle>
        </CardHeader>
        <CardContent>
          {debts.length > 0 ? (
            <div className="space-y-4">
              {debts.map((debt) => {
                const progress = ((debt.total_amount - debt.remaining_amount) / debt.total_amount) * 100;
                return (
                  <div key={debt.id} className="p-4 rounded-lg bg-[#0d0d0d]/50 border border-white/[0.06] hover:border-white/[0.08] transition-colors">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="font-medium text-white">{debt.name}</p>
                        <p className="text-sm text-zinc-500">Due day: {debt.due_day} | Rate: {debt.interest_rate}%</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="btn-secondary"
                        onClick={() => { setSelectedDebt(debt); setPaymentDialogOpen(true); }}
                        data-testid={`make-payment-${debt.id}`}
                      >
                        Make Payment
                      </Button>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-zinc-400">Remaining: ${formatNumber(debt.remaining_amount)}</span>
                        <span className="text-zinc-400">of ${formatNumber(debt.total_amount)}</span>
                      </div>
                      <Progress value={progress} className="h-2" />
                      <p className="text-xs text-emerald-400">{formatNumber(progress, 1)}% paid off</p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No debts recorded. Add a debt to start tracking your repayment progress!
            </div>
          )}
        </CardContent>
      </Card>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent className="glass-card border-white/[0.06]">
          <DialogHeader>
            <DialogTitle className="text-white">Record Payment for {selectedDebt?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="p-4 rounded-lg bg-[#0d0d0d]/50">
              <p className="text-sm text-zinc-400">Remaining Balance</p>
              <p className="text-2xl font-mono font-bold text-white">${formatNumber(selectedDebt?.remaining_amount || 0)}</p>
            </div>
            <div>
              <Label className="text-zinc-300">Payment Amount</Label>
              <Input
                type="number"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                placeholder="Enter payment amount"
                className="input-dark mt-1"
                data-testid="payment-amount-input"
              />
            </div>
            <Button onClick={handlePayment} className="w-full btn-primary" data-testid="confirm-payment">
              Record Payment
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      </div>
    </TooltipProvider>
  );
};
