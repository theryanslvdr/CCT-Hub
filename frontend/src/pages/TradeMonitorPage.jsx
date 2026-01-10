import React, { useState, useEffect, useRef, useCallback } from 'react';
import { tradeAPI, profitAPI } from '@/lib/api';
import { formatNumber, calculateExitValue, getPerformanceMessage } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  Play, Square, Calculator, Clock, AlertTriangle, Trophy, Target, 
  TrendingUp, TrendingDown, Volume2, VolumeX, ArrowRight, Send,
  Sparkles, ExternalLink, Rocket
} from 'lucide-react';

// Truncate to 2 decimal places without rounding
const truncateTo2Decimals = (num) => {
  return Math.trunc(num * 100) / 100;
};

// Format large numbers (millions, billions)
const formatLargeNumber = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  
  if (absAmount >= 1e9) {
    return `${sign}$${(absAmount / 1e9).toFixed(2)} Billion`;
  } else if (absAmount >= 1e6) {
    return `${sign}$${(absAmount / 1e6).toFixed(2)} Million`;
  } else {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  }
};

export const TradeMonitorPage = () => {
  const { user } = useAuth();
  const [signal, setSignal] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [profitSummary, setProfitSummary] = useState(null);
  const [isTrading, setIsTrading] = useState(false);
  const [tradeEnded, setTradeEnded] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [showExitAlert, setShowExitAlert] = useState(false);
  const [exitValue, setExitValue] = useState(0);
  const [worldTime, setWorldTime] = useState(new Date());
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [actualExitValue, setActualExitValue] = useState('');
  const [lastTrade, setLastTrade] = useState(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationMessage, setCelebrationMessage] = useState('');
  const [showExitCalculator, setShowExitCalculator] = useState(false);
  const [customLotSize, setCustomLotSize] = useState('');
  const [preTradeCountdown, setPreTradeCountdown] = useState(null);

  const audioRef = useRef(null);
  const beepRef = useRef(null);
  const countdownRef = useRef(null);
  const preTradeBeepRef = useRef(null);

  // Get LOT size from profit tracker
  const lotSize = profitSummary?.account_value ? truncateTo2Decimals(profitSummary.account_value / 980) : 0;
  const userTimezone = user?.timezone || 'Asia/Manila';
  const isPhilippines = userTimezone === 'Asia/Manila';
  const profitMultiplier = signal?.profit_points || 15;

  // Load data
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // World clock
  useEffect(() => {
    const timer = setInterval(() => setWorldTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Calculate exit value when lot size or multiplier changes
  useEffect(() => {
    setExitValue(lotSize * profitMultiplier);
  }, [lotSize, profitMultiplier]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
      if (preTradeBeepRef.current) clearInterval(preTradeBeepRef.current);
    };
  }, []);

  const loadData = async () => {
    try {
      const [signalRes, summaryRes, profitRes] = await Promise.all([
        tradeAPI.getActiveSignal(),
        tradeAPI.getDailySummary(),
        profitAPI.getSummary(),
      ]);
      setSignal(signalRes.data.signal);
      setDailySummary(summaryRes.data);
      setProfitSummary(profitRes.data);
    } catch (error) {
      console.error('Failed to load trade data:', error);
    }
  };

  const formatTimeForTimezone = (date, tz = 'UTC') => {
    try {
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
        timeZone: tz,
      });
    } catch {
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    }
  };

  const formatTimeOnly = (date, tz = 'UTC') => {
    try {
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: tz,
      });
    } catch {
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    }
  };

  // Convert signal time to user's local timezone
  const getSignalTimeInLocalTz = () => {
    if (!signal) return null;
    const [hours, minutes] = signal.trade_time.split(':').map(Number);
    const signalTz = signal.trade_timezone || 'Asia/Manila';
    
    // Create a date object with the signal time in signal's timezone
    const now = new Date();
    const signalDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes, 0);
    
    // Format in user's timezone
    return signalDate.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
      timeZone: userTimezone,
    });
  };

  // Play beep sound for countdown
  const playBeep = () => {
    if (beepRef.current && soundEnabled) {
      beepRef.current.currentTime = 0;
      beepRef.current.play().catch(console.error);
    }
  };

  const startTrade = useCallback(() => {
    if (!signal) {
      toast.error('No active trading signal!');
      return;
    }

    setIsTrading(true);
    setTradeEnded(false);
    setShowExitAlert(false);
    setLastTrade(null);
    setShowCelebration(false);
    setPreTradeCountdown(null);

    // Parse trade time based on signal timezone
    const [hours, minutes] = signal.trade_time.split(':').map(Number);
    const signalTz = signal.trade_timezone || 'Asia/Manila';
    
    // Create target time in signal's timezone
    const now = new Date();
    const tradeTime = new Date();
    
    // Convert signal time to UTC for comparison
    const tzOffset = getTimezoneOffset(signalTz);
    tradeTime.setUTCHours(hours - tzOffset, minutes, 0, 0);

    // If trade time has passed, set for tomorrow
    if (tradeTime <= now) {
      tradeTime.setDate(tradeTime.getDate() + 1);
    }

    // Start countdown
    countdownRef.current = setInterval(() => {
      const now = new Date();
      const diff = tradeTime - now;

      if (diff <= 0) {
        clearInterval(countdownRef.current);
        setShowExitAlert(true);
        setCountdown(null);
        setPreTradeCountdown(null);
        
        if (soundEnabled && audioRef.current) {
          audioRef.current.play().catch(console.error);
        }
        
        toast.success('🚨 ENTER THE TRADE NOW!', { duration: 10000 });
      } else {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        // 5-second countdown beep before trade time
        if (diff <= 5000 && diff > 0) {
          const secondsLeft = Math.ceil(diff / 1000);
          setPreTradeCountdown(secondsLeft);
          playBeep();
        } else {
          setPreTradeCountdown(null);
        }
        
        setCountdown({ hours, minutes, seconds, total: diff });
      }
    }, 1000);
  }, [signal, soundEnabled]);

  const getTimezoneOffset = (tz) => {
    const tzOffsets = {
      'Asia/Manila': 8,
      'Asia/Singapore': 8,
      'Asia/Taipei': 8,
      'UTC': 0,
    };
    return tzOffsets[tz] || 0;
  };

  const endTrade = () => {
    setShowExitAlert(false);
    setTradeEnded(true);
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

  const stopTrade = () => {
    setIsTrading(false);
    setShowExitAlert(false);
    setTradeEnded(false);
    setCountdown(null);
    setPreTradeCountdown(null);
    setLastTrade(null);
    setActualExitValue('');
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

  const submitActualProfit = async () => {
    if (!actualExitValue || parseFloat(actualExitValue) < 0) {
      toast.error('Please enter a valid exit value');
      return;
    }

    try {
      const response = await tradeAPI.logTrade({
        lot_size: lotSize,
        direction: signal?.direction || 'BUY',
        actual_profit: parseFloat(actualExitValue),
        notes: `Signal: ${signal?.product || 'MOIL10'}`,
      });

      const result = response.data;
      setLastTrade(result);
      setTradeEnded(false);
      setIsTrading(false);

      // Show celebration popup based on performance
      const message = getPerformanceMessage(result.performance);
      setCelebrationMessage(message);
      setShowCelebration(true);

      setActualExitValue('');
      loadData();
    } catch (error) {
      toast.error('Failed to log trade');
    }
  };

  const forwardToProfit = async (tradeId) => {
    try {
      await tradeAPI.forwardToProfit(tradeId);
      toast.success('Trade profit forwarded to Profit Tracker!');
      setLastTrade(null);
      setShowCelebration(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to forward trade');
    }
  };

  // Calculate custom exit value
  const customExitValue = customLotSize ? parseFloat(customLotSize) * profitMultiplier : 0;

  // Performance message for today's summary
  const getDailyPerformanceMessage = () => {
    const diff = dailySummary?.difference || 0;
    if (diff > 0) return "🎉 Great job! You're exceeding targets today!";
    if (diff === 0) return "✨ Perfect execution! Right on target!";
    return "💪 Keep pushing! Every trade is a learning opportunity.";
  };

  return (
    <div className="space-y-6">
      {/* Audio elements */}
      <audio ref={audioRef} loop>
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg" />
      </audio>
      <audio ref={beepRef}>
        <source src="https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3" type="audio/mpeg" />
      </audio>

      {/* Active Signal Banner with User Local Time & Profit Multiplier */}
      {signal ? (
        <div className={`glass-highlight p-6 ${showExitAlert ? 'exit-section active' : ''}`} data-testid="active-signal-banner">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <p className="text-xs text-zinc-400 uppercase tracking-wider">Active Signal</p>
                <p className="text-3xl font-bold text-white">{signal.product}</p>
              </div>
              <div className={`px-6 py-3 rounded-xl text-2xl font-bold ${signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                {signal.direction}
              </div>
              <div>
                <p className="text-xs text-zinc-400 uppercase tracking-wider">
                  Trade Time (Philippines)
                </p>
                <p className="text-3xl font-mono font-bold text-blue-400">{signal.trade_time}</p>
              </div>
              {/* User Local Time & Profit Multiplier */}
              <div className="flex items-center gap-4">
                {!isPhilippines && (
                  <div>
                    <p className="text-xs text-zinc-400 uppercase tracking-wider">Your Time ({userTimezone.split('/')[1]})</p>
                    <p className="text-xl font-mono font-bold text-cyan-400">{getSignalTimeInLocalTz()}</p>
                  </div>
                )}
                <div className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30">
                  <p className="text-xs text-zinc-400 uppercase tracking-wider text-center">Multiplier</p>
                  <p className="text-2xl font-mono font-bold text-purple-400 text-center">×{profitMultiplier}</p>
                </div>
              </div>
            </div>
            {signal.notes && (
              <div className="text-zinc-400 text-sm max-w-md">{signal.notes}</div>
            )}
          </div>
        </div>
      ) : (
        <div className="glass-card p-6 border-2 border-dashed border-zinc-700">
          <div className="flex items-center gap-4 text-zinc-500">
            <AlertTriangle className="w-6 h-6" />
            <p>No active trading signal. Wait for admin to post today's signal.</p>
          </div>
        </div>
      )}

      {/* LOT Size & Projected Exit Value Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* LOT Size Card */}
        <Card className="glass-card" data-testid="lot-size-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Current LOT Size</p>
                <p className="text-4xl font-mono font-bold text-purple-400 mt-2" data-testid="lot-size-value">
                  {lotSize.toFixed(2)}
                </p>
                <p className="text-xs text-zinc-500 mt-1">From Profit Tracker (Balance ÷ 980)</p>
              </div>
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                <Calculator className="w-7 h-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Projected Exit Value Card */}
        <Card className="glass-card" data-testid="projected-exit-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm text-zinc-400">Projected Exit Value</p>
                <p className="text-4xl font-mono font-bold text-emerald-400 mt-2" data-testid="projected-exit-value">
                  {formatLargeNumber(exitValue)}
                </p>
                <p className="text-xs text-zinc-500 mt-1">LOT × {profitMultiplier} = {formatLargeNumber(exitValue)}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                  <Rocket className="w-7 h-7 text-white" />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowExitCalculator(true)}
                  className="text-blue-400 border-blue-400/30 hover:bg-blue-400/10"
                  data-testid="open-exit-calculator"
                >
                  <Calculator className="w-4 h-4 mr-1" /> Calculator
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trade Control */}
      <Card className={`glass-card ${showExitAlert ? 'exit-section active' : ''}`} data-testid="trade-control-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white">Trade Control</CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="text-zinc-400"
            data-testid="sound-toggle"
          >
            {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
          </Button>
        </CardHeader>
        <CardContent>
          {showExitAlert ? (
            <div className="text-center space-y-6">
              <div className="animate-bounce">
                <div className="text-6xl">🚨</div>
              </div>
              <h2 className="text-4xl font-bold text-emerald-400 animate-pulse">ENTER THE TRADE NOW!</h2>
              <p className="text-xl text-zinc-300">Target Exit Value: <span className="font-mono text-emerald-400">{formatLargeNumber(exitValue)}</span></p>
              <div className="flex gap-4 justify-center">
                <Button onClick={endTrade} className="btn-primary text-xl py-6 px-8" data-testid="end-trade-button">
                  <Square className="w-6 h-6 mr-2" /> End Trade
                </Button>
              </div>
            </div>
          ) : tradeEnded ? (
            <div className="text-center space-y-6">
              <h3 className="text-2xl font-bold text-white">Enter Your Actual Profit</h3>
              <p className="text-zinc-400">How much did you actually make from this trade?</p>
              <div className="max-w-xs mx-auto">
                <Label className="text-zinc-300">Actual Profit (USD)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={actualExitValue}
                  onChange={(e) => setActualExitValue(e.target.value)}
                  placeholder="Enter actual profit"
                  className="input-dark mt-1 text-xl font-mono text-center"
                  data-testid="actual-exit-input"
                />
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Projected Value</p>
                <p className="text-2xl font-mono font-bold text-blue-400">{formatLargeNumber(exitValue)}</p>
              </div>
              <Button onClick={submitActualProfit} className="btn-primary py-4 px-8" data-testid="submit-actual-button">
                Submit & See Results
              </Button>
            </div>
          ) : isTrading && countdown ? (
            <div className="text-center space-y-6">
              <p className="text-zinc-400">Time until trade:</p>
              
              {/* Pre-trade countdown beep indicator */}
              {preTradeCountdown && (
                <div className="animate-pulse p-4 rounded-xl bg-red-500/20 border border-red-500/50">
                  <p className="text-3xl font-mono font-bold text-red-400">
                    GET READY IN {preTradeCountdown}...
                  </p>
                </div>
              )}
              
              <div className="flex justify-center gap-4">
                {['hours', 'minutes', 'seconds'].map((unit) => (
                  <div key={unit} className={`glass-card p-4 min-w-[100px] ${preTradeCountdown ? 'border-red-500/50 animate-pulse' : ''}`}>
                    <p className={`text-4xl font-mono font-bold ${preTradeCountdown ? 'text-red-400' : 'text-white'}`}>
                      {String(countdown[unit]).padStart(2, '0')}
                    </p>
                    <p className="text-xs text-zinc-500 uppercase">{unit}</p>
                  </div>
                ))}
              </div>
              <div className="text-zinc-400">
                Target Exit: <span className="text-2xl font-mono font-bold text-emerald-400">{formatLargeNumber(exitValue)}</span>
              </div>
              <Button onClick={stopTrade} variant="outline" className="btn-secondary" data-testid="cancel-trade-button">
                <Square className="w-5 h-5 mr-2" /> Cancel
              </Button>
            </div>
          ) : (
            <div className="text-center space-y-6">
              <p className="text-zinc-400">Ready to trade? Check in when you're ready.</p>
              <Button
                onClick={startTrade}
                className="exit-button idle py-8 text-2xl w-full max-w-md"
                disabled={!signal}
                data-testid="check-in-button"
              >
                <Play className="w-8 h-8 mr-3" /> Enter the Trade Now!
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* World Timer & Today's Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* World Timer - Prioritize Philippines Time */}
        <Card className="glass-card" data-testid="time-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5" /> Your Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              {/* Primary: Philippine Time */}
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                Philippines (Asia/Manila)
              </p>
              <p className="text-6xl font-mono font-bold text-white tracking-wider" data-testid="ph-time">
                {formatTimeForTimezone(worldTime, 'Asia/Manila')}
              </p>
              
              {/* Secondary: User's Local Time (smaller, underneath) */}
              {!isPhilippines && (
                <div className="mt-4 pt-4 border-t border-zinc-800">
                  <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">
                    Your Local Time ({userTimezone})
                  </p>
                  <p className="text-2xl font-mono text-zinc-400" data-testid="local-time">
                    {formatTimeForTimezone(worldTime, userTimezone)}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Today's Summary - Simplified: Only Actual Total & P/L Difference + Encouragement */}
        <Card className="glass-card" data-testid="todays-summary-card">
          <CardHeader>
            <CardTitle className="text-white">Today's Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Actual Total</p>
                <p className="text-3xl font-mono font-bold text-emerald-400" data-testid="actual-total">
                  {formatLargeNumber(dailySummary?.total_actual || 0)}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">P/L Difference</p>
                <p className={`text-3xl font-mono font-bold ${(dailySummary?.difference || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`} data-testid="pl-difference">
                  {(dailySummary?.difference || 0) >= 0 ? '+' : ''}{formatLargeNumber(dailySummary?.difference || 0)}
                </p>
              </div>
            </div>
            {/* Encouragement phrase placed here */}
            <div className="mt-4 p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 text-center">
              <p className="text-zinc-300" data-testid="encouragement-message">{getDailyPerformanceMessage()}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Exit Value Calculator Popup */}
      <Dialog open={showExitCalculator} onOpenChange={setShowExitCalculator}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Calculator className="w-5 h-5 text-blue-400" /> Exit Value Calculator
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Custom LOT Size</Label>
              <Input
                type="number"
                step="0.01"
                value={customLotSize}
                onChange={(e) => setCustomLotSize(e.target.value)}
                placeholder="Enter LOT size"
                className="input-dark mt-1 text-xl font-mono"
                data-testid="custom-lot-input"
              />
            </div>
            <div className="p-6 rounded-xl bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 text-center">
              <p className="text-sm text-zinc-400 mb-2">Exit Value (LOT × {profitMultiplier})</p>
              <p className="text-5xl font-mono font-bold text-gradient" data-testid="custom-exit-value">
                {formatLargeNumber(customExitValue)}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/50 text-sm text-zinc-400">
              <p>• Current LOT from Profit Tracker: <span className="text-purple-400 font-mono">{lotSize.toFixed(2)}</span></p>
              <p>• Profit Multiplier: <span className="text-cyan-400 font-mono">×{profitMultiplier}</span></p>
              <p>• Formula: LOT Size × {profitMultiplier} = Exit Value</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Celebration Popup - Shows after entering actual profit */}
      <Dialog open={showCelebration} onOpenChange={setShowCelebration}>
        <DialogContent className={`glass-card border-zinc-800 ${lastTrade?.performance === 'exceeded' ? 'border-emerald-500/50' : lastTrade?.performance === 'perfect' ? 'border-blue-500/50' : 'border-amber-500/50'}`}>
          <div className="text-center space-y-6 py-4">
            {lastTrade?.performance === 'exceeded' && (
              <div className="animate-bounce">
                <Trophy className="w-20 h-20 text-emerald-400 mx-auto" />
              </div>
            )}
            {lastTrade?.performance === 'perfect' && (
              <Target className="w-20 h-20 text-blue-400 mx-auto" />
            )}
            {lastTrade?.performance === 'below' && (
              <TrendingDown className="w-20 h-20 text-amber-400 mx-auto" />
            )}
            
            <h2 className="text-3xl font-bold text-white" data-testid="celebration-message">{celebrationMessage}</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Projected</p>
                <p className="text-2xl font-mono font-bold text-blue-400">{formatLargeNumber(lastTrade?.projected_profit || 0)}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Actual</p>
                <p className="text-2xl font-mono font-bold text-emerald-400">{formatLargeNumber(lastTrade?.actual_profit || 0)}</p>
              </div>
            </div>
            
            <div className="p-4 rounded-lg bg-zinc-900/50">
              <p className="text-sm text-zinc-400">P/L Difference</p>
              <p className={`text-4xl font-mono font-bold ${(lastTrade?.profit_difference || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`} data-testid="celebration-pl-diff">
                {(lastTrade?.profit_difference || 0) >= 0 ? '+' : ''}{formatLargeNumber(lastTrade?.profit_difference || 0)}
              </p>
            </div>

            <Button
              onClick={() => forwardToProfit(lastTrade?.id)}
              className="btn-primary gap-2 w-full"
              data-testid="forward-to-profit-button"
            >
              <Send className="w-4 h-4" /> Forward to Profit Tracker
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
