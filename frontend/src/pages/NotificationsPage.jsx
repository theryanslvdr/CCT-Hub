import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import { usePullToRefresh, PullToRefreshIndicator } from '@/hooks/usePullToRefresh';
import { toast } from 'sonner';
import { 
  Bell, Users, TrendingUp, DollarSign, Radio, AlertTriangle,
  CheckCircle, RefreshCw, Loader2, UserPlus, Wallet, RotateCcw
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const NotificationIcon = ({ type }) => {
  switch (type) {
    case 'new_user':
    case 'new_member':
      return <UserPlus className="w-4 h-4 text-green-400" />;
    case 'deposit':
      return <DollarSign className="w-4 h-4 text-emerald-400" />;
    case 'withdrawal':
      return <Wallet className="w-4 h-4 text-amber-400" />;
    case 'trading_signal':
      return <Radio className="w-4 h-4 text-blue-400" />;
    case 'profit_submitted':
      return <TrendingUp className="w-4 h-4 text-cyan-400" />;
    case 'trade_underperform':
      return <AlertTriangle className="w-4 h-4 text-red-400" />;
    case 'tracker_reset':
      return <RotateCcw className="w-4 h-4 text-purple-400" />;
    default:
      return <Bell className="w-4 h-4 text-zinc-400" />;
  }
};

const NotificationCard = ({ notification }) => {
  // Safe time parsing with fallback
  let timeAgo = '';
  try {
    if (notification.created_at) {
      const date = new Date(notification.created_at);
      // Check if date is valid
      if (!isNaN(date.getTime())) {
        timeAgo = formatDistanceToNow(date, { addSuffix: true });
      } else {
        timeAgo = 'Recently';
      }
    }
  } catch (e) {
    timeAgo = 'Recently';
  }

  const getSourceBadge = (source) => {
    switch (source) {
      case 'admin':
        return <Badge variant="outline" className="text-xs bg-red-500/20 text-red-400 border-red-500/30">Admin</Badge>;
      case 'community':
        return <Badge variant="outline" className="text-xs bg-blue-500/20 text-blue-400 border-blue-500/30">Community</Badge>;
      default:
        return <Badge variant="outline" className="text-xs bg-zinc-500/20 text-zinc-400 border-zinc-500/30">Personal</Badge>;
    }
  };

  return (
    <div className="flex items-start gap-3 p-4 bg-zinc-900/50 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors">
      <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
        <NotificationIcon type={notification.type} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <h4 className="text-sm font-medium text-white truncate">
            {notification.title}
          </h4>
          {getSourceBadge(notification.source)}
        </div>
        <p className="text-xs text-zinc-400 line-clamp-2">
          {notification.message}
        </p>
        <p className="text-[10px] text-zinc-500 mt-1">
          {timeAgo}
        </p>
      </div>
    </div>
  );
};

export const NotificationsPage = () => {
  const { user, isSuperAdmin, isMasterAdmin } = useAuth();
  const isAdmin = isSuperAdmin() || isMasterAdmin();
  
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/notifications?limit=50');
      setNotifications(res.data.notifications || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Pull-to-refresh
  const handleRefresh = useCallback(async () => {
    await fetchNotifications();
    toast.success('Notifications refreshed');
  }, [fetchNotifications]);

  const { pullDistance, isRefreshing, threshold } = usePullToRefresh(handleRefresh);

  // Filter notifications by tab
  const filteredNotifications = notifications.filter(n => {
    if (activeTab === 'all') return true;
    if (activeTab === 'admin') return n.source === 'admin';
    if (activeTab === 'community') return n.source === 'community';
    return n.source === 'personal';
  });

  return (
    <div className="space-y-4 pb-20">
      {/* Pull-to-Refresh Indicator */}
      <PullToRefreshIndicator 
        pullDistance={pullDistance} 
        threshold={threshold} 
        isRefreshing={isRefreshing} 
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Notifications</h1>
          <p className="text-sm text-zinc-400">
            {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up!'}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchNotifications}
          disabled={loading}
          className="border-zinc-700"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 bg-zinc-900">
          <TabsTrigger value="all" className="data-[state=active]:bg-zinc-800">
            All
          </TabsTrigger>
          <TabsTrigger value="community" className="data-[state=active]:bg-zinc-800">
            Community
          </TabsTrigger>
          {isAdmin && (
            <TabsTrigger value="admin" className="data-[state=active]:bg-zinc-800">
              Admin
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
            </div>
          ) : filteredNotifications.length > 0 ? (
            <div className="space-y-3">
              {filteredNotifications.map((notification, index) => (
                <NotificationCard key={notification.id || index} notification={notification} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Bell className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">No notifications yet</p>
              <p className="text-sm text-zinc-500 mt-1">
                Pull down to refresh
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NotificationsPage;
