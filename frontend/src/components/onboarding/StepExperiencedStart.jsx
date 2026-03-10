import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { format } from 'date-fns';
import { Calendar as CalendarIcon, DollarSign, TrendingUp } from 'lucide-react';

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
  return Math.floor((numBalance / 980) * 100) / 100;
};

// Calculate projected profit from lot size
const calculateProjectedProfit = (lotSize) => {
  return Math.floor((lotSize * 15) * 100) / 100;
};

/**
 * Step 2: Experienced Trader - Start Date and Balance
 * User enters when they started trading and their initial balance
 */
export const StepExperiencedStart = ({ 
  startDate, 
  setStartDate, 
  startingBalance, 
  setStartingBalance,
  minDate // Minimum allowed start date
}) => {
  const lotSize = calculateLotSize(startingBalance);
  const dailyProfit = calculateProjectedProfit(lotSize);
  const today = new Date();

  // Handle balance input with 2 decimal place limit
  const handleBalanceChange = (e) => {
    const value = e.target.value;
    if (value === '' || /^\d*\.?\d{0,2}$/.test(value)) {
      setStartingBalance(value);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/20 flex items-center justify-center">
          <CalendarIcon className="w-8 h-8 text-purple-400" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">When did you start?</h2>
        <p className="text-zinc-400 text-sm">
          Select your first trading date and starting balance
        </p>
      </div>
      
      <div className="max-w-md mx-auto space-y-6">
        {/* Start Date */}
        <div>
          <Label className="text-zinc-300">Start Date</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-full mt-2 justify-start text-left font-normal input-dark"
                data-testid="start-date-picker"
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {startDate ? format(startDate, 'PPP') : <span className="text-zinc-500">Pick a date</span>}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0 bg-[#0d0d0d] border-white/[0.08]" align="start">
              <Calendar
                mode="single"
                selected={startDate}
                onSelect={setStartDate}
                disabled={(date) => date > today || (minDate && date < minDate)}
                initialFocus
                className="bg-[#0d0d0d]"
              />
            </PopoverContent>
          </Popover>
        </div>
        
        {/* Starting Balance */}
        <div>
          <Label className="text-zinc-300">Starting Balance on that day (USDT)</Label>
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
              data-testid="starting-balance-experienced"
            />
          </div>
        </div>
        
        {/* Preview Cards */}
        {startingBalance && parseFloat(startingBalance) > 0 && (
          <div className="grid grid-cols-2 gap-4">
            <Card className="glass-card">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-zinc-400 uppercase mb-1">Starting LOT</p>
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
        
        {/* Info Box */}
        <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-purple-400 mt-0.5" />
            <div>
              <p className="text-sm text-purple-400 font-medium">Importing History</p>
              <p className="text-xs text-zinc-400 mt-1">
                We&apos;ll help you import your trading history from this date forward. 
                You&apos;ll enter your daily profits in the next steps.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StepExperiencedStart;
