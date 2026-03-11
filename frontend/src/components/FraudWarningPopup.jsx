import React, { useState, useEffect } from 'react';
import { habitAPI } from '@/lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Clock, Shield } from 'lucide-react';

const FraudWarningPopup = () => {
  const [warning, setWarning] = useState(null);
  const [open, setOpen] = useState(false);
  const [acknowledging, setAcknowledging] = useState(false);

  useEffect(() => {
    const checkWarnings = async () => {
      try {
        const res = await habitAPI.getMyWarnings();
        const active = res.data.active_warning;
        if (active && !active.acknowledged) {
          setWarning(active);
          setOpen(true);
        }
      } catch {
        // Silently fail — this is a background check
      }
    };
    checkWarnings();
  }, []);

  const handleAcknowledge = async () => {
    if (!warning) return;
    setAcknowledging(true);
    try {
      const res = await habitAPI.acknowledgeWarning(warning.id);
      setWarning(prev => ({ ...prev, acknowledged: true, countdown_end: res.data.countdown_end }));
      setOpen(false);
    } catch {
      // Keep open
    }
    setAcknowledging(false);
  };

  if (!warning || !open) return null;

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent className="bg-[#111] border-red-500/30 max-w-md [&>button]:hidden" data-testid="fraud-warning-popup">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-red-400" />
            </div>
            <DialogTitle className="text-red-400 text-lg">Important Notice</DialogTitle>
          </div>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <p className="text-sm text-zinc-300 leading-relaxed">
            Your recent habit screenshot submissions have been flagged as fraudulent by an admin.
          </p>

          <div className="bg-red-500/5 border border-red-500/15 rounded-lg p-3">
            <p className="text-sm text-red-300 font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              You have until next week to correct this behavior.
            </p>
            <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
              If fraudulent submissions continue after acknowledgment, your account will be
              <span className="text-red-400 font-semibold"> permanently suspended</span> and you will not be able to re-register.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Clock className="w-3.5 h-3.5" />
            <span>Flagged {warning.fraud_count} time{warning.fraud_count > 1 ? 's' : ''}</span>
          </div>

          <p className="text-xs text-zinc-500 italic">
            Note: You can still access signals and all features during this period.
          </p>
        </div>

        <DialogFooter>
          <Button
            onClick={handleAcknowledge}
            disabled={acknowledging}
            className="w-full bg-red-600 hover:bg-red-700 text-white"
            data-testid="acknowledge-warning-btn"
          >
            {acknowledging ? 'Processing...' : 'I Understand — Start 7-Day Countdown'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default FraudWarningPopup;
