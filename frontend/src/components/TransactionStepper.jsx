import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const DEFAULT_STEPS = [
  { id: 'submitted', label: 'Submitted' },
  { id: 'reviewing', label: 'Under Review' },
  { id: 'processing', label: 'Processing' },
  { id: 'completed', label: 'Completed' },
];

const STATUS_MAP = {
  pending: 1,
  under_review: 2,
  reviewing: 2,
  approved: 3,
  processing: 3,
  completed: 4,
  done: 4,
  rejected: -1,
  cancelled: -1,
};

export const TransactionStepper = ({ status = 'pending', className, steps, activeStep: activeStepProp }) => {
  const displaySteps = steps || DEFAULT_STEPS;
  const activeStep = activeStepProp || STATUS_MAP[status] || 1;
  const isRejected = activeStep === -1;

  if (isRejected) {
    return (
      <div className={cn("flex items-center gap-2 p-3 rounded-xl bg-red-500/5 border border-red-500/15", className)}>
        <div className="w-6 h-6 rounded-full bg-red-500/20 flex items-center justify-center">
          <span className="text-red-400 text-xs font-bold">!</span>
        </div>
        <span className="text-sm text-red-400 font-medium capitalize">{status}</span>
      </div>
    );
  }

  return (
    <div className={cn("p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]", className)} data-testid="transaction-stepper">
      <div className="flex items-center justify-between relative">
        {/* Progress line background */}
        <div className="absolute top-4 left-6 right-6 h-0.5 bg-white/[0.06]" />
        {/* Active progress line */}
        <div
          className="absolute top-4 left-6 h-0.5 bg-gradient-to-r from-orange-500 to-amber-500 transition-all duration-500"
          style={{ width: `${Math.max(0, ((activeStep - 1) / (displaySteps.length - 1)) * 100)}%`, maxWidth: 'calc(100% - 48px)' }}
        />

        {displaySteps.map((step, i) => {
          const stepNum = i + 1;
          const isDone = stepNum < activeStep;
          const isActive = stepNum === activeStep;

          return (
            <div key={step.id} className="relative flex flex-col items-center z-10" data-testid={`step-${step.id}`}>
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center transition-all",
                isDone
                  ? "bg-gradient-to-br from-orange-500 to-amber-500 shadow-lg shadow-orange-500/20"
                  : isActive
                    ? "bg-orange-500/20 border-2 border-orange-500 shadow-lg shadow-orange-500/20"
                    : "bg-[#1a1a1a] border border-white/[0.08]"
              )}>
                {isDone ? (
                  <Check className="w-4 h-4 text-white" />
                ) : (
                  <span className={cn("text-xs font-bold", isActive ? "text-orange-400" : "text-zinc-600")}>{stepNum}</span>
                )}
              </div>
              <p className={cn(
                "text-[10px] mt-2 text-center whitespace-nowrap font-medium",
                isDone || isActive ? "text-orange-400" : "text-zinc-600"
              )}>
                {step.label}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TransactionStepper;
