import React, { useState, useEffect, useRef, useCallback } from 'react';
import { tradeAPI, profitAPI } from '@/lib/api';
import { formatNumber, calculateExitValue, getPerformanceMessage } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Play, Square, Calculator, Clock, Globe, AlertTriangle, Trophy, Target, TrendingUp, TrendingDown, Volume2, VolumeX } from 'lucide-react';

export const TradeMonitorPage = () => {
  const { user } = useAuth();
  const [signal, setSignal] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [isTrading, setIsTrading] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [showExitAlert, setShowExitAlert] = useState(false);
  const [lotSize, setLotSize] = useState(user?.lot_size || 0.01);
  const [exitValue, setExitValue] = useState(0);
  const [worldTime, setWorldTime] = useState(new Date());
  const [selectedTimezone, setSelectedTimezone] = useState(user?.timezone || 'UTC');
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [logDialogOpen, setLogDialogOpen] = useState(false);
  const [newTrade, setNewTrade] = useState({ lot_size: lotSize, direction: 'BUY', actual_profit: '', notes: '' });
  const [lastPerformance, setLastPerformance] = useState(null);

  const audioRef = useRef(null);
  const countdownRef = useRef(null);

  // Load data
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // World clock
  useEffect(() => {
    const timer = setInterval(() => setWorldTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Calculate exit value when lot size changes
  useEffect(() => {
    setExitValue(calculateExitValue(lotSize));
    setNewTrade(prev => ({ ...prev, lot_size: lotSize }));
  }, [lotSize]);

  const loadData = async () => {
    try {
      const [signalRes, summaryRes] = await Promise.all([
        tradeAPI.getActiveSignal(),
        tradeAPI.getDailySummary(),
      ]);
      setSignal(signalRes.data.signal);
      setDailySummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to load trade data:', error);
    }
  };

  const formatTimeForTimezone = (date, timezone) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: timezone,
    });
  };

  const startTrade = useCallback(() => {
    if (!signal) {
      toast.error('No active trading signal!');
      return;
    }

    setIsTrading(true);
    setShowExitAlert(false);

    // Parse trade time
    const [hours, minutes] = signal.trade_time.split(':').map(Number);
    const now = new Date();
    const tradeTime = new Date();
    tradeTime.setUTCHours(hours, minutes, 0, 0);

    // If trade time has passed, set for tomorrow
    if (tradeTime <= now) {
      tradeTime.setDate(tradeTime.getDate() + 1);
    }

    // Start countdown
    countdownRef.current = setInterval(() => {
      const now = new Date();
      const diff = tradeTime - now;

      if (diff <= 0) {
        // Trade time reached - show exit alert!
        clearInterval(countdownRef.current);
        setShowExitAlert(true);
        setCountdown(null);
        
        // Play alarm sound
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

  const stopTrade = () => {
    setIsTrading(false);
    setShowExitAlert(false);
    setCountdown(null);
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

  const handleLogTrade = async () => {
    if (!newTrade.actual_profit) {
      toast.error('Please enter your actual profit');
      return;
    }

    try {
      const response = await tradeAPI.logTrade({
        lot_size: parseFloat(newTrade.lot_size),
        direction: signal?.direction || newTrade.direction,
        actual_profit: parseFloat(newTrade.actual_profit),
        notes: newTrade.notes,
      });

      const result = response.data;
      setLastPerformance(result);

      // Show celebration/encouragement based on performance
      const message = getPerformanceMessage(result.performance);
      if (result.performance === 'exceeded') {
        toast.success(message, { duration: 5000 });
      } else if (result.performance === 'perfect') {
        toast.success(message, { duration: 5000 });
      } else {
        toast.info(message, { duration: 5000 });
      }

      setLogDialogOpen(false);
      setNewTrade({ lot_size: lotSize, direction: 'BUY', actual_profit: '', notes: '' });
      stopTrade();
      loadData();
    } catch (error) {
      toast.error('Failed to log trade');
    }
  };

  const timezones = [
    { value: 'UTC', label: 'UTC' },
    { value: 'America/New_York', label: 'New York' },
    { value: 'Europe/London', label: 'London' },
    { value: 'Asia/Tokyo', label: 'Tokyo' },
    { value: 'Asia/Singapore', label: 'Singapore' },
    { value: 'Asia/Manila', label: 'Manila' },
    { value: 'Australia/Sydney', label: 'Sydney' },
  ];

  return (
    <div className="space-y-6">
      {/* Audio element for alarm */}
      <audio ref={audioRef} loop>
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg" />
      </audio>

      {/* Active Signal Banner */}
      {signal ? (
        <div className={`glass-highlight p-6 ${showExitAlert ? 'exit-alert-pulse border-emerald-400' : ''}`}>
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
                <p className="text-xs text-zinc-400 uppercase tracking-wider">Trade Time (UTC)</p>
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
        {/* Exit Alert Section */}
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
                <p className="text-xl text-zinc-300">Trade time reached. Exit at ${formatNumber(exitValue)}</p>
                <div className="flex gap-4 justify-center">
                  <Dialog open={logDialogOpen} onOpenChange={setLogDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="btn-primary text-xl py-6 px-8" data-testid="log-trade-button">
                        <Trophy className="w-6 h-6 mr-2" /> Log Trade
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="glass-card border-zinc-800">
                      <DialogHeader>
                        <DialogTitle className="text-white">Log Your Trade</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4 mt-4">
                        <div className="p-4 rounded-lg bg-zinc-900/50">
                          <p className="text-sm text-zinc-400">Projected Exit Value</p>
                          <p className="text-3xl font-bold font-mono text-blue-400">${formatNumber(exitValue)}</p>
                        </div>
                        <div>
                          <Label className="text-zinc-300">Actual Profit ($)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={newTrade.actual_profit}
                            onChange={(e) => setNewTrade({ ...newTrade, actual_profit: e.target.value })}
                            placeholder="Enter your actual profit"
                            className="input-dark mt-1"
                            data-testid="actual-profit-input"
                          />
                        </div>
                        <div>
                          <Label className="text-zinc-300">Notes (optional)</Label>
                          <Input
                            value={newTrade.notes}
                            onChange={(e) => setNewTrade({ ...newTrade, notes: e.target.value })}
                            placeholder="Add notes..."
                            className="input-dark mt-1"
                          />
                        </div>
                        <Button onClick={handleLogTrade} className="w-full btn-primary" data-testid="confirm-log-trade">
                          Confirm Trade
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                  <Button onClick={stopTrade} variant="outline" className="btn-secondary" data-testid="stop-trade-button">
                    <Square className="w-5 h-5 mr-2" /> Stop
                  </Button>
                </div>
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
                  Exit at: <span className="text-2xl font-mono font-bold text-emerald-400">${formatNumber(exitValue)}</span>
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
                  className="exit-button idle py-8 text-2xl"
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

      {/* World Timer & Daily Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* World Timer */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Globe className="w-5 h-5" /> World Timer
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {timezones.slice(0, 6).map((tz) => (
                <div
                  key={tz.value}
                  className={`p-4 rounded-lg transition-all cursor-pointer ${selectedTimezone === tz.value ? 'bg-blue-500/20 border border-blue-500/30' : 'bg-zinc-900/50 hover:bg-zinc-800/50'}`}
                  onClick={() => setSelectedTimezone(tz.value)}
                >
                  <p className="text-xs text-zinc-500">{tz.label}</p>
                  <p className="text-2xl font-mono font-bold text-white">
                    {formatTimeForTimezone(worldTime, tz.value)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Daily Summary */}
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
                <p className="text-sm text-zinc-400">Projected</p>
                <p className="text-3xl font-mono font-bold text-blue-400">${formatNumber(dailySummary?.total_projected || 0)}</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Actual</p>
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

      {/* Last Performance Celebration */}
      {lastPerformance && (
        <Card className={`glass-card ${lastPerformance.performance === 'exceeded' ? 'border-emerald-500/30 neon-success' : lastPerformance.performance === 'perfect' ? 'border-blue-500/30 neon-glow' : 'border-amber-500/30 neon-warning'}`}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {lastPerformance.performance === 'exceeded' && <Trophy className="w-12 h-12 text-emerald-400" />}
                {lastPerformance.performance === 'perfect' && <Target className="w-12 h-12 text-blue-400" />}
                {lastPerformance.performance === 'below' && <TrendingDown className="w-12 h-12 text-amber-400" />}
                <div>
                  <p className="text-2xl font-bold text-white">{getPerformanceMessage(lastPerformance.performance)}</p>
                  <p className="text-zinc-400">
                    Projected: ${formatNumber(lastPerformance.projected_profit)} | Actual: ${formatNumber(lastPerformance.actual_profit)}
                  </p>
                </div>
              </div>
              <div className={`text-4xl font-mono font-bold ${lastPerformance.profit_difference >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {lastPerformance.profit_difference >= 0 ? '+' : ''}${formatNumber(lastPerformance.profit_difference)}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
