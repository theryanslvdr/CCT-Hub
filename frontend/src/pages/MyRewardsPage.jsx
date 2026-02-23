import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { rewardsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Star, Trophy, TrendingUp, ArrowUpRight, Gift, Clock, Zap, Award, ExternalLink } from 'lucide-react';

const LEVEL_COLORS = {
  'Newbie': { bg: 'from-zinc-500/20 to-zinc-600/10', border: 'border-zinc-500/30', text: 'text-zinc-300', badge: 'bg-zinc-700' },
  'Trader': { bg: 'from-blue-500/20 to-blue-600/10', border: 'border-blue-500/30', text: 'text-blue-300', badge: 'bg-blue-900' },
  'Investor': { bg: 'from-emerald-500/20 to-emerald-600/10', border: 'border-emerald-500/30', text: 'text-emerald-300', badge: 'bg-emerald-900' },
  'Connector': { bg: 'from-purple-500/20 to-purple-600/10', border: 'border-purple-500/30', text: 'text-purple-300', badge: 'bg-purple-900' },
  'Trade Novice': { bg: 'from-cyan-500/20 to-cyan-600/10', border: 'border-cyan-500/30', text: 'text-cyan-300', badge: 'bg-cyan-900' },
  'Amateur Trader': { bg: 'from-teal-500/20 to-teal-600/10', border: 'border-teal-500/30', text: 'text-teal-300', badge: 'bg-teal-900' },
  'Seasoned Trader': { bg: 'from-orange-500/20 to-orange-600/10', border: 'border-orange-500/30', text: 'text-orange-300', badge: 'bg-orange-900' },
  'Pro Trader': { bg: 'from-amber-500/20 to-amber-600/10', border: 'border-amber-500/30', text: 'text-amber-300', badge: 'bg-amber-900' },
  'Elite': { bg: 'from-yellow-500/20 to-yellow-600/10', border: 'border-yellow-500/30', text: 'text-yellow-300', badge: 'bg-yellow-900' },
};

const SOURCE_LABELS = {
  signup_verify: 'Sign Up & Verify',
  first_trade: 'First Trade Bonus',
  deposit: 'Deposit',
  withdrawal: 'Withdrawal',
  qualified_referral: 'Referral',
  streak_5_day: '5-Day Streak',
  milestone_10_trade: '10-Trade Milestone',
  milestone_20_trade_streak: 'Trade Milestone',
  join_community: 'Join Community',
  first_daily_win: 'Daily Win',
  help_chat: 'Help Chat',
  manual_bonus: 'Bonus',
  manual_promo: 'Promotion',
  system_check_credit: 'System Test',
  system_check_restore: 'System Test',
  redeem: 'Redemption',
};

