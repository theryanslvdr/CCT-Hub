import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  LineChart, 
  Radio, 
  Users, 
  User,
  Settings
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

export const MobileBottomNav = () => {
  const { isSuperAdmin, isMasterAdmin } = useAuth();
  const location = useLocation();
  const isAdmin = isSuperAdmin() || isMasterAdmin();

  // Haptic feedback function
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
    ...(isAdmin ? [{ 
      to: '/admin/members', 
      icon: Users, 
      label: 'Members',
      testId: 'mobile-nav-members'
    }] : [{ 
      to: '/goals', 
      icon: Settings, 
      label: 'Goals',
      testId: 'mobile-nav-goals'
    }]),
    { 
      to: '/profile', 
      icon: User, 
      label: 'Profile',
      testId: 'mobile-nav-profile'
    },
  ];

  return (
    <nav 
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-zinc-900/95 backdrop-blur-lg border-t border-zinc-800 safe-area-bottom"
      data-testid="mobile-bottom-nav"
    >
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.to || 
            (item.to !== '/dashboard' && location.pathname.startsWith(item.to));
          
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
          
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => triggerHaptic('light')}
              className={cn(
                "flex flex-col items-center justify-center py-2 px-3 rounded-lg min-w-[60px]",
                "transition-all duration-200 active:scale-95",
                isActive 
                  ? "text-blue-400" 
                  : "text-zinc-500 hover:text-zinc-300"
              )}
              data-testid={item.testId}
            >
              <Icon className={cn(
                "w-5 h-5 mb-1",
                isActive && "text-blue-400"
              )} />
              <span className={cn(
                "text-[10px] font-medium",
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
