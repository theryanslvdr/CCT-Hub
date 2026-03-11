import React, { useState, useEffect, useCallback } from 'react';
import { referralAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, AlertTriangle, TrendingUp, UserPlus, Activity, Clock, Shield, Flame, Bot, Lightbulb, RefreshCw } from 'lucide-react';
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

const TeamPage = () => {
  const [team, setTeam] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, in_danger: 0, new_this_week: 0 });
  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [showRecs, setShowRecs] = useState(false);

  const loadTeam = useCallback(async () => {
    try {
      const res = await referralAPI.getMyTeam();
      setTeam(res.data.team || []);
      setStats(res.data.stats || {});
    } catch {
      toast.error('Failed to load team data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTeam(); }, [loadTeam]);

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
          <p className="text-sm text-zinc-400 mt-1">Members you've invited and their activity</p>
        </div>
        {stats.in_danger > 0 && (
          <Button
            variant="outline"
            size="sm"
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

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="glass-card" data-testid="team-stat-total">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/15 flex items-center justify-center">
                <Users className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white font-mono">{stats.total}</p>
                <p className="text-[11px] text-zinc-500">Total Members</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card" data-testid="team-stat-active">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/15 flex items-center justify-center">
                <Activity className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-emerald-400 font-mono">{stats.active}</p>
                <p className="text-[11px] text-zinc-500">Active This Week</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card" data-testid="team-stat-danger">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/15 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-amber-400 font-mono">{stats.in_danger}</p>
                <p className="text-[11px] text-zinc-500">In Danger</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-card" data-testid="team-stat-new">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/15 flex items-center justify-center">
                <UserPlus className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-cyan-400 font-mono">{stats.new_this_week}</p>
                <p className="text-[11px] text-zinc-500">New This Week</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Recommendations Panel */}
      {showRecs && (
        <Card className="glass-card border-amber-500/20" data-testid="ai-recommendations-panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-400" /> AI Recommendations
              <span className="text-xs text-zinc-500 font-normal ml-1">Personalized suggestions for your team</span>
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
                  <div
                    key={i}
                    className={`p-3 rounded-lg border ${URGENCY_COLORS[rec.urgency] || URGENCY_COLORS.medium}`}
                    data-testid={`recommendation-${i}`}
                  >
                    {rec.type === 'all_clear' ? (
                      <p className="text-sm text-emerald-400">{rec.message}</p>
                    ) : (
                      <>
                        <div className="flex items-center gap-2 mb-1">
                          {rec.member && <span className="text-xs font-semibold text-white">{rec.member}</span>}
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full uppercase tracking-wider font-semibold ${
                            rec.urgency === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                          }`}>{rec.urgency}</span>
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

      {/* Team Members List */}
      {team.length === 0 ? (
        <Card className="glass-card">
          <CardContent className="py-16 text-center">
            <Users className="w-12 h-12 mx-auto mb-3 text-zinc-600" />
            <p className="text-zinc-400">No team members yet</p>
            <p className="text-sm text-zinc-500 mt-1">Share your referral code to grow your team</p>
          </CardContent>
        </Card>
      ) : (
        <Card className="glass-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base">Team Members</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-white/[0.04]">
              {team.map(m => (
                <div key={m.id} className="px-4 py-3 flex items-center gap-3 hover:bg-white/[0.02] transition-colors" data-testid={`team-member-${m.id}`}>
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${
                    m.status === 'danger' ? 'bg-amber-500/20 text-amber-400' :
                    m.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                    m.status === 'suspended' ? 'bg-red-500/20 text-red-400' :
                    'bg-zinc-700 text-zinc-400'
                  }`}>
                    {m.name?.charAt(0)?.toUpperCase() || '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white truncate">{m.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full border capitalize ${STATUS_COLORS[m.status] || STATUS_COLORS.inactive}`}>
                        {m.status}
                      </span>
                      {m.fraud_warnings > 0 && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 flex items-center gap-0.5">
                          <Shield className="w-2.5 h-2.5" /> {m.fraud_warnings} warning{m.fraud_warnings > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-zinc-500">{m.email}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="flex items-center gap-1 text-xs text-zinc-400">
                      <TrendingUp className="w-3 h-3" />
                      <span>{m.recent_trades} trade{m.recent_trades !== 1 ? 's' : ''} this week</span>
                    </div>
                    {m.habits_today > 0 && (
                      <div className="flex items-center gap-1 text-[10px] text-emerald-400 mt-0.5 justify-end">
                        <Flame className="w-3 h-3" /> {m.habits_today} habit{m.habits_today !== 1 ? 's' : ''} today
                      </div>
                    )}
                    {m.last_trade && (
                      <p className="text-[10px] text-zinc-600 mt-0.5 flex items-center gap-1 justify-end">
                        <Clock className="w-2.5 h-2.5" />
                        Last: {new Date(m.last_trade).toLocaleDateString()}
                      </p>
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
