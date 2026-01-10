import React, { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { TrendingUp, Mail, Lock, User, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export const RegisterPage = () => {
  const { register, isAuthenticated, loading } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    heartbeat_email: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  if (isAuthenticated && !loading) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    const result = await register({
      full_name: formData.full_name,
      email: formData.email,
      password: formData.password,
      heartbeat_email: formData.heartbeat_email || formData.email,
    });
    
    if (result.success) {
      toast.success('Welcome to CrossCurrent!');
    } else {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 grid-bg">
      <div className="glass-card w-full max-w-md p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mb-4">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Join CrossCurrent</h1>
          <p className="text-zinc-400 mt-1">Create your account</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full_name" className="text-zinc-300">Full Name</Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <Input
                id="full_name"
                name="full_name"
                type="text"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="John Doe"
                className="pl-10 input-dark"
                required
                data-testid="register-name"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-zinc-300">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
                className="pl-10 input-dark"
                required
                data-testid="register-email"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="heartbeat_email" className="text-zinc-300">
              Heartbeat Email <span className="text-zinc-500">(if different)</span>
            </Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <Input
                id="heartbeat_email"
                name="heartbeat_email"
                type="email"
                value={formData.heartbeat_email}
                onChange={handleChange}
                placeholder="heartbeat@email.com"
                className="pl-10 input-dark"
                data-testid="register-heartbeat-email"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-zinc-300">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <Input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="pl-10 input-dark"
                required
                data-testid="register-password"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-zinc-300">Confirm Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="••••••••"
                className="pl-10 input-dark"
                required
                data-testid="register-confirm-password"
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full btn-primary py-3"
            disabled={isLoading}
            data-testid="register-submit"
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-zinc-500 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-400 hover:text-blue-300 transition-colors">
              Sign In
            </Link>
          </p>
        </div>

        {/* Heartbeat notice */}
        <div className="mt-6 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800">
          <p className="text-xs text-zinc-500 text-center">
            You must be a Heartbeat community member to register.
            Your membership will be verified automatically.
          </p>
        </div>
      </div>
    </div>
  );
};
