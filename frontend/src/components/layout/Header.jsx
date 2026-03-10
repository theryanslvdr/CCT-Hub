import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useBVE } from '@/contexts/BVEContext';
import { adminAPI } from '@/lib/api';
import { Settings, Menu, Bell, ArrowDownToLine, ArrowUpFromLine, AlertTriangle, Check, ExternalLink, Wifi, WifiOff, FlaskConical, RotateCcw, LogOut as ExitIcon, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { authAPI } from '@/lib/api';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { NotificationSheet } from '@/components/NotificationSheet';

const SECRET_CODE = 'SUPER_ADMIN_BYPASS';
const CLICKS_REQUIRED = 10;

export const Header = ({ onMenuClick, title }) => {
  const { user, updateUser, isSuperAdmin, isMasterAdmin } = useAuth();
  const { isInBVE, canAccessBVE, enterBVE, exitBVE, rewindBVE, loading: bveLoading } = useBVE();
  const { connected: wsConnected, notifications: wsNotifications, unreadCount: wsUnreadCount, markAllAsRead: wsMarkAllRead } = useWebSocket();
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  
  // Secret upgrade feature state
  const [clickCount, setClickCount] = useState(0);
  const [showSecretDialog, setShowSecretDialog] = useState(false);
  const [secretCode, setSecretCode] = useState('');
  const [isUpgrading, setIsUpgrading] = useState(false);
  const clickResetTimeout = useRef(null);

  // Notifications state
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [loadingNotifications, setLoadingNotifications] = useState(false);
  const notificationRef = useRef(null);

  // Can see notifications
  const canSeeNotifications = isSuperAdmin() || isMasterAdmin();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Load notifications for admins
  useEffect(() => {
    if (canSeeNotifications) {
      loadNotifications();
      // Poll for new notifications every 30 seconds
      const interval = setInterval(loadNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [canSeeNotifications]);

  // Close notifications when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadNotifications = async () => {
    try {
      const res = await adminAPI.getNotifications(20, false);
      setNotifications(res.data.notifications || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch (error) {
      console.error('Failed to load notifications');
    }
  };

  // Reset click count after 3 seconds of no clicks
  useEffect(() => {
    return () => {
      if (clickResetTimeout.current) {
        clearTimeout(clickResetTimeout.current);
      }
    };
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

  const handleSettingsClick = () => {
    // If already super_admin or higher, just navigate to settings
    if (user?.role === 'super_admin' || user?.role === 'master_admin') {
      navigate('/admin/settings');
      return;
    }

    // Secret click counter
    const newCount = clickCount + 1;
    setClickCount(newCount);

    // Clear existing timeout
    if (clickResetTimeout.current) {
      clearTimeout(clickResetTimeout.current);
    }

    // Reset after 3 seconds of no clicks
    clickResetTimeout.current = setTimeout(() => {
      setClickCount(0);
    }, 3000);

    // Check if reached required clicks
    if (newCount >= CLICKS_REQUIRED) {
      setShowSecretDialog(true);
      setClickCount(0);
    }
  };

  const handleSecretUpgrade = async () => {
    if (secretCode !== SECRET_CODE) {
      toast.error('Invalid secret code');
      return;
    }

    setIsUpgrading(true);
    try {
      await authAPI.secretUpgrade({
        user_id: user.id,
        new_role: 'super_admin',
        secret_code: secretCode
      });
      
      toast.success('Upgraded to Super Admin! Please refresh the page.');
      setShowSecretDialog(false);
      setSecretCode('');
      
      if (updateUser) {
        updateUser({ ...user, role: 'super_admin' });
      }
      
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upgrade failed');
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleNotificationClick = async (notification) => {
    // Mark as read
    if (!notification.is_read) {
      try {
        await adminAPI.markNotificationRead(notification.id);
        setNotifications(prev => 
          prev.map(n => n.id === notification.id ? { ...n, is_read: true } : n)
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      } catch (error) {
        console.error('Failed to mark notification as read');
      }
    }
    
    // Navigate to transactions dashboard
    setShowNotifications(false);
    navigate('/admin/transactions');
  };

  const handleMarkAllRead = async () => {
    try {
      await adminAPI.markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'deposit':
        return <ArrowDownToLine className="w-4 h-4 text-emerald-400" />;
      case 'withdrawal':
        return <ArrowUpFromLine className="w-4 h-4 text-orange-400" />;
      case 'trade_underperform':
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      default:
        return <Bell className="w-4 h-4 text-orange-400" />;
    }
  };

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return 'Recently';
    
    try {
      const date = new Date(dateStr);
      
      // Check if date is valid
      if (isNaN(date.getTime())) return 'Recently';
      
      const now = new Date();
      const diff = Math.floor((now - date) / 1000);
      
      if (diff < 0) return 'Just now';
      if (diff < 60) return 'Just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return `${Math.floor(diff / 86400)}d ago`;
    } catch (e) {
      return 'Recently';
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 h-16 flex items-center justify-between px-6 bg-[#0a0a0a]/80 backdrop-blur-xl border-b border-[#1f1f1f]">
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

        <div className="flex items-center gap-4">
          {/* World Timer */}
          <div className="hidden lg:flex items-center gap-4 text-xs font-mono">
            <div className="flex flex-col items-center">
              <span className="text-zinc-500">UTC</span>
              <span className="text-white font-medium">{formatTime(currentTime, 'UTC')}</span>
            </div>
            <div className="w-px h-8 bg-[#1a1a1a]" />
            <div className="flex flex-col items-center">
              <span className="text-zinc-500">{user?.timezone || 'Local'}</span>
              <span className="text-orange-400 font-medium">{formatTime(currentTime, user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone)}</span>
            </div>
          </div>

          {/* Mobile Notification Bell - Links to /notifications page */}
          <button
            onClick={() => navigate('/notifications')}
            className="md:hidden relative p-2 hover:bg-white/5 rounded-lg text-zinc-400 hover:text-white transition-colors"
            data-testid="mobile-notifications-bell"
          >
            <Bell className="w-5 h-5" />
            {wsUnreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full">
                {wsUnreadCount > 99 ? '99+' : wsUnreadCount}
              </span>
            )}
          </button>

          {/* Notification Sheet - Off-Canvas Panel - Only for Super/Master Admin (Desktop) */}
          {canSeeNotifications && (
            <div className="hidden md:block">
              <NotificationSheet />
            </div>
          )}

          {/* BVE Toggle - Only for Super/Master Admin */}
          {canAccessBVE && (
            <div className="flex items-center gap-2">
              {isInBVE ? (
                <>
                  {/* BVE Active Badge */}
                  <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-500/20 border border-orange-500/20">
                    <FlaskConical className="w-4 h-4 text-purple-400 animate-pulse" />
                    <span className="text-xs font-medium text-purple-300">BVE Active</span>
                  </div>
                  
                  {/* Rewind Button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={rewindBVE}
                    disabled={bveLoading}
                    className="text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                    title="Rewind to entry point"
                    data-testid="bve-rewind"
                  >
                    {bveLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <RotateCcw className="w-5 h-5" />}
                  </Button>
                  
                  {/* Exit BVE Button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={exitBVE}
                    disabled={bveLoading}
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                    title="Exit Beta Virtual Environment"
                    data-testid="bve-exit"
                  >
                    <ExitIcon className="w-5 h-5" />
                  </Button>
                </>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={enterBVE}
                  disabled={bveLoading}
                  className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 gap-2"
                  title="Enter Beta Virtual Environment"
                  data-testid="bve-enter"
                >
                  {bveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
                  <span className="hidden sm:inline">BVE</span>
                </Button>
              )}
            </div>
          )}

          {/* Settings Button with Secret Feature */}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleSettingsClick}
            className="text-zinc-400 hover:text-white hover:bg-white/5 relative"
            data-testid="header-settings-button"
          >
            <Settings className="w-5 h-5" />
            {clickCount > 0 && clickCount < CLICKS_REQUIRED && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-purple-500/20 text-purple-400 text-[10px] flex items-center justify-center">
                {clickCount}
              </span>
            )}
          </Button>
        </div>
      </header>

      {/* Secret Upgrade Dialog */}
      <Dialog open={showSecretDialog} onOpenChange={setShowSecretDialog}>
        <DialogContent className="glass-card border-white/[0.06] max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              🔐 Secret Access
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              Enter the secret code to unlock Super Admin privileges.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="secret-code" className="text-zinc-400">Secret Code</Label>
              <Input
                id="secret-code"
                type="password"
                value={secretCode}
                onChange={(e) => setSecretCode(e.target.value)}
                placeholder="Enter secret code..."
                className="input-dark"
                onKeyDown={(e) => e.key === 'Enter' && handleSecretUpgrade()}
                data-testid="secret-code-input"
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleSecretUpgrade}
                disabled={isUpgrading || !secretCode}
                className="btn-primary flex-1"
                data-testid="secret-upgrade-btn"
              >
                {isUpgrading ? 'Upgrading...' : 'Unlock'}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowSecretDialog(false);
                  setSecretCode('');
                }}
                className="btn-secondary"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
