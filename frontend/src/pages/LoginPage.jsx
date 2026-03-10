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

  // Check for reset_token in URL params (from email link)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get('reset_token');
    if (tokenFromUrl) {
      setResetToken(tokenFromUrl);
      setForgotStep('token');
      setForgotPasswordOpen(true);
      // Clean the URL
      window.history.replaceState({}, '', window.location.pathname);
    }
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
      <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden" style={{ background: '#0a0a0a' }}>
        <div className="absolute inset-0 grid-bg opacity-50" />
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-amber-500/[0.05] rounded-full blur-[120px]" />
        <div className="relative z-10 w-full max-w-2xl text-center">
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
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center">
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
            <div className="w-24 h-24 mx-auto rounded-full bg-amber-500/10 border-2 border-amber-500/30 flex items-center justify-center animate-pulse">
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
            <p className="text-zinc-600 mt-6 text-sm">
              We're working hard to bring you an improved experience. Please check back later.
            </p>
          </div>

          {/* Footer */}
          <p className="mt-8 text-zinc-700 text-sm">
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

  const handleForgotPasswordRequest = async () => {
    if (!forgotEmail.trim()) {
      toast.error('Please enter your email');
      return;
    }
    setForgotLoading(true);
    try {
      await api.post('/auth/forgot-password', { email: forgotEmail.trim() });
      setForgotStep('sent');
      toast.success('If that email exists, a reset link has been sent.');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to request password reset');
    } finally {
      setForgotLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!resetToken.trim()) {
      toast.error('Please enter the reset token');
      return;
    }
    if (resetNewPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    if (resetNewPassword !== resetConfirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    setForgotLoading(true);
    try {
      await api.post('/auth/reset-password', {
        token: resetToken.trim(),
        new_password: resetNewPassword
      });
      setForgotStep('success');
      toast.success('Password reset successfully!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden" style={{ background: '#050505' }}>
      {/* Particle star background */}
      <div className="absolute inset-0 star-bg" />
      {/* Ambient glow - top center */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-orange-500/[0.04] rounded-full blur-[150px]" />
      {/* Ambient glow - bottom right */}
      <div className="absolute -bottom-40 -right-20 w-[400px] h-[400px] bg-amber-500/[0.03] rounded-full blur-[130px]" />
      
      <div className="relative z-10 w-full max-w-[420px]">
        {/* Premium opaque dark card */}
        <div 
          className="rounded-3xl p-9 bg-[#111111] border border-[#222222] shadow-[0_8px_60px_rgba(0,0,0,0.6)]"
        >
          {/* Logo */}
          <div className="flex flex-col items-center mb-10">
            {platformSettings?.logo_url ? (
              <img 
                src={platformSettings.logo_url} 
                alt={platformSettings?.platform_name || 'Platform'} 
                className="max-w-[200px] max-h-[80px] object-contain mb-4"
              />
            ) : (
              <div 
                className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                style={{
                  background: 'linear-gradient(135deg, #f97316, #ea580c)',
                  boxShadow: '0 0 40px rgba(249,115,22,0.35), 0 4px 16px rgba(0,0,0,0.4)',
                }}
              >
                <TrendingUp className="w-8 h-8 text-white" />
              </div>
            )}
            {platformSettings?.login_title && (
              <h1 className="text-2xl font-bold text-white tracking-tight">{platformSettings.login_title}</h1>
            )}
            <p className="text-zinc-500 text-sm mt-1.5">{platformSettings?.login_tagline || platformSettings?.tagline || 'Your Trading Finance Hub'}</p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-red-500/8 border border-red-500/15 flex items-start gap-3" data-testid="login-error">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-500 text-[11px] uppercase tracking-widest font-medium">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="pl-11 h-12 rounded-xl text-white placeholder:text-gray-600 bg-[#1a1a1a] border-[#2a2a2a] focus-visible:border-orange-500/50"
                  required
                  data-testid="login-email"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-500 text-[11px] uppercase tracking-widest font-medium">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-11 h-12 rounded-xl text-white placeholder:text-gray-600 bg-[#1a1a1a] border-[#2a2a2a] focus-visible:border-orange-500/50"
                  required
                  data-testid="login-password"
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-12 bg-orange-500 hover:bg-orange-400 text-white font-semibold rounded-xl transition-all active:scale-[0.98]"
              disabled={isLoading}
              data-testid="login-submit"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Signing in...</>
              ) : 'Sign In'}
            </Button>
          </form>

          {/* Forgot Password Link */}
          <div className="mt-5 text-center">
            <button
              onClick={() => {
                setForgotPasswordOpen(true);
                setForgotStep('email');
                setForgotEmail('');
                setResetToken('');
                setResetNewPassword('');
                setResetConfirmPassword('');
              }}
              className="text-zinc-600 hover:text-zinc-400 transition-colors text-sm"
              data-testid="forgot-password-link"
            >
              Forgot Password?
            </button>
          </div>

          {/* No Account Link */}
          <div className="mt-4 text-center">
            <button
              onClick={handleOpenNoAccount}
              className="text-orange-500/70 hover:text-orange-400 transition-colors text-sm flex items-center gap-1.5 mx-auto"
            >
              <HelpCircle className="w-4 h-4" />
              Don't have an account/password?
            </button>
          </div>

          {/* Community notice */}
          <div className="mt-8 pt-6 border-t border-white/[0.04]">
            <p className="text-[11px] text-zinc-700 text-center leading-relaxed">
              {platformSettings?.login_notice || 'Only CrossCurrent community members can access this platform.'}
            </p>
          </div>
        </div>
      </div>

      {/* No Account Dialog */}
      <Dialog open={noAccountOpen} onOpenChange={setNoAccountOpen}>
        <DialogContent className="bg-[#111111] border-white/[0.08] max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-orange-400" />
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
        <DialogContent className="bg-[#111111] border-white/[0.08]" data-testid="force-change-password-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Key className="w-5 h-5 text-amber-400" /> Password Reset Required
            </DialogTitle>
            <DialogDescription className="text-zinc-500">
              Your admin has assigned you a temporary password. Please set a new password to continue.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">New Password</Label>
              <Input
                type="password"
                value={forceNewPassword}
                onChange={(e) => setForceNewPassword(e.target.value)}
                placeholder="Enter new password (min 6 chars)"
                className="bg-[#0a0a0a] border-white/[0.06] text-white mt-1"
                data-testid="force-new-password-input"
              />
            </div>
            <div>
              <Label className="text-zinc-400 text-xs uppercase tracking-wider">Confirm Password</Label>
              <Input
                type="password"
                value={forceConfirmPassword}
                onChange={(e) => setForceConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className="bg-[#0a0a0a] border-white/[0.06] text-white mt-1"
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

      {/* Forgot Password Dialog */}
      <Dialog open={forgotPasswordOpen} onOpenChange={setForgotPasswordOpen}>
        <DialogContent className="bg-[#111111] border-white/[0.08] max-w-md" data-testid="forgot-password-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Key className="w-5 h-5 text-orange-400" />
              {forgotStep === 'email' && 'Reset Your Password'}
              {forgotStep === 'sent' && 'Check Your Email'}
              {forgotStep === 'token' && 'Enter Reset Token'}
              {forgotStep === 'success' && 'Password Reset Complete'}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            {forgotStep === 'email' && (
              <div className="space-y-4">
                <p className="text-zinc-400 text-sm">
                  Enter your email address and we&apos;ll send you a password reset link.
                </p>
                <div>
                  <Label className="text-zinc-300">Email Address</Label>
                  <div className="relative mt-1">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      type="email"
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      placeholder="your@email.com"
                      className="pl-10 input-dark"
                      onKeyDown={(e) => e.key === 'Enter' && handleForgotPasswordRequest()}
                      data-testid="forgot-email-input"
                    />
                  </div>
                </div>
                <Button
                  onClick={handleForgotPasswordRequest}
                  className="w-full btn-primary"
                  disabled={forgotLoading}
                  data-testid="forgot-submit-email"
                >
                  {forgotLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Mail className="w-4 h-4 mr-2" />}
                  Send Reset Link
                </Button>
              </div>
            )}
            {forgotStep === 'sent' && (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/15 text-center">
                  <Mail className="w-10 h-10 text-orange-400 mx-auto mb-2" />
                  <p className="text-orange-300 font-medium">Reset link sent!</p>
                  <p className="text-zinc-400 text-sm mt-1">
                    If an account exists for <span className="text-zinc-300">{forgotEmail}</span>, you&apos;ll receive a password reset link shortly. Check your inbox and spam folder.
                  </p>
                </div>
                <Button
                  onClick={() => setForgotStep('token')}
                  variant="outline"
                  className="w-full"
                  data-testid="enter-token-manually-btn"
                >
                  I have a reset token
                </Button>
                <Button
                  onClick={() => { setForgotPasswordOpen(false); setForgotStep('email'); }}
                  className="w-full btn-primary"
                  data-testid="back-to-login-btn"
                >
                  Back to Login
                </Button>
              </div>
            )}
            {forgotStep === 'token' && (
              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/15">
                  <p className="text-orange-400 text-sm">
                    Enter the reset token from your email, then set your new password.
                  </p>
                </div>
                <div>
                  <Label className="text-zinc-300">Reset Token</Label>
                  <Input
                    type="text"
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    placeholder="Paste your reset token"
                    className="input-dark mt-1"
                    data-testid="reset-token-input"
                  />
                </div>
                <div>
                  <Label className="text-zinc-300">New Password</Label>
                  <div className="relative mt-1">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      type="password"
                      value={resetNewPassword}
                      onChange={(e) => setResetNewPassword(e.target.value)}
                      placeholder="At least 6 characters"
                      className="pl-10 input-dark"
                      data-testid="reset-new-password-input"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-zinc-300">Confirm Password</Label>
                  <div className="relative mt-1">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      type="password"
                      value={resetConfirmPassword}
                      onChange={(e) => setResetConfirmPassword(e.target.value)}
                      placeholder="Confirm password"
                      className="pl-10 input-dark"
                      data-testid="reset-confirm-password-input"
                    />
                  </div>
                </div>
                <Button
                  onClick={handleResetPassword}
                  className="w-full btn-primary"
                  disabled={forgotLoading}
                  data-testid="reset-password-submit"
                >
                  {forgotLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Key className="w-4 h-4 mr-2" />}
                  Reset Password
                </Button>
              </div>
            )}
            {forgotStep === 'success' && (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
                  <p className="text-emerald-400 font-medium">Password reset successfully!</p>
                  <p className="text-zinc-400 text-sm mt-1">You can now log in with your new password.</p>
                </div>
                <Button
                  onClick={() => setForgotPasswordOpen(false)}
                  className="w-full btn-primary"
                  data-testid="reset-done-btn"
                >
                  Back to Login
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
