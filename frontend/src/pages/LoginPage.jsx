import React, { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { TrendingUp, Mail, Lock, AlertCircle, HelpCircle, CheckCircle2, XCircle, ExternalLink, Loader2, Key } from 'lucide-react';
import { toast } from 'sonner';
import api, { settingsAPI } from '@/lib/api';

export const LoginPage = () => {
  const { login, isAuthenticated, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // No account dialog states
  const [noAccountOpen, setNoAccountOpen] = useState(false);
  const [step, setStep] = useState('ask'); // 'ask', 'verify', 'password', 'error'
  const [heartbeatEmail, setHeartbeatEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verifiedUser, setVerifiedUser] = useState(null);
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [customLink, setCustomLink] = useState('');
  const [creating, setCreating] = useState(false);

  if (isAuthenticated && !loading) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const result = await login(email, password);
    
    if (result.success) {
      toast.success('Welcome back!');
    } else {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

  const handleOpenNoAccount = async () => {
    setNoAccountOpen(true);
    setStep('ask');
    setHeartbeatEmail('');
    setNewPassword('');
    setConfirmPassword('');
    setVerifiedUser(null);
    
    // Fetch custom link from settings
    try {
      const res = await settingsAPI.get();
      setCustomLink(res.data.custom_registration_link || '');
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    }
  };

  const handleVerifyHeartbeat = async () => {
    if (!heartbeatEmail.trim()) {
      toast.error('Please enter your email');
      return;
    }

    setVerifying(true);
    try {
      const res = await api.post('/auth/verify-heartbeat', { email: heartbeatEmail.trim() });
      if (res.data.verified && res.data.user) {
        setVerifiedUser(res.data.user);
        setStep('password');
        setFailedAttempts(0);
      } else {
        setFailedAttempts(prev => prev + 1);
        setStep('error');
      }
    } catch (error) {
      setFailedAttempts(prev => prev + 1);
      setStep('error');
    } finally {
      setVerifying(false);
    }
  };

  const handleSetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setCreating(true);
    try {
      await api.post('/auth/set-password', {
        email: heartbeatEmail.trim(),
        password: newPassword
      });
      toast.success('Password set successfully! You can now log in.');
      setNoAccountOpen(false);
      setEmail(heartbeatEmail);
      setPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to set password');
    } finally {
      setCreating(false);
    }
  };

  const handleRetry = () => {
    setStep('verify');
    setHeartbeatEmail('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 grid-bg">
      <div className="glass-card w-full max-w-md p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mb-4">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">CrossCurrent</h1>
          <p className="text-zinc-400 mt-1">Finance Center</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-3" data-testid="login-error">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-zinc-300">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="pl-10 input-dark"
                required
                data-testid="login-email"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-zinc-300">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="pl-10 input-dark"
                required
                data-testid="login-password"
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full btn-primary py-3"
            disabled={isLoading}
            data-testid="login-submit"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        {/* No Account Link */}
        <div className="mt-6 text-center">
          <button
            onClick={handleOpenNoAccount}
            className="text-blue-400 hover:text-blue-300 transition-colors text-sm flex items-center gap-1 mx-auto"
          >
            <HelpCircle className="w-4 h-4" />
            Don't have an account/password?
          </button>
        </div>

        {/* Heartbeat notice */}
        <div className="mt-6 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
          <p className="text-xs text-zinc-500 text-center">
            Only Heartbeat community members can access this platform.
          </p>
        </div>
      </div>

      {/* No Account Dialog */}
      <Dialog open={noAccountOpen} onOpenChange={setNoAccountOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-blue-400" />
              {step === 'ask' && 'Account Setup'}
              {step === 'verify' && 'Verify Membership'}
              {step === 'password' && 'Set Your Password'}
              {step === 'error' && 'Verification Failed'}
            </DialogTitle>
          </DialogHeader>

          <div className="mt-4">
            {/* Step: Ask if member */}
            {step === 'ask' && (
              <div className="space-y-4">
                <p className="text-zinc-300 text-sm">
                  Are you already a member of CrossCurrent Traders?
                </p>
                <div className="flex gap-3">
                  <Button 
                    onClick={() => setStep('verify')}
                    className="flex-1 btn-primary"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Yes, I am
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      if (customLink) {
                        window.open(customLink, '_blank');
                      } else {
                        toast.info('Registration link not configured. Please contact admin.');
                      }
                    }}
                    className="flex-1 btn-secondary"
                  >
                    <XCircle className="w-4 h-4 mr-2" /> No, I'm not
                  </Button>
                </div>
              </div>
            )}

            {/* Step: Verify Heartbeat */}
            {step === 'verify' && (
              <div className="space-y-4">
                <p className="text-zinc-400 text-sm">
                  Enter your Heartbeat email to verify your membership.
                </p>
                <div>
                  <Label className="text-zinc-300">Heartbeat Email</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      type="email"
                      value={heartbeatEmail}
                      onChange={(e) => setHeartbeatEmail(e.target.value)}
                      placeholder="your@email.com"
                      className="pl-10 input-dark"
                      onKeyDown={(e) => e.key === 'Enter' && handleVerifyHeartbeat()}
                    />
                  </div>
                </div>
                <Button 
                  onClick={handleVerifyHeartbeat}
                  className="w-full btn-primary"
                  disabled={verifying}
                >
                  {verifying ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Verifying...</>
                  ) : (
                    <>Verify Membership</>
                  )}
                </Button>
              </div>
            )}

            {/* Step: Set Password */}
            {step === 'password' && (
              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <p className="text-emerald-400 text-sm flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Membership verified! Welcome, {verifiedUser?.full_name || 'member'}
                  </p>
                </div>
                
                <div>
                  <Label className="text-zinc-300">New Password</Label>
                  <div className="relative mt-1">
                    <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="At least 6 characters"
                      className="pl-10 input-dark"
                    />
                  </div>
                </div>
                
                <div>
                  <Label className="text-zinc-300">Confirm Password</Label>
                  <div className="relative mt-1">
                    <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm your password"
                      className="pl-10 input-dark"
                    />
                  </div>
                </div>

                <Button 
                  onClick={handleSetPassword}
                  className="w-full btn-primary"
                  disabled={creating}
                >
                  {creating ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Setting Password...</>
                  ) : (
                    <>Set Password & Continue</>
                  )}
                </Button>
              </div>
            )}

            {/* Step: Error */}
            {step === 'error' && (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                  <p className="text-red-400 text-sm">
                    The email you've entered is either wrong or you're not a member of CrossCurrent Traders.
                  </p>
                </div>
                
                <div className="flex gap-3">
                  <Button 
                    onClick={handleRetry}
                    className="flex-1 btn-secondary"
                  >
                    Try Again
                  </Button>
                  {failedAttempts >= 2 && customLink && (
                    <Button 
                      onClick={() => window.open(customLink, '_blank')}
                      className="flex-1 btn-primary"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" /> Register as Member
                    </Button>
                  )}
                </div>
                
                {failedAttempts < 2 && (
                  <p className="text-zinc-500 text-xs text-center">
                    {2 - failedAttempts} attempt(s) remaining before registration option appears
                  </p>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
