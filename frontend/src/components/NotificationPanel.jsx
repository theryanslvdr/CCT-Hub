import React from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { Bell, Check, Trash2, X, DollarSign, ArrowUpRight, ArrowDownRight, Radio, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

const NotificationIcon = ({ type }) => {
  switch (type) {
    case 'deposit_request':
      return <ArrowDownRight className="w-4 h-4 text-emerald-400" />;
    case 'withdrawal_request':
      return <ArrowUpRight className="w-4 h-4 text-amber-400" />;
    case 'transaction_status':
      return <DollarSign className="w-4 h-4 text-orange-400" />;
    case 'trade_signal':
      return <Radio className="w-4 h-4 text-purple-400" />;
    case 'system_announcement':
      return <AlertCircle className="w-4 h-4 text-cyan-400" />;
    default:
      return <Bell className="w-4 h-4 text-zinc-400" />;
  }
};

const formatTimeAgo = (timestamp) => {
  if (!timestamp) return 'Recently';
  
  try {
    const now = new Date();
    const time = new Date(timestamp);
    
    // Check if date is valid
    if (isNaN(time.getTime())) return 'Recently';
    
    const diff = Math.floor((now - time) / 1000);
    
    if (diff < 0) return 'Just now';
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  } catch (e) {
    return 'Recently';
  }
};

export const NotificationPanel = () => {
  const { notifications, unreadCount, markAllAsRead, clearNotifications, connected } = useWebSocket();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="relative"
          data-testid="notification-bell"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
          {/* Connection status indicator */}
          <span 
            className={cn(
              "absolute bottom-0 right-0 w-2 h-2 rounded-full border border-background",
              connected ? "bg-emerald-500" : "bg-zinc-500"
            )}
          />
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 p-0 bg-zinc-900 border-zinc-800" 
        align="end"
        data-testid="notification-panel"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-white">Notifications</h3>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 bg-orange-500/10 text-orange-400 text-xs rounded-full">
                {unreadCount} new
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {unreadCount > 0 && (
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-8 w-8 text-zinc-400 hover:text-white"
                onClick={markAllAsRead}
                title="Mark all as read"
              >
                <Check className="w-4 h-4" />
              </Button>
            )}
            {notifications.length > 0 && (
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-8 w-8 text-zinc-400 hover:text-white"
                onClick={clearNotifications}
                title="Clear all"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Notifications List */}
        <ScrollArea className="h-[300px]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[200px] text-zinc-500">
              <Bell className="w-8 h-8 mb-2" />
              <p>No notifications yet</p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-800">
              {notifications.map((notification, index) => (
                <div 
                  key={notification.id || index}
                  className="p-4 hover:bg-zinc-800/50 transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-zinc-800">
                      <NotificationIcon type={notification.type} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {notification.title}
                      </p>
                      <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
                        {notification.message}
                      </p>
                      {notification.amount && (
                        <p className="text-sm font-mono text-emerald-400 mt-1">
                          ${notification.amount.toLocaleString()}
                        </p>
                      )}
                      <p className="text-xs text-zinc-500 mt-2">
                        {formatTimeAgo(notification.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="p-3 border-t border-zinc-800">
          <div className="flex items-center justify-center gap-2 text-xs text-zinc-500">
            <span 
              className={cn(
                "w-2 h-2 rounded-full",
                connected ? "bg-emerald-500" : "bg-zinc-500"
              )}
            />
            {connected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default NotificationPanel;
