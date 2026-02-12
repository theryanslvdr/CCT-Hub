import React from 'react';
import { ShieldCheck, AlertTriangle, ChevronRight } from 'lucide-react';

export function DataHealthBadge({ healthData, onClick }) {
  if (!healthData || !healthData.summary) return null;

  const { total_trading_days, reported_days, missing_days } = healthData.summary;
  if (total_trading_days === 0) return null;

  const percentage = Math.round((reported_days / total_trading_days) * 100);
  const isComplete = missing_days === 0;

  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-medium transition-all cursor-pointer
        ${isComplete
          ? 'bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25'
          : 'bg-amber-500/15 text-amber-400 hover:bg-amber-500/25'}
      `}
      data-testid="data-health-badge"
    >
      {isComplete ? (
        <ShieldCheck className="w-3 h-3" />
      ) : (
        <AlertTriangle className="w-3 h-3" />
      )}
      <span>{percentage}%</span>
      {!isComplete && (
        <>
          <span className="text-zinc-500 hidden sm:inline">·</span>
          <span className="text-zinc-500 hidden sm:inline">{missing_days} missing</span>
          <ChevronRight className="w-2.5 h-2.5 opacity-60" />
        </>
      )}
    </button>
  );
}
