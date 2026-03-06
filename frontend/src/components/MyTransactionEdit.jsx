import React, { useState, useEffect, useCallback } from 'react';
import { profitAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { Edit3, Clock, Lock, AlertTriangle, CheckCircle2 } from 'lucide-react';

function formatCurrency(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(val));
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });
}

function timeRemaining(createdAt) {
  const created = new Date(createdAt);
  const deadline = new Date(created.getTime() + 48 * 60 * 60 * 1000);
  const now = new Date();
  const diff = deadline - now;
  if (diff <= 0) return null;
  const hrs = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  return `${hrs}h ${mins}m left to edit`;
}

export default function MyTransactionEdit() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);
  const [newAmount, setNewAmount] = useState('');
  const [reason, setReason] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await profitAPI.getMyRecentTransactions();
      setTransactions(res.data.transactions || []);
    } catch (e) {
      console.error('Failed to load recent transactions:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openEdit = (tx) => {
    setSelectedTx(tx);
    setNewAmount(String(Math.abs(tx.amount)));
    setReason('');
    setEditDialogOpen(true);
  };

  const handleEdit = async () => {
    if (!selectedTx || !newAmount) return;
    try {
      let amount = parseFloat(newAmount);
      if (selectedTx.is_withdrawal || selectedTx.amount < 0) {
        amount = -Math.abs(amount);
      }
      await profitAPI.editMyTransaction(selectedTx.id, {
        new_amount: amount,
        reason: reason || 'Corrected wrong amount',
      });
      toast.success('Transaction updated successfully!');
      setEditDialogOpen(false);
      load();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update transaction');
    }
  };

  if (transactions.length === 0) return null;

  return (
    <>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden" data-testid="my-transaction-edit">
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800">
          <h3 className="text-sm font-semibold text-white">My Recent Transactions</h3>
          <span className="text-[10px] text-zinc-500">Edit within 48 hours</span>
        </div>
        <div className="divide-y divide-zinc-800/50">
          {transactions.map(tx => {
            const isWithdrawal = tx.is_withdrawal || tx.amount < 0;
            const remaining = tx.editable ? timeRemaining(tx.created_at) : null;
            return (
              <div key={tx.id} className="flex items-center justify-between px-4 py-3" data-testid={`my-tx-${tx.id}`}>
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isWithdrawal ? 'bg-red-500/10' : 'bg-emerald-500/10'}`}>
                    <span className={`text-xs font-bold ${isWithdrawal ? 'text-red-400' : 'text-emerald-400'}`}>
                      {isWithdrawal ? 'W' : 'D'}
                    </span>
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-mono font-medium ${isWithdrawal ? 'text-red-400' : 'text-emerald-400'}`}>
                        {isWithdrawal ? '-' : '+'}{formatCurrency(tx.amount)}
                      </span>
                      {tx.corrections?.length > 0 && (
                        <span className="text-[9px] px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Edited</span>
                      )}
                    </div>
                    <p className="text-[10px] text-zinc-500">{formatDate(tx.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {tx.editable ? (
                    <>
                      {remaining && <span className="text-[10px] text-zinc-500 hidden sm:inline"><Clock className="w-3 h-3 inline mr-0.5" />{remaining}</span>}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openEdit(tx)}
                        className="btn-secondary text-blue-400 hover:text-blue-300 h-7 px-2 gap-1"
                        data-testid={`edit-my-tx-${tx.id}`}
                      >
                        <Edit3 className="w-3 h-3" /> Edit
                      </Button>
                    </>
                  ) : (
                    <span className="text-[10px] text-zinc-600 flex items-center gap-1"><Lock className="w-3 h-3" /> Locked</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="dialog-content max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-blue-400" /> Edit Transaction
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Correct the amount for this {selectedTx?.is_withdrawal ? 'withdrawal' : 'deposit'}. Current: {formatCurrency(selectedTx?.amount || 0)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-300/80">This will update your balance immediately. You can only edit this once, and only within the 48-hour window.</p>
              </div>
            </div>
            <div>
              <label className="text-sm text-zinc-300 block mb-1">Correct Amount ($)</label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={newAmount}
                onChange={e => setNewAmount(e.target.value)}
                className="input-dark font-mono"
                data-testid="my-tx-new-amount"
              />
            </div>
            <div>
              <label className="text-sm text-zinc-300 block mb-1">Reason (optional)</label>
              <Textarea
                value={reason}
                onChange={e => setReason(e.target.value)}
                placeholder="e.g., Entered wrong amount..."
                rows={2}
                className="input-dark resize-none"
                data-testid="my-tx-reason"
              />
            </div>
            <div className="flex gap-2 justify-end pt-1">
              <Button variant="outline" onClick={() => setEditDialogOpen(false)} className="btn-secondary">Cancel</Button>
              <Button onClick={handleEdit} className="bg-blue-600 hover:bg-blue-700 gap-2" data-testid="my-tx-confirm-btn">
                <CheckCircle2 className="w-4 h-4" /> Update
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
