import React, { useState, useEffect, useCallback, useRef } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  LineChart, 
  Radio, 
  MessageCircle,
  Gift
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import api from '@/lib/api';

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

export const MobileBottomNav = () => {
  const { user } = useAuth();
  const location = useLocation();

  // Handle external app links
  const handleHeartbeatClick = (e) => {
    e.preventDefault();
    triggerHaptic('medium');
    
    // Detect platform
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const url = isIOS 
      ? 'https://apps.apple.com/us/app/heartbeat-chat/id1540206041'
      : 'https://play.google.com/store/apps/details?id=com.heartbeatreactnative&hl=en_US';
    
    window.open(url, '_blank');
  };

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
      onClick: handleHeartbeatClick,
      icon: MessageCircle, 
      label: 'Chat',
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
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-zinc-900/95 backdrop-blur-lg border-t border-zinc-800 safe-area-bottom"
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
                    ? "bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg shadow-blue-500/30" 
                    : "bg-zinc-800 border-2 border-zinc-700"
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

          // External link buttons
          if (item.type === 'external') {
            return (
              <button
                key={index}
                onClick={item.onClick}
                className={cn(
                  "relative flex flex-col items-center justify-center py-2 px-3 rounded-lg min-w-[60px]",
                  "transition-all duration-200 active:scale-95",
                  "text-zinc-500 hover:text-zinc-300"
                )}
                data-testid={item.testId}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[10px] font-medium mt-1">
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
                  ? "text-blue-400" 
                  : "text-zinc-500 hover:text-zinc-300"
              )}
              data-testid={item.testId}
            >
              <Icon className={cn(
                "w-5 h-5",
                isActive && "text-blue-400"
              )} />
              <span className={cn(
                "text-[10px] font-medium mt-1",
                isActive ? "text-blue-400" : "text-zinc-500"
              )}>
                {item.label}
              </span>
              {isActive && (
                <div className="absolute -bottom-0.5 w-1 h-1 rounded-full bg-blue-400" />
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileBottomNav;
