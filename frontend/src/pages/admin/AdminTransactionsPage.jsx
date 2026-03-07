import React, { useState, useEffect, useCallback } from 'react';
import { adminAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { formatNumber } from '@/lib/utils';
import { 
  ArrowDownToLine, ArrowUpFromLine, DollarSign, Users, 
  ChevronLeft, ChevronRight, TrendingUp, TrendingDown, RefreshCw,
  Edit3, Trash2, AlertTriangle, CheckCircle2, Search, X, HelpCircle
} from 'lucide-react';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';

export const AdminTransactionsPage = () => {
  const { isSuperAdmin, isMasterAdmin } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [userSearch, setUserSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  
  // Correction dialog state
  const [correctDialogOpen, setCorrectDialogOpen] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);
  const [correctionAmount, setCorrectionAmount] = useState('');
  const [correctionReason, setCorrectionReason] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [txRes, statsRes] = await Promise.all([
        adminAPI.getTeamTransactions(page, 20, filterType === 'all' ? null : filterType, userSearch || null),
        adminAPI.getTransactionStats()
      ]);
      
      setTransactions(txRes.data.transactions || []);
      setTotalPages(txRes.data.total_pages || 1);
      setTotal(txRes.data.total || 0);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load transactions:', error);
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  }, [page, filterType, userSearch]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSearch = () => {
    setUserSearch(searchInput.trim());
    setPage(1);
  };

  const clearSearch = () => {
    setSearchInput('');
    setUserSearch('');
    setPage(1);
  };

  const handleRefresh = () => {
    loadData();
    toast.success('Transactions refreshed');
  };

  const openCorrection = (tx) => {
    setSelectedTx(tx);
    setCorrectionAmount(String(Math.abs(tx.amount)));
    setCorrectionReason('');
    setCorrectDialogOpen(true);
  };

  const handleCorrect = async () => {
    if (!selectedTx || !correctionAmount) return;
    try {
      let newAmount = parseFloat(correctionAmount);
      if (selectedTx.type === 'withdrawal' || selectedTx.is_withdrawal) {
        newAmount = -Math.abs(newAmount);
      }
      await adminAPI.correctTransaction(selectedTx.id, {
        new_amount: newAmount,
        reason: correctionReason || 'Admin correction',
      });
      toast.success('Transaction corrected successfully');
      setCorrectDialogOpen(false);
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to correct transaction');
    }
  };

  const handleDeleteTx = async (tx) => {
    if (!window.confirm(`Delete this ${tx.type} of $${formatNumber(Math.abs(tx.amount), 2)} by ${tx.user_name}? This action is logged.`)) return;
    try {
      await adminAPI.deleteTransaction(tx.id);
      toast.success('Transaction deleted');
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to delete transaction');
    }
  };

  // Check access
  if (!isSuperAdmin() && !isMasterAdmin()) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-zinc-500">Only Super Admin and Master Admin can access this page.</p>
      </div>
    );
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Team Transactions</h1>
          <p className="text-zinc-400">Manage deposits, withdrawals, and view profit entries</p>
        </div>
        <Button onClick={handleRefresh} variant="outline" className="btn-secondary gap-2" data-testid="refresh-transactions">
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-card" data-testid="total-deposits-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Deposits</p>
                <p className="text-3xl font-bold font-mono text-emerald-400 mt-2">${formatNumber(stats?.total_deposits || 0, 2)}</p>
                <p className="text-xs text-zinc-500 mt-1">{stats?.deposit_count || 0} transactions</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                <ArrowDownToLine className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="total-withdrawals-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Total Withdrawals</p>
                <p className="text-3xl font-bold font-mono text-orange-400 mt-2">${formatNumber(stats?.total_withdrawals || 0, 2)}</p>
                <p className="text-xs text-zinc-500 mt-1">{stats?.withdrawal_count || 0} transactions</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
                <ArrowUpFromLine className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="net-flow-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Net Flow</p>
                <p className={`text-3xl font-bold font-mono mt-2 ${(stats?.net_flow || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {(stats?.net_flow || 0) >= 0 ? '+' : '-'}${formatNumber(Math.abs(stats?.net_flow || 0), 2)}
                </p>
                <p className="text-xs text-zinc-500 mt-1">{(stats?.net_flow || 0) >= 0 ? 'Inflow' : 'Outflow'}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${(stats?.net_flow || 0) >= 0 ? 'bg-gradient-to-br from-emerald-500 to-green-600' : 'bg-gradient-to-br from-red-500 to-red-600'}`}>
                {(stats?.net_flow || 0) >= 0 ? <TrendingUp className="w-6 h-6 text-white" /> : <TrendingDown className="w-6 h-6 text-white" />}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="unique-depositors-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Unique Depositors</p>
                <p className="text-3xl font-bold font-mono text-blue-400 mt-2">{stats?.unique_depositors || 0}</p>
                <p className="text-xs text-zinc-500 mt-1">Team members with deposits</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Today's Activity */}
      {(stats?.today_deposits > 0 || stats?.today_withdrawals > 0) && (
        <Card className="glass-card border-blue-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-zinc-400">Today:</span>
              </div>
              <div className="flex items-center gap-2">
                <ArrowDownToLine className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400 font-mono">${formatNumber(stats?.today_deposits || 0, 2)}</span>
                <span className="text-zinc-500">deposits</span>
              </div>
              <div className="flex items-center gap-2">
                <ArrowUpFromLine className="w-4 h-4 text-orange-400" />
                <span className="text-orange-400 font-mono">${formatNumber(stats?.today_withdrawals || 0, 2)}</span>
                <span className="text-zinc-500">withdrawals</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transactions Table */}
      <Card className="glass-card">
        <CardHeader className="flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-1.5">
              <CardTitle className="text-white">Transaction History</CardTitle>
              <Popover>
                <PopoverTrigger asChild>
                  <button className="text-zinc-500 hover:text-blue-400 transition-colors" data-testid="admin-tx-help-button">
                    <HelpCircle className="w-3.5 h-3.5" />
                  </button>
                </PopoverTrigger>
                <PopoverContent className="w-72 p-0 bg-zinc-900 border-zinc-700" side="bottom" align="start">
                  <div className="p-3 space-y-2.5">
                    <p className="text-xs font-semibold text-white">How to Correct a Transaction</p>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-[10px] font-bold text-blue-400">1</span>
                        </div>
                        <p className="text-[11px] text-zinc-400">Find the transaction and click the <Edit3 className="w-3 h-3 inline text-blue-400" /> <span className="text-blue-400">pencil icon</span> in the Actions column.</p>
                      </div>
                      <div className="flex gap-2">
                        <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-[10px] font-bold text-blue-400">2</span>
                        </div>
                        <p className="text-[11px] text-zinc-400">Enter the correct amount and a reason for the correction.</p>
                      </div>
                      <div className="flex gap-2">
                        <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-[10px] font-bold text-blue-400">3</span>
                        </div>
                        <p className="text-[11px] text-zinc-400">Click <span className="text-white font-medium">Apply Correction</span>. The member&apos;s balance updates immediately.</p>
                      </div>
                    </div>
                    <div className="pt-2 border-t border-zinc-800 space-y-1">
                      <p className="text-[10px] text-zinc-500">Corrections are logged in the audit trail. The member will be notified and their edit access is locked.</p>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
            </div>
            <Tabs value={filterType} onValueChange={(v) => { setFilterType(v); setPage(1); }}>
              <TabsList className="bg-zinc-900/50">
                <TabsTrigger value="all" className="data-[state=active]:bg-blue-500/20">All</TabsTrigger>
                <TabsTrigger value="deposit" className="data-[state=active]:bg-emerald-500/20">Deposits</TabsTrigger>
                <TabsTrigger value="withdrawal" className="data-[state=active]:bg-orange-500/20">Withdrawals</TabsTrigger>
                <TabsTrigger value="profit" className="data-[state=active]:bg-blue-500/20">Profits</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
          
          {/* User Search */}
          <div className="flex gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <Input
                placeholder="Search by name or email..."
                value={searchInput}
                onChange={e => setSearchInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                className="pl-9 input-dark"
                data-testid="user-search-input"
              />
            </div>
            <Button onClick={handleSearch} size="sm" className="bg-blue-600 hover:bg-blue-700" data-testid="user-search-btn">
              Search
            </Button>
            {userSearch && (
              <Button onClick={clearSearch} size="sm" variant="outline" className="btn-secondary gap-1" data-testid="clear-search-btn">
                <X className="w-3 h-3" /> Clear
              </Button>
            )}
          </div>
          
          {userSearch && (
            <p className="text-xs text-blue-400">Filtered by: "{userSearch}" — {total} result{total !== 1 ? 's' : ''}</p>
          )}
        </CardHeader>
        
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            </div>
          ) : transactions.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full data-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Member</th>
                      <th>Amount</th>
                      <th>Product/Notes</th>
                      <th>Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>
                          <div className="flex items-center gap-2">
                            {tx.type === 'withdrawal' ? (
                              <>
                                <ArrowUpFromLine className="w-4 h-4 text-orange-400" />
                                <span className="status-badge bg-orange-500/20 text-orange-400">Withdrawal</span>
                              </>
                            ) : tx.type === 'profit' ? (
                              <>
                                <TrendingUp className="w-4 h-4 text-blue-400" />
                                <span className="status-badge bg-blue-500/20 text-blue-400">Profit</span>
                              </>
                            ) : (
                              <>
                                <ArrowDownToLine className="w-4 h-4 text-emerald-400" />
                                <span className="status-badge bg-emerald-500/20 text-emerald-400">Deposit</span>
                              </>
                            )}
                          </div>
                        </td>
                        <td>
                          <div>
                            <p className="font-medium text-white">{tx.user_name}</p>
                            <p className="text-xs text-zinc-500">{tx.user_email}</p>
                          </div>
                        </td>
                        <td>
                          <span className={`font-mono font-bold ${tx.type === 'withdrawal' ? 'text-orange-400' : tx.type === 'profit' ? 'text-blue-400' : 'text-emerald-400'}`}>
                            {tx.type === 'withdrawal' ? '-' : '+'} ${formatNumber(Math.abs(tx.amount), 2)}
                          </span>
                          {tx.type === 'withdrawal' && tx.net_amount && (
                            <p className="text-xs text-zinc-500">Net: ${formatNumber(tx.net_amount, 2)}</p>
                          )}
                        </td>
                        <td>
                          <span className="text-zinc-400 text-sm">{tx.product || tx.notes || '-'}</span>
                        </td>
                        <td>
                          <span className="text-zinc-400 text-sm font-mono">{formatDate(tx.created_at)}</span>
                        </td>
                        <td>
                          <div className="flex items-center gap-1">
                            {tx.is_corrected && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 mr-1">Corrected</span>
                            )}
                            {tx.type !== 'profit' && (
                              <>
                                <Button size="sm" variant="ghost" onClick={() => openCorrection(tx)} className="text-zinc-500 hover:text-blue-400 h-7 w-7 p-0" title="Correct amount" data-testid={`correct-tx-${tx.id}`}>
                                  <Edit3 className="w-3.5 h-3.5" />
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => handleDeleteTx(tx)} className="text-zinc-500 hover:text-red-400 h-7 w-7 p-0" title="Delete transaction" data-testid={`delete-tx-${tx.id}`}>
                                  <Trash2 className="w-3.5 h-3.5" />
                                </Button>
                              </>
                            )}
                            {tx.type === 'profit' && (
                              <span className="text-[10px] text-zinc-600">System</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                <p className="text-sm text-zinc-500">Showing {transactions.length} of {total} transactions</p>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary">
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-zinc-400">Page {page} of {totalPages}</span>
                  <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary">
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
              <DollarSign className="w-12 h-12 mb-4 opacity-30" />
              <p className="text-lg font-medium">No transactions found</p>
              <p className="text-sm mt-1">
                {userSearch ? `No results for "${userSearch}"` : 'No deposits or withdrawals recorded yet'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Correction Dialog */}
      <Dialog open={correctDialogOpen} onOpenChange={setCorrectDialogOpen}>
        <DialogContent className="dialog-content max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" /> Correct Transaction
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Update the amount for this {selectedTx?.type || 'transaction'}. Original: ${formatNumber(Math.abs(selectedTx?.amount || 0), 2)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <p className="text-xs text-zinc-500 mb-1">Member: <span className="text-zinc-300">{selectedTx?.user_name}</span></p>
              <p className="text-xs text-zinc-500 mb-3">Date: <span className="text-zinc-300">{formatDate(selectedTx?.created_at)}</span></p>
            </div>
            <div>
              <label className="text-sm text-zinc-300 block mb-1">New Amount ($)</label>
              <Input type="number" step="0.01" value={correctionAmount} onChange={e => setCorrectionAmount(e.target.value)} className="input-dark font-mono" data-testid="correction-amount-input" />
            </div>
            <div>
              <label className="text-sm text-zinc-300 block mb-1">Reason for Correction</label>
              <Textarea value={correctionReason} onChange={e => setCorrectionReason(e.target.value)} placeholder="e.g., Member entered wrong amount..." rows={2} className="input-dark resize-none" data-testid="correction-reason-input" />
            </div>
            <div className="flex gap-2 justify-end pt-2">
              <Button variant="outline" onClick={() => setCorrectDialogOpen(false)} className="btn-secondary">Cancel</Button>
              <Button onClick={handleCorrect} className="bg-blue-600 hover:bg-blue-700 gap-2" data-testid="confirm-correction-btn">
                <CheckCircle2 className="w-4 h-4" /> Apply Correction
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminTransactionsPage;
