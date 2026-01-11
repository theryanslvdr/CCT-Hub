import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { formatNumber } from '@/lib/utils';
import { 
  ArrowDownToLine, ArrowUpFromLine, DollarSign, Users, 
  ChevronLeft, ChevronRight, TrendingUp, TrendingDown, RefreshCw
} from 'lucide-react';

export const AdminTransactionsPage = () => {
  const { isSuperAdmin, isMasterAdmin } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadData();
  }, [page, filterType]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [txRes, statsRes] = await Promise.all([
        adminAPI.getTeamTransactions(page, 20, filterType === 'all' ? null : filterType),
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
  };

  const handleRefresh = () => {
    loadData();
    toast.success('Transactions refreshed');
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
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Team Transactions</h1>
          <p className="text-zinc-400">Track all deposits and withdrawals across the team</p>
        </div>
        <Button 
          onClick={handleRefresh} 
          variant="outline" 
          className="btn-secondary gap-2"
          data-testid="refresh-transactions"
        >
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
                <p className="text-3xl font-bold font-mono text-emerald-400 mt-2">
                  ${formatNumber(stats?.total_deposits || 0, 2)}
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  {stats?.deposit_count || 0} transactions
                </p>
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
                <p className="text-3xl font-bold font-mono text-orange-400 mt-2">
                  ${formatNumber(stats?.total_withdrawals || 0, 2)}
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  {stats?.withdrawal_count || 0} transactions
                </p>
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
                <p className="text-xs text-zinc-500 mt-1">
                  {(stats?.net_flow || 0) >= 0 ? 'Inflow' : 'Outflow'}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                (stats?.net_flow || 0) >= 0 
                  ? 'bg-gradient-to-br from-emerald-500 to-green-600' 
                  : 'bg-gradient-to-br from-red-500 to-red-600'
              }`}>
                {(stats?.net_flow || 0) >= 0 
                  ? <TrendingUp className="w-6 h-6 text-white" />
                  : <TrendingDown className="w-6 h-6 text-white" />
                }
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card" data-testid="unique-depositors-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Unique Depositors</p>
                <p className="text-3xl font-bold font-mono text-blue-400 mt-2">
                  {stats?.unique_depositors || 0}
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  Team members with deposits
                </p>
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
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white">Transaction History</CardTitle>
          
          {/* Filter Tabs */}
          <Tabs value={filterType} onValueChange={(v) => { setFilterType(v); setPage(1); }}>
            <TabsList className="bg-zinc-900/50">
              <TabsTrigger value="all" className="data-[state=active]:bg-blue-500/20">
                All
              </TabsTrigger>
              <TabsTrigger value="deposit" className="data-[state=active]:bg-emerald-500/20">
                Deposits
              </TabsTrigger>
              <TabsTrigger value="withdrawal" className="data-[state=active]:bg-orange-500/20">
                Withdrawals
              </TabsTrigger>
            </TabsList>
          </Tabs>
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
                          <span className={`font-mono font-bold ${tx.type === 'withdrawal' ? 'text-orange-400' : 'text-emerald-400'}`}>
                            {tx.type === 'withdrawal' ? '-' : '+'}${formatNumber(Math.abs(tx.amount), 2)}
                          </span>
                          {tx.type === 'withdrawal' && tx.net_amount && (
                            <p className="text-xs text-zinc-500">
                              Net: ${formatNumber(tx.net_amount, 2)}
                            </p>
                          )}
                        </td>
                        <td>
                          <span className="text-zinc-400 text-sm">
                            {tx.product || tx.notes || '-'}
                          </span>
                        </td>
                        <td>
                          <span className="text-zinc-400 text-sm font-mono">
                            {formatDate(tx.created_at)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                <p className="text-sm text-zinc-500">
                  Showing {transactions.length} of {total} transactions
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn-secondary"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-zinc-400 px-2">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="btn-secondary"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <DollarSign className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500">No transactions found</p>
              <p className="text-zinc-600 text-sm mt-1">
                {filterType !== 'all' ? 'Try changing the filter' : 'Transactions will appear here when members deposit or withdraw'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
