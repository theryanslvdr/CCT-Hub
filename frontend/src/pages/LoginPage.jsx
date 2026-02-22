import React, { useState, useEffect } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { TrendingUp, Mail, Lock, AlertCircle, HelpCircle, CheckCircle2, XCircle, ExternalLink, Loader2, Key, Wrench } from 'lucide-react';
import { toast } from 'sonner';
import api, { settingsAPI } from '@/lib/api';

export const LoginPage = () => {
  const { login, isAuthenticated, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [platformSettings, setPlatformSettings] = useState(null);
  
  // Maintenance mode states
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [maintenanceMessage, setMaintenanceMessage] = useState('');
  const [masterOverrideClicks, setMasterOverrideClicks] = useState(0);
  const [showLoginOverride, setShowLoginOverride] = useState(false);
  
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
  
  // Forced password change states
  const [showForceChangePassword, setShowForceChangePassword] = useState(false);
  const [forceNewPassword, setForceNewPassword] = useState('');
  const [forceConfirmPassword, setForceConfirmPassword] = useState('');
  const [forceChanging, setForceChanging] = useState(false);

  // Forgot Password states
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  const [forgotStep, setForgotStep] = useState('email'); // 'email', 'token', 'success'
  const [forgotEmail, setForgotEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [resetNewPassword, setResetNewPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);

  // Load platform settings for logo and maintenance mode
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await settingsAPI.getPlatform();
        setPlatformSettings(res.data);
        
        // Check maintenance mode
        if (res.data?.maintenance_mode) {
          setMaintenanceMode(true);
          setMaintenanceMessage(res.data.maintenance_message || 'Our services are undergoing maintenance, and will be back soon!');
        }
      } catch (error) {
        console.error('Failed to load platform settings');
      }
    };
    loadSettings();
  }, []);

  // Handle master admin override clicks
  const handleOverrideClick = () => {
    const newClicks = masterOverrideClicks + 1;
    setMasterOverrideClicks(newClicks);
    
    if (newClicks >= 5) {
      setShowLoginOverride(true);
      toast.info('Master Admin override activated');
    }
  };

  if (isAuthenticated && !loading && !showForceChangePassword) {
    return <Navigate to="/dashboard" replace />;
  }

  // Maintenance Page
  if (maintenanceMode && !showLoginOverride) {
    return (
      <div className="min-h-screen bg-background grid-bg flex items-center justify-center p-4">
        <div className="w-full max-w-2xl text-center">
          {/* Logo */}
          <div className="mb-8">
            {platformSettings?.logo_url ? (
              <img 
                src={platformSettings.logo_url} 
                alt={platformSettings?.platform_name || 'Logo'} 
                className="h-16 mx-auto mb-4"
              />
            ) : (
              <div className="flex items-center justify-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                  <TrendingUp className="w-7 h-7 text-white" />
                </div>
                <span className="text-2xl font-bold text-white tracking-wider">
                  {platformSettings?.platform_name || 'CROSS CURRENT'}
                </span>
              </div>
            )}
          </div>

          {/* Maintenance Icon */}
          <div className="mb-8">
            <div className="w-24 h-24 mx-auto rounded-full bg-amber-500/20 border-2 border-amber-500/50 flex items-center justify-center animate-pulse">
              <Wrench className="w-12 h-12 text-amber-400" />
            </div>
          </div>

          {/* Maintenance Message */}
          <div className="glass-card p-8 rounded-2xl">
            <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Under Maintenance
            </h1>
            <p className="text-lg sm:text-xl text-zinc-300 leading-relaxed">
              {maintenanceMessage.split('soon').map((part, index, array) => (
                <React.Fragment key={index}>
                  {part}
                  {index < array.length - 1 && (
                    <span 
                      onClick={handleOverrideClick}
                      className="cursor-default select-none"
                      data-testid="maintenance-override-trigger"
                    >
                      soon
                    </span>
                  )}
                </React.Fragment>
              ))}
            </p>
            <p className="text-zinc-500 mt-6 text-sm">
              We're working hard to bring you an improved experience. Please check back later.
            </p>
          </div>

          {/* Footer */}
          <p className="mt-8 text-zinc-600 text-sm">
            {platformSettings?.footer_copyright || '© 2024 CrossCurrent Finance Center'}
          </p>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const result = await login(email, password);
    
    if (result.success) {
      if (result.must_change_password) {
        setShowForceChangePassword(true);
      } else {
        toast.success('Welcome back!');
      }
    } else {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

  const handleForceChangePassword = async () => {
    if (forceNewPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    if (forceNewPassword !== forceConfirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    setForceChanging(true);
    try {
      await api.post('/auth/force-change-password', { new_password: forceNewPassword });
      toast.success('Password updated successfully!');
      setShowForceChangePassword(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setForceChanging(false);
    }
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
      } else if (res.data.is_deactivated) {
        // User is deactivated in Heartbeat
        toast.error(res.data.message || 'Your Heartbeat account has been deactivated. Please contact support.');
        setStep('error');
      } else {
        setFailedAttempts(prev => prev + 1);
        setStep('error');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || '';
      if (errorMessage.toLowerCase().includes('deactivated')) {
        toast.error(errorMessage);
      }
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
          {platformSettings?.logo_url ? (
            <img 
              src={platformSettings.logo_url} 
              alt={platformSettings?.platform_name || 'Platform'} 
              className="max-w-[200px] max-h-[80px] object-contain mb-2"
            />
          ) : (
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mb-2">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
          )}
          {platformSettings?.login_title && (
            <h1 className="text-2xl font-bold text-white">{platformSettings.login_title}</h1>
          )}
          <p className="text-zinc-400 text-sm mt-1">{platformSettings?.login_tagline || platformSettings?.tagline || 'Finance Center'}</p>
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

        {/* Community notice */}
        <div className="mt-6 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
          <p className="text-xs text-zinc-500 text-center">
            {platformSettings?.login_notice || 'Only CrossCurrent community members can access this platform.'}
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

      {/* Force Change Password Dialog */}
      <Dialog open={showForceChangePassword} onOpenChange={() => {}}>
        <DialogContent className="bg-zinc-900 border-zinc-800" data-testid="force-change-password-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Key className="w-5 h-5 text-amber-400" /> Password Reset Required
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Your admin has assigned you a temporary password. Please set a new password to continue.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <Label className="text-zinc-300">New Password</Label>
              <Input
                type="password"
                value={forceNewPassword}
                onChange={(e) => setForceNewPassword(e.target.value)}
                placeholder="Enter new password (min 6 chars)"
                className="bg-zinc-800 border-zinc-700 text-white mt-1"
                data-testid="force-new-password-input"
              />
            </div>
            <div>
              <Label className="text-zinc-300">Confirm Password</Label>
              <Input
                type="password"
                value={forceConfirmPassword}
                onChange={(e) => setForceConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className="bg-zinc-800 border-zinc-700 text-white mt-1"
                data-testid="force-confirm-password-input"
              />
            </div>
            <Button
              onClick={handleForceChangePassword}
              disabled={forceChanging || forceNewPassword.length < 6 || forceNewPassword !== forceConfirmPassword}
              className="w-full btn-primary"
              data-testid="force-change-password-submit"
            >
              {forceChanging ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Key className="w-4 h-4 mr-2" />}
              Set New Password
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
