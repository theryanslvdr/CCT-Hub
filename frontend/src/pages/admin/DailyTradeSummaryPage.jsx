import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import {
  Users, TrendingUp, TrendingDown, AlertTriangle, CheckCircle2,
  X, Calendar, Radio, Loader2, DollarSign, BarChart3,
  ArrowLeft, RefreshCw
} from 'lucide-react';
import { format } from 'date-fns';

const formatMoney = (val) => {
  if (val === undefined || val === null) return '$0.00';
  const num = typeof val === 'number' ? val : parseFloat(val) || 0;
  return `${num < 0 ? '-' : ''}$${Math.abs(num).toFixed(2)}`;
};

export const DailyTradeSummaryPage = () => {
  const { isSuperAdmin, isMasterAdmin } = useAuth();
  const isAdmin = isSuperAdmin() || isMasterAdmin();
  const [searchParams, setSearchParams] = useSearchParams();
  const [date, setDate] = useState(searchParams.get('date') || format(new Date(), 'yyyy-MM-dd'));
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSummary = useCallback(async (targetDate) => {
    setLoading(true);
    try {
      const res = await api.get('/admin/daily-trade-summary', { params: { date: targetDate } });
      setSummary(res.data);
    } catch (error) {
      toast.error('Failed to load daily summary');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAdmin) fetchSummary(date);
  }, [isAdmin, date, fetchSummary]);

  const handleDateChange = (newDate) => {
    setDate(newDate);
    setSearchParams({ date: newDate });
  };

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-zinc-400">Admin access required</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-400" /> Daily Trade Summary
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Comprehensive view of all trading activity
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="date"
            value={date}
            onChange={(e) => handleDateChange(e.target.value)}
            className="input-dark w-44"
            data-testid="summary-date-input"
          />
          <Button variant="outline" size="sm" onClick={() => fetchSummary(date)} disabled={loading} className="border-zinc-700" data-testid="refresh-summary-btn">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        </div>
      ) : summary ? (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Card className="glass-card" data-testid="stat-traded">
              <CardContent className="p-4 text-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 mx-auto mb-1" />
                <p className="text-2xl font-bold text-white">{summary.stats.total_traded}</p>
                <p className="text-xs text-zinc-500">Traded</p>
              </CardContent>
            </Card>
            <Card className="glass-card" data-testid="stat-missed">
              <CardContent className="p-4 text-center">
                <AlertTriangle className="w-5 h-5 text-red-400 mx-auto mb-1" />
                <p className="text-2xl font-bold text-white">{summary.stats.total_missed}</p>
                <p className="text-xs text-zinc-500">Missed</p>
              </CardContent>
            </Card>
            <Card className="glass-card" data-testid="stat-profit">
              <CardContent className="p-4 text-center">
                <DollarSign className="w-5 h-5 text-cyan-400 mx-auto mb-1" />
                <p className={`text-2xl font-bold font-mono ${summary.stats.total_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {formatMoney(summary.stats.total_profit)}
                </p>
                <p className="text-xs text-zinc-500">Total Profit</p>
              </CardContent>
            </Card>
            <Card className="glass-card" data-testid="stat-commission">
              <CardContent className="p-4 text-center">
                <TrendingUp className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                <p className="text-2xl font-bold font-mono text-purple-400">{formatMoney(summary.stats.total_commission)}</p>
                <p className="text-xs text-zinc-500">Commission</p>
              </CardContent>
            </Card>
          </div>

          {/* Signal Info */}
          {summary.signal && (
            <Card className="glass-card border-blue-500/30" data-testid="signal-info-card">
              <CardContent className="p-4 flex items-center gap-4">
                <Radio className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <div className="flex items-center gap-3 flex-1">
                  <Badge className={`${summary.signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'} text-sm px-3`}>
                    {summary.signal.direction}
                  </Badge>
                  <span className="text-zinc-300 text-sm">{summary.signal.product}</span>
                  <span className="text-zinc-500 text-xs">at {summary.signal.trade_time}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Traded Members */}
          <Card className="glass-card" data-testid="traded-members-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-white text-base flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Traded ({summary.traded.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summary.traded.length > 0 ? (
                <div className="space-y-2">
                  {summary.traded.map((t, i) => (
                    <div key={`${t.user_id}-${i}`} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-zinc-800" data-testid={`traded-member-${i}`}>
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs font-bold text-emerald-400">
                          {(t.name || '?')[0]}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-white truncate">{t.name}</p>
                          <div className="flex items-center gap-2 text-xs text-zinc-500">
                            <span>{t.direction}</span>
                            <span>LOT: {(t.lot_size || 0).toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0 ml-3">
                        <p className={`text-sm font-mono font-bold ${t.actual_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {formatMoney(t.actual_profit)}
                        </p>
                        {t.commission > 0 && (
                          <p className="text-xs text-purple-400 font-mono">+{formatMoney(t.commission)} comm</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500 text-center py-4">No trades recorded</p>
              )}
            </CardContent>
          </Card>

          {/* Missed Members */}
          <Card className="glass-card border-red-500/20" data-testid="missed-members-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-white text-base flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                Missed / No Report ({summary.missed.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summary.missed.length > 0 ? (
                <div className="space-y-2">
                  {summary.missed.map((m, i) => (
                    <div key={`${m.user_id}-${i}`} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-red-500/10" data-testid={`missed-member-${i}`}>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center text-xs font-bold text-red-400">
                          {(m.name || '?')[0]}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">{m.name}</p>
                          <p className="text-xs text-zinc-500">{m.email}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="border-red-500/30 text-red-400 text-xs">No Report</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500 text-center py-4">Everyone reported!</p>
              )}
            </CardContent>
          </Card>

          {/* Did Not Trade */}
          {summary.did_not_trade.length > 0 && (
            <Card className="glass-card border-amber-500/20" data-testid="dnt-members-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-base flex items-center gap-2">
                  <X className="w-4 h-4 text-amber-400" />
                  Did Not Trade ({summary.did_not_trade.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {summary.did_not_trade.map((m, i) => (
                    <div key={`${m.user_id}-${i}`} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 border border-amber-500/10">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center text-xs font-bold text-amber-400">
                          {(m.name || '?')[0]}
                        </div>
                        <p className="text-sm font-medium text-white">{m.name}</p>
                      </div>
                      <Badge variant="outline" className="border-amber-500/30 text-amber-400 text-xs">DNT</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <div className="text-center py-20">
          <BarChart3 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
          <p className="text-zinc-400">No data available for this date</p>
        </div>
      )}
    </div>
  );
};

export default DailyTradeSummaryPage;
