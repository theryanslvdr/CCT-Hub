import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  LineChart, 
  Radio, 
  Heart,
  Gift
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

// Haptic feedback function (defined at module level)
const triggerHaptic = (type = 'light') => {
  if ('vibrate' in navigator) {
    switch (type) {
      case 'light':
        navigator.vibrate(10);
        break;
      case 'medium':
        navigator.vibrate(20);
        break;
      case 'heavy':
        navigator.vibrate([30, 10, 30]);
        break;
      default:
        navigator.vibrate(10);
    }
  }
};

// Smart app opener - tries to open app, falls back to store
const openHeartbeatApp = () => {
  triggerHaptic('medium');
  
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isAndroid = /Android/.test(navigator.userAgent);
  
  // App store URLs
  const appStoreUrl = 'https://apps.apple.com/us/app/heartbeat-chat/id1540206041';
  const playStoreUrl = 'https://play.google.com/store/apps/details?id=com.heartbeatreactnative&hl=en_US';
  
  // Custom URL scheme for Heartbeat app
  // Common patterns: heartbeat://, heartbeatchat://, or the bundle ID
  const heartbeatScheme = 'heartbeat://';
  
  if (isIOS) {
    // iOS: Try to open app via custom URL scheme
    // Use a hidden iframe to attempt opening the app
    const now = Date.now();
    
    // Create a hidden iframe to try opening the app
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = heartbeatScheme;
    document.body.appendChild(iframe);
    
    // Set a timeout to check if app opened
    setTimeout(() => {
      document.body.removeChild(iframe);
      // If we're still here and not much time passed, app probably not installed
      // The page visibility check helps detect if app opened
      if (document.visibilityState === 'visible' && Date.now() - now < 2000) {
        // App not installed, go to App Store
        window.location.href = appStoreUrl;
      }
    }, 1500);
    
    // Also try window.location as backup
    setTimeout(() => {
      window.location.href = heartbeatScheme;
    }, 100);
    
  } else if (isAndroid) {
    // Android: Use intent URL which handles both cases
    // Intent URL format handles "open app or go to store" natively
    const intentUrl = `intent://open#Intent;scheme=heartbeat;package=com.heartbeatreactnative;S.browser_fallback_url=${encodeURIComponent(playStoreUrl)};end`;
    
    // Try the intent URL first
    window.location.href = intentUrl;
    
    // Fallback: If intent doesn't work, try direct scheme then store
    setTimeout(() => {
      if (document.visibilityState === 'visible') {
        window.location.href = playStoreUrl;
      }
    }, 2000);
    
  } else {
    // Desktop or unknown - just open the iOS App Store page
    window.open(appStoreUrl, '_blank');
  }
};

export const MobileBottomNav = () => {
  const { user } = useAuth();
  const location = useLocation();

  const handleRewardsClick = (e) => {
    e.preventDefault();
    triggerHaptic('medium');
    window.open('https://rewards.crosscur.rent/login', '_blank');
  };

  const navItems = [
    { 
      to: '/dashboard', 
      icon: LayoutDashboard, 
      label: 'Home',
      testId: 'mobile-nav-dashboard'
    },
    { 
      to: '/profit-tracker', 
      icon: LineChart, 
      label: 'Tracker',
      testId: 'mobile-nav-tracker'
    },
    { 
      to: '/trade-monitor', 
      icon: Radio, 
      label: 'Trade',
      isCenter: true,
      testId: 'mobile-nav-trade'
    },
    { 
      type: 'external',
      onClick: openHeartbeatApp,
      icon: Heart, 
      label: 'Heartbeat',
      testId: 'mobile-nav-heartbeat'
    },
    { 
      type: 'external',
      onClick: handleRewardsClick,
      icon: Gift, 
      label: 'Rewards',
      testId: 'mobile-nav-rewards'
    },
  ];

  return (
    <nav 
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#0a0a0a]/95 backdrop-blur-lg border-t border-white/[0.06] safe-area-bottom"
      data-testid="mobile-bottom-nav"
    >
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = item.to && (
            location.pathname === item.to || 
            (item.to !== '/dashboard' && location.pathname.startsWith(item.to))
          );
          
          if (item.isCenter) {
            // Center Trade Monitor button - larger and highlighted
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => triggerHaptic('medium')}
                className={cn(
                  "relative flex flex-col items-center justify-center -mt-6",
                  "w-16 h-16 rounded-full",
                  isActive 
                    ? "bg-gradient-to-br from-orange-500 to-amber-500 shadow-lg shadow-orange-500/30" 
                    : "bg-[#1a1a1a] border-2 border-white/[0.08]"
                )}
                data-testid={item.testId}
              >
                <Icon className={cn(
                  "w-6 h-6",
                  isActive ? "text-white" : "text-zinc-400"
                )} />
                <span className={cn(
                  "text-[10px] font-medium mt-0.5",
                  isActive ? "text-white" : "text-zinc-400"
                )}>
                  {item.label}
                </span>
              </NavLink>
            );
          }

          // External link buttons (Heartbeat, Rewards)
          if (item.type === 'external') {
            return (
              <button
                key={index}
                onClick={item.onClick}
                className={cn(
                  "relative flex flex-col items-center justify-center py-2 px-3 rounded-lg min-w-[60px]",
                  "transition-all duration-200 active:scale-95",
                  "text-zinc-500 hover:text-zinc-300",
                  // Special styling for Heartbeat icon
                  item.label === 'Heartbeat' && "hover:text-red-400"
                )}
                data-testid={item.testId}
              >
                <Icon className={cn(
                  "w-5 h-5",
                  item.label === 'Heartbeat' && "text-red-400"
                )} />
                <span className={cn(
                  "text-[10px] font-medium mt-1",
                  item.label === 'Heartbeat' ? "text-red-400" : "text-zinc-500"
                )}>
                  {item.label}
                </span>
              </button>
            );
          }
          
          // Regular nav links
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => triggerHaptic('light')}
              className={cn(
                "relative flex flex-col items-center justify-center py-2 px-3 rounded-lg min-w-[60px]",
                "transition-all duration-200 active:scale-95",
                isActive 
                  ? "text-orange-400" 
                  : "text-zinc-500 hover:text-zinc-300"
              )}
              data-testid={item.testId}
            >
              <Icon className={cn(
                "w-5 h-5",
                isActive && "text-orange-400"
              )} />
              <span className={cn(
                "text-[10px] font-medium mt-1",
                isActive ? "text-orange-400" : "text-zinc-500"
              )}>
                {item.label}
              </span>
              {isActive && (
                <div className="absolute -bottom-0.5 w-1 h-1 rounded-full bg-orange-400" />
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileBottomNav;
