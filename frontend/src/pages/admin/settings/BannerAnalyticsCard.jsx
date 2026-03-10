import React, { useState, useEffect } from 'react';
import { settingsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, TrendingUp } from 'lucide-react';

export const BannerAnalyticsCard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const res = await settingsAPI.getBannerAnalytics(30);
      setAnalytics(res.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadAnalytics(); }, []);

  const formatLabel = (key) => key === 'notice_banner' ? 'Notice Banner' : key === 'promo_popup' ? 'Promotion Popup' : key;

  return (
    <Card className="glass-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" /> Banner Analytics (30 days)
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={loadAnalytics} disabled={loading} data-testid="refresh-analytics">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {!analytics || !Object.keys(analytics.summary || {}).length ? (
          <p className="text-sm text-zinc-500">No analytics data yet. Enable a banner or popup to start tracking.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {Object.entries(analytics.summary).map(([key, data]) => (
              <div key={key} className="p-4 rounded-lg bg-[#0d0d0d]/60 border border-white/[0.06] space-y-2" data-testid={`analytics-${key}`}>
                <p className="text-sm font-medium text-zinc-300">{formatLabel(key)}</p>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-xl font-bold text-white">{data.impressions}</p>
                    <p className="text-xs text-zinc-500">Views</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold text-white">{data.dismissals}</p>
                    <p className="text-xs text-zinc-500">Dismissed</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold text-white">{data.dismiss_rate}%</p>
                    <p className="text-xs text-zinc-500">Dismiss Rate</p>
                  </div>
                </div>
                <p className="text-xs text-zinc-600">Active {data.days_active} day{data.days_active !== 1 ? 's' : ''}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
