import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { adminAPI } from '@/lib/api';
import { Settings, Menu, Bell, ArrowDownToLine, ArrowUpFromLine, AlertTriangle, Check, ExternalLink, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { authAPI } from '@/lib/api';
import { useWebSocket } from '@/contexts/WebSocketContext';

const SECRET_CODE = 'SUPER_ADMIN_BYPASS';
const CLICKS_REQUIRED = 10;

export const Header = ({ onMenuClick, title }) => {
  const { user, updateUser, isSuperAdmin, isMasterAdmin } = useAuth();
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
        return <Bell className="w-4 h-4 text-blue-400" />;
    }
  };

  const formatTimeAgo = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <>
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

        <div className="flex items-center gap-4">
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

          {/* Notification Bell - Only for Super/Master Admin */}
          {canSeeNotifications && (
            <div className="relative" ref={notificationRef}>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowNotifications(!showNotifications)}
                className="text-zinc-400 hover:text-white hover:bg-white/5 relative"
                data-testid="notification-bell"
              >
                <Bell className="w-5 h-5" />
                {(unreadCount + wsUnreadCount) > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-medium">
                    {(unreadCount + wsUnreadCount) > 9 ? '9+' : (unreadCount + wsUnreadCount)}
                  </span>
                )}
                {/* WebSocket connection indicator */}
                <span className={`absolute bottom-0 right-0 w-2 h-2 rounded-full border border-zinc-950 ${wsConnected ? 'bg-emerald-500' : 'bg-zinc-500'}`} />
              </Button>

              {/* Notifications Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 top-12 w-80 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden z-50">
                  <div className="p-3 border-b border-zinc-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-white">Notifications</h3>
                    {unreadCount > 0 && (
                      <button
                        onClick={handleMarkAllRead}
                        className="text-xs text-blue-400 hover:text-blue-300"
                      >
                        Mark all read
                      </button>
                    )}
                  </div>
                  
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.length > 0 ? (
                      notifications.map((notification) => (
                        <button
                          key={notification.id}
                          onClick={() => handleNotificationClick(notification)}
                          className={`w-full p-3 flex items-start gap-3 hover:bg-zinc-800/50 transition-colors text-left border-b border-zinc-800/50 last:border-0 ${
                            !notification.is_read ? 'bg-blue-500/5' : ''
                          }`}
                        >
                          <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0">
                            {getNotificationIcon(notification.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-white truncate">
                                {notification.title}
                              </p>
                              {!notification.is_read && (
                                <div className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                              )}
                            </div>
                            <p className="text-xs text-zinc-400 truncate">{notification.message}</p>
                            <p className="text-xs text-zinc-500 mt-1">{formatTimeAgo(notification.created_at)}</p>
                          </div>
                        </button>
                      ))
                    ) : (
                      <div className="p-8 text-center text-zinc-500 text-sm">
                        No notifications yet
                      </div>
                    )}
                  </div>
                  
                  <div className="p-2 border-t border-zinc-800">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setShowNotifications(false);
                        navigate('/admin/transactions');
                      }}
                      className="w-full text-xs text-zinc-400 hover:text-white"
                    >
                      View Team Transactions <ExternalLink className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                </div>
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
        <DialogContent className="glass-card border-zinc-800 max-w-sm">
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
