import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { DollarSign, TrendingUp } from 'lucide-react';

// Format money helper
const formatMoney = (amount) => {
  if (typeof amount !== 'number' || isNaN(amount)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Calculate lot size from balance
const calculateLotSize = (balance) => {
  const numBalance = parseFloat(balance) || 0;
  return Math.floor((numBalance / 980) * 100) / 100; // Truncate to 2 decimals
};

// Calculate projected profit from lot size
const calculateProjectedProfit = (lotSize) => {
  return Math.floor((lotSize * 15) * 100) / 100; // Truncate to 2 decimals
};

/**
 * Step 2: Starting Balance Entry (for new traders)
 * User enters their initial balance to start tracking
 */
export const StepNewTraderBalance = ({ startingBalance, setStartingBalance }) => {
  const lotSize = calculateLotSize(startingBalance);
  const dailyProfit = calculateProjectedProfit(lotSize);

  // Handle balance input with 2 decimal place limit
  const handleBalanceChange = (e) => {
    const value = e.target.value;
    // Allow empty input or valid decimal numbers
    if (value === '' || /^\d*\.?\d{0,2}$/.test(value)) {
      setStartingBalance(value);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
          <DollarSign className="w-8 h-8 text-emerald-400" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">What&apos;s your starting balance?</h2>
        <p className="text-zinc-400 text-sm">
          Enter the amount you&apos;re starting with on Merin
        </p>
      </div>
      
      <div className="max-w-md mx-auto">
        <Label className="text-zinc-300">Starting Balance (USDT)</Label>
        <div className="relative mt-2">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400">$</span>
          <Input
            type="number"
            step="0.01"
            min="0"
            value={startingBalance}
            onChange={handleBalanceChange}
            placeholder="10000"
            className="input-dark pl-8 text-xl font-mono"
            data-testid="starting-balance-input"
          />
        </div>
        
        {startingBalance && parseFloat(startingBalance) > 0 && (
          <div className="mt-6 grid grid-cols-2 gap-4">
            <Card className="glass-card">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-zinc-400 uppercase mb-1">Your LOT Size</p>
                <p className="text-2xl font-mono text-purple-400">
                  {lotSize.toFixed(2)}
                </p>
              </CardContent>
            </Card>
            <Card className="glass-card">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-zinc-400 uppercase mb-1">Daily Target</p>
                <p className="text-2xl font-mono text-emerald-400">
                  {formatMoney(dailyProfit)}
                </p>
              </CardContent>
            </Card>
          </div>
        )}
        
        <div className="mt-6 p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <p className="text-sm text-blue-400 font-medium">How it works</p>
              <p className="text-xs text-zinc-400 mt-1">
                LOT Size = Balance ÷ 980<br />
                Daily Target = LOT × $15
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StepNewTraderBalance;
