import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle2, Circle, ExternalLink, Copy, Loader2, ChevronRight, Link2, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { onboardingAPI } from '@/lib/api';
import { settingsAPI } from '@/lib/api';
import { toast } from 'sonner';

const OnboardingGate = ({ children, user }) => {
  const [checklist, setChecklist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gateEnabled, setGateEnabled] = useState(true);
  const [merinCode, setMerinCode] = useState('');
  const [savingCode, setSavingCode] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteLink, setInviteLink] = useState(null);

  const isAdmin = user?.role === 'master_admin' || user?.role === 'super_admin';

  const loadChecklist = useCallback(async () => {
    try {
      const [checklistRes, settingsRes] = await Promise.all([
        onboardingAPI.getChecklist(),
        settingsAPI.getPlatform().catch(() => ({ data: {} })),
      ]);
      setChecklist(checklistRes.data);
      setMerinCode(checklistRes.data.merin_referral_code || '');
      setGateEnabled(settingsRes.data?.onboarding_gate_enabled !== false);
    } catch {
      setChecklist({ all_completed: true });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadChecklist(); }, [loadChecklist]);

  const handleStepToggle = async (stepKey, currentlyCompleted) => {
    try {
      const payload = { step_key: stepKey, completed: !currentlyCompleted };
      if (stepKey === 'merin_registered' && merinCode) {
        payload.merin_referral_code = merinCode;
      }
      const res = await onboardingAPI.updateStep(payload);
      await loadChecklist();
      if (res.data.all_completed) {
        toast.success('Onboarding complete! Welcome to CrossCurrent Hub!');
      }
    } catch {
      toast.error('Failed to update step');
    }
  };

  const handleSaveMerinCode = async () => {
    if (!merinCode.trim()) return;
    setSavingCode(true);
    try {
      await onboardingAPI.updateMerinCode(merinCode.trim());
      toast.success('Merin referral code saved!');
    } catch {
      toast.error('Failed to save code');
    } finally {
      setSavingCode(false);
    }
  };

  const handleGetInviteLink = async () => {
    try {
      const res = await onboardingAPI.getInviteLink();
      setInviteLink(res.data);
      setShowInvite(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Set your Merin code first');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    );
  }

  if (isAdmin || !gateEnabled || checklist?.all_completed) {
    return children;
  }

  const steps = checklist?.steps || [];
  const completedCount = checklist?.completed_count || 0;
  const progress = (completedCount / 7) * 100;

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20">
            <Sparkles className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-orange-400 font-medium">Getting Started</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Welcome to CrossCurrent Hub</h1>
          <p className="text-zinc-500 max-w-md mx-auto">
            Complete all onboarding steps to unlock full platform access.
          </p>
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-zinc-500">
            <span>{completedCount} of 7 steps completed</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-2 bg-[#1a1a1a] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Merin Referral Code Input */}
        <Card className="border-orange-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <p className="text-sm text-white font-medium mb-1">Your Merin Referral Code</p>
                <p className="text-xs text-zinc-500 mb-2">Enter your personal Merin code so others can use it when you invite them.</p>
                <div className="flex gap-2">
                  <Input
                    value={merinCode}
                    onChange={e => setMerinCode(e.target.value.toUpperCase())}
                    placeholder="e.g. BDVMAF"
                    className="bg-[#0a0a0a] border-white/[0.06] text-white font-mono uppercase"
                    data-testid="merin-code-input"
                  />
                  <Button
                    onClick={handleSaveMerinCode}
                    disabled={!merinCode.trim() || savingCode}
                    className="bg-orange-500 hover:bg-orange-600 text-white shrink-0"
                    data-testid="save-merin-code-btn"
                  >
                    {savingCode ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Steps */}
        <div className="space-y-2" data-testid="onboarding-steps">
          {steps.map((step, i) => (
            <Card
              key={step.key}
              className={`transition-all duration-200 ${
                step.completed
                  ? 'border-emerald-500/20 bg-emerald-500/[0.03]'
                  : 'border-white/[0.06] hover:border-white/[0.12]'
              }`}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => !step.auto_verified && handleStepToggle(step.key, step.completed)}
                    disabled={step.auto_verified}
                    className="mt-0.5 shrink-0"
                    data-testid={`step-toggle-${step.key}`}
                  >
                    {step.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <Circle className="w-5 h-5 text-zinc-600 hover:text-zinc-400 transition-colors" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-zinc-600 font-mono">Step {step.step}</span>
                      {step.auto_verified && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">Auto-verified</span>
                      )}
                    </div>
                    <p className={`text-sm font-medium mt-0.5 ${step.completed ? 'text-emerald-400' : 'text-white'}`}>
                      {step.title}
                    </p>
                    <p className="text-xs text-zinc-500 mt-0.5">{step.description}</p>
                    {step.external_url && !step.completed && (
                      <a
                        href={step.external_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-xs text-orange-400 hover:text-orange-300 transition-colors"
                        data-testid={`step-link-${step.key}`}
                      >
                        Open Registration <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    {step.key === 'merin_registered' && !step.completed && (
                      <p className="text-[10px] text-zinc-600 mt-1">
                        After registering, note your own Merin referral code above.
                      </p>
                    )}
                  </div>
                  {!step.completed && !step.auto_verified && (
                    <ChevronRight className="w-4 h-4 text-zinc-600 shrink-0 mt-1" />
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Invite Button */}
        {merinCode && (
          <Button
            onClick={handleGetInviteLink}
            variant="outline"
            className="w-full border-orange-500/20 text-orange-400 hover:bg-orange-500/10"
            data-testid="invite-btn"
          >
            <Link2 className="w-4 h-4 mr-2" />
            Invite Someone with Your Merin Code
          </Button>
        )}

        {/* Invite Dialog */}
        <Dialog open={showInvite} onOpenChange={setShowInvite}>
          <DialogContent className="bg-[#111111] border-white/[0.08]">
            <DialogHeader>
              <DialogTitle className="text-white">Invite Link</DialogTitle>
            </DialogHeader>
            {inviteLink && (
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Your Merin Registration Link</p>
                  <div className="flex gap-2">
                    <Input
                      value={inviteLink.merin_link}
                      readOnly
                      className="bg-[#0a0a0a] border-white/[0.06] text-white font-mono text-xs"
                      data-testid="invite-link-input"
                    />
                    <Button
                      onClick={() => copyToClipboard(inviteLink.merin_link)}
                      size="sm"
                      className="bg-orange-500 hover:bg-orange-600 shrink-0"
                      data-testid="copy-invite-link-btn"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-[#0a0a0a] border border-white/[0.06]">
                  <p className="text-xs text-zinc-400">
                    Share this link with people you want to invite. It automatically includes your Merin referral code <span className="text-orange-400 font-mono">{inviteLink.referral_code}</span> in the registration URL.
                  </p>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default OnboardingGate;
