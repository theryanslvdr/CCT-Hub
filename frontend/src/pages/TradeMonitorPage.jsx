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
import { Play, Square, Calculator, Clock, AlertTriangle, Trophy, Target, TrendingUp, TrendingDown, Volume2, VolumeX, ArrowRight, Send } from 'lucide-react';

export const TradeMonitorPage = () => {
  const { user } = useAuth();
  const [signal, setSignal] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [profitSummary, setProfitSummary] = useState(null);
  const [isTrading, setIsTrading] = useState(false);
  const [tradeEnded, setTradeEnded] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [showExitAlert, setShowExitAlert] = useState(false);
  const [lotSize, setLotSize] = useState(user?.lot_size || 0.01);
  const [exitValue, setExitValue] = useState(0);
  const [worldTime, setWorldTime] = useState(new Date());
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [actualExitValue, setActualExitValue] = useState('');
  const [lastTrade, setLastTrade] = useState(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationMessage, setCelebrationMessage] = useState('');

  const audioRef = useRef(null);
  const countdownRef = useRef(null);

  // Load data
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // World clock - uses user's timezone from profile
  useEffect(() => {
    const timer = setInterval(() => setWorldTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Calculate exit value when lot size changes
  useEffect(() => {
    setExitValue(calculateExitValue(lotSize));
  }, [lotSize]);

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
        
        if (soundEnabled && audioRef.current) {
          audioRef.current.play().catch(console.error);
        }
        
        toast.success('🚨 EXIT NOW! Trade time reached!', { duration: 10000 });
      } else {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
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

      // Show celebration based on performance
      const message = getPerformanceMessage(result.performance);
      setCelebrationMessage(message);
      setShowCelebration(true);

      if (result.performance === 'exceeded') {
        toast.success(message, { duration: 5000 });
      } else if (result.performance === 'perfect') {
        toast.success(message, { duration: 5000 });
      } else {
        toast.info(message, { duration: 5000 });
      }

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

  // Get projected profit from profit tracker
  const projectedProfit = profitSummary?.total_projected_profit || 0;

  return (
    <div className="space-y-6">
      {/* Audio element for alarm */}
      <audio ref={audioRef} loop>
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg" />
      </audio>

      {/* Active Signal Banner */}
      {signal ? (
        <div className={`glass-highlight p-6 ${showExitAlert ? 'exit-section active' : ''}`}>
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
            <div className="flex items-center gap-6">
              <div>
                <p className="text-xs text-zinc-400 uppercase tracking-wider">Active Signal</p>
                <p className="text-3xl font-bold text-white">{signal.product}</p>
              </div>
              <div className={`px-6 py-3 rounded-xl text-2xl font-bold ${signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                {signal.direction}
              </div>
              <div>
                <p className="text-xs text-zinc-400 uppercase tracking-wider">Trade Time ({signal.trade_timezone || 'Asia/Manila'})</p>
                <p className="text-3xl font-mono font-bold text-blue-400">{signal.trade_time}</p>
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

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trade Control */}
        <Card className={`glass-card lg:col-span-2 ${showExitAlert ? 'exit-section active' : ''}`}>
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
                <h2 className="text-4xl font-bold text-emerald-400 animate-pulse">EXIT NOW!</h2>
                <p className="text-xl text-zinc-300">Target Exit Value: <span className="font-mono text-emerald-400">${formatNumber(exitValue)}</span></p>
                <div className="flex gap-4 justify-center">
                  <Button onClick={endTrade} className="btn-primary text-xl py-6 px-8" data-testid="end-trade-button">
                    <Square className="w-6 h-6 mr-2" /> End Trade
                  </Button>
                </div>
              </div>
            ) : tradeEnded ? (
              <div className="text-center space-y-6">
                <h3 className="text-2xl font-bold text-white">Enter Your Exit Value</h3>
                <p className="text-zinc-400">How much did you actually exit with?</p>
                <div className="max-w-xs mx-auto">
                  <Label className="text-zinc-300">Actual Exit Value (USD)</Label>
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
                  <p className="text-2xl font-mono font-bold text-blue-400">${formatNumber(exitValue)}</p>
                </div>
                <Button onClick={submitActualProfit} className="btn-primary py-4 px-8" data-testid="submit-actual-button">
                  Submit & See Results
                </Button>
              </div>
            ) : isTrading && countdown ? (
              <div className="text-center space-y-6">
                <p className="text-zinc-400">Time until trade:</p>
                <div className="flex justify-center gap-4">
                  {['hours', 'minutes', 'seconds'].map((unit) => (
                    <div key={unit} className="glass-card p-4 min-w-[100px]">
                      <p className="text-4xl font-mono font-bold text-white">
                        {String(countdown[unit]).padStart(2, '0')}
                      </p>
                      <p className="text-xs text-zinc-500 uppercase">{unit}</p>
                    </div>
                  ))}
                </div>
                <div className="text-zinc-400">
                  Target Exit: <span className="text-2xl font-mono font-bold text-emerald-400">${formatNumber(exitValue)}</span>
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
                  <Play className="w-8 h-8 mr-3" /> Check In
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* LOT Calculator */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Calculator className="w-5 h-5" /> LOT Calculator
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-zinc-300">Your LOT Size</Label>
              <Input
                type="number"
                step="0.01"
                value={lotSize}
                onChange={(e) => setLotSize(parseFloat(e.target.value) || 0)}
                className="input-dark mt-1 text-xl font-mono"
                data-testid="lot-size-input"
              />
            </div>
            <div className="p-6 rounded-xl bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 text-center">
              <p className="text-sm text-zinc-400 mb-2">Exit Value (LOT × 15)</p>
              <p className="text-5xl font-mono font-bold text-gradient" data-testid="exit-value-display">
                ${formatNumber(exitValue)}
              </p>
            </div>
            <p className="text-xs text-zinc-500 text-center">Formula: LOT Size × 15 = Exit Value</p>
          </CardContent>
        </Card>
      </div>

      {/* World Timer & Today's Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* World Timer - Shows only user's timezone */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5" /> Your Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                {user?.timezone || 'UTC'}
              </p>
              <p className="text-6xl font-mono font-bold text-white tracking-wider">
                {formatTimeForTimezone(worldTime, user?.timezone || 'UTC')}
              </p>
              <p className="text-sm text-zinc-500 mt-4">
                Set your timezone in Profile Settings
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Today's Summary */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white">Today's Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Trades Today</p>
                <p className="text-3xl font-mono font-bold text-white">{dailySummary?.trades_count || 0}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Projected Total</p>
                <p className="text-3xl font-mono font-bold text-blue-400">${formatNumber(dailySummary?.total_projected || 0)}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Actual Total</p>
                <p className="text-3xl font-mono font-bold text-emerald-400">${formatNumber(dailySummary?.total_actual || 0)}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Difference</p>
                <p className={`text-3xl font-mono font-bold ${(dailySummary?.difference || 0) >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {(dailySummary?.difference || 0) >= 0 ? '+' : ''}${formatNumber(dailySummary?.difference || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Celebration/Result Card */}
      {showCelebration && lastTrade && (
        <Card className={`glass-card ${lastTrade.performance === 'exceeded' ? 'border-emerald-500/30 neon-success' : lastTrade.performance === 'perfect' ? 'border-blue-500/30 neon-glow' : 'border-amber-500/30 neon-warning'}`}>
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                {lastTrade.performance === 'exceeded' && <Trophy className="w-16 h-16 text-emerald-400 animate-bounce" />}
                {lastTrade.performance === 'perfect' && <Target className="w-16 h-16 text-blue-400" />}
                {lastTrade.performance === 'below' && <TrendingDown className="w-16 h-16 text-amber-400" />}
                <div>
                  <p className="text-3xl font-bold text-white">{celebrationMessage}</p>
                  <p className="text-zinc-400 mt-1">
                    Projected: ${formatNumber(lastTrade.projected_profit)} | Actual: ${formatNumber(lastTrade.actual_profit)}
                  </p>
                </div>
              </div>
              <div className="text-center md:text-right">
                <p className={`text-5xl font-mono font-bold ${lastTrade.profit_difference >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {lastTrade.profit_difference >= 0 ? '+' : ''}${formatNumber(lastTrade.profit_difference)}
                </p>
                <p className="text-sm text-zinc-500 mt-1">Difference</p>
              </div>
            </div>
            
            {/* Forward to Profit Tracker Button */}
            <div className="mt-6 pt-6 border-t border-zinc-800 flex justify-center">
              <Button
                onClick={() => forwardToProfit(lastTrade.id)}
                className="btn-primary gap-2"
                data-testid="forward-to-profit-button"
              >
                <Send className="w-4 h-4" /> Forward to Profit Tracker
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