export default function MyRewardsPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!user?.id) return;
    try {
      const [sumRes, lbRes, histRes] = await Promise.allSettled([
        rewardsAPI.getSummary(user.id),
        rewardsAPI.getLeaderboard(user.id),
        rewardsAPI.getHistory(null, 200),
      ]);
      if (sumRes.status === 'fulfilled') setSummary(sumRes.value.data);
      if (lbRes.status === 'fulfilled') setLeaderboard(lbRes.value.data);
      if (histRes.status === 'fulfilled') setHistory(histRes.value.data?.history || []);
    } catch (e) {
      console.error('Failed to load rewards:', e);
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  useEffect(() => { loadData(); }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-blue-500" />
      </div>
    );
  }

  const levelStyle = LEVEL_COLORS[summary?.level] || LEVEL_COLORS['Newbie'];

  return (
    <div className="space-y-6 max-w-5xl mx-auto" data-testid="my-rewards-page">
      <div>
        <h1 className="text-2xl font-bold text-white">My Rewards</h1>
        <p className="text-sm text-zinc-400 mt-1">Track your points, level, and rank</p>
      </div>

      {/* Top stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Points balance */}
        <Card className="glass-card" data-testid="rewards-points-card">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">Points Balance</p>
                <p className="text-3xl font-bold font-mono text-white mt-1">
                  {(summary?.lifetime_points || 0).toLocaleString()}
                </p>
                <p className="text-sm text-emerald-400 mt-1 font-mono">
                  ~ ${(summary?.estimated_usdt || 0).toFixed(2)} USDT
                </p>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/10">
                <Star className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Level */}
        <Card className="glass-card" data-testid="rewards-level-card">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">Level</p>
                <div className="mt-2">
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${levelStyle.badge} ${levelStyle.text}`}>
                    {summary?.level || 'Newbie'}
                  </span>
                </div>
                <p className="text-xs text-zinc-500 mt-2">Keep trading & depositing to level up</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-500/10">
                <Award className="w-6 h-6 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Rank */}
        <Card className="glass-card" data-testid="rewards-rank-card">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">Monthly Rank</p>
                <p className="text-3xl font-bold font-mono text-white mt-1">
                  {leaderboard?.current_rank ? `#${leaderboard.current_rank}` : '--'}
                </p>
                {leaderboard?.distance_to_next > 0 && (
                  <p className="text-xs text-cyan-400 mt-1">
                    {leaderboard.distance_to_next} pts to pass {leaderboard.next_user_name}
                  </p>
                )}
              </div>
              <div className="p-3 rounded-xl bg-cyan-500/10">
                <Trophy className="w-6 h-6 text-cyan-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Motivational message */}
      {leaderboard?.suggested_message && (
        <div className="px-4 py-3 rounded-lg bg-blue-500/10 border border-blue-500/20" data-testid="rewards-message">
          <p className="text-sm text-blue-300 flex items-center gap-2">
            <Zap className="w-4 h-4 flex-shrink-0" />
            {leaderboard.suggested_message}
          </p>
        </div>
      )}

      {/* CTA */}
      <a
        href={`https://rewards.crosscur.rent/?user_id=${user?.id}`}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-semibold transition-all"
        data-testid="open-rewards-store-btn"
      >
        <Gift className="w-5 h-5" />
        Open Rewards & Store
        <ExternalLink className="w-4 h-4 ml-1" />
      </a>
      <p className="text-xs text-zinc-500 text-center -mt-4">
        Redeem points for USDT vouchers and items at rewards.crosscur.rent
      </p>

      {/* Points History */}
      <Card className="glass-card" data-testid="rewards-history-card">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-zinc-400" /> Points History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <div className="text-center py-10 text-zinc-500">
              <TrendingUp className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p>No points activity yet.</p>
              <p className="text-xs mt-1">Start trading or depositing to earn your first points!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="rewards-history-table">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium">Date</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium">Type</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium">Source</th>
                    <th className="text-right py-2 px-3 text-zinc-400 font-medium">Points</th>
                    <th className="text-right py-2 px-3 text-zinc-400 font-medium">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((row, i) => {
                    const pts = row.points || 0;
                    const isEarn = pts > 0;
                    const isAdmin = row.metadata?.admin_test;
                    return (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30" data-testid={`history-row-${i}`}>
                        <td className="py-2 px-3 text-zinc-300 font-mono text-xs whitespace-nowrap">
                          {row.created_at ? new Date(row.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : '--'}
                        </td>
                        <td className="py-2 px-3">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${isEarn ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                            {isEarn ? 'Earn' : 'Spend'}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-zinc-300 text-xs">
                          {SOURCE_LABELS[row.source] || row.source}
                          {isAdmin && <span className="ml-1 text-amber-400 text-[10px]">(Admin)</span>}
                        </td>
                        <td className={`py-2 px-3 text-right font-mono text-xs font-semibold ${isEarn ? 'text-emerald-400' : 'text-red-400'}`}>
                          {isEarn ? '+' : ''}{pts.toLocaleString()}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-xs text-zinc-300">
                          {(row.balance_after ?? 0).toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
