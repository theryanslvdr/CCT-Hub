import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, TrendingUp, Activity, Radio, Users, BarChart3,
  User, Settings, LogOut, X, Award, Wallet, Target, CreditCard,
  ChevronRight, Shield, Eye, ExternalLink, Heart, Gift
} from 'lucide-react';
import { Button } from '@/components/ui/button';

// Smart app opener - tries to open app, falls back to store
const openHeartbeatApp = () => {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isAndroid = /Android/.test(navigator.userAgent);
  
  const appStoreUrl = 'https://apps.apple.com/us/app/heartbeat-chat/id1540206041';
  const playStoreUrl = 'https://play.google.com/store/apps/details?id=com.heartbeatreactnative&hl=en_US';
  const heartbeatScheme = 'heartbeat://';
  
  if (isIOS) {
    const now = Date.now();
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = heartbeatScheme;
    document.body.appendChild(iframe);
    
    setTimeout(() => {
      document.body.removeChild(iframe);
      if (document.visibilityState === 'visible' && Date.now() - now < 2000) {
        window.location.href = appStoreUrl;
      }
    }, 1500);
    
    setTimeout(() => {
      window.location.href = heartbeatScheme;
    }, 100);
    
  } else if (isAndroid) {
    const intentUrl = `intent://open#Intent;scheme=heartbeat;package=com.heartbeatreactnative;S.browser_fallback_url=${encodeURIComponent(playStoreUrl)};end`;
    window.location.href = intentUrl;
    
    setTimeout(() => {
      if (document.visibilityState === 'visible') {
        window.location.href = playStoreUrl;
      }
    }, 2000);
    
  } else {
    window.open(appStoreUrl, '_blank');
  }
};

export const MobileMenu = ({ isOpen, onClose }) => {
  const { 
    user, isAdmin, isMasterAdmin, isSuperAdmin, 
    simulatedView, exitSimulation, logout 
  } = useAuth();
  const navigate = useNavigate();

  // Check if user is a licensee
  const isLicenseeView = simulatedView?.license_type || user?.license_type;

  // Navigation items
  const mainNavItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/profit-tracker', icon: TrendingUp, label: 'Profit Tracker' },
    { path: '/trade-monitor', icon: Activity, label: 'Trade Monitor', hideForLicensee: true },
    { path: '/licensee-account', icon: Award, label: 'Deposit/Withdrawal', licenseeOnly: true },
  ];

  const adminNavItems = [
    { path: '/admin/members', icon: Users, label: 'Members' },
    { path: '/admin/signals', icon: Radio, label: 'Trading Signals' },
    { path: '/admin/analytics', icon: BarChart3, label: 'Team Analytics' },
  ];

  const superAdminItems = [
    { path: '/admin/transactions', icon: Wallet, label: 'Transactions' },
    { path: '/admin/settings', icon: Settings, label: 'Platform Settings' },
  ];

  // External links
  const externalLinks = [
    { 
      label: 'Heartbeat', 
      icon: Heart, 
      iconColor: 'text-red-400',
      action: () => {
        openHeartbeatApp();
        onClose();
      }
    },
    { 
      label: 'Rewards Platform', 
      icon: Gift, 
      url: 'https://rewards.crosscur.rent/login'
    },
  ];

  const handleNavClick = (path) => {
    navigate(path);
    onClose();
  };

  const handleExternalLink = (link) => {
    if (link.action) {
      link.action();
    } else if (link.url) {
      window.open(link.url, '_blank');
      onClose();
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    onClose();
  };

  const getVisibleMainItems = () => {
    return mainNavItems.filter(item => {
      if (item.hideForLicensee && isLicenseeView) return false;
      if (item.licenseeOnly && !isLicenseeView) return false;
      return true;
    });
  };

  if (!isOpen) return null;

  return (
    <div className="md:hidden fixed inset-0 z-[100] bg-zinc-950/98 backdrop-blur-xl">
      {/* Header with close button */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">CrossCurrent</h1>
            <p className="text-xs text-zinc-500">Finance Center</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="w-10 h-10 rounded-full bg-zinc-800 hover:bg-zinc-700"
          data-testid="mobile-menu-close"
        >
          <X className="w-5 h-5 text-white" />
        </Button>
      </div>

      {/* Simulation banner */}
      {simulatedView && (
        <div className="mx-4 mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-400 text-sm">
              <Eye className="w-4 h-4" />
              <span>Simulating: {simulatedView.displayName || simulatedView.role}</span>
            </div>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => { exitSimulation(); onClose(); }}
              className="h-7 text-xs border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
            >
              Exit
            </Button>
          </div>
        </div>
      )}

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-4 pb-24">
        {/* User info */}
        <div 
          onClick={() => handleNavClick('/profile')}
          className="flex items-center gap-3 p-4 mb-4 rounded-xl bg-zinc-900/50 border border-zinc-800 active:bg-zinc-800"
        >
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <User className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-white">{user?.full_name || 'User'}</p>
            <p className="text-sm text-zinc-400">{user?.email}</p>
          </div>
          <ChevronRight className="w-5 h-5 text-zinc-500" />
        </div>

        {/* Main Navigation */}
        <div className="space-y-1 mb-6">
          <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider px-3 mb-2">Navigation</p>
          {getVisibleMainItems().map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl transition-all",
                  isActive 
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/30" 
                    : "text-zinc-300 active:bg-zinc-800"
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Admin Navigation */}
        {isAdmin() && !simulatedView && (
          <div className="space-y-1 mb-6">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider px-3 mb-2">Admin</p>
            {adminNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) => cn(
                    "flex items-center gap-3 px-4 py-3 rounded-xl transition-all",
                    isActive 
                      ? "bg-purple-500/20 text-purple-400 border border-purple-500/30" 
                      : "text-zinc-300 active:bg-zinc-800"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              );
            })}
            
            {/* Super Admin items */}
            {(isSuperAdmin() || isMasterAdmin()) && superAdminItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) => cn(
                    "flex items-center gap-3 px-4 py-3 rounded-xl transition-all",
                    isActive 
                      ? "bg-purple-500/20 text-purple-400 border border-purple-500/30" 
                      : "text-zinc-300 active:bg-zinc-800"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        )}

        {/* External Links */}
        <div className="space-y-1 mb-6">
          <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider px-3 mb-2">Apps & Links</p>
          {externalLinks.map((link, index) => {
            const Icon = link.icon;
            return (
              <button
                key={index}
                onClick={() => handleExternalLink(link)}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-zinc-300 active:bg-zinc-800 transition-all"
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium flex-1 text-left">{link.label}</span>
                <ExternalLink className="w-4 h-4 text-zinc-500" />
              </button>
            );
          })}
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 active:bg-red-500/10 transition-all"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </div>
  );
};

export default MobileMenu;
