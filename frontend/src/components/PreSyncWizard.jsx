import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Calendar, CheckCircle2, AlertTriangle, Loader2, 
  X, Clock, ArrowRight, ShieldCheck, Edit3
} from 'lucide-react';

const STEP_LABELS = ['Start Date', 'Missing Days', 'Pre-Start', 'Sync'];

function StepIndicator({ currentStep, totalSteps = 4 }) {
  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        {STEP_LABELS.map((label, i) => {
          const stepNum = i + 1;
          const isActive = stepNum === currentStep;
          const isDone = stepNum < currentStep;
          return (
            <div key={label} className="flex flex-col items-center flex-1">
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all
                ${isDone ? 'bg-emerald-500 text-white' : ''}
                ${isActive ? 'bg-blue-500 text-white ring-2 ring-blue-400/50' : ''}
                ${!isActive && !isDone ? 'bg-zinc-800 text-zinc-500' : ''}
              `}>
                {isDone ? <CheckCircle2 className="w-4 h-4" /> : stepNum}
              </div>
              <span className={`text-[10px] mt-1 ${isActive ? 'text-blue-400' : isDone ? 'text-emerald-400' : 'text-zinc-600'}`}>
                {label}
              </span>
            </div>
          );
        })}
      </div>
      <Progress value={(currentStep / totalSteps) * 100} className="h-1 bg-zinc-800" />
    </div>
  );
}

function StepStartDate({ validation, newStartDate, onStartDateChange, onSetStartDate, loading }) {
  const suggested = validation?.suggested_start_date;

  return (
    <div className="space-y-4" data-testid="sync-wizard-step-start-date">
      <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-300">Trading Start Date Required</p>
            <p className="text-xs text-zinc-400 mt-1">
              We need to know when you started trading to calculate your balances accurately.
            </p>
          </div>
        </div>
      </div>

      <div>
        <Label className="text-zinc-300 text-sm">When did you start trading?</Label>
        <Input
          type="date"
          value={newStartDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="input-dark mt-1.5"
          data-testid="start-date-input"
        />
        {suggested && (
          <button
            onClick={() => onStartDateChange(suggested)}
            className="text-xs text-blue-400 hover:text-blue-300 mt-2 flex items-center gap-1"
            data-testid="use-suggested-date-btn"
          >
            <Calendar className="w-3 h-3" />
            Use detected date: {suggested}
          </button>
        )}
      </div>

      <Button
        onClick={onSetStartDate}
        disabled={!newStartDate || loading}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white"
        data-testid="set-start-date-btn"
      >
        {loading ? (
          <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Setting...</>
        ) : (
          <><ArrowRight className="w-4 h-4 mr-2" /> Set Start Date & Continue</>
        )}
      </Button>
    </div>
  );
}

function StepMissingDays({ validation, onMarkDidNotTrade, onMarkAllDidNotTrade, onAdjustTrade, loading }) {
  const missing = validation?.missing_trade_days || [];
  const summary = validation?.summary || {};

  return (
    <div className="space-y-4" data-testid="sync-wizard-step-missing-days">
      <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-300">
              {missing.length} Unreported Trading Day{missing.length !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-zinc-400 mt-1">
              {summary.reported_days} of {summary.total_trading_days} days reported. 
              Resolve each day before syncing.
            </p>
          </div>
        </div>
      </div>

      <div className="max-h-52 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
        {missing.map((day) => (
          <div 
            key={day.date} 
            className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-800/80 border border-zinc-700/50"
            data-testid={`missing-day-${day.date}`}
          >
            <div className="flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-zinc-500" />
              <span className="text-sm text-zinc-200 font-mono">{day.date}</span>
              <Badge variant="outline" className="text-[10px] border-red-500/40 text-red-400">
                {day.status === 'no_entry' ? 'No entry' : 'Incomplete'}
              </Badge>
            </div>
            <div className="flex items-center gap-1.5">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                onClick={() => onAdjustTrade(day.date)}
                data-testid={`adjust-trade-${day.date}`}
              >
                <Edit3 className="w-3 h-3 mr-1" /> Adjust
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                onClick={() => onMarkDidNotTrade(day.date)}
                disabled={loading}
                data-testid={`did-not-trade-${day.date}`}
              >
                <X className="w-3 h-3 mr-1" /> DNT
              </Button>
            </div>
          </div>
        ))}
      </div>

      {missing.length > 1 && (
        <Button
          onClick={onMarkAllDidNotTrade}
          disabled={loading}
          variant="outline"
          className="w-full border-amber-500/40 text-amber-400 hover:bg-amber-500/10"
          data-testid="mark-all-dnt-btn"
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing...</>
          ) : (
            <><X className="w-4 h-4 mr-2" /> Mark All {missing.length} Days as "Did Not Trade"</>
          )}
        </Button>
      )}
    </div>
  );
}

function StepPreStartWarning({ validation, acknowledged, onToggleAcknowledge, onContinue }) {
  const preStartTrades = validation?.pre_start_trades || [];

  return (
    <div className="space-y-4" data-testid="sync-wizard-step-pre-start">
      <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-300">
              {preStartTrades.length} Trade{preStartTrades.length !== 1 ? 's' : ''} Before Start Date
            </p>
            <p className="text-xs text-zinc-400 mt-1">
              These trades were logged before your start date ({validation?.trading_start_date}). 
              They won't affect your balance calculations going forward.
            </p>
          </div>
        </div>
      </div>

      <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
        {preStartTrades.map((trade, i) => (
          <div 
            key={`${trade.date}-${i}`}
            className="flex items-center justify-between p-2 rounded bg-zinc-800/60 text-sm"
          >
            <span className="font-mono text-zinc-300">{trade.date}</span>
            <div className="flex gap-3 text-xs">
              <span className={trade.actual_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                ${(trade.actual_profit || 0).toFixed(2)}
              </span>
              {trade.did_not_trade && (
                <Badge variant="outline" className="text-[10px] border-zinc-600 text-zinc-400">DNT</Badge>
              )}
            </div>
          </div>
        ))}
      </div>

      <label className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/60 border border-zinc-700/50 cursor-pointer hover:border-zinc-600 transition-colors">
        <input
          type="checkbox"
          checked={acknowledged}
          onChange={(e) => onToggleAcknowledge(e.target.checked)}
          className="mt-1 accent-blue-500"
          data-testid="acknowledge-pre-start-checkbox"
        />
        <span className="text-xs text-zinc-400">
          I understand these pre-start trades won't be included in my balance calculations.
        </span>
      </label>

      <Button
        onClick={onContinue}
        disabled={!acknowledged}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white"
        data-testid="acknowledge-pre-start-btn"
      >
        <ArrowRight className="w-4 h-4 mr-2" /> Continue to Sync
      </Button>
    </div>
  );
}

function StepSync({ 
  calculatedBalance, actualBalanceInput, onActualBalanceChange, 
  onSync, loading 
}) {
  const adjustment = actualBalanceInput ? parseFloat(actualBalanceInput) - calculatedBalance : 0;

  return (
    <div className="space-y-4" data-testid="sync-wizard-step-sync">
      <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-emerald-300">Ready to Sync</p>
            <p className="text-xs text-zinc-400 mt-1">
              All checks passed. Enter your actual Merin balance to sync.
            </p>
          </div>
        </div>
      </div>

      <div className="p-4 rounded-lg bg-zinc-800/80 border border-zinc-700/50">
        <p className="text-xs text-zinc-500 mb-1">Calculated balance:</p>
        <p className="text-2xl font-bold text-white font-mono">
          ${calculatedBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
      </div>

      <div>
        <Label className="text-zinc-300 text-sm">Actual Merin Balance (USDT)</Label>
        <div className="relative mt-1.5">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
          <Input
            type="number"
            value={actualBalanceInput}
            onChange={(e) => onActualBalanceChange(e.target.value)}
            placeholder="0.00"
            className="input-dark pl-7 text-lg"
            data-testid="wizard-actual-balance-input"
          />
        </div>
        {actualBalanceInput && Math.abs(adjustment) > 0.01 && (
          <p className={`text-xs mt-2 ${adjustment > 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
            Adjustment: {adjustment > 0 ? '+' : ''}${adjustment.toFixed(2)}
          </p>
        )}
      </div>

      <Button
        onClick={onSync}
        disabled={loading || !actualBalanceInput}
        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
        data-testid="wizard-sync-balance-btn"
      >
        {loading ? (
          <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Syncing...</>
        ) : (
          <><CheckCircle2 className="w-4 h-4 mr-2" /> Sync Balance</>
        )}
      </Button>

      <p className="text-[11px] text-zinc-600 text-center">
        Future trade days will use this synced balance as the starting point.
      </p>
    </div>
  );
}

export function PreSyncWizard({
  open,
  onOpenChange,
  step,
  validation,
  validationLoading,
  newStartDate,
  onStartDateChange,
  onSetStartDate,
  onMarkDidNotTrade,
  onMarkAllDidNotTrade,
  onAdjustTrade,
  preStartAcknowledged,
  onAcknowledgePreStart,
  calculatedBalance,
  actualBalanceInput,
  onActualBalanceChange,
  onSync,
  syncLoading,
}) {
  if (validationLoading && !validation) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
            <p className="text-sm text-zinc-400">Validating your account...</p>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass-card border-zinc-800 max-w-md" data-testid="pre-sync-wizard-dialog">
        <DialogHeader>
          <DialogTitle className="text-white text-base">Balance Sync Wizard</DialogTitle>
        </DialogHeader>

        <StepIndicator currentStep={step} />

        {step === 1 && (
          <StepStartDate
            validation={validation}
            newStartDate={newStartDate}
            onStartDateChange={onStartDateChange}
            onSetStartDate={onSetStartDate}
            loading={validationLoading}
          />
        )}

        {step === 2 && (
          <StepMissingDays
            validation={validation}
            onMarkDidNotTrade={onMarkDidNotTrade}
            onMarkAllDidNotTrade={onMarkAllDidNotTrade}
            onAdjustTrade={onAdjustTrade}
            loading={validationLoading}
          />
        )}

        {step === 3 && (
          <StepPreStartWarning
            validation={validation}
            acknowledged={preStartAcknowledged}
            onAcknowledge={onAcknowledgePreStart}
          />
        )}

        {step === 4 && (
          <StepSync
            calculatedBalance={calculatedBalance}
            actualBalanceInput={actualBalanceInput}
            onActualBalanceChange={onActualBalanceChange}
            onSync={onSync}
            loading={syncLoading}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
