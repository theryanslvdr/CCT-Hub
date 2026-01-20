import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { profitAPI } from '@/lib/api';
import { toast } from 'sonner';
import { Wallet, Calendar, ArrowRight, Sparkles } from 'lucide-react';

export const LicenseeWelcomeScreen = ({ 
  welcomeInfo, 
  onContinue 
}) => {
  const [loading, setLoading] = useState(false);

  const handleContinue = async () => {
    setLoading(true);
    try {
      await profitAPI.markLicenseeWelcomeSeen();
      onContinue();
    } catch (error) {
      console.error('Error marking welcome as seen:', error);
      toast.error('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Not set';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 flex items-center justify-center p-4">
      <Card className="glass-card max-w-lg w-full border-blue-500/30" data-testid="licensee-welcome-screen">
        <CardContent className="p-6 md:p-8">
          {/* Sparkle Animation */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center animate-pulse">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
          </div>

          {/* Welcome Message */}
          <div className="text-center mb-8">
            <h1 className="text-2xl md:text-3xl font-bold text-white mb-4">
              Hey, {welcomeInfo.licensee_name}! 👋
            </h1>
            <p className="text-zinc-300 text-base md:text-lg leading-relaxed">
              You deposited{' '}
              <span className="text-emerald-400 font-bold font-mono">
                {formatCurrency(welcomeInfo.starting_balance)}
              </span>{' '}
              to{' '}
              <span className="text-blue-400 font-semibold">
                {welcomeInfo.master_admin_name}
              </span>{' '}
              and your effective start date is{' '}
              <span className="text-purple-400 font-semibold">
                {formatDate(welcomeInfo.effective_start_date)}
              </span>.
            </p>
          </div>

          {/* Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <Wallet className="w-5 h-5 text-emerald-400" />
                </div>
                <span className="text-xs text-zinc-400 uppercase tracking-wider">Account Value</span>
              </div>
              <p className="text-2xl font-bold font-mono text-emerald-400" data-testid="welcome-account-value">
                {formatCurrency(welcomeInfo.current_balance || welcomeInfo.starting_balance)}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-purple-400" />
                </div>
                <span className="text-xs text-zinc-400 uppercase tracking-wider">Start Date</span>
              </div>
              <p className="text-lg font-semibold text-purple-400" data-testid="welcome-start-date">
                {formatDate(welcomeInfo.effective_start_date)}
              </p>
            </div>
          </div>

          {/* License Type Badge */}
          <div className="text-center mb-6">
            <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${
              welcomeInfo.license_type === 'extended' 
                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' 
                : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
            }`}>
              {welcomeInfo.license_type === 'extended' ? '💎 Extended Licensee' : '⭐ Honorary Licensee'}
            </span>
          </div>

          {/* Continue Button */}
          <Button
            onClick={handleContinue}
            disabled={loading}
            className="w-full btn-primary py-6 text-lg gap-2"
            data-testid="continue-to-tracker-btn"
          >
            {loading ? (
              <>Loading...</>
            ) : (
              <>
                Continue to Profit Tracker
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </Button>

          {/* Subtle Note */}
          <p className="text-center text-xs text-zinc-500 mt-4">
            Your profit tracker will show projections starting from your effective start date.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default LicenseeWelcomeScreen;
