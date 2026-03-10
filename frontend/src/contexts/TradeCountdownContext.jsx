import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Clock, ArrowRight, Volume2, VolumeX } from 'lucide-react';

const TradeCountdownContext = createContext(null);

export const useTradeCountdown = () => {
  const context = useContext(TradeCountdownContext);
  if (!context) {
    throw new Error('useTradeCountdown must be used within TradeCountdownProvider');
  }
  return context;
};

export const TradeCountdownProvider = ({ children }) => {
  const [activeCountdown, setActiveCountdown] = useState(null);
  const [countdown, setCountdown] = useState(null);
  const [isBeeping, setIsBeeping] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const beepIntervalRef = useRef(null);
  const beepAudioRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize beep audio
  useEffect(() => {
    beepAudioRef.current = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2telezkALZ7Y7slXAwBMz/XqAMH/7v/B/8//APj/+P8A//8A');
  }, []);

  const playBeep = useCallback(() => {
    if (soundEnabled && beepAudioRef.current) {
      beepAudioRef.current.currentTime = 0;
      beepAudioRef.current.play().catch(() => {});
    }
  }, [soundEnabled]);

  // Start a countdown
  const startCountdown = useCallback((targetTime, signalInfo) => {
    setActiveCountdown({
      targetTime: new Date(targetTime),
      signalInfo
    });
  }, []);

  // Stop the countdown
  const stopCountdown = useCallback(() => {
    setActiveCountdown(null);
    setCountdown(null);
    setIsBeeping(false);
    if (beepIntervalRef.current) {
      clearInterval(beepIntervalRef.current);
      beepIntervalRef.current = null;
    }
    // Also clear the localStorage check-in to prevent restoring an expired countdown
    localStorage.removeItem('trade_check_in');
  }, []);

  // Update countdown every second
  useEffect(() => {
    if (!activeCountdown) return;

    const updateCountdown = () => {
      const now = new Date();
      const diff = activeCountdown.targetTime - now;

      if (diff <= 0) {
        stopCountdown();
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setCountdown({ hours, minutes, seconds, total: diff });

      // Start beeping in the last 30 seconds
      if (diff <= 30000 && !isBeeping) {
        setIsBeeping(true);
        // Clear any existing interval
        if (beepIntervalRef.current) clearInterval(beepIntervalRef.current);
        // Start continuous beeping every second for 5 seconds
        beepIntervalRef.current = setInterval(() => {
          playBeep();
        }, 200);
        // Stop beeping after 5 seconds
        setTimeout(() => {
          if (beepIntervalRef.current) {
            clearInterval(beepIntervalRef.current);
            beepIntervalRef.current = null;
          }
        }, 5000);
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [activeCountdown, isBeeping, playBeep, stopCountdown]);

  // Check if on trade monitor page or pages with iframes (like Merin)
  const isOnTradeMonitor = location.pathname === '/trade-monitor';
  const isOnMerinPage = location.pathname === '/merin' || location.pathname.includes('merin');
  const isOnProfilePage = location.pathname === '/profile';
  const isOnAdminPage = location.pathname.startsWith('/admin');
  
  // Hide floating popup on trade monitor (main timer is there), merin pages (has iframe), and admin pages
  const shouldHideFloatingPopup = isOnTradeMonitor || isOnMerinPage || isOnProfilePage || isOnAdminPage;

  // Format countdown
  const formatCountdown = () => {
    if (!countdown) return '--:--:--';
    const h = String(countdown.hours).padStart(2, '0');
    const m = String(countdown.minutes).padStart(2, '0');
    const s = String(countdown.seconds).padStart(2, '0');
    return countdown.hours > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;
  };

  const goToTradeMonitor = () => {
    navigate('/trade-monitor');
  };

  return (
    <TradeCountdownContext.Provider value={{ startCountdown, stopCountdown, activeCountdown, soundEnabled, setSoundEnabled }}>
      {children}
      
      {/* Floating countdown popup - only show when NOT on trade monitor/merin/admin and countdown is active */}
      {activeCountdown && countdown && !shouldHideFloatingPopup && (
        <div 
          className={`fixed bottom-6 right-6 z-50 bg-zinc-900/95 border ${countdown.total <= 30000 ? 'border-red-500 animate-pulse' : 'border-orange-500/30'} rounded-xl shadow-2xl p-4 max-w-sm backdrop-blur-lg`}
          data-testid="floating-countdown"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-10 h-10 rounded-lg ${countdown.total <= 30000 ? 'bg-red-500/20' : 'bg-orange-500/10'} flex items-center justify-center`}>
              <Clock className={`w-5 h-5 ${countdown.total <= 30000 ? 'text-red-400' : 'text-orange-400'}`} />
            </div>
            <div>
              <p className="text-xs text-zinc-400 uppercase tracking-wider">Trade Starting In</p>
              <p className={`text-2xl font-mono font-bold ${countdown.total <= 30000 ? 'text-red-400' : 'text-orange-400'}`}>
                {formatCountdown()}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSoundEnabled(!soundEnabled)}
              className="ml-auto text-zinc-400 hover:text-white"
            >
              {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </Button>
          </div>
          
          {countdown.total <= 30000 && (
            <p className="text-xs text-red-400 mb-3 animate-pulse">
              ⚠️ Trade starting soon! Return to Trade Monitor!
            </p>
          )}
          
          <Button 
            onClick={goToTradeMonitor} 
            className="w-full btn-primary gap-2"
            data-testid="return-to-trade-monitor"
          >
            Go to Trade Monitor <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </TradeCountdownContext.Provider>
  );
};

export default TradeCountdownProvider;
