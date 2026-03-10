import React from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { Bell, Check, Trash2, DollarSign, ArrowUpRight, ArrowDownRight, Radio, AlertCircle, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
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
    case 'new_user':
      return <Bell className="w-4 h-4 text-emerald-400" />;
    case 'missed_trade':
      return <AlertCircle className="w-4 h-4 text-red-400" />;
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

export const NotificationSheet = () => {
  const { notifications, unreadCount, markAllAsRead, clearNotifications, connected, reconnect } = useWebSocket();

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="relative"
          data-testid="notification-bell"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
          {/* Connection status indicator */}
          <span 
            className={cn(
              "absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-background",
              connected ? "bg-emerald-500" : "bg-red-500 animate-pulse"
            )}
            title={connected ? 'Connected' : 'Disconnected'}
          />
        </Button>
      </SheetTrigger>
      <SheetContent 
        className="w-[400px] sm:w-[540px] bg-[#0d0d0d] border-white/[0.06] p-0"
        data-testid="notification-sheet"
      >
        <SheetHeader className="p-4 border-b border-white/[0.06]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <SheetTitle className="text-white flex items-center gap-2">
                <Bell className="w-5 h-5 text-orange-400" />
                Notifications
              </SheetTitle>
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
        </SheetHeader>

        {/* Connection Status Banner */}
        {!connected && (
          <div className="px-4 py-3 bg-red-500/10 border-b border-red-500/20 flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-400">
              <WifiOff className="w-4 h-4" />
              <span className="text-sm">Connection lost</span>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={reconnect}
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
            >
              <RefreshCw className="w-4 h-4 mr-1" /> Reconnect
            </Button>
          </div>
        )}

        {/* Notifications List */}
        <ScrollArea className="h-[calc(100vh-180px)]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[300px] text-zinc-500">
              <Bell className="w-12 h-12 mb-3 opacity-50" />
              <p className="text-lg">No notifications yet</p>
              <p className="text-sm mt-1">You&apos;ll see updates here</p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-800/50">
              {notifications.map((notification, index) => (
                <div 
                  key={notification.id || index}
                  className="p-4 hover:bg-white/[0.03] transition-colors cursor-pointer group"
                >
                  <div className="flex items-start gap-3">
                    <div className={cn(
                      "p-2.5 rounded-lg shrink-0",
                      notification.type === 'missed_trade' ? 'bg-red-500/10' :
                      notification.type === 'deposit_request' ? 'bg-emerald-500/10' :
                      notification.type === 'withdrawal_request' ? 'bg-amber-500/10' :
                      notification.type === 'new_user' ? 'bg-emerald-500/10' :
                      'bg-[#1a1a1a]'
                    )}>
                      <NotificationIcon type={notification.type} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium text-white">
                          {notification.title}
                        </p>
                        <span className="text-xs text-zinc-500 shrink-0">
                          {formatTimeAgo(notification.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-400 mt-1 leading-relaxed">
                        {notification.message}
                      </p>
                      {notification.amount && (
                        <p className="text-sm font-mono text-emerald-400 mt-2">
                          ${notification.amount.toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/[0.06] bg-[#0d0d0d]">
          <div className="flex items-center justify-center gap-2 text-sm">
            {connected ? (
              <>
                <Wifi className="w-4 h-4 text-emerald-500" />
                <span className="text-emerald-400">Live updates active</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-500" />
                <span className="text-red-400">Disconnected - Click reconnect</span>
              </>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default NotificationSheet;
