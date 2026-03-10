import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { referralAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import { Check, Loader2, Link2, Users, ArrowRight, Sparkles } from 'lucide-react';

const ReferralOnboardingModal = () => {
  const { user, refreshUser, isAdmin } = useAuth();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(1); // 1: Set your code, 2: Who referred you, 3: Done
  const [code, setCode] = useState('');
  const [referredByCode, setReferredByCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);

  useEffect(() => {
    if (!user || isAdmin()) {
      setCheckingStatus(false);
      return;
    }
    const check = async () => {
      try {
        const res = await referralAPI.checkOnboarding();
        if (res.data.needs_onboarding) {
          setOpen(true);
        }
      } catch {
        // Don't block the app if the check fails
      } finally {
        setCheckingStatus(false);
      }
    };
    check();
  }, [user, isAdmin]);

  const handleSetCode = async () => {
    if (!code.trim() || code.trim().length < 3) {
      toast.error('Referral code must be at least 3 characters');
      return;
    }
    setLoading(true);
    try {
      const res = await referralAPI.setCode(code.trim());
      if (res.data.success) {
        toast.success(res.data.message);
        setStep(2);
        await refreshUser();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to set referral code');
    } finally {
      setLoading(false);
    }
  };

  const handleSetReferredBy = async () => {
    if (!referredByCode.trim()) {
      // Allow skip
      setStep(3);
      return;
    }
    setLoading(true);
    try {
      const res = await referralAPI.setReferredBy(referredByCode.trim());
      if (res.data.success) {
        toast.success(`Linked to ${res.data.inviter_name}'s referral network!`);
        setStep(3);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid referral code');
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = () => {
    setOpen(false);
  };

  if (checkingStatus || !open) return null;

  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent
        className="glass-card border-blue-500/30 max-w-md [&>button]:hidden"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
        data-testid="referral-onboarding-modal"
      >
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            {step === 1 && <><Link2 className="w-5 h-5 text-blue-400" /> Set Your Merin Referral Code</>}
            {step === 2 && <><Users className="w-5 h-5 text-green-400" /> Who Referred You?</>}
            {step === 3 && <><Sparkles className="w-5 h-5 text-amber-400" /> You're All Set!</>}
          </DialogTitle>
          <DialogDescription className="text-zinc-400">
            {step === 1 && 'Enter your Merin referral code from the rewards platform. This is required to participate in the community.'}
            {step === 2 && 'If someone invited you, enter their referral code below. This helps build our referral network.'}
            {step === 3 && 'Your referral setup is complete. Welcome to the community!'}
          </DialogDescription>
        </DialogHeader>

        {/* Progress Steps */}
        <div className="flex items-center gap-2 my-3">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-2 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                s < step ? 'bg-green-500 text-white' :
                s === step ? 'bg-blue-500 text-white ring-2 ring-blue-400/50' :
                'bg-zinc-700 text-zinc-400'
              }`}>
                {s < step ? <Check className="w-4 h-4" /> : s}
              </div>
              {s < 3 && <div className={`flex-1 h-0.5 ${s < step ? 'bg-green-500' : 'bg-zinc-700'}`} />}
            </div>
          ))}
        </div>

        {/* Step 1: Set Your Code */}
        {step === 1 && (
          <div className="space-y-4 mt-2" data-testid="referral-step-1">
            <div>
              <label className="text-sm text-zinc-300 mb-1.5 block">Your Merin Referral Code</label>
              <Input
                data-testid="referral-code-input"
                placeholder="e.g. JOHN_MERIN"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                className="bg-zinc-800/50 border-zinc-600 text-white"
                onKeyDown={(e) => e.key === 'Enter' && handleSetCode()}
              />
              <p className="text-xs text-zinc-500 mt-1">This will be your unique identifier in the referral network.</p>
            </div>
            <Button
              data-testid="referral-set-code-btn"
              onClick={handleSetCode}
              disabled={loading || !code.trim()}
              className="w-full btn-primary gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
              Set My Code
            </Button>
          </div>
        )}

        {/* Step 2: Who Referred You */}
        {step === 2 && (
          <div className="space-y-4 mt-2" data-testid="referral-step-2">
            <div>
              <label className="text-sm text-zinc-300 mb-1.5 block">Inviter's Referral Code (Optional)</label>
              <Input
                data-testid="referred-by-input"
                placeholder="e.g. RYAN_MERIN"
                value={referredByCode}
                onChange={(e) => setReferredByCode(e.target.value.toUpperCase())}
                className="bg-zinc-800/50 border-zinc-600 text-white"
                onKeyDown={(e) => e.key === 'Enter' && handleSetReferredBy()}
              />
              <p className="text-xs text-zinc-500 mt-1">Enter the code of the person who invited you.</p>
            </div>
            <div className="flex gap-3">
              <Button
                data-testid="referral-skip-btn"
                variant="outline"
                onClick={() => setStep(3)}
                className="flex-1 btn-secondary"
              >
                Skip
              </Button>
              <Button
                data-testid="referral-set-referred-btn"
                onClick={handleSetReferredBy}
                disabled={loading}
                className="flex-1 btn-primary gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                Submit
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Done */}
        {step === 3 && (
          <div className="space-y-4 mt-2 text-center" data-testid="referral-step-3">
            <div className="w-16 h-16 mx-auto rounded-full bg-green-500/20 flex items-center justify-center">
              <Check className="w-8 h-8 text-green-400" />
            </div>
            <p className="text-zinc-300">
              Your referral profile is ready. Share your code with friends to grow the network!
            </p>
            <Button
              data-testid="referral-finish-btn"
              onClick={handleFinish}
              className="w-full btn-primary"
            >
              Get Started
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ReferralOnboardingModal;
