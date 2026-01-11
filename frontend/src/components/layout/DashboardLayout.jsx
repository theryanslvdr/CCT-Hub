import React, { useState, useEffect } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { settingsAPI } from '@/lib/api';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';
import { Toaster } from '@/components/ui/sonner';
import { OnboardingTour, useOnboarding } from '@/components/OnboardingTour';

const pagesTitles = {
  '/dashboard': 'Dashboard',
  '/profit-tracker': 'Profit Tracker',
  '/trade-monitor': 'Trade Monitor',
  '/goals': 'Profit Planner',
  '/debt': 'Debt Management',
  '/profile': 'Profile Settings',
  '/admin/signals': 'Trading Signals',
  '/admin/members': 'Member Management',
  '/admin/api-center': 'API Center',
  '/admin/settings': 'Platform Settings',
  '/admin/analytics': 'Team Analytics',
  '/admin/transactions': 'Team Transactions',
  '/profit-planner': 'Profit Planner',
  '/debt-management': 'Debt Management',
};

export const DashboardLayout = () => {
  const { isAuthenticated, loading } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [platformSettings, setPlatformSettings] = useState(null);
  const location = useLocation();
  const { showTour, completeTour, resetTour } = useOnboarding();

  // Load platform settings
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const res = await settingsAPI.getPlatform();
        setPlatformSettings(res.data);
        
        // Apply favicon
        if (res.data?.favicon_url) {
          const favicon = document.querySelector("link[rel~='icon']") || document.createElement('link');
          favicon.rel = 'icon';
          favicon.href = res.data.favicon_url;
          document.head.appendChild(favicon);
        }
        
        // Apply title
        if (res.data?.site_title) {
          document.title = res.data.site_title;
        }
      } catch (error) {
        console.error('Failed to load platform settings');
      }
    };
    
    if (isAuthenticated) {
      loadSettings();
    }
  }, [isAuthenticated]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-zinc-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const currentTitle = pagesTitles[location.pathname] || 'CrossCurrent Finance';
  const hideEmergentBadge = platformSettings?.hide_emergent_badge === true;

  return (
    <div className="min-h-screen bg-background grid-bg">
      <Sidebar
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onShowTour={resetTour}
      />
      
      <main className={cn(
        "min-h-screen transition-all duration-300",
        sidebarCollapsed ? "ml-16" : "ml-64"
      )}>
        <Header
          title={currentTitle}
          onMenuClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        />
        
        <div className="p-6">
          <Outlet />
        </div>
      </main>

      <Toaster position="top-right" richColors />
      
      {/* Onboarding Tour */}
      <OnboardingTour isOpen={showTour} onClose={completeTour} />

      {/* Made with Emergent Badge - can be hidden via settings */}
      {!hideEmergentBadge && (
        <a
          href="https://emergentagent.com"
          target="_blank"
          rel="noopener noreferrer"
          className="fixed bottom-4 right-4 z-50 flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/90 border border-zinc-700/50 text-xs text-zinc-400 hover:text-white hover:border-zinc-600 transition-all backdrop-blur-sm"
          data-testid="emergent-badge"
        >
          <span>Made with</span>
          <span className="font-semibold text-blue-400">Emergent</span>
        </a>
      )}
    </div>
  );
};
