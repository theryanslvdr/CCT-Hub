import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { TrendingUp, DollarSign, Flame, Activity, X, BarChart3 } from 'lucide-react';
import { profitSummaryAPI } from '@/lib/api';

const DailyProfitSummary = ({ onClose }) => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    profitSummaryAPI.getDailySummary()
      .then(r => setSummary(r.data))
      .catch(() => {});
  }, []);

  if (!summary || !summary.has_traded_today) return null;

  const isPositive = summary.net_profit >= 0;

  return (
    <Card className="relative overflow-hidden bg-[#111111]/90 border border-white/[0.08] rounded-xl" data-testid="daily-profit-summary">
      <div className="absolute -top-8 -right-8 w-32 h-32 bg-gradient-to-br from-orange-500/[0.06] to-transparent rounded-full blur-2xl pointer-events-none" />
      {onClose && (
        <button onClick={onClose} className="absolute top-3 right-3 text-zinc-600 hover:text-zinc-400 transition-colors z-10">
          <X className="w-4 h-4" />
        </button>
      )}
      <CardContent className="p-4 relative">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-xs font-semibold text-white">Today's Summary</p>
            <p className="text-[10px] text-zinc-500">{summary.date}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
            <div className="flex items-center gap-1.5 mb-1">
              <Activity className="w-3 h-3 text-orange-400" />
              <span className="text-[9px] text-zinc-500 uppercase">Trades</span>
            </div>
            <p className="text-lg font-bold font-mono text-white">{summary.trade_count}</p>
          </div>
          <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp className={`w-3 h-3 ${isPositive ? 'text-emerald-400' : 'text-red-400'}`} />
              <span className="text-[9px] text-zinc-500 uppercase">Net Profit</span>
            </div>
            <p className={`text-lg font-bold font-mono ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
              {isPositive ? '+' : ''}${Math.abs(summary.net_profit).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
            <div className="flex items-center gap-1.5 mb-1">
              <DollarSign className="w-3 h-3 text-teal-400" />
              <span className="text-[9px] text-zinc-500 uppercase">Account</span>
            </div>
            <p className="text-lg font-bold font-mono text-white">
              ${summary.account_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.04]">
            <div className="flex items-center gap-1.5 mb-1">
              <Flame className="w-3 h-3 text-amber-400" />
              <span className="text-[9px] text-zinc-500 uppercase">Streak</span>
            </div>
            <p className="text-lg font-bold font-mono text-orange-400">{summary.current_streak} days</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DailyProfitSummary;
