import React, { useState, useEffect, useRef, useCallback } from 'react';
import { tradeAPI, profitAPI } from '@/lib/api';
import { formatNumber, calculateExitValue, getPerformanceMessage } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { useTradeCountdown } from '@/contexts/TradeCountdownContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { MobileNotice } from '@/components/MobileNotice';
import { 
  Play, Square, Calculator, Clock, AlertTriangle, Trophy, Target, 
  TrendingUp, TrendingDown, Volume2, VolumeX, ArrowRight, Send,
  Sparkles, ExternalLink, Rocket, Radio, FlaskConical, Flame,
  ChevronLeft, ChevronRight, Edit2, Check, X, Calendar, Eye, RefreshCw
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

// Convert time from one timezone to another
const convertTimeToTimezone = (timeStr, fromTz, toTz) => {
  if (!timeStr) return '';
  
  try {
    const [hours, minutes] = timeStr.split(':').map(Number);
    
    // Create a date object for today
    const now = new Date();
    
    // Create a date string with the time in the source timezone
    const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}T${timeStr}:00`;
    
    // Parse as if it's in the source timezone
    const sourceDate = new Date(dateStr);
    
    // Get the time difference between source and target timezones
    const sourceOffset = getTimezoneOffset(fromTz);
    const targetOffset = getTimezoneOffset(toTz);
    const diffHours = targetOffset - sourceOffset;
    
    // Adjust the time
    let newHours = hours + diffHours;
    let newMinutes = minutes;
    let dayShift = '';
    
    if (newHours >= 24) {
      newHours -= 24;
      dayShift = ' (+1 day)';
    } else if (newHours < 0) {
      newHours += 24;
      dayShift = ' (-1 day)';
    }
    
    // Format in 12-hour format
    const period = newHours >= 12 ? 'PM' : 'AM';
    const displayHours = newHours % 12 || 12;
    
    return `${displayHours}:${String(newMinutes).padStart(2, '0')} ${period}${dayShift}`;
  } catch (e) {
    return timeStr;
  }
};

// Get timezone offset in hours
const getTimezoneOffset = (tz) => {
  const offsets = {
    'Asia/Manila': 8,
    'Asia/Singapore': 8,
    'Asia/Taipei': 8,
    'America/New_York': -5,
    'America/Chicago': -6,
    'America/Denver': -7,
    'America/Los_Angeles': -8,
    'Europe/London': 0,
    'Europe/Paris': 1,
    'Europe/Berlin': 1,
    'Australia/Sydney': 11,
    'Asia/Tokyo': 9,
    'Asia/Shanghai': 8,
    'UTC': 0,
  };
  
  // Try to get from browser if not in list
  if (!offsets[tz]) {
    try {
      const date = new Date();
      const utcDate = new Date(date.toLocaleString('en-US', { timeZone: 'UTC' }));
      const tzDate = new Date(date.toLocaleString('en-US', { timeZone: tz }));
      return Math.round((tzDate - utcDate) / (1000 * 60 * 60));
    } catch {
      return 0;
    }
  }
  
  return offsets[tz];
};

// Get user's local timezone
const getUserTimezone = () => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

export const TradeMonitorPage = () => {
  const { user, simulatedView, getSimulatedAccountValue, getSimulatedLotSize, getSimulatedMemberName } = useAuth();
  const { startCountdown: startGlobalCountdown, stopCountdown: stopGlobalCountdown } = useTradeCountdown();
  
  // Check if user is a licensee - redirect them away
  const isLicensee = simulatedView?.license_type || user?.license_type;
  
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
  const [showDreamProfit, setShowDreamProfit] = useState(false);
  const [dreamDailyProfit, setDreamDailyProfit] = useState('');
  const [preTradeCountdown, setPreTradeCountdown] = useState(null);
  const [checkInRestored, setCheckInRestored] = useState(false);
  
  // Trade History state
  const [tradeHistory, setTradeHistory] = useState([]);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyTotalPages, setHistoryTotalPages] = useState(1);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [streak, setStreak] = useState({ streak: 0, streak_type: null });
  const [editingTimeId, setEditingTimeId] = useState(null);
  const [editTimeValue, setEditTimeValue] = useState('');

  const audioRef = useRef(null);
  const beepRef = useRef(null);
  const countdownRef = useRef(null);

  // Get LOT size - use simulated value if in simulation mode, otherwise from profit tracker
  const simulatedAccountValue = getSimulatedAccountValue();
  const simulatedLotSize = getSimulatedLotSize();
  const simulatedMemberName = getSimulatedMemberName();
  
  const accountValue = simulatedAccountValue !== null 
    ? simulatedAccountValue 
    : (profitSummary?.account_value || 0);
  const lotSize = simulatedLotSize !== null 
    ? truncateTo2Decimals(simulatedLotSize) 
    : truncateTo2Decimals(accountValue / 980);
  
  const userTimezone = user?.timezone || getUserTimezone();
  const isPhilippines = userTimezone === 'Asia/Manila';
  const profitMultiplier = signal?.profit_points || 15;

  // Get current trading date
  const getTradingDate = () => {
    const now = new Date();
    return now.toLocaleDateString('en-US', { 
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone: 'Asia/Manila'
    });
  };

  // Calculate time until trade and whether trading window is open (20 min before trade time)
  const getTradeWindowInfo = useCallback(() => {
    if (!signal?.trade_time) return { canTrade: false, minutesUntilOpen: null, isTradeTime: false };
    
    const [hours, minutes] = signal.trade_time.split(':').map(Number);
    const signalTz = signal.trade_timezone || 'Asia/Manila';
    
    const now = new Date();
    const tradeTime = new Date();
    
    // Convert signal time to UTC for comparison
    const tzOffset = getTimezoneOffset(signalTz);
    tradeTime.setUTCHours(hours - tzOffset, minutes, 0, 0);
    
    // If trade time has passed for today, check if within 30 min post-trade window
    if (tradeTime <= now) {
      const timeSinceTrade = now - tradeTime;
      const thirtyMinutesMs = 30 * 60 * 1000;
      if (timeSinceTrade <= thirtyMinutesMs) {
        return { canTrade: true, minutesUntilOpen: 0, isTradeTime: true, isPostTrade: true };
      }
      // Trade window closed for today
      tradeTime.setDate(tradeTime.getDate() + 1);
    }
    
    const timeUntilTrade = tradeTime - now;
    const twentyMinutesMs = 20 * 60 * 1000;
    const minutesUntilOpen = Math.ceil((timeUntilTrade - twentyMinutesMs) / (60 * 1000));
    
    return {
      canTrade: timeUntilTrade <= twentyMinutesMs,
      minutesUntilOpen: minutesUntilOpen > 0 ? minutesUntilOpen : 0,
      isTradeTime: timeUntilTrade <= 0,
      timeUntilTrade
    };
  }, [signal]);

  // Update trade window info every second
  const [tradeWindowInfo, setTradeWindowInfo] = useState({ canTrade: false, minutesUntilOpen: null });
  
  useEffect(() => {
    const updateTradeWindow = () => setTradeWindowInfo(getTradeWindowInfo());
    updateTradeWindow();
    const interval = setInterval(updateTradeWindow, 1000);
    return () => clearInterval(interval);
  }, [getTradeWindowInfo]);

  // Data loading functions
  const loadData = async () => {
    try {
      const [signalRes, summaryRes, profitRes, streakRes] = await Promise.all([
        tradeAPI.getActiveSignal(),
        tradeAPI.getDailySummary(),
        profitAPI.getSummary(),
        tradeAPI.getStreak(),
      ]);
      setSignal(signalRes.data.signal);
      setDailySummary(summaryRes.data);
      setProfitSummary(profitRes.data);
      setStreak(streakRes.data);
    } catch (error) {
      console.error('Failed to load trade data:', error);
    }
  };

  const loadTradeHistory = async () => {
    try {
      const res = await tradeAPI.getHistory(historyPage, 10);
      setTradeHistory(res.data.trades);
      setHistoryTotalPages(res.data.total_pages);
      setHistoryTotal(res.data.total);
    } catch (error) {
      console.error('Failed to load trade history:', error);
    }
  };

  // Load data
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load trade history when page changes
  useEffect(() => {
    loadTradeHistory();
  }, [historyPage]);

  // Restore check-in state from localStorage on mount
  useEffect(() => {
    const savedCheckIn = localStorage.getItem('trade_check_in');
    if (savedCheckIn && !checkInRestored) {
      try {
        const checkInData = JSON.parse(savedCheckIn);
        const targetTime = new Date(checkInData.targetTime);
        const now = new Date();
        
        // Check if the saved check-in is still valid (not expired - within 30 min after trade time)
        const thirtyMinAfterTrade = new Date(targetTime.getTime() + 30 * 60 * 1000);
        
        if (now < thirtyMinAfterTrade && checkInData.signalId) {
          // Restore the check-in state and resume countdown
          setIsTrading(true);
          setCheckInRestored(true);
          
          // Start the countdown from saved target time
          startGlobalCountdown(targetTime, checkInData.signalInfo);
          
          // Resume countdown interval
          countdownRef.current = setInterval(() => {
            const currentNow = new Date();
            const diff = targetTime - currentNow;

            if (diff <= 0) {
              // Trade time reached
              setShowExitAlert(true);
              setTradeEnded(true);
              setCountdown(null);
              if (countdownRef.current) clearInterval(countdownRef.current);
              if (soundEnabled && audioRef.current) {
                audioRef.current.play().catch(() => {});
              }
            } else {
              const hours = Math.floor(diff / (1000 * 60 * 60));
              const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
              const seconds = Math.floor((diff % (1000 * 60)) / 1000);
              setCountdown({ hours, minutes, seconds, total: diff });
              
              // Beep in last 5 seconds
              if (diff <= 5000 && diff > 0) {
                if (soundEnabled && beepRef.current) {
                  beepRef.current.play().catch(() => {});
                }
              }
            }
          }, 1000);
        } else {
          // Expired check-in, clear it
          localStorage.removeItem('trade_check_in');
        }
      } catch (e) {
        localStorage.removeItem('trade_check_in');
      }
    }
  }, [signal, checkInRestored, soundEnabled, startGlobalCountdown]);

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
    };
  }, []);

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

    // Save check-in state to localStorage for persistence
    localStorage.setItem('trade_check_in', JSON.stringify({
      targetTime: tradeTime.toISOString(),
      signalId: signal.id,
      signalInfo: { product: signal.product, direction: signal.direction },
      checkedInAt: now.toISOString()
    }));

    // Start global countdown for floating popup when navigating away
    startGlobalCountdown(tradeTime, { product: signal.product, direction: signal.direction });

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
    stopGlobalCountdown(); // Stop global countdown when trade is stopped
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
      
      // Stop global countdown
      stopGlobalCountdown();

      // Show celebration popup based on performance
      const message = getPerformanceMessage(result.performance);
      setCelebrationMessage(message);
      setShowCelebration(true);

      setActualExitValue('');
      loadData();
      loadTradeHistory();
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
      // Redirect to profit tracker after a brief delay
      setTimeout(() => {
        window.location.href = '/profit-tracker';
      }, 500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to forward trade');
    }
  };

  const handleEditTimeEntered = (tradeId, currentTime) => {
    setEditingTimeId(tradeId);
    setEditTimeValue(currentTime || '');
  };

  const handleSaveTimeEntered = async (tradeId) => {
    try {
      await tradeAPI.updateTimeEntered(tradeId, editTimeValue);
      toast.success('Time updated');
      setEditingTimeId(null);
      loadTradeHistory();
    } catch (error) {
      toast.error('Failed to update time');
    }
  };

  const handleCancelEditTime = () => {
    setEditingTimeId(null);
    setEditTimeValue('');
  };

  // Performance message for today's summary
  const getDailyPerformanceMessage = () => {
    const diff = dailySummary?.difference || 0;
    if (diff > 0) return "🎉 Great job! You're exceeding targets today!";
    if (diff === 0) return "✨ Perfect execution! Right on target!";
    return "💪 Keep pushing! Every trade is a learning opportunity.";
  };

  // Get user local time from signal time
  const getUserLocalTradeTime = () => {
    if (!signal) return '';
    const signalTz = signal.trade_timezone || 'Asia/Manila';
    return convertTimeToTimezone(signal.trade_time, signalTz, userTimezone);
  };

  // Restrict licensees from accessing Trade Monitor
  if (isLicensee) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="w-16 h-16 text-amber-500/60 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">Access Restricted</h2>
        <p className="text-zinc-500 max-w-md">
          Trade Monitor is not available for licensed accounts.
          Please use the Deposit/Withdrawal page to manage your account.
        </p>
      </div>
    );
  }

  return (
    <MobileNotice featureName="Trade Monitor" showOnMobile={true}>
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Left Panel - Trade Monitor Controls */}
      <div className="flex-1 space-y-6 lg:overflow-y-auto lg:pr-4">
        {/* Simulation Banner */}
        {simulatedView && simulatedMemberName && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30" data-testid="simulation-banner">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Eye className="w-5 h-5 text-amber-400" />
                <div>
                  <p className="text-amber-400 font-medium">Simulating: {simulatedMemberName}</p>
                  <p className="text-xs text-amber-400/70">Account Value: ${formatLargeNumber(accountValue)} • LOT Size: {lotSize.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Audio elements */}
        <audio ref={audioRef} loop>
          <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg" />
        </audio>
        <audio ref={beepRef}>
          <source src="https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3" type="audio/mpeg" />
        </audio>

        {/* Active Signal Card - Redesigned like AdminSignalsPage */}
        {signal ? (
          <Card className={`glass-highlight ${signal.is_simulated ? 'border-amber-500/30' : 'border-blue-500/30'}`} data-testid="active-signal-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-white flex items-center gap-2">
                <Radio className="w-5 h-5 text-blue-400 animate-pulse" /> 
                Active Signal
                {signal.is_simulated && (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded-full flex items-center gap-1">
                    <FlaskConical className="w-3 h-3" /> SIMULATED
                  </span>
                )}
              </CardTitle>
              <p className="text-sm text-zinc-400 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {getTradingDate()}
              </p>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                <div className="flex flex-wrap items-center gap-6">
                  <div>
                    <p className="text-xs text-zinc-400">Product</p>
                    <p className="text-2xl font-bold text-white">{signal.product}</p>
                  </div>
                  <div className={`px-6 py-3 rounded-xl text-xl font-bold ${signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                    {signal.direction === 'BUY' ? <TrendingUp className="inline w-5 h-5 mr-2" /> : <TrendingDown className="inline w-5 h-5 mr-2" />}
                    {signal.direction}
                  </div>
                  <div>
                    <p className="text-xs text-zinc-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Trade Time ({signal.trade_timezone || 'Asia/Manila'})
                    </p>
                    <p className="text-2xl font-mono font-bold text-blue-400">{signal.trade_time}</p>
                  </div>
                  {!isPhilippines && (
                    <div>
                      <p className="text-xs text-zinc-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Your Time ({userTimezone.split('/').pop()})
                      </p>
                      <p className="text-xl font-mono font-bold text-cyan-400">{getUserLocalTradeTime()}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-zinc-400 flex items-center gap-1">
                      <Target className="w-3 h-3" /> Profit Multiplier
                    </p>
                    <p className="text-2xl font-mono font-bold text-purple-400">×{profitMultiplier}</p>
                  </div>
                </div>
              </div>
            {signal.notes && (
              <p className="text-zinc-400 mt-4 p-3 bg-zinc-900/50 rounded-lg">{signal.notes}</p>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card className="glass-card border-2 border-dashed border-zinc-700">
          <CardContent className="p-6">
            <div className="flex items-center gap-4 text-zinc-500">
              <AlertTriangle className="w-6 h-6" />
              <p>No active trading signal. Wait for admin to post today's signal.</p>
            </div>
          </CardContent>
        </Card>
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
                  onClick={() => setShowDreamProfit(true)}
                  className="text-purple-400 border-purple-400/30 hover:bg-purple-400/10"
                  data-testid="open-dream-profit"
                >
                  <Sparkles className="w-4 h-4 mr-1" /> Dream Profit
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
              <h2 className="text-4xl font-bold text-emerald-400 animate-pulse">ENTER YOUR TRADE NOW!</h2>
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
              {!tradeWindowInfo.canTrade && signal && (
                <div className="mb-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-center">
                  <p className="text-amber-400 text-sm mb-2">Trading window opens in:</p>
                  <p className="text-2xl font-mono font-bold text-amber-300">
                    {tradeWindowInfo.minutesUntilOpen > 60 
                      ? `${Math.floor(tradeWindowInfo.minutesUntilOpen / 60)}h ${tradeWindowInfo.minutesUntilOpen % 60}m`
                      : `${tradeWindowInfo.minutesUntilOpen} minutes`}
                  </p>
                  <p className="text-xs text-zinc-500 mt-2">You can check in 20 minutes before the scheduled trade time</p>
                </div>
              )}
              <Button
                onClick={startTrade}
                className={`exit-button idle py-8 text-2xl w-full max-w-md ${!tradeWindowInfo.canTrade ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={!signal || !tradeWindowInfo.canTrade}
                data-testid="check-in-button"
              >
                <Play className="w-8 h-8 mr-3" /> I'm Ready to Trade
              </Button>
              {!tradeWindowInfo.canTrade && signal && (
                <p className="text-xs text-zinc-500 mt-2">Button will be enabled 20 minutes before trade time</p>
              )}
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
            <div className="text-center overflow-hidden">
              {/* Primary: Philippine Time */}
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                Philippines (Asia/Manila)
              </p>
              <p className="text-4xl sm:text-5xl lg:text-6xl font-mono font-bold text-white tracking-wider truncate" data-testid="ph-time">
                {formatTimeForTimezone(worldTime, 'Asia/Manila')}
              </p>
              
              {/* Secondary: User's Local Time (smaller, underneath) */}
              {!isPhilippines && (
                <div className="mt-4 pt-4 border-t border-zinc-800">
                  <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1 truncate">
                    Your Local Time ({userTimezone.split('/').pop()})
                  </p>
                  <p className="text-xl sm:text-2xl font-mono text-zinc-400 truncate" data-testid="local-time">
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

      {/* Trade History Card */}
      <Card className="glass-card" data-testid="trade-history-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white">Trade History</CardTitle>
          {/* Streak indicator */}
          {streak.streak > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/30" data-testid="streak-indicator">
              <Flame className="w-5 h-5 text-orange-400" />
              <span className="font-bold text-orange-400">{streak.streak}</span>
              <span className="text-xs text-zinc-400">streak</span>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {tradeHistory.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Product</th>
                      <th>Direction</th>
                      <th>LOT Size</th>
                      <th>Time Set</th>
                      <th>Time Entered</th>
                      <th>Projected</th>
                      <th>Actual</th>
                      <th>P/L Diff</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tradeHistory.map((trade) => (
                      <tr key={trade.id}>
                        <td className="font-mono text-zinc-400">
                          {new Date(trade.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </td>
                        <td className="font-medium text-white">
                          {trade.signal_details?.product || 'MOIL10'}
                        </td>
                        <td>
                          <span className={`status-badge ${trade.direction === 'BUY' ? 'direction-buy' : 'direction-sell'}`}>
                            {trade.direction}
                          </span>
                        </td>
                        <td className="font-mono text-purple-400">{trade.lot_size?.toFixed(2)}</td>
                        <td className="font-mono text-zinc-400">
                          {trade.signal_details?.trade_time || '-'}
                        </td>
                        <td>
                          {editingTimeId === trade.id ? (
                            <div className="flex items-center gap-1">
                              <Input
                                type="time"
                                value={editTimeValue}
                                onChange={(e) => setEditTimeValue(e.target.value)}
                                className="input-dark w-24 h-8 text-sm"
                              />
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleSaveTimeEntered(trade.id)}
                                className="h-8 w-8 text-emerald-400 hover:text-emerald-300"
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={handleCancelEditTime}
                                className="h-8 w-8 text-red-400 hover:text-red-300"
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1">
                              <span className="font-mono text-cyan-400">
                                {trade.time_entered || '-'}
                              </span>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleEditTimeEntered(trade.id, trade.time_entered)}
                                className="h-6 w-6 text-zinc-500 hover:text-blue-400"
                                data-testid={`edit-time-${trade.id}`}
                              >
                                <Edit2 className="w-3 h-3" />
                              </Button>
                            </div>
                          )}
                        </td>
                        <td className="font-mono text-blue-400">${formatNumber(trade.projected_profit)}</td>
                        <td className="font-mono text-emerald-400">${formatNumber(trade.actual_profit)}</td>
                        <td className={`font-mono font-bold ${trade.profit_difference >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {trade.profit_difference >= 0 ? '+' : ''}${formatNumber(trade.profit_difference)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                <p className="text-sm text-zinc-500">
                  Showing {((historyPage - 1) * 10) + 1} - {Math.min(historyPage * 10, historyTotal)} of {historyTotal} trades
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setHistoryPage(p => Math.max(1, p - 1))}
                    disabled={historyPage === 1}
                    className="btn-secondary"
                    data-testid="prev-page"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-zinc-400">
                    Page {historyPage} of {historyTotalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setHistoryPage(p => Math.min(historyTotalPages, p + 1))}
                    disabled={historyPage === historyTotalPages}
                    className="btn-secondary"
                    data-testid="next-page"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No trade history yet. Start trading to see your history here!
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dream Daily Profit Calculator */}
      <Dialog open={showDreamProfit} onOpenChange={setShowDreamProfit}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-400" /> Dream Daily Profit
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-sm text-zinc-400">
              Enter your target daily profit to see how much you need to add to your account.
            </p>
            <div>
              <Label className="text-zinc-300">Target Daily Profit (USDT)</Label>
              <div className="relative mt-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">$</span>
                <Input
                  type="number"
                  step="0.01"
                  value={dreamDailyProfit}
                  onChange={(e) => setDreamDailyProfit(e.target.value)}
                  placeholder="Enter your dream daily profit"
                  className="input-dark pl-7 text-xl font-mono"
                  data-testid="dream-profit-input"
                />
              </div>
            </div>
            
            {dreamDailyProfit && parseFloat(dreamDailyProfit) > 0 && (
              <>
                <div className="p-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20">
                  <p className="text-sm text-zinc-400 mb-2">Required Account Balance</p>
                  <p className="text-4xl font-mono font-bold text-purple-400" data-testid="required-balance">
                    {formatLargeNumber((parseFloat(dreamDailyProfit) * 980) / 15)}
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">Formula: (Target ÷ 15) × 980</p>
                </div>
                
                <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20">
                  <p className="text-sm text-zinc-400 mb-2">Amount You Need to Add</p>
                  <p className={`text-4xl font-mono font-bold ${Math.max(0, ((parseFloat(dreamDailyProfit) * 980) / 15) - accountValue) > 0 ? 'text-emerald-400' : 'text-blue-400'}`} data-testid="amount-to-add">
                    {Math.max(0, ((parseFloat(dreamDailyProfit) * 980) / 15) - accountValue) > 0 
                      ? `+${formatLargeNumber(Math.max(0, ((parseFloat(dreamDailyProfit) * 980) / 15) - accountValue))}`
                      : 'You already have enough!'}
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">Current Balance: {formatLargeNumber(accountValue)}</p>
                </div>
              </>
            )}
            
            <div className="p-3 rounded-lg bg-zinc-900/50 text-sm text-zinc-400">
              <p>• Current Balance: <span className="text-white font-mono">{formatLargeNumber(accountValue)}</span></p>
              <p>• Current Daily Profit: <span className="text-emerald-400 font-mono">{formatLargeNumber(exitValue)}</span></p>
              <p>• Formula: Balance ÷ 980 × 15 = Daily Profit</p>
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

            <div className="flex flex-col gap-2">
              <Button
                onClick={() => forwardToProfit(lastTrade?.id)}
                className="btn-primary gap-2 w-full"
                data-testid="forward-to-profit-button"
              >
                <Send className="w-4 h-4" /> Forward to Profit Tracker
                <ArrowRight className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowCelebration(false);
                  window.location.href = '/profit-tracker';
                }}
                className="gap-2 w-full text-blue-400 border-blue-400/30 hover:bg-blue-400/10"
                data-testid="view-daily-projection-button"
              >
                <Eye className="w-4 h-4" /> View Daily Projection
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      </div>

      {/* Right Panel - Merin Trading Platform */}
      <div className="lg:w-[400px] xl:w-[450px] flex-shrink-0" data-testid="merin-panel">
        <Card className="glass-card h-full sticky top-0">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  <ExternalLink className="w-5 h-5 text-blue-400" />
                  Merin Trading Platform
                </CardTitle>
                <p className="text-xs text-zinc-500">Trade directly from here</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  const iframe = document.querySelector('[data-testid="merin-iframe"]');
                  if (iframe) iframe.src = iframe.src;
                }}
                className="text-zinc-400 hover:text-blue-400"
                data-testid="merin-refresh-button"
              >
                <RefreshCw className="w-5 h-5" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="relative w-full bg-zinc-900 rounded-b-xl overflow-hidden" style={{ aspectRatio: '9/16', maxHeight: 'calc(100vh - 200px)' }}>
              <iframe
                src="https://www.meringlobaltrading.com/"
                title="Merin Trading Platform"
                className="absolute inset-0 w-full h-full border-0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                data-testid="merin-iframe"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
    </MobileNotice>
  );
};
