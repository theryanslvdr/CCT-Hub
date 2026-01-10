import React, { useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '../../lib/utils';
import { Toaster } from '../ui/sonner';

const pagesTitles = {
  '/dashboard': 'Dashboard',
  '/profit-tracker': 'Profit Tracker',
  '/trade-monitor': 'Trade Monitor',
  '/goals': 'Profit Planner',
  '/debt': 'Debt Management',
  '/admin/signals': 'Trading Signals',
  '/admin/members': 'Member Management',
  '/admin/api-center': 'API Center',
  '/admin/settings': 'Platform Settings',
  '/profile': 'Profile Settings',
};

export const DashboardLayout = () => {
  const { isAuthenticated, loading } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

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

  return (
    <div className="min-h-screen bg-background grid-bg">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
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
    </div>
  );
};
