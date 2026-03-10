import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for pull-to-refresh functionality on mobile
 * @param {Function} onRefresh - Async function to call when refreshing
 * @param {Object} options - Configuration options
 * @returns {Object} - Pull-to-refresh state and handlers
 */
export const usePullToRefresh = (onRefresh, options = {}) => {
  const {
    threshold = 80, // Pull distance to trigger refresh
    resistance = 2.5, // Resistance factor for pull
    maxPull = 120, // Maximum pull distance
  } = options;

  const [isPulling, setIsPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const startY = useRef(0);
  const currentY = useRef(0);
  const containerRef = useRef(null);

  const triggerHaptic = useCallback((type = 'light') => {
    if ('vibrate' in navigator) {
      switch (type) {
        case 'light':
          navigator.vibrate(10);
          break;
        case 'medium':
          navigator.vibrate(25);
          break;
        case 'success':
          navigator.vibrate([15, 50, 15]);
          break;
        default:
          navigator.vibrate(10);
      }
    }
  }, []);

  const handleTouchStart = useCallback((e) => {
    // Only enable pull-to-refresh if we're at the top of the page
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    if (scrollTop > 5) return;

    startY.current = e.touches[0].clientY;
    setIsPulling(true);
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (!isPulling) return;

    currentY.current = e.touches[0].clientY;
    const diff = currentY.current - startY.current;

    if (diff > 0) {
      // Apply resistance to make pull feel natural
      const pull = Math.min(diff / resistance, maxPull);
      setPullDistance(pull);

      // Haptic feedback when crossing threshold
      if (pull >= threshold && pullDistance < threshold) {
        triggerHaptic('medium');
      }
    }
  }, [isPulling, pullDistance, threshold, resistance, maxPull, triggerHaptic]);

  const handleTouchEnd = useCallback(async () => {
    if (!isPulling) return;

    if (pullDistance >= threshold && !isRefreshing) {
      setIsRefreshing(true);
      triggerHaptic('success');

      try {
        await onRefresh();
      } catch (error) {
        console.error('Refresh failed:', error);
      } finally {
        setIsRefreshing(false);
      }
    }

    setIsPulling(false);
    setPullDistance(0);
  }, [isPulling, pullDistance, threshold, isRefreshing, onRefresh, triggerHaptic]);

  useEffect(() => {
    const container = containerRef.current || document;

    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    container.addEventListener('touchmove', handleTouchMove, { passive: true });
    container.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
      container.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    containerRef,
    isPulling,
    pullDistance,
    isRefreshing,
    threshold,
    // Helper to get the pull indicator transform
    pullIndicatorStyle: {
      transform: `translateY(${Math.min(pullDistance, maxPull)}px)`,
      opacity: Math.min(pullDistance / threshold, 1),
    },
    // Helper to check if should trigger
    shouldTrigger: pullDistance >= threshold,
  };
};

/**
 * Pull-to-Refresh Indicator Component
 */
export const PullToRefreshIndicator = ({ 
  pullDistance, 
  threshold, 
  isRefreshing,
  className = '' 
}) => {
  const progress = Math.min(pullDistance / threshold, 1);
  const rotation = progress * 360;

  if (pullDistance === 0 && !isRefreshing) return null;

  return (
    <div 
      className={`fixed top-0 left-0 right-0 flex justify-center z-50 pointer-events-none ${className}`}
      style={{ 
        transform: `translateY(${Math.min(pullDistance, 120)}px)`,
        opacity: Math.min(pullDistance / 30, 1),
      }}
    >
      <div className={`
        w-10 h-10 rounded-full bg-[#1a1a1a] border border-white/[0.08] 
        flex items-center justify-center shadow-lg
        ${isRefreshing ? 'animate-spin' : ''}
      `}>
        <svg 
          className="w-5 h-5 text-orange-400" 
          viewBox="0 0 24 24"
          style={{ transform: isRefreshing ? 'none' : `rotate(${rotation}deg)` }}
        >
          <path 
            fill="currentColor" 
            d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"
          />
        </svg>
      </div>
    </div>
  );
};

export default usePullToRefresh;
