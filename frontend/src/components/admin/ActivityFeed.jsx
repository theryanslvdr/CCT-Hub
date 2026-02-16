import React, { useState, useEffect, useRef, useCallback } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, TrendingUp, XCircle, Clock, Camera, Zap } from 'lucide-react';

const POLL_INTERVAL = 8000; // Poll every 8 seconds

const ACTIVITY_CONFIG = {
  habit_completed: { icon: CheckCircle2, color: 'text-teal-400', bg: 'bg-teal-500/10', label: 'Habit' },
  trade_logged: { icon: TrendingUp, color: 'text-blue-400', bg: 'bg-blue-500/10', label: 'Trade' },
};

const timeAgo = (ts) => {
  if (!ts) return '';
  const diff = (Date.now() - new Date(ts).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

const ActivityItem = ({ activity, isNew }) => {
  const config = ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.trade_logged;
  const Icon = config.icon;

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg transition-all duration-500 ${isNew ? 'bg-teal-500/5 border border-teal-500/20 animate-pulse' : 'hover:bg-zinc-800/40'}`}
      data-testid={`activity-item-${activity.timestamp}`}
    >
      <div className={`w-8 h-8 rounded-full ${config.bg} flex items-center justify-center shrink-0 mt-0.5`}>
        <Icon className={`w-4 h-4 ${config.color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white truncate">{activity.user_name}</span>
          {isNew && <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse shrink-0" />}
        </div>
        <p className="text-xs text-zinc-400 mt-0.5">{activity.detail}</p>
        {activity.screenshot_url && activity.screenshot_url.length > 50 && (
          <div className="mt-2 flex items-center gap-1.5">
            <Camera className="w-3 h-3 text-zinc-500" />
            <img src={activity.screenshot_url} alt="Proof" className="max-h-16 rounded border border-zinc-700" onError={(e) => e.target.style.display='none'} />
          </div>
        )}
      </div>
      <span className="text-[11px] text-zinc-600 shrink-0 mt-1">{timeAgo(activity.timestamp)}</span>
    </div>
  );
};

export const ActivityFeed = () => {
  const [activities, setActivities] = useState([]);
  const [newIds, setNewIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [liveCount, setLiveCount] = useState(0);
  const latestTs = useRef('');
  const isFirstLoad = useRef(true);

  const fetchActivities = useCallback(async () => {
    try {
      const since = isFirstLoad.current ? '' : latestTs.current;
      const res = await adminAPI.getActivityFeed(since, 50);
      const fetched = res.data.activities || [];

      if (isFirstLoad.current) {
        setActivities(fetched);
        isFirstLoad.current = false;
      } else if (fetched.length > 0) {
        // Mark new items
        const newSet = new Set(fetched.map(a => a.timestamp));
        setNewIds(newSet);
        setLiveCount(prev => prev + fetched.length);
        setActivities(prev => {
          const existingTs = new Set(prev.map(a => a.timestamp));
          const unique = fetched.filter(a => !existingTs.has(a.timestamp));
          return [...unique, ...prev].slice(0, 100);
        });
        // Clear new highlight after 5 seconds
        setTimeout(() => setNewIds(new Set()), 5000);
      }

      if (fetched.length > 0 && fetched[0].timestamp) {
        latestTs.current = fetched[0].timestamp;
      }
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchActivities();
    const interval = setInterval(fetchActivities, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchActivities]);

  return (
    <Card className="glass-card" data-testid="activity-feed">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2 text-base">
            <Zap className="w-5 h-5 text-teal-400" />
            Live Activity
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-teal-500" />
            </span>
            <span className="text-xs text-zinc-500">
              {liveCount > 0 ? `${liveCount} new` : 'Listening'}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="py-6 flex justify-center">
            <div className="w-5 h-5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : activities.length === 0 ? (
          <div className="py-6 text-center">
            <Clock className="w-8 h-8 text-zinc-700 mx-auto mb-2" />
            <p className="text-sm text-zinc-500">No activity yet today.</p>
            <p className="text-xs text-zinc-600 mt-1">Member actions will appear here in real-time</p>
          </div>
        ) : (
          <div className="space-y-1 max-h-[400px] overflow-y-auto pr-1 scrollbar-thin" data-testid="activity-list">
            {activities.map((a, i) => (
              <ActivityItem key={`${a.timestamp}-${i}`} activity={a} isNew={newIds.has(a.timestamp)} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
