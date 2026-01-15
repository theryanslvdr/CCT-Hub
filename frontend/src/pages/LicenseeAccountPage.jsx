import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Wallet, ArrowUpCircle, ArrowDownCircle, Clock, CheckCircle2, 
  XCircle, AlertCircle, Upload, Eye, Loader2, MessageSquare,
  DollarSign, Calendar, Image as ImageIcon, FileText, RefreshCw
} from 'lucide-react';
import { licenseeAPI, profitAPI, adminAPI } from '@/lib/api';

export const LicenseeAccountPage = () => {
  const { user, simulatedView, isMasterAdmin } = useAuth();
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [license, setLicense] = useState(null);
  const [isLicensee, setIsLicensee] = useState(false);
  const [accountSummary, setAccountSummary] = useState(null);
  
  // Check if simulating a licensee view
  const isSimulatingLicensee = simulatedView?.license_type && isMasterAdmin();
  
  // Deposit form
  const [depositDialogOpen, setDepositDialogOpen] = useState(false);
  const [depositForm, setDepositForm] = useState({
    amount: '',
    deposit_date: new Date().toISOString().split('T')[0],
    notes: '',
    screenshot: null
  });
  const [screenshotPreview, setScreenshotPreview] = useState(null);
  const [submittingDeposit, setSubmittingDeposit] = useState(false);
  
  // Withdrawal form
  const [withdrawalDialogOpen, setWithdrawalDialogOpen] = useState(false);
  const [withdrawalForm, setWithdrawalForm] = useState({
    amount: '',
    notes: ''
  });
  const [submittingWithdrawal, setSubmittingWithdrawal] = useState(false);
  
  // Transaction detail
  const [viewTransactionOpen, setViewTransactionOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // If simulating a licensee, load that licensee's data
      if (isSimulatingLicensee && simulatedView?.memberId) {
        // Load simulated licensee's data
        const licRes = await adminAPI.getLicenses();
        const memberLicense = licRes.data.licenses?.find(
          l => l.user_id === simulatedView.memberId && l.is_active
        );
        
        if (memberLicense) {
          // Get licensee's transactions
          const txRes = await adminAPI.getLicenseeTransactions();
          const memberTx = txRes.data.transactions?.filter(
            t => t.user_id === simulatedView.memberId
          ) || [];
          
          setTransactions(memberTx);
          setIsLicensee(true);
          setLicense(memberLicense);
          // Use license.current_amount as it's synced with profit tracker
          setAccountSummary({ 
            current_balance: memberLicense.current_amount || 0,
            account_value: memberLicense.current_amount || 0
          });
        } else {
          setIsLicensee(false);
        }
      } else {
        // Normal flow - load current user's data
        // Use profitAPI.getSummary as the single source of truth for balance
        const [txRes, summaryRes] = await Promise.all([
          licenseeAPI.getMyTransactions(),
          profitAPI.getSummary()
        ]);
        
        setTransactions(txRes.data.transactions || []);
        setIsLicensee(txRes.data.is_licensee);
        setLicense(txRes.data.license || null);
        
        // Use the unified profit summary for account_value (works for both licensees and regular users)
        // This ensures synchronization with Dashboard and Profit Tracker
        setAccountSummary({ 
          current_balance: summaryRes.data.account_value || 0,
          account_value: summaryRes.data.account_value || 0,
          is_licensee: summaryRes.data.is_licensee,
          license_type: summaryRes.data.license_type
        });
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load account data');
    } finally {
      setLoading(false);
    }
  }, [isSimulatingLicensee, simulatedView?.memberId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleScreenshotChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setDepositForm(prev => ({ ...prev, screenshot: file }));
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setScreenshotPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmitDeposit = async () => {
    if (!depositForm.amount || parseFloat(depositForm.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    if (!depositForm.deposit_date) {
      toast.error('Please select a deposit date');
      return;
    }
    if (!depositForm.screenshot) {
      toast.error('Please upload a screenshot as proof of deposit');
      return;
    }

    setSubmittingDeposit(true);
    try {
      const formData = new FormData();
      formData.append('amount', depositForm.amount);
      formData.append('deposit_date', depositForm.deposit_date);
      if (depositForm.notes) formData.append('notes', depositForm.notes);
      formData.append('screenshot', depositForm.screenshot);

      await licenseeAPI.submitDeposit(formData);
      toast.success('Deposit request submitted! Awaiting admin approval.');
      setDepositDialogOpen(false);
      setDepositForm({
        amount: '',
        deposit_date: new Date().toISOString().split('T')[0],
        notes: '',
        screenshot: null
      });
      setScreenshotPreview(null);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit deposit request');
    } finally {
      setSubmittingDeposit(false);
    }
  };

  const handleSubmitWithdrawal = async () => {
    if (!withdrawalForm.amount || parseFloat(withdrawalForm.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    const balance = accountSummary?.current_balance || 0;
    if (parseFloat(withdrawalForm.amount) > balance) {
      toast.error(`Insufficient balance. Maximum withdrawal: $${balance.toLocaleString()}`);
      return;
    }

    setSubmittingWithdrawal(true);
    try {
      const formData = new FormData();
      formData.append('amount', withdrawalForm.amount);
      if (withdrawalForm.notes) formData.append('notes', withdrawalForm.notes);

      await licenseeAPI.submitWithdrawal(formData);
      toast.success('Withdrawal request submitted! 5 business days processing time.');
      setWithdrawalDialogOpen(false);
      setWithdrawalForm({ amount: '', notes: '' });
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit withdrawal request');
    } finally {
      setSubmittingWithdrawal(false);
    }
  };

  const handleConfirmTransaction = async (txId) => {
    try {
      await licenseeAPI.confirmTransaction(txId);
      toast.success('Transaction confirmed!');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to confirm transaction');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      'pending': { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: Clock, label: 'Pending' },
      'processing': { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: RefreshCw, label: 'Processing' },
      'awaiting_confirmation': { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: AlertCircle, label: 'Awaiting Your Confirmation' },
      'approved': { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: CheckCircle2, label: 'Approved' },
      'completed': { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: CheckCircle2, label: 'Completed' },
      'rejected': { bg: 'bg-red-500/20', text: 'text-red-400', icon: XCircle, label: 'Rejected' },
    };
    const badge = badges[status] || badges['pending'];
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        <Icon className="w-3 h-3" />
        {badge.label}
      </span>
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  // Allow access if user is licensee OR if simulating a licensee
  if (!isLicensee && !isSimulatingLicensee) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Wallet className="w-16 h-16 text-zinc-600 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">Licensed Account Required</h2>
        <p className="text-zinc-500 max-w-md">
          This page is only available for Extended and Honorary Licensees.
          Contact the platform administrator if you believe you should have access.
        </p>
      </div>
    );
  }

  const pendingCount = transactions.filter(t => t.status === 'pending').length;
  const awaitingCount = transactions.filter(t => t.status === 'awaiting_confirmation').length;

  return (
    <div className="space-y-6" data-testid="licensee-account-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Wallet className="w-6 h-6" /> Deposit / Withdrawal
            {isSimulatingLicensee && (
              <span className="text-sm bg-amber-500/20 text-amber-400 px-2 py-1 rounded-full ml-2">
                Simulating: {simulatedView?.memberName}
              </span>
            )}
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            {license?.license_type === 'extended' ? 'Extended' : 'Honorary'} Licensee • 
            Since {formatDate(license?.start_date)}
          </p>
        </div>
        {!isSimulatingLicensee && (
          <div className="flex gap-3">
            <Button 
              onClick={() => setDepositDialogOpen(true)}
              className="btn-primary gap-2"
              data-testid="new-deposit-btn"
            >
              <ArrowUpCircle className="w-4 h-4" /> New Deposit
            </Button>
            <Button 
              onClick={() => setWithdrawalDialogOpen(true)}
              variant="outline"
              className="btn-secondary gap-2"
              data-testid="new-withdrawal-btn"
            >
              <ArrowDownCircle className="w-4 h-4" /> Request Withdrawal
            </Button>
          </div>
        )}
      </div>

      {/* Quick Stats - 3 cards only (removed Starting Amount) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wider">Current Balance</p>
                <p className="text-2xl font-bold text-white mt-1">
                  ${(accountSummary?.current_balance || license?.current_amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-emerald-500/10">
                <DollarSign className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wider">Pending Requests</p>
                <p className="text-2xl font-bold text-white mt-1">{pendingCount}</p>
              </div>
              <div className="p-3 rounded-lg bg-yellow-500/10">
                <Clock className="w-5 h-5 text-yellow-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wider">Needs Action</p>
                <p className="text-2xl font-bold text-white mt-1">{awaitingCount}</p>
              </div>
              <div className="p-3 rounded-lg bg-purple-500/10">
                <AlertCircle className="w-5 h-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Awaiting Confirmation Banner */}
      {awaitingCount > 0 && !isSimulatingLicensee && (
        <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-purple-400 shrink-0" />
            <div>
              <p className="text-purple-400 font-medium">
                {awaitingCount} transaction{awaitingCount > 1 ? 's' : ''} awaiting your confirmation
              </p>
              <p className="text-sm text-zinc-400 mt-0.5">
                Please review and confirm the transaction details below.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Transactions List */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" /> Transaction History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="bg-zinc-900/50 border border-zinc-800 mb-4">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="deposits">Deposits</TabsTrigger>
              <TabsTrigger value="withdrawals">Withdrawals</TabsTrigger>
              <TabsTrigger value="pending">Pending</TabsTrigger>
            </TabsList>

            {['all', 'deposits', 'withdrawals', 'pending'].map((tab) => (
              <TabsContent key={tab} value={tab}>
                {transactions.filter(tx => {
                  if (tab === 'all') return true;
                  if (tab === 'deposits') return tx.type === 'deposit';
                  if (tab === 'withdrawals') return tx.type === 'withdrawal';
                  if (tab === 'pending') return ['pending', 'processing', 'awaiting_confirmation'].includes(tx.status);
                  return true;
                }).length === 0 ? (
                  <div className="text-center py-12">
                    <FileText className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-zinc-500">No transactions found</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {transactions.filter(tx => {
                      if (tab === 'all') return true;
                      if (tab === 'deposits') return tx.type === 'deposit';
                      if (tab === 'withdrawals') return tx.type === 'withdrawal';
                      if (tab === 'pending') return ['pending', 'processing', 'awaiting_confirmation'].includes(tx.status);
                      return true;
                    }).map((tx) => (
                      <div 
                        key={tx.id}
                        className={`p-4 rounded-lg border transition-all ${
                          tx.status === 'awaiting_confirmation'
                            ? 'bg-purple-500/5 border-purple-500/30'
                            : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className={`p-2 rounded-lg ${
                              tx.type === 'deposit' 
                                ? 'bg-emerald-500/10' 
                                : 'bg-red-500/10'
                            }`}>
                              {tx.type === 'deposit' 
                                ? <ArrowUpCircle className="w-5 h-5 text-emerald-400" />
                                : <ArrowDownCircle className="w-5 h-5 text-red-400" />
                              }
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="text-white font-medium capitalize">{tx.type}</p>
                                {getStatusBadge(tx.status)}
                              </div>
                              <p className="text-sm text-zinc-500">
                                {formatDateTime(tx.created_at)}
                                {tx.deposit_date && ` • Deposit Date: ${formatDate(tx.deposit_date)}`}
                              </p>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className={`text-xl font-bold ${
                                tx.type === 'deposit' ? 'text-emerald-400' : 'text-red-400'
                              }`}>
                                {tx.type === 'deposit' ? '+' : '-'}${tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </p>
                              {tx.final_amount && tx.final_amount !== tx.amount && (
                                <p className="text-xs text-zinc-500">
                                  Final: ${tx.final_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </p>
                              )}
                            </div>
                            
                            <div className="flex gap-2">
                              {tx.status === 'awaiting_confirmation' && (
                                <Button 
                                  size="sm"
                                  onClick={() => handleConfirmTransaction(tx.id)}
                                  className="btn-primary"
                                  data-testid={`confirm-tx-${tx.id}`}
                                >
                                  <CheckCircle2 className="w-4 h-4 mr-1" /> Confirm
                                </Button>
                              )}
                              <Button 
                                size="sm" 
                                variant="ghost"
                                onClick={() => {
                                  setSelectedTransaction(tx);
                                  setViewTransactionOpen(true);
                                }}
                                className="text-blue-400 hover:text-blue-300"
                                data-testid={`view-tx-${tx.id}`}
                              >
                                <Eye className="w-4 h-4 mr-1" /> View
                              </Button>
                            </div>
                          </div>
                        </div>

                        {/* Feedback preview */}
                        {tx.feedback && tx.feedback.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-zinc-800">
                            <p className="text-xs text-zinc-500 mb-1">Latest Feedback:</p>
                            <p className="text-sm text-zinc-300">
                              {tx.feedback[tx.feedback.length - 1].message}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Deposit Dialog */}
      <Dialog open={depositDialogOpen} onOpenChange={setDepositDialogOpen}>
        <DialogContent className="bg-zinc-900 border border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <ArrowUpCircle className="w-5 h-5 text-emerald-400" /> Submit Deposit Request
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Upload proof of your deposit for admin verification
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <Label className="text-zinc-300">Deposit Amount ($)</Label>
              <Input
                type="number"
                value={depositForm.amount}
                onChange={(e) => setDepositForm(prev => ({ ...prev, amount: e.target.value }))}
                placeholder="0.00"
                className="input-dark mt-1"
                step="0.01"
                min="0"
                data-testid="deposit-amount-input"
              />
            </div>

            <div>
              <Label className="text-zinc-300">Deposit Date</Label>
              <Input
                type="date"
                value={depositForm.deposit_date}
                onChange={(e) => setDepositForm(prev => ({ ...prev, deposit_date: e.target.value }))}
                className="input-dark mt-1"
                data-testid="deposit-date-input"
              />
            </div>

            <div>
              <Label className="text-zinc-300">Notes (Optional)</Label>
              <Textarea
                value={depositForm.notes}
                onChange={(e) => setDepositForm(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Any additional information..."
                className="input-dark mt-1"
                rows={2}
              />
            </div>

            <div>
              <Label className="text-zinc-300">Screenshot (Required)</Label>
              <div className="mt-2">
                {screenshotPreview ? (
                  <div className="relative">
                    <img 
                      src={screenshotPreview} 
                      alt="Screenshot preview" 
                      className="w-full h-40 object-cover rounded-lg border border-zinc-700"
                    />
                    <Button
                      size="sm"
                      variant="ghost"
                      className="absolute top-2 right-2 bg-zinc-900/80 hover:bg-zinc-800"
                      onClick={() => {
                        setScreenshotPreview(null);
                        setDepositForm(prev => ({ ...prev, screenshot: null }));
                      }}
                    >
                      <XCircle className="w-4 h-4 text-red-400" />
                    </Button>
                  </div>
                ) : (
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-zinc-700 rounded-lg cursor-pointer hover:border-zinc-600 transition-colors">
                    <Upload className="w-8 h-8 text-zinc-500 mb-2" />
                    <span className="text-sm text-zinc-500">Click to upload screenshot</span>
                    <span className="text-xs text-zinc-600 mt-1">PNG, JPG up to 10MB</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleScreenshotChange}
                      className="hidden"
                      data-testid="deposit-screenshot-input"
                    />
                  </label>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setDepositDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmitDeposit}
              disabled={submittingDeposit}
              className="btn-primary"
              data-testid="submit-deposit-btn"
            >
              {submittingDeposit ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...</>
              ) : (
                <><ArrowUpCircle className="w-4 h-4 mr-2" /> Submit Request</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Withdrawal Dialog */}
      <Dialog open={withdrawalDialogOpen} onOpenChange={setWithdrawalDialogOpen}>
        <DialogContent className="bg-zinc-900 border border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <ArrowDownCircle className="w-5 h-5 text-red-400" /> Request Withdrawal
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Withdrawals take 5 business days to process
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <p className="text-sm text-blue-400">
                Available Balance: <span className="font-bold">${(accountSummary?.current_balance || 0).toLocaleString()}</span>
              </p>
            </div>

            <div>
              <Label className="text-zinc-300">Withdrawal Amount ($)</Label>
              <Input
                type="number"
                value={withdrawalForm.amount}
                onChange={(e) => setWithdrawalForm(prev => ({ ...prev, amount: e.target.value }))}
                placeholder="0.00"
                className="input-dark mt-1"
                step="0.01"
                min="0"
                max={accountSummary?.current_balance || 0}
                data-testid="withdrawal-amount-input"
              />
            </div>

            <div>
              <Label className="text-zinc-300">Notes (Optional)</Label>
              <Textarea
                value={withdrawalForm.notes}
                onChange={(e) => setWithdrawalForm(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Any additional information..."
                className="input-dark mt-1"
                rows={2}
              />
            </div>

            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5" />
                <div className="text-sm text-amber-400">
                  <p className="font-medium">Processing Time</p>
                  <p className="text-amber-400/80 mt-0.5">
                    Withdrawals require 5 business days for processing after approval.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setWithdrawalDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmitWithdrawal}
              disabled={submittingWithdrawal}
              className="bg-red-600 hover:bg-red-700 text-white"
              data-testid="submit-withdrawal-btn"
            >
              {submittingWithdrawal ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...</>
              ) : (
                <><ArrowDownCircle className="w-4 h-4 mr-2" /> Submit Request</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Transaction Dialog */}
      <Dialog open={viewTransactionOpen} onOpenChange={setViewTransactionOpen}>
        <DialogContent className="bg-zinc-900 border border-zinc-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              {selectedTransaction?.type === 'deposit' 
                ? <ArrowUpCircle className="w-5 h-5 text-emerald-400" />
                : <ArrowDownCircle className="w-5 h-5 text-red-400" />
              }
              {selectedTransaction?.type === 'deposit' ? 'Deposit' : 'Withdrawal'} Details
            </DialogTitle>
          </DialogHeader>

          {selectedTransaction && (
            <div className="space-y-4 py-4">
              <div className="flex items-center justify-between">
                <span className="text-zinc-500">Status</span>
                {getStatusBadge(selectedTransaction.status)}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-zinc-500">Amount</span>
                <span className={`text-lg font-bold ${
                  selectedTransaction.type === 'deposit' ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {selectedTransaction.type === 'deposit' ? '+' : '-'}
                  ${selectedTransaction.amount.toLocaleString()}
                </span>
              </div>

              {selectedTransaction.final_amount && selectedTransaction.final_amount !== selectedTransaction.amount && (
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500">Final Amount (After Processing)</span>
                  <span className="text-white font-bold">
                    ${selectedTransaction.final_amount.toLocaleString()}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-zinc-500">Submitted</span>
                <span className="text-white">{formatDateTime(selectedTransaction.created_at)}</span>
              </div>

              {selectedTransaction.deposit_date && (
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500">Deposit Date</span>
                  <span className="text-white">{formatDate(selectedTransaction.deposit_date)}</span>
                </div>
              )}

              {selectedTransaction.notes && (
                <div>
                  <span className="text-zinc-500 text-sm">Your Notes</span>
                  <p className="text-white mt-1 p-2 bg-zinc-800 rounded">{selectedTransaction.notes}</p>
                </div>
              )}

              {selectedTransaction.screenshot_url && (
                <div>
                  <span className="text-zinc-500 text-sm">Screenshot</span>
                  <a 
                    href={selectedTransaction.screenshot_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block mt-1"
                  >
                    <img 
                      src={selectedTransaction.screenshot_url} 
                      alt="Deposit screenshot" 
                      className="w-full max-h-48 object-cover rounded-lg border border-zinc-700 hover:border-blue-500 transition-colors"
                    />
                  </a>
                </div>
              )}

              {selectedTransaction.proof_url && (
                <div>
                  <span className="text-zinc-500 text-sm">Admin Proof of Transfer</span>
                  <a 
                    href={selectedTransaction.proof_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block mt-1"
                  >
                    <img 
                      src={selectedTransaction.proof_url} 
                      alt="Proof of transfer" 
                      className="w-full max-h-48 object-cover rounded-lg border border-zinc-700 hover:border-blue-500 transition-colors"
                    />
                  </a>
                </div>
              )}

              {/* Feedback History */}
              {selectedTransaction.feedback && selectedTransaction.feedback.length > 0 && (
                <div>
                  <span className="text-zinc-500 text-sm flex items-center gap-1">
                    <MessageSquare className="w-4 h-4" /> Communication History
                  </span>
                  <div className="mt-2 space-y-2 max-h-48 overflow-y-auto">
                    {selectedTransaction.feedback.map((fb, idx) => (
                      <div key={idx} className="p-2 bg-zinc-800 rounded text-sm">
                        <div className="flex items-center justify-between text-xs text-zinc-500 mb-1">
                          <span>{fb.from_admin ? 'Admin' : 'You'}</span>
                          <span>{formatDateTime(fb.created_at)}</span>
                        </div>
                        <p className="text-zinc-300">{fb.message}</p>
                        {fb.screenshot_url && (
                          <a 
                            href={fb.screenshot_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-blue-400 hover:underline text-xs mt-1"
                          >
                            <ImageIcon className="w-3 h-3" /> View Attachment
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confirm Button */}
              {selectedTransaction.status === 'awaiting_confirmation' && (
                <div className="pt-4 border-t border-zinc-800">
                  <p className="text-sm text-purple-400 mb-3">
                    Please review the details and confirm this transaction.
                  </p>
                  <Button 
                    onClick={() => {
                      handleConfirmTransaction(selectedTransaction.id);
                      setViewTransactionOpen(false);
                    }}
                    className="btn-primary w-full"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Confirm Transaction
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
