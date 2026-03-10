import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
  CheckCircle, RefreshCw, Loader2, UserPlus, Wallet, RotateCcw,
  BarChart3, ArrowRight
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

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
      return <Radio className="w-4 h-4 text-orange-400" />;
    case 'profit_submitted':
      return <TrendingUp className="w-4 h-4 text-cyan-400" />;
    case 'trade_underperform':
      return <AlertTriangle className="w-4 h-4 text-red-400" />;
    case 'tracker_reset':
      return <RotateCcw className="w-4 h-4 text-purple-400" />;
    case 'daily_summary':
      return <BarChart3 className="w-4 h-4 text-orange-400" />;
    default:
      return <Bell className="w-4 h-4 text-zinc-400" />;
  }
};

const NotificationCard = ({ notification, isAdmin, navigate }) => {
  let timeAgo = '';
  try {
    if (notification.created_at) {
      const date = new Date(notification.created_at);
      if (!isNaN(date.getTime())) {
        timeAgo = formatDistanceToNow(date, { addSuffix: true });
      } else {
        timeAgo = 'Recently';
      }
    }
  } catch {
    timeAgo = 'Recently';
  }

  const getSourceBadge = (source) => {
    switch (source) {
      case 'admin':
        return <Badge variant="outline" className="text-xs bg-red-500/20 text-red-400 border-red-500/30">Admin</Badge>;
      case 'community':
        return <Badge variant="outline" className="text-xs bg-orange-500/10 text-orange-400 border-orange-500/20">Community</Badge>;
      default:
        return <Badge variant="outline" className="text-xs bg-zinc-500/20 text-zinc-400 border-zinc-500/30">Personal</Badge>;
    }
  };

  // For admin trade-related notifications, link to daily summary
  const isClickable = isAdmin && (
    notification.type === 'profit_submitted' || 
    notification.type === 'daily_summary' || 
    notification.type === 'trade_underperform'
  );

  const handleClick = () => {
    if (!isClickable) return;
    const notifDate = notification.created_at ? format(new Date(notification.created_at), 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd');
    navigate(`/admin/daily-summary?date=${notifDate}`);
  };

  return (
    <div 
      className={`flex items-start gap-3 p-4 bg-[#0d0d0d]/50 rounded-lg border border-white/[0.06] transition-colors ${isClickable ? 'hover:border-orange-500/20 cursor-pointer' : 'hover:border-white/[0.08]'}`}
      onClick={handleClick}
      data-testid={`notification-card-${notification.id || ''}`}
    >
      <div className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center flex-shrink-0">
        <NotificationIcon type={notification.type} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <h4 className="text-sm font-medium text-white truncate">{notification.title}</h4>
          {getSourceBadge(notification.source)}
        </div>
        <p className="text-xs text-zinc-400 line-clamp-2">{notification.message}</p>
        <div className="flex items-center justify-between mt-1">
          <p className="text-[10px] text-zinc-500">{timeAgo}</p>
          {isClickable && (
            <span className="text-[10px] text-orange-400 flex items-center gap-0.5">
              View Details <ArrowRight className="w-3 h-3" />
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export const NotificationsPage = () => {
  const { user, isSuperAdmin, isMasterAdmin } = useAuth();
  const isAdmin = isSuperAdmin() || isMasterAdmin();
  const navigate = useNavigate();
  
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

  const handleRefresh = useCallback(async () => {
    await fetchNotifications();
    toast.success('Notifications refreshed');
  }, [fetchNotifications]);

  const { pullDistance, isRefreshing, threshold } = usePullToRefresh(handleRefresh);

  const filteredNotifications = notifications.filter(n => {
    if (activeTab === 'all') return true;
    if (activeTab === 'admin') return n.source === 'admin';
    if (activeTab === 'community') return n.source === 'community';
    return n.source === 'personal';
  });

  return (
    <div className="space-y-4 pb-20">
      <PullToRefreshIndicator pullDistance={pullDistance} threshold={threshold} isRefreshing={isRefreshing} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Notifications</h1>
          <p className="text-sm text-zinc-400">
            {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up!'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/admin/daily-summary')}
              className="border-white/[0.08] text-xs gap-1"
              data-testid="go-to-daily-summary-btn"
            >
              <BarChart3 className="w-3.5 h-3.5" /> Daily Summary
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={fetchNotifications} disabled={loading} className="border-white/[0.08]">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 bg-[#0d0d0d]">
          <TabsTrigger value="all" className="data-[state=active]:bg-[#1a1a1a]">All</TabsTrigger>
          <TabsTrigger value="community" className="data-[state=active]:bg-[#1a1a1a]">Community</TabsTrigger>
          {isAdmin && (
            <TabsTrigger value="admin" className="data-[state=active]:bg-[#1a1a1a]">Admin</TabsTrigger>
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
                <NotificationCard 
                  key={notification.id || index} 
                  notification={notification} 
                  isAdmin={isAdmin}
                  navigate={navigate}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Bell className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">No notifications yet</p>
              <p className="text-sm text-zinc-500 mt-1">Pull down to refresh</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NotificationsPage;
