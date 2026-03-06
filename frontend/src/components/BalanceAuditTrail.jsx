import React, { useState, useEffect, useCallback } from 'react';
import { profitAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ArrowUpRight, ArrowDownRight, TrendingUp, DollarSign, Minus, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';

const EVENT_STYLES = {
  deposit: { icon: ArrowDownRight, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: 'Deposit' },
  withdrawal: { icon: ArrowUpRight, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'Withdrawal' },
  trade: { icon: TrendingUp, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30', label: 'Trade Profit' },
  commission: { icon: DollarSign, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'Commission' },
};

function formatCurrency(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function BalanceAuditTrail({ userId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [y, m] = month.split('-').map(Number);
      const startDate = `${y}-${String(m).padStart(2, '0')}-01`;
      const lastDay = new Date(y, m, 0).getDate();
      const endDate = `${y}-${String(m).padStart(2, '0')}-${lastDay}`;
      
      const res = await profitAPI.getDailyBalances(startDate, endDate, userId);
      const dailyBalances = res.data?.daily_balances || [];
      
      // Convert daily balances into an audit trail
      const trail = [];
      for (const day of dailyBalances) {
        const date = day.date;
        
        if (day.day_deposits > 0) {
          trail.push({
            date,
            type: 'deposit',
            amount: day.day_deposits,
            balanceAfter: day.balance_before + day.day_deposits,
            description: `Deposit received`,
          });
        }
        
        if (day.day_withdrawals > 0) {
          trail.push({
            date,
            type: 'withdrawal',
            amount: -day.day_withdrawals,
            balanceAfter: day.balance_before - day.day_withdrawals,
            description: `Withdrawal processed`,
          });
        }
        
        if (day.actual_profit != null && day.actual_profit !== 0) {
          trail.push({
            date,
            type: 'trade',
            amount: day.actual_profit,
            balanceAfter: day.balance_before + (day.day_deposits || 0) - (day.day_withdrawals || 0) + day.actual_profit,
            description: `Trading profit (LOT ${day.lot_size})`,
          });
        }
        
        if (day.commission != null && day.commission > 0) {
          trail.push({
            date,
            type: 'commission',
            amount: day.commission,
            balanceAfter: day.balance_before + (day.day_deposits || 0) - (day.day_withdrawals || 0) + (day.actual_profit || 0) + day.commission,
            description: `Trade commission`,
          });
        }
      }
      
      setEvents(trail);
    } catch (e) {
      console.error('Failed to load audit trail:', e);
    } finally {
      setLoading(false);
    }
  }, [month, userId]);

  useEffect(() => { load(); }, [load]);

  const displayEvents = expanded ? events : events.slice(-10);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden" data-testid="balance-audit-trail">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <h3 className="text-sm font-semibold text-white">Balance Audit Trail</h3>
        <div className="flex items-center gap-2">
          <input
            type="month"
            value={month}
            onChange={e => setMonth(e.target.value)}
            className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
            data-testid="audit-trail-month"
          />
        </div>
      </div>
      
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 animate-spin text-zinc-500" />
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-8 text-zinc-500 text-sm">No transactions this month</div>
      ) : (
        <div className="relative">
          {/* Timeline */}
          <div className="absolute left-6 top-0 bottom-0 w-px bg-zinc-800" />
          
          <div className="px-4 py-3 space-y-0">
            {!expanded && events.length > 10 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(true)}
                className="w-full text-xs text-zinc-500 hover:text-zinc-300 mb-2"
                data-testid="show-all-events"
              >
                <ChevronUp className="w-3 h-3 mr-1" /> Show {events.length - 10} earlier events
              </Button>
            )}
            
            {displayEvents.map((event, idx) => {
              const style = EVENT_STYLES[event.type] || EVENT_STYLES.trade;
              const Icon = style.icon;
              const isPositive = event.amount > 0;
              
              return (
                <div key={idx} className="relative flex items-start gap-3 py-2 group">
                  {/* Timeline dot */}
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
            })}
            
            {expanded && events.length > 10 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(false)}
                className="w-full text-xs text-zinc-500 hover:text-zinc-300 mt-2"
              >
                <ChevronDown className="w-3 h-3 mr-1" /> Show less
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
