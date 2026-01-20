import React, { useState, useEffect, useRef, useCallback } from 'react';
import { tradeAPI, profitAPI } from '@/lib/api';
import api from '@/lib/api';
import { formatNumber, calculateExitValue, getPerformanceMessage } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { useTradeCountdown } from '@/contexts/TradeCountdownContext';
import { useBVE } from '@/contexts/BVEContext';
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
  ChevronLeft, ChevronRight, Edit2, Check, X, Calendar, Eye, RefreshCw,
  RotateCcw, MessageSquare, Loader2
} from 'lucide-react';

// Truncate to 2 decimal places without rounding
const truncateTo2Decimals = (num) => {
  return Math.trunc(num * 100) / 100;
};

// Format large numbers with K, M, B abbreviations
const formatLargeNumber = (amount) => {
  if (amount === null || amount === undefined) return '$0';
  
  const absAmount = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  
  if (absAmount >= 1e12) return `${sign}$${(absAmount / 1e12).toFixed(2)}T`;
  if (absAmount >= 1e9) return `${sign}$${(absAmount / 1e9).toFixed(2)}B`;
  if (absAmount >= 1e6) return `${sign}$${(absAmount / 1e6).toFixed(2)}M`;
  if (absAmount >= 1e3) return `${sign}$${(absAmount / 1e3).toFixed(2)}K`;
  return `${sign}$${absAmount.toFixed(2)}`;
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
  const { isInBVE } = useBVE();
  
  // Check if user is a licensee - redirect them away
  const isLicensee = simulatedView?.license_type || user?.license_type;
  
  const [signal, setSignal] = useState(null);
  const [dailySummary, setDailySummary] = useState(null);
  const [profitSummary, setProfitSummary] = useState(null);
  const [isTrading, setIsTrading] = useState(false);
  const [tradeEnded, setTradeEnded] = useState(false);
  const [tradeEntered, setTradeEntered] = useState(false); // New: Track if user has entered the trade
  const [countdown, setCountdown] = useState(null);
  const [showExitAlert, setShowExitAlert] = useState(false);
  const [exitValue, setExitValue] = useState(0);
  const [worldTime, setWorldTime] = useState(new Date());
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [actualExitValue, setActualExitValue] = useState('');
  const [commissionValue, setCommissionValue] = useState(''); // Commission input
  const [lastTrade, setLastTrade] = useState(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationMessage, setCelebrationMessage] = useState('');
  const [showDreamProfit, setShowDreamProfit] = useState(false);
  const [dreamDailyProfit, setDreamDailyProfit] = useState('');
  const [preTradeCountdown, setPreTradeCountdown] = useState(null);
  const [checkInRestored, setCheckInRestored] = useState(false);
  
  // Missed Trade Popup state
  const [showMissedTradePopup, setShowMissedTradePopup] = useState(false);
  const [missedTradeChecked, setMissedTradeChecked] = useState(false);
  
  // Trade History state
  const [tradeHistory, setTradeHistory] = useState([]);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyTotalPages, setHistoryTotalPages] = useState(1);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [streak, setStreak] = useState({ streak: 0, streak_type: null });
  const [editingTimeId, setEditingTimeId] = useState(null);
  const [editTimeValue, setEditTimeValue] = useState('');
  
  // Trade action states
  const [resetTradeLoading, setResetTradeLoading] = useState(null);
  const [requestChangeLoading, setRequestChangeLoading] = useState(null);
  const [showRequestChangeDialog, setShowRequestChangeDialog] = useState(false);
  const [selectedTradeForChange, setSelectedTradeForChange] = useState(null);
  const [changeRequestReason, setChangeRequestReason] = useState('');
  
  // Countdown stall detection state
  const [countdownStalled, setCountdownStalled] = useState(false);
  const lastCountdownUpdateRef = useRef(Date.now());  const audioRef = useRef(null);
  const beepRef = useRef(null);
  const countdownRef = useRef(null);
  const tradeNotifiedRef = useRef(false); // Track if trade notification has been shown
  const tradeEnteredRef = useRef(false); // Track if user has clicked "Trade Entered"

  // Get LOT size - use simulated value if in simulation mode, otherwise from profit tracker
  const simulatedAccountValue = getSimulatedAccountValue();
  const simulatedLotSize = getSimulatedLotSize();
  const simulatedMemberName = getSimulatedMemberName();
  
  const accountValue = simulatedAccountValue !== null 
    ? simulatedAccountValue 
    : (profitSummary?.account_value || 0);
  // NOTE: lotSize here is for UI DISPLAY ONLY. 
  // When logging trades, the backend recalculates lot_size from authoritative account_value
  // to prevent stale frontend values from corrupting trade history.
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

  // Data loading functions - use useCallback to capture isInBVE correctly
  const loadData = useCallback(async () => {
    try {
      // If in BVE mode, fetch signal from BVE endpoints
      const signalEndpoint = isInBVE ? api.get('/bve/active-signal') : tradeAPI.getActiveSignal();
      const summaryEndpoint = isInBVE ? api.get('/bve/summary') : profitAPI.getSummary();
      
      const [signalRes, summaryRes, profitRes, streakRes] = await Promise.all([
        signalEndpoint,
        tradeAPI.getDailySummary(),
        summaryEndpoint,
        tradeAPI.getStreak(),
      ]);
      setSignal(signalRes.data.signal);
      setDailySummary(summaryRes.data);
      setProfitSummary(profitRes.data);
      setStreak(streakRes.data);
    } catch (error) {
      console.error('Failed to load trade data:', error);
    }
  }, [isInBVE]);

  const loadTradeHistory = useCallback(async () => {
    try {
      const res = await tradeAPI.getHistory(historyPage, 10);
      setTradeHistory(res.data.trades);
      setHistoryTotalPages(res.data.total_pages);
      setHistoryTotal(res.data.total);
    } catch (error) {
      console.error('Failed to load trade history:', error);
    }
  }, [historyPage]);

  // Load data
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]); // Reload when loadData changes (which depends on isInBVE)

  // Check for missed trade from backend - auto-show popup if needed
  useEffect(() => {
    if (isTrading || tradeEnded || tradeEntered || missedTradeChecked || showCelebration) {
      return;
    }

    const checkMissedTradeFromBackend = async () => {
      try {
        const response = await tradeAPI.getMissedTradeStatus();
        const status = response.data;
        
        // Show popup if backend says user should see it
        if (status.should_show_missed_popup && !missedTradeChecked) {
          setShowMissedTradePopup(true);
        }
      } catch (error) {
        console.error('Failed to check missed trade status:', error);
        // Fallback to local check if backend fails
        const info = getTradeWindowInfo();
        if (info.isPostTrade && dailySummary?.trades_count === 0) {
          setShowMissedTradePopup(true);
        }
      }
    };

    // Check after a short delay to allow data to load
    const timeout = setTimeout(checkMissedTradeFromBackend, 2000);
    return () => clearTimeout(timeout);
  }, [isTrading, tradeEnded, tradeEntered, missedTradeChecked, showCelebration, getTradeWindowInfo, dailySummary]);

  // Reset missed trade check when signal changes
  useEffect(() => {
    setMissedTradeChecked(false);
    setShowMissedTradePopup(false);
  }, [signal?.id]);

  // Load trade history when page changes
  useEffect(() => {
    loadTradeHistory();
  }, [loadTradeHistory]);

  // Restore trade entered state from localStorage on mount
  useEffect(() => {
    const savedTradeState = localStorage.getItem('trade_entered_state');
    if (savedTradeState) {
      try {
        const tradeState = JSON.parse(savedTradeState);
        const savedTime = new Date(tradeState.timestamp);
        const now = new Date();
        
        // Check if saved state is still valid (within 30 minutes)
        const thirtyMinutes = 30 * 60 * 1000;
        if (now - savedTime < thirtyMinutes && tradeState.signalId === signal?.id) {
          // Restore the trade entered state
          setTradeEntered(true);
          setIsTrading(true);
          tradeEnteredRef.current = true;
          tradeNotifiedRef.current = true;
          // Don't show exit alert since user already entered trade
          setShowExitAlert(false);
        } else {
          // Expired or different signal, clear it
          localStorage.removeItem('trade_entered_state');
        }
      } catch (e) {
        localStorage.removeItem('trade_entered_state');
      }
    }
  }, [signal?.id]);

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
              // Trade time reached - clear interval immediately
              if (countdownRef.current) {
                clearInterval(countdownRef.current);
                countdownRef.current = null;
              }
              // Only show exit alert if user hasn't already confirmed trade entry
              if (!tradeEnteredRef.current) {
                setShowExitAlert(true);
                setCountdown(null);
                if (soundEnabled && audioRef.current) {
                  audioRef.current.play().catch(() => {});
                }
                // Only show toast once using ref to prevent flood
                if (!tradeNotifiedRef.current) {
                  tradeNotifiedRef.current = true;
                  toast.success('🚨 ENTER THE TRADE NOW!', { duration: 10000 });
                }
              }
            } else {
              const hours = Math.floor(diff / (1000 * 60 * 60));
              const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
              const seconds = Math.floor((diff % (1000 * 60)) / 1000);
              
              // Track last update time for stall detection
              lastCountdownUpdateRef.current = Date.now();
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
    
    // Cleanup function to clear interval when component unmounts or deps change
    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
        countdownRef.current = null;
      }
    };
  }, [signal, checkInRestored, soundEnabled, startGlobalCountdown]);

  // World clock
  useEffect(() => {
    const timer = setInterval(() => setWorldTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Handle visibility change - force countdown update when tab becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && isTrading) {
        // Force immediate countdown update when tab becomes visible
        const savedCheckIn = localStorage.getItem('trade_check_in');
        if (savedCheckIn) {
          try {
            const checkInData = JSON.parse(savedCheckIn);
            const targetTime = new Date(checkInData.targetTime);
            const now = new Date();
            const diff = targetTime - now;
            
            if (diff > 0) {
              const hours = Math.floor(diff / (1000 * 60 * 60));
              const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
              const seconds = Math.floor((diff % (1000 * 60)) / 1000);
              
              lastCountdownUpdateRef.current = Date.now();
              setCountdownStalled(false);
              setCountdown({ hours, minutes, seconds, total: diff });
            } else {
              // Trade time has passed - show the "Trade Entered" button if not already clicked
              if (!tradeEnteredRef.current) {
                setShowExitAlert(true);
                setCountdown(null);
                setPreTradeCountdown(null);
                
                if (soundEnabled && audioRef.current) {
                  audioRef.current.play().catch(console.error);
                }
              }
            }
          } catch (e) {
            console.error('Error restoring countdown on visibility change:', e);
          }
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isTrading, soundEnabled]);

  // Countdown stall detection - check if countdown hasn't updated in 3 seconds
  useEffect(() => {
    if (!isTrading || !countdown) {
      setCountdownStalled(false);
      return;
    }

    const stallChecker = setInterval(() => {
      const timeSinceLastUpdate = Date.now() - lastCountdownUpdateRef.current;
      // If countdown hasn't updated in 3 seconds, mark as stalled
      if (timeSinceLastUpdate > 3000) {
        setCountdownStalled(true);
        
        // Auto-refresh countdown when stalled
        const savedCheckIn = localStorage.getItem('trade_check_in');
        if (savedCheckIn) {
          try {
            const checkInData = JSON.parse(savedCheckIn);
            const targetTime = new Date(checkInData.targetTime);
            const now = new Date();
            const diff = targetTime - now;
            
            if (diff > 0) {
              const hours = Math.floor(diff / (1000 * 60 * 60));
              const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
              const seconds = Math.floor((diff % (1000 * 60)) / 1000);
              
              lastCountdownUpdateRef.current = Date.now();
              setCountdownStalled(false);
              setCountdown({ hours, minutes, seconds, total: diff });
            } else {
              // Trade time has passed - show the "Trade Entered" button if not already clicked
              if (!tradeEnteredRef.current) {
                setShowExitAlert(true);
                setCountdown(null);
                setPreTradeCountdown(null);
                setCountdownStalled(false);
                
                if (soundEnabled && audioRef.current) {
                  audioRef.current.play().catch(console.error);
                }
              }
            }
          } catch (e) {
            // Ignore errors
          }
        }
      } else {
        setCountdownStalled(false);
      }
    }, 1000);

    return () => clearInterval(stallChecker);
  }, [isTrading, countdown, soundEnabled]);

  // Calculate exit value when lot size or multiplier changes
  // Use truncateTo2Decimals for consistency with ProfitTrackerPage
  useEffect(() => {
    setExitValue(truncateTo2Decimals(lotSize * profitMultiplier));
  }, [lotSize, profitMultiplier]);

  // Stop audio immediately when sound is disabled
  useEffect(() => {
    if (!soundEnabled) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      if (beepRef.current) {
        beepRef.current.pause();
        beepRef.current.currentTime = 0;
      }
    }
  }, [soundEnabled]);

  // Cleanup on unmount - ensure all intervals and audio are stopped
  useEffect(() => {
    const audioElement = audioRef.current;
    const beepElement = beepRef.current;
    
    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
        countdownRef.current = null;
      }
      if (audioElement) {
        audioElement.pause();
        audioElement.currentTime = 0;
      }
      if (beepElement) {
        beepElement.pause();
        beepElement.currentTime = 0;
      }
      // Dismiss any active toasts - not needed since we don't use IDs anymore
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
  const playBeep = useCallback(() => {
    if (beepRef.current && soundEnabled) {
      beepRef.current.currentTime = 0;
      beepRef.current.play().catch(console.error);
    }
  }, [soundEnabled]);

  const startTrade = useCallback(() => {
    if (!signal) {
      toast.error('No active trading signal!');
      return;
    }

    setIsTrading(true);
    setTradeEnded(false);
    setTradeEntered(false);
    setShowExitAlert(false);
    setLastTrade(null);
    setShowCelebration(false);
    setPreTradeCountdown(null);
    tradeNotifiedRef.current = false; // Reset notification ref for new trade
    tradeEnteredRef.current = false; // Reset trade entered ref for new trade

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
    const checkInData = {
      targetTime: tradeTime.toISOString(),
      signalId: signal.id,
      signalInfo: { product: signal.product, direction: signal.direction },
      checkedInAt: now.toISOString()
    };
    localStorage.setItem('trade_check_in', JSON.stringify(checkInData));

    // Start global countdown for floating popup when navigating away
    startGlobalCountdown(tradeTime, { product: signal.product, direction: signal.direction });

    // The countdown always reads from localStorage to avoid stale closures
    // This makes it resilient to browser throttling
    const updateCountdown = () => {
      // Always read target time from localStorage to avoid stale closure issues
      const savedCheckIn = localStorage.getItem('trade_check_in');
      if (!savedCheckIn) {
        // localStorage was cleared - stop the countdown
        if (countdownRef.current) {
          clearInterval(countdownRef.current);
          countdownRef.current = null;
        }
        return;
      }
      
      let targetTimeMs;
      try {
        const data = JSON.parse(savedCheckIn);
        targetTimeMs = new Date(data.targetTime).getTime();
      } catch (e) {
        console.error('Failed to parse trade_check_in:', e);
        return;
      }
      
      const nowMs = Date.now();
      const diff = targetTimeMs - nowMs;

      if (diff <= 0) {
        if (countdownRef.current) {
          clearInterval(countdownRef.current);
          countdownRef.current = null;
        }
        
        // Only show exit alert if user hasn't already confirmed trade entry
        if (!tradeEnteredRef.current) {
          setShowExitAlert(true);
          setCountdown(null);
          setPreTradeCountdown(null);
          
          if (soundEnabled && audioRef.current) {
            audioRef.current.play().catch(console.error);
          }
          
          // Only show toast once using ref to prevent flood
          if (!tradeNotifiedRef.current) {
            tradeNotifiedRef.current = true;
            toast.success('🚨 ENTER THE TRADE NOW!', { duration: 10000 });
          }
        }
      } else {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        // Show active countdown only in the last 30 seconds (user requested simplification)
        if (diff <= 30000 && diff > 0) {
          const secondsLeft = Math.ceil(diff / 1000);
          setPreTradeCountdown(secondsLeft);
          // Play beep every 5 seconds in the last 30 seconds, every second in last 5
          if (diff <= 5000) {
            playBeep();
          } else if (secondsLeft % 5 === 0) {
            playBeep();
          }
        } else {
          setPreTradeCountdown(null);
        }
        
        // Track last update time for stall detection
        lastCountdownUpdateRef.current = Date.now();
        setCountdown({ hours, minutes, seconds, total: diff });
      }
    };

    // Initial update
    updateCountdown();
    
    // Use 500ms interval for more frequent updates
    // The function reads from localStorage each time, so it's resilient to throttling
    countdownRef.current = setInterval(updateCountdown, 500);
  }, [signal, soundEnabled, startGlobalCountdown, playBeep]);

  // Restart countdown if it stalls
  const restartCountdown = useCallback(() => {
    // Clear existing interval
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    
    // Get target time from localStorage
    const savedCheckIn = localStorage.getItem('trade_check_in');
    if (!savedCheckIn) {
      // If no localStorage but we're in trading state, recreate it from signal
      if (isTrading && signal) {
        // Recreate the check-in data
        const [hours, minutes] = signal.trade_time.split(':').map(Number);
        const signalTz = signal.trade_timezone || 'Asia/Manila';
        const now = new Date();
        const tradeTime = new Date();
        const tzOffset = getTimezoneOffset(signalTz);
        tradeTime.setUTCHours(hours - tzOffset, minutes, 0, 0);
        
        if (tradeTime <= now) {
          tradeTime.setDate(tradeTime.getDate() + 1);
        }
        
        localStorage.setItem('trade_check_in', JSON.stringify({
          targetTime: tradeTime.toISOString(),
          signalId: signal.id,
          signalInfo: { product: signal.product, direction: signal.direction },
          checkedInAt: now.toISOString()
        }));
        
        toast.success('Countdown restored from signal');
      } else {
        toast.error('No active countdown to restart');
        return;
      }
    }
    
    // Reset stall state
    setCountdownStalled(false);
    lastCountdownUpdateRef.current = Date.now();
    
    // Start fresh countdown that reads from localStorage each tick
    const updateFromStorage = () => {
      const checkInStr = localStorage.getItem('trade_check_in');
      if (!checkInStr) {
        clearInterval(countdownRef.current);
        countdownRef.current = null;
        return;
      }
      
      try {
        const checkInData = JSON.parse(checkInStr);
        const targetTime = new Date(checkInData.targetTime);
        const currentNow = new Date();
        const diff = targetTime - currentNow;
        
        if (diff <= 0) {
          clearInterval(countdownRef.current);
          countdownRef.current = null;
          if (!tradeEnteredRef.current) {
            setShowExitAlert(true);
            setCountdown(null);
            setPreTradeCountdown(null);
            if (soundEnabled && audioRef.current) {
              audioRef.current.play().catch(() => {});
            }
            if (!tradeNotifiedRef.current) {
              tradeNotifiedRef.current = true;
              toast.success('🚨 ENTER THE TRADE NOW!', { duration: 10000 });
            }
          }
        } else {
          const hours = Math.floor(diff / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diff % (1000 * 60)) / 1000);
          
          // Show active countdown in last 30 seconds
          if (diff <= 30000 && diff > 0) {
            const secondsLeft = Math.ceil(diff / 1000);
            setPreTradeCountdown(secondsLeft);
            if (diff <= 5000) {
              playBeep();
            } else if (secondsLeft % 5 === 0) {
              playBeep();
            }
          } else {
            setPreTradeCountdown(null);
          }
          
          lastCountdownUpdateRef.current = Date.now();
          setCountdown({ hours, minutes, seconds, total: diff });
        }
      } catch (e) {
        console.error('Failed to parse check-in data:', e);
      }
    };
    
    // Run immediately
    updateFromStorage();
    
    // Then every 500ms
    countdownRef.current = setInterval(updateFromStorage, 500);
    
    toast.success('Countdown restarted');
  }, [soundEnabled, playBeep, isTrading, signal]);

  // User clicked "Trade Entered" - they have entered the trade, stop alarm
  const confirmTradeEntered = () => {
    // Set ref FIRST to prevent any interval from re-triggering
    tradeEnteredRef.current = true;
    
    // Clear the interval to prevent state reset
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    
    setTradeEntered(true);
    setShowExitAlert(false);
    
    // Persist trade entered state to localStorage for refresh resilience
    const tradeState = {
      tradeEntered: true,
      signalId: signal?.id,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem('trade_entered_state', JSON.stringify(tradeState));
    
    // Stop all audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (beepRef.current) {
      beepRef.current.pause();
      beepRef.current.currentTime = 0;
    }
    
    // Clear localStorage check-in since user has confirmed entry
    // But keep isTrading true so they can proceed to exit
  };

  // User clicked "Exit Trade" - they have exited and need to enter actual profit
  const confirmTradeExited = () => {
    // Keep tradeEnteredRef true to prevent alarm from re-triggering
    tradeEnteredRef.current = true;
    
    // Clear interval
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    
    // Stop any audio just in case
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (beepRef.current) {
      beepRef.current.pause();
      beepRef.current.currentTime = 0;
    }
    
    setTradeEntered(false);
    setTradeEnded(true);
  };

  const endTrade = () => {
    setShowExitAlert(false);
    setTradeEnded(true);
    setTradeEntered(false);
    tradeEnteredRef.current = false;
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
    setTradeEntered(false);
    setCountdown(null);
    setPreTradeCountdown(null);
    setLastTrade(null);
    setActualExitValue('');
    stopGlobalCountdown(); // Stop global countdown when trade is stopped
    localStorage.removeItem('trade_check_in'); // Clear persisted check-in state
    localStorage.removeItem('trade_entered_state'); // Clear persisted trade entered state
    tradeNotifiedRef.current = false; // Reset notification ref
    tradeEnteredRef.current = false; // Reset trade entered ref
    // Clear the interval ref completely
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (beepRef.current) {
      beepRef.current.pause();
      beepRef.current.currentTime = 0;
    }
    // No need to dismiss toasts since we don't use IDs
  };

  const submitActualProfit = async () => {
    if (!actualExitValue || parseFloat(actualExitValue) < 0) {
      toast.error('Please enter a valid exit value');
      return;
    }

    try {
      // Use BVE endpoint if in BVE mode, otherwise use regular trade endpoint
      // NOTE: For regular trades, lot_size is calculated server-side from authoritative account_value
      // to prevent stale frontend values. BVE mode still uses frontend lot_size for simulation.
      const commissionAmount = parseFloat(commissionValue) || 0;
      
      const logTradeEndpoint = isInBVE 
        ? api.post('/bve/trade/log', {
            lot_size: lotSize,  // BVE uses frontend value for simulation
            direction: signal?.direction || 'BUY',
            actual_profit: parseFloat(actualExitValue),
            commission: commissionAmount,
            notes: `Signal: ${signal?.product || 'MOIL10'}`,
          })
        : tradeAPI.logTrade({
            // lot_size is NOT sent - backend calculates it from authoritative account_value
            direction: signal?.direction || 'BUY',
            actual_profit: parseFloat(actualExitValue),
            commission: commissionAmount,
            notes: `Signal: ${signal?.product || 'MOIL10'}`,
          });
      
      const response = await logTradeEndpoint;

      const result = response.data;
      
      // IMPORTANT: Clear interval FIRST before any state changes
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
        countdownRef.current = null;
      }
      
      // Stop all audio immediately
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      if (beepRef.current) {
        beepRef.current.pause();
        beepRef.current.currentTime = 0;
      }
      
      // Stop global countdown and clear ALL persisted state
      stopGlobalCountdown();
      localStorage.removeItem('trade_check_in');
      localStorage.removeItem('trade_entered_state');
      
      // Keep tradeEnteredRef true to prevent any stray triggers
      // It will be reset on next startTrade
      tradeEnteredRef.current = true;
      tradeNotifiedRef.current = true; // Prevent any new notifications
      
      setLastTrade(result);
      setTradeEnded(false);
      setTradeEntered(false);
      setIsTrading(false);
      setShowExitAlert(false);
      setShowMissedTradePopup(false);
      setMissedTradeChecked(true); // Mark as checked for this signal

      // Show celebration popup based on performance
      const message = getPerformanceMessage(result.performance);
      setCelebrationMessage(message);
      setShowCelebration(true);

      setActualExitValue('');
      setCommissionValue('');
      loadData();
      loadTradeHistory();
    } catch (error) {
      toast.error('Failed to log trade');
    }
  };

  const forwardToProfit = async (tradeId) => {
    try {
      // Pass BVE mode to prevent BVE trades from being forwarded to production
      await tradeAPI.forwardToProfit(tradeId, isInBVE);
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

  // Trade action handlers (Reset / Request Change)
  const isMasterAdmin = user?.role === 'master_admin';

  const handleResetTrade = async (tradeId) => {
    if (!window.confirm('Are you sure you want to reset this trade? This action cannot be undone.')) {
      return;
    }
    
    setResetTradeLoading(tradeId);
    try {
      await tradeAPI.resetTrade(tradeId);
      toast.success('Trade has been reset successfully');
      loadTradeHistory();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset trade');
    } finally {
      setResetTradeLoading(null);
    }
  };

  const openRequestChangeDialog = (trade) => {
    setSelectedTradeForChange(trade);
    setChangeRequestReason('');
    setShowRequestChangeDialog(true);
  };

  const handleRequestChange = async () => {
    if (!changeRequestReason.trim()) {
      toast.error('Please provide a reason for the change request');
      return;
    }

    setRequestChangeLoading(selectedTradeForChange?.id);
    try {
      await tradeAPI.requestTradeChange({
        trade_id: selectedTradeForChange.id,
        reason: changeRequestReason.trim()
      });
      toast.success('Change request submitted to admin');
      setShowRequestChangeDialog(false);
      setSelectedTradeForChange(null);
      setChangeRequestReason('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit change request');
    } finally {
      setRequestChangeLoading(null);
    }
  };

  // Missed trade handlers
  const handleConfirmMissedTrade = () => {
    setShowMissedTradePopup(false);
    setMissedTradeChecked(true);
    toast.info('Trade marked as missed. You can still log it manually from your trade history.');
  };

  const handleDidNotMissTrade = () => {
    // User says they did trade - show the actual profit entry form
    setShowMissedTradePopup(false);
    setTradeEnded(true);
    setIsTrading(true);
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

        {/* Active Signal Card - Mobile optimized */}
        {signal ? (
          <Card className={`glass-highlight ${signal.is_simulated ? 'border-amber-500/30' : 'border-blue-500/30'}`} data-testid="active-signal-card">
            <CardHeader className="pb-2 px-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2 text-base">
                  <Radio className="w-4 h-4 text-blue-400 animate-pulse" /> 
                  Active Signal
                </CardTitle>
                {signal.is_simulated && (
                  <span className="px-2 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 rounded-full flex items-center gap-1">
                    <FlaskConical className="w-3 h-3" /> SIM
                  </span>
                )}
              </div>
              <p className="text-xs text-zinc-500 flex items-center gap-1 mt-1">
                <Calendar className="w-3 h-3" />
                {getTradingDate()}
              </p>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              {/* Signal Info Grid - Single column on mobile */}
              <div className="space-y-3">
                {/* Direction Badge - Prominent */}
                <div className="flex items-center gap-3">
                  <div className={`flex-1 px-4 py-3 rounded-lg text-center font-bold ${signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                    <div className="flex items-center justify-center gap-2">
                      {signal.direction === 'BUY' ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                      <span className="text-xl">{signal.direction}</span>
                    </div>
                    <p className="text-xs opacity-70 mt-1">{signal.product}</p>
                  </div>
                  <div className="flex-1 px-4 py-3 rounded-lg bg-purple-500/10 text-center">
                    <p className="text-[10px] text-zinc-500 uppercase">Multiplier</p>
                    <p className="text-xl font-mono font-bold text-purple-400">×{profitMultiplier}</p>
                  </div>
                </div>
                
                {/* Time Row */}
                <div className="flex gap-3">
                  <div className="flex-1 p-3 rounded-lg bg-zinc-900/50">
                    <p className="text-[10px] text-zinc-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Trade Time
                    </p>
                    <p className="text-lg font-mono font-bold text-blue-400">{signal.trade_time}</p>
                    <p className="text-[10px] text-zinc-600">{signal.trade_timezone || 'Asia/Manila'}</p>
                  </div>
                  {!isPhilippines && (
                    <div className="flex-1 p-3 rounded-lg bg-zinc-900/50">
                      <p className="text-[10px] text-zinc-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Your Time
                      </p>
                      <p className="text-lg font-mono font-bold text-cyan-400">{getUserLocalTradeTime()}</p>
                      <p className="text-[10px] text-zinc-600">{userTimezone.split('/').pop()}</p>
                    </div>
                  )}
                </div>
              </div>
              
              {signal.notes && (
                <p className="text-zinc-400 mt-3 p-2 bg-zinc-900/50 rounded-lg text-xs">{signal.notes}</p>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card className="glass-card border-2 border-dashed border-zinc-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 text-zinc-500">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <p className="text-sm">No active signal. Wait for today&apos;s signal.</p>
              </div>
            </CardContent>
          </Card>
        )}

      {/* LOT Size & Projected Exit Value Cards - Single column on mobile */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* LOT Size Card */}
        <Card className="glass-card" data-testid="lot-size-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-zinc-400">LOT Size</p>
                <p className="text-3xl font-mono font-bold text-purple-400 mt-1" data-testid="lot-size-value">
                  {lotSize.toFixed(2)}
                </p>
                <p className="text-[10px] text-zinc-500">Balance ÷ 980</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Calculator className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Projected Exit Value Card */}
        <Card className="glass-card" data-testid="projected-exit-card">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-zinc-400">Projected Exit</p>
                <p className="text-3xl font-mono font-bold text-emerald-400 mt-1" data-testid="projected-exit-value">
                  {formatLargeNumber(exitValue)}
                </p>
                <p className="text-[10px] text-zinc-500">LOT × {profitMultiplier}</p>
              </div>
              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                  <Rocket className="w-6 h-6 text-white" />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDreamProfit(true)}
                  className="text-purple-400 border-purple-400/30 hover:bg-purple-400/10 text-xs h-7 px-2"
                  data-testid="open-dream-profit"
                >
                  <Sparkles className="w-3 h-3 mr-1" /> Dream
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
            onClick={() => {
              const newSoundEnabled = !soundEnabled;
              setSoundEnabled(newSoundEnabled);
              // If muting, stop any currently playing audio immediately
              if (!newSoundEnabled) {
                if (audioRef.current) {
                  audioRef.current.pause();
                  audioRef.current.currentTime = 0;
                }
                if (beepRef.current) {
                  beepRef.current.pause();
                  beepRef.current.currentTime = 0;
                }
              }
            }}
            className="text-zinc-400"
            data-testid="sound-toggle"
          >
            {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
          </Button>
        </CardHeader>
        <CardContent>
          {showExitAlert ? (
            // Step 1: Alarm is ringing - show "Trade Entered" button
            <div className="text-center space-y-6">
              <div className="animate-bounce">
                <div className="text-6xl">🚨</div>
              </div>
              <h2 className="text-4xl font-bold text-emerald-400 animate-pulse">ENTER YOUR TRADE NOW!</h2>
              <p className="text-xl text-zinc-300">Target Exit Value: <span className="font-mono text-emerald-400">{formatLargeNumber(exitValue)}</span></p>
              <div className="flex gap-4 justify-center">
                <Button onClick={confirmTradeEntered} className="btn-primary text-xl py-6 px-8" data-testid="trade-entered-button">
                  <Check className="w-6 h-6 mr-2" /> Trade Entered
                </Button>
              </div>
            </div>
          ) : tradeEntered ? (
            // Step 2: User entered trade - show "Exit Trade" button
            <div className="text-center space-y-6">
              <div className="p-4 rounded-xl bg-emerald-500/20 border border-emerald-500/30">
                <p className="text-emerald-400 text-lg font-semibold">✓ Trade Active</p>
                <p className="text-zinc-400 text-sm mt-1">Click &quot;Exit Trade&quot; when you&apos;ve closed your position</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-sm text-zinc-400">Target Exit Value</p>
                <p className="text-3xl font-mono font-bold text-emerald-400">{formatLargeNumber(exitValue)}</p>
              </div>
              <Button onClick={confirmTradeExited} className="btn-primary text-xl py-6 px-8" data-testid="exit-trade-button">
                <ArrowRight className="w-6 h-6 mr-2" /> Exit Trade
              </Button>
            </div>
          ) : tradeEnded ? (
            // Step 3: User exited trade - show actual profit input
            <div className="text-center space-y-6">
              <h3 className="text-2xl font-bold text-white">Enter Your Actual Profit</h3>
              <p className="text-zinc-400">How much did you actually make from this trade?</p>
              <div className="max-w-sm mx-auto space-y-4">
                <div>
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
                <div>
                  <Label className="text-zinc-300">Commission (optional)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={commissionValue}
                    onChange={(e) => setCommissionValue(e.target.value)}
                    placeholder="0.00"
                    className="input-dark mt-1 text-lg font-mono text-center"
                    data-testid="commission-input"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Daily commission from referrals</p>
                </div>
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
              {/* Countdown stall warning */}
              {countdownStalled && (
                <div className="p-3 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  <span className="text-amber-400 text-sm">Countdown may have stalled</span>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={restartCountdown}
                    className="text-amber-400 border-amber-400/30 hover:bg-amber-400/10"
                    data-testid="restart-countdown-btn"
                  >
                    <RefreshCw className="w-4 h-4 mr-1" /> Refresh
                  </Button>
                </div>
              )}
              
              {/* Show active 30-second countdown when within 30 seconds */}
              {preTradeCountdown ? (
                <div className="space-y-4">
                  <div className="animate-pulse p-6 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 border border-red-500/50">
                    <p className="text-lg text-red-300 mb-2">🚨 TRADE STARTING IN</p>
                    <p className="text-6xl font-mono font-bold text-red-400">
                      {preTradeCountdown}
                    </p>
                    <p className="text-sm text-red-300 mt-2">SECONDS</p>
                  </div>
                  <p className="text-zinc-400">
                    Target Exit: <span className="text-2xl font-mono font-bold text-emerald-400">{formatLargeNumber(exitValue)}</span>
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-zinc-400">Waiting for trade time...</p>
                  <div className="flex justify-center gap-4">
                    {['hours', 'minutes', 'seconds'].map((unit) => (
                      <div key={unit} className={`glass-card p-4 min-w-[100px] ${countdownStalled ? 'border-amber-500/50' : ''}`}>
                        <p className={`text-4xl font-mono font-bold ${countdownStalled ? 'text-amber-400' : 'text-white'}`}>
                          {String(countdown[unit]).padStart(2, '0')}
                        </p>
                        <p className="text-xs text-zinc-500 uppercase">{unit}</p>
                      </div>
                    ))}
                  </div>
                  <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                    <p className="text-sm text-blue-300">
                      💡 Active countdown will appear 30 seconds before trade time
                    </p>
                  </div>
                  <div className="text-zinc-400">
                    Target Exit: <span className="text-2xl font-mono font-bold text-emerald-400">{formatLargeNumber(exitValue)}</span>
                  </div>
                </>
              )}
              <div className="flex gap-3 justify-center">
                <Button onClick={stopTrade} variant="outline" className="btn-secondary" data-testid="cancel-trade-button">
                  <Square className="w-5 h-5 mr-2" /> Cancel
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={restartCountdown}
                  className="text-zinc-400 hover:text-white"
                  data-testid="refresh-countdown-btn"
                >
                  <RefreshCw className="w-4 h-4 mr-1" /> Refresh Timer
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center space-y-6">
              <p className="text-zinc-400">Ready to trade? Check in when you&apos;re ready.</p>
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
                <Play className="w-8 h-8 mr-3" /> I&apos;m Ready to Trade
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
            <CardTitle className="text-white">Today&apos;s Summary</CardTitle>
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
                      <th>Projected</th>
                      <th>Actual</th>
                      <th>P/L Diff</th>
                      <th>Actions</th>
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
                        <td className="font-mono text-blue-400">${formatNumber(trade.projected_profit || 0)}</td>
                        <td className="font-mono text-emerald-400">${formatNumber(trade.actual_profit || 0)}</td>
                        <td className={`font-mono font-bold ${(trade.profit_difference || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {(trade.profit_difference || 0) >= 0 ? '+' : ''}${formatNumber(trade.profit_difference || (trade.actual_profit - trade.projected_profit) || 0)}
                        </td>
                        <td>
                          {isMasterAdmin ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleResetTrade(trade.id)}
                              disabled={resetTradeLoading === trade.id}
                              className="h-7 px-2 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              data-testid={`reset-trade-${trade.id}`}
                            >
                              {resetTradeLoading === trade.id ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <>
                                  <RotateCcw className="w-3 h-3 mr-1" />
                                  Reset
                                </>
                              )}
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openRequestChangeDialog(trade)}
                              disabled={requestChangeLoading === trade.id}
                              className="h-7 px-2 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                              data-testid={`request-change-${trade.id}`}
                            >
                              {requestChangeLoading === trade.id ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <>
                                  <MessageSquare className="w-3 h-3 mr-1" />
                                  Request Change
                                </>
                              )}
                            </Button>
                          )}
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

      {/* Missed Trade Popup - Shows when user misses the trade window */}
      <Dialog open={showMissedTradePopup} onOpenChange={setShowMissedTradePopup}>
        <DialogContent className="glass-card border-zinc-800 border-amber-500/30">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" /> Did you miss the trade?
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <p className="text-zinc-400 text-center">
              The trading window for today&apos;s signal has passed. Did you miss the trade?
            </p>
            
            <div className="p-4 rounded-lg bg-zinc-900/50">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400">Signal</span>
                <span className="font-mono text-white">{signal?.product || 'MOIL10'}</span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-zinc-400">Direction</span>
                <span className={`font-bold ${signal?.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {signal?.direction || 'BUY'}
                </span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-zinc-400">Trade Time</span>
                <span className="font-mono text-blue-400">{signal?.trade_time}</span>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <Button 
                onClick={handleConfirmMissedTrade} 
                variant="outline"
                className="w-full btn-secondary gap-2"
                data-testid="confirm-missed-trade-button"
              >
                <X className="w-4 h-4" /> Yes, I missed it
              </Button>
              <Button 
                onClick={handleDidNotMissTrade} 
                className="w-full btn-primary gap-2"
                data-testid="did-not-miss-trade-button"
              >
                <Check className="w-4 h-4" /> No, I traded
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Request Change Dialog */}
      <Dialog open={showRequestChangeDialog} onOpenChange={setShowRequestChangeDialog}>
        <DialogContent className="glass-card border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-amber-400" /> Request Trade Change
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedTradeForChange && (
              <div className="p-3 rounded-lg bg-zinc-900/50 text-sm">
                <div className="flex justify-between mb-1">
                  <span className="text-zinc-400">Trade Date:</span>
                  <span className="text-white font-mono">
                    {new Date(selectedTradeForChange.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </div>
                <div className="flex justify-between mb-1">
                  <span className="text-zinc-400">Actual Profit:</span>
                  <span className="text-emerald-400 font-mono">${formatNumber(selectedTradeForChange.actual_profit || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">Direction:</span>
                  <span className={selectedTradeForChange.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}>
                    {selectedTradeForChange.direction}
                  </span>
                </div>
              </div>
            )}
            
            <div>
              <Label className="text-zinc-300">Reason for Change Request</Label>
              <textarea
                value={changeRequestReason}
                onChange={(e) => setChangeRequestReason(e.target.value)}
                placeholder="Please explain why you need this trade modified..."
                className="w-full mt-2 p-3 rounded-lg bg-zinc-900 border border-zinc-700 text-white placeholder-zinc-500 resize-none focus:outline-none focus:border-amber-500/50"
                rows={4}
                data-testid="change-request-reason"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                variant="outline"
                onClick={() => setShowRequestChangeDialog(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </Button>
              <Button
                onClick={handleRequestChange}
                disabled={!changeRequestReason.trim() || requestChangeLoading}
                className="flex-1 btn-primary"
                data-testid="submit-change-request"
              >
                {requestChangeLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Submit Request
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      </div>

      {/* Right Panel - Merin Trading Platform */}
      {/* Desktop: Show iframe, Mobile: Show button to open in new tab */}
      <div className="hidden lg:block lg:w-[400px] xl:w-[450px] flex-shrink-0" data-testid="merin-panel">
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
      
      {/* Mobile: Open Merin Button (shows only on mobile) */}
      <div className="lg:hidden fixed bottom-4 left-4 right-4 z-50" data-testid="merin-mobile-button">
        <a
          href="https://www.meringlobaltrading.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="mobile-external-link-btn"
        >
          <ExternalLink className="w-5 h-5" />
          Open Merin Trading Platform
        </a>
      </div>
    </div>
    </MobileNotice>
  );
};
