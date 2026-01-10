import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Bell, Settings, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export const Header = ({ onMenuClick, title }) => {
  const { user } = useAuth();
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date, timezone = 'UTC') => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: timezone,
    });
  };

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-xl flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="md:hidden p-2 hover:bg-white/5 rounded-lg text-zinc-400 hover:text-white transition-colors"
          data-testid="mobile-menu-toggle"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold text-white">{title || 'Dashboard'}</h1>
      </div>

      <div className="flex items-center gap-6">
        {/* World Timer */}
        <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
          <div className="flex flex-col items-center">
            <span className="text-zinc-500">UTC</span>
            <span className="text-white font-medium">{formatTime(currentTime, 'UTC')}</span>
          </div>
          <div className="w-px h-8 bg-zinc-800" />
          <div className="flex flex-col items-center">
            <span className="text-zinc-500">{user?.timezone || 'Local'}</span>
            <span className="text-blue-400 font-medium">{formatTime(currentTime, user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone)}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="text-zinc-400 hover:text-white hover:bg-white/5"
            data-testid="notifications-button"
          >
            <Bell className="w-5 h-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-zinc-400 hover:text-white hover:bg-white/5"
            data-testid="header-settings-button"
          >
            <Settings className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  );
};
