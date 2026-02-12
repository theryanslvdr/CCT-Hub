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
        w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-all
        ${isComplete 
          ? 'bg-emerald-500/10 border border-emerald-500/20 hover:border-emerald-500/40' 
          : 'bg-amber-500/10 border border-amber-500/20 hover:border-amber-500/40'}
      `}
      data-testid="data-health-badge"
    >
      <div className="flex items-center gap-2">
        {isComplete ? (
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        ) : (
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
        )}
        <span className={isComplete ? 'text-emerald-400' : 'text-amber-400'}>
          {percentage}% complete
        </span>
        <span className="text-zinc-500">
          {isComplete
            ? `All ${total_trading_days} days reported`
            : `${missing_days} day${missing_days !== 1 ? 's' : ''} missing`}
        </span>
      </div>
      {!isComplete && (
        <div className="flex items-center gap-1 text-amber-400/70">
          <span>Fix</span>
          <ChevronRight className="w-3 h-3" />
        </div>
      )}
    </button>
  );
}
