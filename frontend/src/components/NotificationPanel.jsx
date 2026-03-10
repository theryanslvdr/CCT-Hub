import React from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { Bell, Check, Trash2, DollarSign, ArrowUpRight, ArrowDownRight, Radio, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

const NotificationIcon = ({ type }) => {
  const icons = {
    deposit_request: <ArrowDownRight className="w-4 h-4 text-emerald-400" />,
    withdrawal_request: <ArrowUpRight className="w-4 h-4 text-amber-400" />,
    transaction_status: <DollarSign className="w-4 h-4 text-orange-400" />,
    trade_signal: <Radio className="w-4 h-4 text-purple-400" />,
    system_announcement: <AlertCircle className="w-4 h-4 text-teal-400" />,
  };
  return icons[type] || <Bell className="w-4 h-4 text-zinc-400" />;
};

const iconBg = {
  deposit_request: 'bg-emerald-500/10',
  withdrawal_request: 'bg-amber-500/10',
  transaction_status: 'bg-orange-500/10',
  trade_signal: 'bg-purple-500/10',
  system_announcement: 'bg-teal-500/10',
};

const formatTimeAgo = (timestamp) => {
  if (!timestamp) return 'Recently';
  try {
    const diff = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
    if (diff < 0 || isNaN(diff)) return 'Just now';
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  } catch { return 'Recently'; }
};

const groupByDate = (notifications) => {
  const groups = {};
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  notifications.forEach(n => {
    let label = 'Older';
    try {
      const d = new Date(n.timestamp).toDateString();
      if (d === today) label = 'Today';
      else if (d === yesterday) label = 'Yesterday';
    } catch { /* ignore */ }
    if (!groups[label]) groups[label] = [];
    groups[label].push(n);
  });
  return groups;
};

export const NotificationPanel = () => {
  const { notifications, unreadCount, markAllAsRead, clearNotifications, connected } = useWebSocket();
  const grouped = groupByDate(notifications);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" data-testid="notification-bell">
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center shadow-lg shadow-orange-500/30">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
          <span className={cn("absolute bottom-0 right-0 w-2 h-2 rounded-full border border-background", connected ? "bg-emerald-500" : "bg-zinc-600")} />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0 bg-[#111111] border border-[#222222] shadow-[0_25px_80px_rgba(0,0,0,0.7)] rounded-2xl" align="end" data-testid="notification-panel">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#1f1f1f]">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-white text-sm">Notifications</h3>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 bg-orange-500/10 text-orange-400 text-[10px] font-bold rounded-full">{unreadCount}</span>
            )}
          </div>
          <div className="flex items-center gap-0.5">
            {unreadCount > 0 && (
              <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-500 hover:text-white" onClick={markAllAsRead} title="Mark all as read">
                <Check className="w-3.5 h-3.5" />
              </Button>
            )}
            {notifications.length > 0 && (
              <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-500 hover:text-white" onClick={clearNotifications} title="Clear all">
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>

        <ScrollArea className="h-[340px]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[240px] text-zinc-600">
              <Bell className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm">No notifications</p>
            </div>
          ) : (
            <div className="py-1">
              {Object.entries(grouped).map(([label, items]) => (
                <div key={label}>
                  <div className="flex items-center justify-between px-4 py-2">
                    <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">{label}</p>
                    <span className="text-[10px] text-zinc-600">{items.length}</span>
                  </div>
                  {items.map((n, i) => (
                    <div key={n.id || i} className={cn("px-4 py-3 hover:bg-[#1a1a1a] transition-colors cursor-pointer border-b border-[#1f1f1f] last:border-0", !n.read && "bg-orange-500/[0.03]")} data-testid={`notification-item-${i}`}>
                      <div className="flex items-start gap-3">
                        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0", iconBg[n.type] || 'bg-white/[0.05]')}>
                          <NotificationIcon type={n.type} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-white leading-tight">{n.title}</p>
                          <p className="text-xs text-zinc-500 mt-0.5 line-clamp-2">{n.message}</p>
                          {n.amount && (
                            <p className="text-sm font-mono text-emerald-400 mt-1">${n.amount.toLocaleString()}</p>
                          )}
                          <p className="text-[10px] text-zinc-600 mt-1.5">{formatTimeAgo(n.timestamp)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-[#1f1f1f]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-[10px] text-zinc-600">
              <span className={cn("w-1.5 h-1.5 rounded-full", connected ? "bg-emerald-500" : "bg-zinc-600")} />
              {connected ? 'Live' : 'Disconnected'}
            </div>
            {notifications.length > 0 && (
              <button className="text-[10px] text-orange-400/70 hover:text-orange-400 transition-colors">
                View all
              </button>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};

export default NotificationPanel;
