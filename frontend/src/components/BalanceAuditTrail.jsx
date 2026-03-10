import React, { useState, useEffect, useCallback } from 'react';
import { profitAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ArrowUpRight, ArrowDownRight, TrendingUp, DollarSign, ChevronLeft, ChevronRight, Loader2, ExternalLink } from 'lucide-react';

const EVENT_STYLES = {
  deposit: { icon: ArrowDownRight, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: 'Deposit' },
  withdrawal: { icon: ArrowUpRight, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Withdrawal' },
  trade: { icon: TrendingUp, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20', label: 'Trade Profit' },
  commission: { icon: DollarSign, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'Commission' },
};

function formatCurrency(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function TimelineRow({ event }) {
  const style = EVENT_STYLES[event.type] || EVENT_STYLES.trade;
  const Icon = style.icon;
  const isPositive = event.amount > 0;

  return (
    <div className="relative flex items-start gap-3 py-2">
      <div className={`relative z-10 w-5 h-5 rounded-full ${style.bg} border ${style.border} flex items-center justify-center flex-shrink-0`}>
        <Icon className={`w-2.5 h-2.5 ${style.color}`} />
      </div>
      <div className="flex-1 flex items-center justify-between min-w-0">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-zinc-300">{style.label}</span>
            <span className="text-[10px] text-zinc-600">{formatDate(event.date)}</span>
          </div>
          <p className="text-[10px] text-zinc-500 truncate">{event.description}</p>
        </div>
        <div className="text-right flex-shrink-0 ml-2">
          <span className={`text-xs font-mono font-medium ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}{formatCurrency(event.amount)}
          </span>
          <p className="text-[10px] text-zinc-600 font-mono">{formatCurrency(event.balanceAfter)}</p>
        </div>
      </div>
    </div>
  );
}

function buildTrail(dailyBalances) {
  const trail = [];
  for (const day of dailyBalances) {
    const date = day.date;
    if (day.day_deposits > 0) {
      trail.push({ date, type: 'deposit', amount: day.day_deposits, balanceAfter: day.balance_before + day.day_deposits, description: 'Deposit received' });
    }
    if (day.day_withdrawals > 0) {
      trail.push({ date, type: 'withdrawal', amount: -day.day_withdrawals, balanceAfter: day.balance_before - day.day_withdrawals, description: 'Withdrawal processed' });
    }
    if (day.actual_profit != null && day.actual_profit !== 0) {
      trail.push({ date, type: 'trade', amount: day.actual_profit, balanceAfter: day.balance_before + (day.day_deposits || 0) - (day.day_withdrawals || 0) + day.actual_profit, description: `Trading profit (LOT ${day.lot_size})` });
    }
    if (day.commission != null && day.commission > 0) {
      trail.push({ date, type: 'commission', amount: day.commission, balanceAfter: day.balance_before + (day.day_deposits || 0) - (day.day_withdrawals || 0) + (day.actual_profit || 0) + day.commission, description: 'Trade commission' });
    }
  }
  return trail;
}

// ─── Inline preview (last 3 events) ───
export function BalanceAuditPreview({ userId, onViewAll }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const startDate = `${y}-${m}-01`;
        const lastDay = new Date(y, now.getMonth() + 1, 0).getDate();
        const endDate = `${y}-${m}-${lastDay}`;
        const res = await profitAPI.getDailyBalances(startDate, endDate, userId);
        setEvents(buildTrail(res.data?.daily_balances || []));
      } catch (e) {
        console.error('Failed to load audit preview:', e);
      } finally {
        setLoading(false);
      }
    })();
  }, [userId]);

  const last3 = events.slice(-3);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden" data-testid="balance-audit-preview">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800">
        <h3 className="text-sm font-semibold text-white">Recent Activity</h3>
        {events.length > 3 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onViewAll}
            className="text-xs text-orange-400 hover:text-orange-300 h-7 px-2 gap-1"
            data-testid="view-all-audit-btn"
          >
            View All <ExternalLink className="w-3 h-3" />
          </Button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-4 h-4 animate-spin text-zinc-500" />
        </div>
      ) : last3.length === 0 ? (
        <div className="text-center py-6 text-zinc-500 text-xs">No activity this month</div>
      ) : (
        <div className="relative px-4 py-2">
          <div className="absolute left-6 top-0 bottom-0 w-px bg-zinc-800" />
          {last3.map((event, idx) => <TimelineRow key={idx} event={event} />)}
        </div>
      )}
    </div>
  );
}

// ─── Full modal with month picker ───
export function BalanceAuditModal({ open, onClose, userId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  const monthLabel = (() => {
    const [y, m] = month.split('-').map(Number);
    return new Date(y, m - 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  })();

  const prevMonth = () => {
    const [y, m] = month.split('-').map(Number);
    const d = new Date(y, m - 2, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  };

  const nextMonth = () => {
    const [y, m] = month.split('-').map(Number);
    const d = new Date(y, m, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [y, m] = month.split('-').map(Number);
      const startDate = `${y}-${String(m).padStart(2, '0')}-01`;
      const lastDay = new Date(y, m, 0).getDate();
      const endDate = `${y}-${String(m).padStart(2, '0')}-${lastDay}`;
      const res = await profitAPI.getDailyBalances(startDate, endDate, userId);
      setEvents(buildTrail(res.data?.daily_balances || []));
    } catch (e) {
      console.error('Failed to load audit trail:', e);
    } finally {
      setLoading(false);
    }
  }, [month, userId]);

  useEffect(() => { if (open) load(); }, [load, open]);

  // Stats
  const totalDeposits = events.filter(e => e.type === 'deposit').reduce((s, e) => s + e.amount, 0);
  const totalWithdrawals = events.filter(e => e.type === 'withdrawal').reduce((s, e) => s + Math.abs(e.amount), 0);
  const totalProfit = events.filter(e => e.type === 'trade').reduce((s, e) => s + e.amount, 0);
  const totalCommission = events.filter(e => e.type === 'commission').reduce((s, e) => s + e.amount, 0);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="dialog-content max-w-2xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-white text-lg">Balance Audit Trail</DialogTitle>
        </DialogHeader>

        {/* Month navigation */}
        <div className="flex items-center justify-between py-2">
          <Button variant="ghost" size="sm" onClick={prevMonth} className="text-zinc-400 hover:text-white h-8 w-8 p-0">
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm font-semibold text-white">{monthLabel}</span>
          <Button variant="ghost" size="sm" onClick={nextMonth} className="text-zinc-400 hover:text-white h-8 w-8 p-0">
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>

        {/* Month summary cards */}
        <div className="grid grid-cols-4 gap-2 pb-3">
          <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-2 text-center">
            <p className="text-[10px] text-emerald-400/70">Deposits</p>
            <p className="text-xs font-mono font-bold text-emerald-400">{formatCurrency(totalDeposits)}</p>
          </div>
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-2 text-center">
            <p className="text-[10px] text-red-400/70">Withdrawals</p>
            <p className="text-xs font-mono font-bold text-red-400">{formatCurrency(totalWithdrawals)}</p>
          </div>
          <div className="rounded-lg bg-orange-500/10 border border-orange-500/15 p-2 text-center">
            <p className="text-[10px] text-orange-400/70">Trade Profit</p>
            <p className="text-xs font-mono font-bold text-orange-400">{formatCurrency(totalProfit)}</p>
          </div>
          <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-2 text-center">
            <p className="text-[10px] text-amber-400/70">Commission</p>
            <p className="text-xs font-mono font-bold text-amber-400">{formatCurrency(totalCommission)}</p>
          </div>
        </div>

        {/* Timeline */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-5 h-5 animate-spin text-zinc-500" />
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12 text-zinc-500 text-sm">No transactions for {monthLabel}</div>
          ) : (
            <div className="relative px-2">
              <div className="absolute left-4 top-0 bottom-0 w-px bg-zinc-800" />
              {events.map((event, idx) => <TimelineRow key={idx} event={event} />)}
              <div className="pt-3 pb-1 text-center text-[10px] text-zinc-600">
                {events.length} transactions in {monthLabel}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Default export for backward compat
export default function BalanceAuditTrail({ userId }) {
  const [modalOpen, setModalOpen] = useState(false);
  return (
    <>
      <BalanceAuditPreview userId={userId} onViewAll={() => setModalOpen(true)} />
      <BalanceAuditModal open={modalOpen} onClose={() => setModalOpen(false)} userId={userId} />
    </>
  );
}
