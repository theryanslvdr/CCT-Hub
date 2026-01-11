import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { 
  Award, User, Mail, Lock, CheckCircle2, XCircle, 
  TrendingUp, DollarSign, Calendar, Loader2
} from 'lucide-react';
import { authAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export const LicenseRegistrationPage = () => {
  const { code } = useParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [validating, setValidating] = useState(true);
  const [inviteData, setInviteData] = useState(null);
  const [error, setError] = useState(null);
  const [registering, setRegistering] = useState(false);
  
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: ''
  });

  useEffect(() => {
    const validateInvite = async () => {
      try {
        const res = await authAPI.validateLicenseInvite(code);
        setInviteData(res.data);
        
        // Pre-fill email and name if available
        if (res.data.invitee_email) {
          setForm(f => ({ ...f, email: res.data.invitee_email }));
        }
        if (res.data.invitee_name) {
          setForm(f => ({ ...f, full_name: res.data.invitee_name }));
        }
      } catch (err) {
        // Handle different error formats
        const errorData = err.response?.data;
        if (typeof errorData === 'string') {
          setError(errorData);
        } else if (errorData?.detail) {
          // FastAPI HTTPException format
          if (typeof errorData.detail === 'string') {
            setError(errorData.detail);
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic validation error format
            setError(errorData.detail.map(e => e.msg).join(', '));
          } else {
            setError('Invalid invite code');
          }
        } else {
          setError('Invalid or expired invite code');
        }
      } finally {
        setValidating(false);
      }
    };

    if (code) {
      validateInvite();
    } else {
      setError('No invite code provided');
      setValidating(false);
    }
  }, [code]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!form.full_name || !form.email || !form.password) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    if (form.password !== form.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (form.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setRegistering(true);
    try {
      const res = await authAPI.registerWithLicense({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        invite_code: code
      });

      toast.success('Registration successful! Welcome to CrossCurrent!');
      
      // Log the user in
      login(res.data.access_token, res.data.user);
      
      // Redirect to dashboard
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setRegistering(false);
    }
  };

  if (validating) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-zinc-400">Validating invite code...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
        <Card className="glass-card max-w-md w-full">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Invalid Invite</h2>
            <p className="text-zinc-400 mb-6">{error}</p>
            <Button onClick={() => navigate('/login')} className="btn-secondary">
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">CrossCurrent Finance Center</h1>
          <p className="text-zinc-400 mt-1">Complete your registration</p>
        </div>

        {/* License Info Card */}
        <Card className={`glass-card mb-6 border ${
          inviteData?.license_type === 'extended' 
            ? 'border-purple-500/30' 
            : 'border-amber-500/30'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                inviteData?.license_type === 'extended'
                  ? 'bg-purple-500/20'
                  : 'bg-amber-500/20'
              }`}>
                <Award className={`w-6 h-6 ${
                  inviteData?.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'
                }`} />
              </div>
              <div>
                <p className="text-xs text-zinc-500">You've been invited as</p>
                <p className={`text-lg font-semibold ${
                  inviteData?.license_type === 'extended' ? 'text-purple-400' : 'text-amber-400'
                }`}>
                  {inviteData?.license_type?.charAt(0).toUpperCase() + inviteData?.license_type?.slice(1)} Licensee
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="p-3 rounded-lg bg-zinc-900/50">
                <div className="flex items-center gap-2 text-zinc-500 mb-1">
                  <DollarSign className="w-4 h-4" />
                  <span>Starting Amount</span>
                </div>
                <p className="text-emerald-400 font-mono text-lg">
                  ${inviteData?.starting_amount?.toLocaleString()}
                </p>
              </div>
              {inviteData?.valid_until && (
                <div className="p-3 rounded-lg bg-zinc-900/50">
                  <div className="flex items-center gap-2 text-zinc-500 mb-1">
                    <Calendar className="w-4 h-4" />
                    <span>Valid Until</span>
                  </div>
                  <p className="text-white">
                    {inviteData.valid_until.split('T')[0]}
                  </p>
                </div>
              )}
            </div>

            {inviteData?.license_type === 'extended' && (
              <div className="mt-4 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <p className="text-xs text-purple-400">
                  Extended License: Your daily profit is calculated quarterly using the formula (Balance ÷ 980) × 15
                </p>
              </div>
            )}

            {inviteData?.license_type === 'honorary' && (
              <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <p className="text-xs text-amber-400">
                  Honorary License: Standard profit calculations apply. Your funds are managed separately from the team pool.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Registration Form */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <User className="w-5 h-5" /> Create Your Account
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label className="text-zinc-300">Full Name *</Label>
                <div className="relative mt-1">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    placeholder="Your full name"
                    className="input-dark pl-10"
                    required
                    data-testid="register-name"
                  />
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">Email Address *</Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="your@email.com"
                    className="input-dark pl-10"
                    required
                    data-testid="register-email"
                  />
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">Password *</Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    placeholder="Min 6 characters"
                    className="input-dark pl-10"
                    required
                    minLength={6}
                    data-testid="register-password"
                  />
                </div>
              </div>

              <div>
                <Label className="text-zinc-300">Confirm Password *</Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type="password"
                    value={form.confirm_password}
                    onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
                    placeholder="Confirm your password"
                    className="input-dark pl-10"
                    required
                    data-testid="register-confirm-password"
                  />
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full btn-primary"
                disabled={registering}
                data-testid="register-submit"
              >
                {registering ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Creating Account...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" /> Complete Registration
                  </>
                )}
              </Button>
            </form>

            <div className="mt-4 text-center">
              <p className="text-sm text-zinc-500">
                Already have an account?{' '}
                <button 
                  onClick={() => navigate('/login')} 
                  className="text-blue-400 hover:underline"
                >
                  Sign in
                </button>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-xs text-zinc-600 mt-6">
          By registering, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
};
