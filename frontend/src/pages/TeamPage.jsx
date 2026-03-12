import React, { useState, useEffect, useCallback } from 'react';
import { referralAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Users, AlertTriangle, TrendingUp, UserPlus, Activity, Clock, Shield, Flame, Bot, Lightbulb, RefreshCw, Link2, Copy, ExternalLink, Trophy, BarChart3, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { toast } from 'sonner';

const STATUS_COLORS = {
  active: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  inactive: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/20',
  danger: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  suspended: 'bg-red-500/15 text-red-400 border-red-500/20',
};

const URGENCY_COLORS = {
  high: 'border-red-500/30 bg-red-500/5',
  medium: 'border-amber-500/30 bg-amber-500/5',
  low: 'border-blue-500/30 bg-blue-500/5',
};

const TrendIndicator = ({ current, previous, isCurrency, isPercent }) => {
  if (previous === undefined || previous === null) return null;
  const diff = current - previous;
  if (diff === 0) return <span className="flex items-center gap-0.5 text-[10px] text-zinc-500"><Minus className="w-3 h-3" /> No change</span>;
  const isUp = diff > 0;
  const Icon = isUp ? ArrowUpRight : ArrowDownRight;
  const color = isUp ? 'text-emerald-400' : 'text-red-400';
  const formatted = isCurrency ? `$${Math.abs(diff).toLocaleString()}` : isPercent ? `${Math.abs(diff).toFixed(1)}%` : Math.abs(diff);
  return <span className={`flex items-center gap-0.5 text-[10px] ${color}`}><Icon className="w-3 h-3" /> {formatted} vs last wk</span>;
};

const TeamPage = () => {
  const [team, setTeam] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, in_danger: 0, new_this_week: 0 });
  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [showRecs, setShowRecs] = useState(false);
  const [tracking, setTracking] = useState(null);
  const [weeklyReport, setWeeklyReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  const loadTeam = useCallback(async () => {
    try {
      const [teamRes, trackRes] = await Promise.all([
        referralAPI.getMyTeam(),
        referralAPI.getTracking().catch(() => ({ data: null })),
      ]);
      setTeam(teamRes.data.team || []);
      setStats(teamRes.data.stats || {});
      setTracking(trackRes.data);
    } catch {
      toast.error('Failed to load team data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTeam(); }, [loadTeam]);

  useEffect(() => {
    const loadReport = async () => {
      setReportLoading(true);
      try {
        const res = await referralAPI.getTeamWeeklyReport();
        setWeeklyReport(res.data.report);
      } catch {}
      setReportLoading(false);
    };
    loadReport();
  }, []);

  const loadRecommendations = async () => {
    setRecsLoading(true);
    setShowRecs(true);
    try {
      const res = await referralAPI.getTeamRecommendations();
      setRecommendations(res.data.recommendations || []);
    } catch {
      toast.error('Failed to load AI recommendations');
    } finally {
      setRecsLoading(false);
    }
  };

  const copyLink = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto" data-testid="team-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Team</h1>
          <p className="text-sm text-zinc-400 mt-1">Invite members, manage your team, and track activity</p>
        </div>
        {stats.in_danger > 0 && (
          <Button
            variant="outline" size="sm"
            onClick={loadRecommendations}
            disabled={recsLoading}
            className="text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
            data-testid="ai-recommendations-btn"
          >
            {recsLoading ? <RefreshCw className="w-4 h-4 mr-1 animate-spin" /> : <Bot className="w-4 h-4 mr-1" />}
            AI Insights
          </Button>
        )}
      </div>

      {/* Invite Link Card - Prominent at top */}
      <Card className="border-orange-500/20 bg-gradient-to-r from-orange-500/[0.04] to-transparent" data-testid="invite-link-card">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center shrink-0">
              <Link2 className="w-6 h-6 text-orange-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white">Invite & Earn</h3>
              <p className="text-xs text-zinc-500 mt-1 mb-3">
                Share your invite link to grow your team. Your code: <span className="text-orange-400 font-mono">{tracking?.merin_code || tracking?.referral_code || '—'}</span>
              </p>
              {tracking?.onboarding_invite_link ? (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <Input
                      value={tracking.onboarding_invite_link}
                      readOnly
                      className="bg-[#0a0a0a] border-white/[0.06] text-white font-mono text-xs"
                      data-testid="invite-link-display"
                    />
                    <Button
                      onClick={() => copyLink(tracking.onboarding_invite_link)}
                      className="bg-orange-500 hover:bg-orange-600 text-white shrink-0"
                      data-testid="copy-invite-link"
                    >
                      <Copy className="w-4 h-4 mr-1.5" /> Copy
                    </Button>
                  </div>
                  {tracking?.invite_link && (
                    <div className="flex items-center gap-1 text-[11px] text-zinc-500">
                      <ExternalLink className="w-3 h-3" />
                      <span>Direct signup:</span>
                      <a href={tracking.invite_link} target="_blank" rel="noopener noreferrer" className="text-zinc-400 hover:text-zinc-300 underline truncate max-w-[300px]">
                        {tracking.invite_link}
                      </a>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-amber-400">Set your Merin referral code in Profile to generate an invite link.</p>
              )}
            </div>
          </div>
          {/* Quick referral stats */}
          <div className="mt-4 pt-3 border-t border-white/[0.04] flex items-center gap-6 text-xs text-zinc-400">
            <span className="flex items-center gap-1"><UserPlus className="w-3 h-3 text-emerald-400" /> <strong className="text-white">{tracking?.direct_count || 0}</strong> Direct Referrals</span>
            <span className="flex items-center gap-1"><Trophy className="w-3 h-3 text-purple-400" /> <strong className="text-white">{tracking?.milestones?.filter(m => m.achieved).length || 0}</strong> Milestones</span>
          </div>
        </CardContent>
      </Card>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="glass-card" data-testid="team-stat-total">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/15 flex items-center justify-center"><Users className="w-5 h-5 text-orange-400" /></div>
              <div><p className="text-2xl font-bold text-white font-mono">{stats.total}</p><p className="text-[11px] text-zinc-500">Total Members</p></div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card" data-testid="team-stat-active">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/15 flex items-center justify-center"><Activity className="w-5 h-5 text-emerald-400" /></div>
              <div><p className="text-2xl font-bold text-emerald-400 font-mono">{stats.active}</p><p className="text-[11px] text-zinc-500">Active This Week</p></div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card" data-testid="team-stat-danger">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/15 flex items-center justify-center"><AlertTriangle className="w-5 h-5 text-amber-400" /></div>
              <div><p className="text-2xl font-bold text-amber-400 font-mono">{stats.in_danger}</p><p className="text-[11px] text-zinc-500">In Danger</p></div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card" data-testid="team-stat-new">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/15 flex items-center justify-center"><UserPlus className="w-5 h-5 text-cyan-400" /></div>
              <div><p className="text-2xl font-bold text-cyan-400 font-mono">{stats.new_this_week}</p><p className="text-[11px] text-zinc-500">New This Week</p></div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Weekly Performance Report */}
      <Card className="glass-card border-cyan-500/10" data-testid="weekly-performance-report">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-base flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" /> Weekly Performance Report
          </CardTitle>
          <p className="text-xs text-zinc-500">Team trading performance for the current week</p>
        </CardHeader>
        <CardContent>
          {reportLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : !weeklyReport ? (
            <p className="text-sm text-zinc-500 py-4 text-center">No report data available yet.</p>
          ) : (
            <div className="space-y-4">
              {/* Summary Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                  <p className="text-[11px] text-zinc-500 mb-1">Total Trades</p>
                  <p className="text-xl font-bold text-white font-mono" data-testid="report-total-trades">{weeklyReport.total_trades}</p>
                  <TrendIndicator current={weeklyReport.total_trades} previous={weeklyReport.prev_week?.total_trades} />
                </div>
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                  <p className="text-[11px] text-zinc-500 mb-1">Total Profit</p>
                  <p className={`text-xl font-bold font-mono ${weeklyReport.total_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`} data-testid="report-total-profit">
                    ${weeklyReport.total_profit?.toLocaleString()}
                  </p>
                  <TrendIndicator current={weeklyReport.total_profit} previous={weeklyReport.prev_week?.total_profit} isCurrency />
                </div>
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                  <p className="text-[11px] text-zinc-500 mb-1">Win Rate</p>
                  <p className="text-xl font-bold text-orange-400 font-mono" data-testid="report-win-rate">{weeklyReport.win_rate}%</p>
                  <TrendIndicator current={weeklyReport.win_rate} previous={weeklyReport.prev_week?.win_rate} isPercent />
                </div>
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                  <p className="text-[11px] text-zinc-500 mb-1">Active Traders</p>
                  <p className="text-xl font-bold text-cyan-400 font-mono" data-testid="report-active-traders">
                    {weeklyReport.active_traders}<span className="text-xs text-zinc-500 font-normal">/{weeklyReport.total_members}</span>
                  </p>
                </div>
              </div>

              {/* Top Performer */}
              {weeklyReport.top_performer && (
                <div className="flex items-center gap-3 p-3 rounded-lg bg-amber-500/[0.06] border border-amber-500/15" data-testid="report-top-performer">
                  <Trophy className="w-5 h-5 text-amber-400 shrink-0" />
                  <div>
                    <p className="text-xs text-zinc-500">Top Performer</p>
                    <p className="text-sm font-semibold text-white">{weeklyReport.top_performer.name}</p>
                  </div>
                  <div className="ml-auto text-right">
                    <p className="text-sm font-bold text-emerald-400 font-mono">${weeklyReport.top_performer.profit?.toLocaleString()}</p>
                    <p className="text-[10px] text-zinc-500">{weeklyReport.top_performer.trades} trades</p>
                  </div>
                </div>
              )}

              {/* Member Breakdown */}
              {weeklyReport.member_breakdown?.length > 0 && (
                <div>
                  <p className="text-xs text-zinc-500 mb-2 uppercase tracking-wider">Member Breakdown</p>
                  <div className="space-y-1.5">
                    {weeklyReport.member_breakdown.map((m, i) => (
                      <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.01] hover:bg-white/[0.03] transition-colors" data-testid={`report-member-${i}`}>
                        <span className="text-xs text-zinc-600 w-4 font-mono">{i + 1}.</span>
                        <span className="text-sm text-white flex-1 truncate">{m.name}</span>
                        <span className="text-xs text-zinc-400 font-mono">{m.trades} trades</span>
                        <span className="text-xs text-zinc-400 font-mono">{m.win_rate}% WR</span>
                        <span className={`text-xs font-mono font-semibold ${m.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          ${m.profit?.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Recommendations */}
      {showRecs && (
        <Card className="glass-card border-amber-500/20" data-testid="ai-recommendations-panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-400" /> AI Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recsLoading ? (
              <div className="flex items-center justify-center py-6">
                <Bot className="w-5 h-5 text-amber-400 animate-pulse mr-2" />
                <span className="text-sm text-zinc-400">Analyzing team activity...</span>
              </div>
            ) : recommendations.length === 0 ? (
              <p className="text-sm text-zinc-500 py-4 text-center">No recommendations at this time.</p>
            ) : (
              <div className="space-y-2.5">
                {recommendations.map((rec, i) => (
                  <div key={i} className={`p-3 rounded-lg border ${URGENCY_COLORS[rec.urgency] || URGENCY_COLORS.medium}`} data-testid={`recommendation-${i}`}>
                    {rec.type === 'all_clear' ? (
                      <p className="text-sm text-emerald-400">{rec.message}</p>
                    ) : (
                      <>
                        <div className="flex items-center gap-2 mb-1">
                          {rec.member && <span className="text-xs font-semibold text-white">{rec.member}</span>}
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full uppercase tracking-wider font-semibold ${rec.urgency === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>{rec.urgency}</span>
                        </div>
                        <p className="text-xs text-zinc-300 leading-relaxed">{rec.suggestion}</p>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Team Members */}
      {team.length === 0 ? (
        <Card className="glass-card">
          <CardContent className="py-16 text-center">
            <Users className="w-12 h-12 mx-auto mb-3 text-zinc-600" />
            <p className="text-zinc-400">No team members yet</p>
            <p className="text-sm text-zinc-500 mt-1">Share your invite link above to grow your team</p>
          </CardContent>
        </Card>
      ) : (
        <Card className="glass-card">
          <CardHeader className="pb-2"><CardTitle className="text-white text-base">Team Members</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/[0.04]">
              {team.map(m => (
                <div key={m.id} className="px-4 py-3 flex items-center gap-3 hover:bg-white/[0.02] transition-colors" data-testid={`team-member-${m.id}`}>
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${
                    m.status === 'danger' ? 'bg-amber-500/20 text-amber-400' :
                    m.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                    m.status === 'suspended' ? 'bg-red-500/20 text-red-400' :
                    'bg-zinc-700 text-zinc-400'
                  }`}>{m.name?.charAt(0)?.toUpperCase() || '?'}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white truncate">{m.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full border capitalize ${STATUS_COLORS[m.status] || STATUS_COLORS.inactive}`}>{m.status}</span>
                      {m.fraud_warnings > 0 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 flex items-center gap-0.5"><Shield className="w-2.5 h-2.5" /> {m.fraud_warnings}</span>
                      )}
                    </div>
                    <p className="text-[11px] text-zinc-500">{m.email}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="flex items-center gap-1 text-xs text-zinc-400">
                      <TrendingUp className="w-3 h-3" /> {m.recent_trades} trade{m.recent_trades !== 1 ? 's' : ''}/wk
                    </div>
                    {m.habits_today > 0 && (
                      <div className="flex items-center gap-1 text-[10px] text-emerald-400 mt-0.5 justify-end"><Flame className="w-3 h-3" /> {m.habits_today} habit{m.habits_today !== 1 ? 's' : ''}</div>
                    )}
                    {m.last_trade && (
                      <p className="text-[10px] text-zinc-600 mt-0.5 flex items-center gap-1 justify-end"><Clock className="w-2.5 h-2.5" /> {new Date(m.last_trade).toLocaleDateString()}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TeamPage;
