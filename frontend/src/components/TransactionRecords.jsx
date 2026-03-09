import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { FileText, Receipt, Award, Check } from 'lucide-react';

function formatMoney(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

function addBusinessDays(date, days) {
  const result = new Date(date);
  let added = 0;
  while (added < days) {
    result.setDate(result.getDate() + 1);
    if (result.getDay() !== 0 && result.getDay() !== 6) added++;
  }
  return result;
}

export function DepositRecordsDialog({ open, onOpenChange, deposits }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
            <div className="text-center py-8 text-zinc-500">No deposits recorded yet.</div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function WithdrawalRecordsDialog({ open, onOpenChange, withdrawals, onConfirmReceipt }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
                          onClick={() => onConfirmReceipt(w.id)}
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
            <div className="text-center py-8 text-zinc-500">No withdrawals recorded yet.</div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function CommissionRecordsDialog({ open, onOpenChange, commissions }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
                  <th>Type</th>
                  <th>Traders</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {commissions.map((c) => (
                  <tr key={c.id}>
                    <td className="font-mono">{new Date(c.created_at).toLocaleDateString()}</td>
                    <td className="font-mono text-purple-400">+{formatMoney(c.amount)}</td>
                    <td>
                      {c.skip_deposit ? (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Historical</span>
                      ) : (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Balance</span>
                      )}
                    </td>
                    <td className="font-mono text-zinc-400">{c.traders_count}</td>
                    <td className="text-zinc-500 max-w-[200px] truncate">{c.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-8 text-zinc-500">No commissions recorded yet.</div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
