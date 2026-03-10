import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { rewardsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Trophy, Medal, Award, Crown, TrendingUp, Calendar, Loader2, User,
  ArrowUp, ArrowDown, Minus, Star, ChevronLeft, ChevronRight
} from 'lucide-react';

const LEVEL_COLORS = {
  'Newbie': 'text-zinc-400',
  'Trader': 'text-orange-400',
  'Trade Novice': 'text-cyan-400',
  'Amateur Trader': 'text-teal-400',
  'Seasoned Trader': 'text-orange-400',
  'Pro Trader': 'text-amber-400',
  'Elite': 'text-yellow-400',
  'Legend': 'text-purple-400',
};

const RANK_STYLES = {
  1: { icon: Crown, bg: 'bg-gradient-to-r from-yellow-500/20 to-amber-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400' },
  2: { icon: Medal, bg: 'bg-gradient-to-r from-zinc-400/20 to-zinc-500/20', border: 'border-zinc-400/50', text: 'text-zinc-300' },
  3: { icon: Award, bg: 'bg-gradient-to-r from-orange-600/20 to-orange-700/20', border: 'border-orange-600/50', text: 'text-orange-400' },
};

export default function LeaderboardPage() {
  const { user } = useAuth();
  const [leaderboard, setLeaderboard] = useState([]);
  const [userRank, setUserRank] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('monthly'); // monthly, alltime
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [lbRes, userRes] = await Promise.allSettled([
        rewardsAPI.getFullLeaderboard(period, 100),
        user?.id ? rewardsAPI.getLeaderboard(user.id) : Promise.resolve({ data: null }),
      ]);
      
      if (lbRes.status === 'fulfilled') {
        setLeaderboard(lbRes.value.data?.leaderboard || []);
      }
      if (userRes.status === 'fulfilled' && userRes.value.data) {
        setUserRank(userRes.value.data);
      }
    } catch (e) {
      console.error('Failed to load leaderboard:', e);
    } finally {
      setLoading(false);
    }
  }, [period, user?.id]);

  useEffect(() => { loadData(); }, [loadData]);

  const totalPages = Math.ceil(leaderboard.length / itemsPerPage);
  const paginatedLeaderboard = leaderboard.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Get top 3 for podium
  const topThree = leaderboard.slice(0, 3);
  const restOfLeaderboard = paginatedLeaderboard.filter(u => u.rank > 3);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto" data-testid="leaderboard-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Trophy className="w-6 h-6 text-amber-400" /> Leaderboard
          </h1>
          <p className="text-sm text-zinc-400 mt-1">See who's earning the most points</p>
        </div>
        
        {/* Period Toggle */}
        <div className="flex gap-2 bg-[#0d0d0d] p-1 rounded-lg">
          <button
            onClick={() => { setPeriod('monthly'); setCurrentPage(1); }}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              period === 'monthly' 
                ? 'bg-orange-500 text-white' 
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <Calendar className="w-4 h-4 inline mr-1" /> This Month
          </button>
          <button
            onClick={() => { setPeriod('alltime'); setCurrentPage(1); }}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              period === 'alltime' 
                ? 'bg-purple-500 text-white' 
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <Star className="w-4 h-4 inline mr-1" /> All Time
          </button>
        </div>
      </div>

      {/* Your Rank Card */}
      {userRank && userRank.current_rank > 0 && (
        <Card className="glass-card border-orange-500/20" data-testid="your-rank-card">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-orange-500/10 flex items-center justify-center">
                  <span className="text-xl font-bold text-orange-400">#{userRank.current_rank}</span>
                </div>
                <div>
                  <p className="text-white font-medium">Your Position</p>
                  <p className="text-sm text-zinc-400">
                    {userRank.monthly_points?.toLocaleString() || 0} points this month
                  </p>
                </div>
              </div>
              {userRank.distance_to_next > 0 && (
                <div className="text-right">
                  <p className="text-xs text-zinc-500">To reach #{userRank.current_rank - 1}</p>
                  <p className="text-cyan-400 font-mono">+{userRank.distance_to_next} pts</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top 3 Podium */}
      {topThree.length > 0 && currentPage === 1 && (
        <div className="grid grid-cols-3 gap-4 mb-6" data-testid="podium">
          {/* Second Place */}
          <div className="order-1 self-end">
            {topThree[1] && (
              <div className={`p-4 rounded-xl ${RANK_STYLES[2].bg} border ${RANK_STYLES[2].border} text-center`}>
                <Medal className={`w-8 h-8 mx-auto mb-2 ${RANK_STYLES[2].text}`} />
                <p className="text-lg font-bold text-white truncate">{topThree[1].display_name || 'Anonymous'}</p>
                <p className={`text-xs ${LEVEL_COLORS[topThree[1].level] || 'text-zinc-400'}`}>{topThree[1].level}</p>
                <p className="text-xl font-mono text-white mt-2">{topThree[1].points?.toLocaleString()}</p>
                <p className="text-xs text-zinc-500">points</p>
              </div>
            )}
          </div>
          
          {/* First Place */}
          <div className="order-2">
            {topThree[0] && (
              <div className={`p-6 rounded-xl ${RANK_STYLES[1].bg} border-2 ${RANK_STYLES[1].border} text-center transform scale-105`}>
                <Crown className={`w-10 h-10 mx-auto mb-2 ${RANK_STYLES[1].text}`} />
                <p className="text-xl font-bold text-white truncate">{topThree[0].display_name || 'Anonymous'}</p>
                <p className={`text-sm ${LEVEL_COLORS[topThree[0].level] || 'text-zinc-400'}`}>{topThree[0].level}</p>
                <p className="text-2xl font-mono text-yellow-400 mt-2">{topThree[0].points?.toLocaleString()}</p>
                <p className="text-xs text-zinc-500">points</p>
              </div>
            )}
          </div>
          
          {/* Third Place */}
          <div className="order-3 self-end">
            {topThree[2] && (
              <div className={`p-4 rounded-xl ${RANK_STYLES[3].bg} border ${RANK_STYLES[3].border} text-center`}>
                <Award className={`w-8 h-8 mx-auto mb-2 ${RANK_STYLES[3].text}`} />
                <p className="text-lg font-bold text-white truncate">{topThree[2].display_name || 'Anonymous'}</p>
                <p className={`text-xs ${LEVEL_COLORS[topThree[2].level] || 'text-zinc-400'}`}>{topThree[2].level}</p>
                <p className="text-xl font-mono text-white mt-2">{topThree[2].points?.toLocaleString()}</p>
                <p className="text-xs text-zinc-500">points</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Full Leaderboard Table */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white text-lg">
            {period === 'monthly' ? 'Monthly Rankings' : 'All-Time Rankings'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {leaderboard.length === 0 ? (
            <div className="text-center py-10 text-zinc-500">
              <Trophy className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p>No rankings yet for this period.</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.06]">
                      <th className="text-left py-3 px-3 text-zinc-400 font-medium w-16">Rank</th>
                      <th className="text-left py-3 px-3 text-zinc-400 font-medium">User</th>
                      <th className="text-center py-3 px-3 text-zinc-400 font-medium">Level</th>
                      <th className="text-right py-3 px-3 text-zinc-400 font-medium">Points</th>
                      <th className="text-right py-3 px-3 text-zinc-400 font-medium w-20">Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(currentPage === 1 ? paginatedLeaderboard : paginatedLeaderboard).map((entry, i) => {
                      const isCurrentUser = entry.user_id === user?.id;
                      const RankStyle = RANK_STYLES[entry.rank];
                      
                      return (
                        <tr 
                          key={entry.user_id || i} 
                          className={`border-b border-white/[0.06]/50 ${isCurrentUser ? 'bg-orange-500/10' : 'hover:bg-white/[0.03]'}`}
                          data-testid={`leaderboard-row-${entry.rank}`}
                        >
                          <td className="py-3 px-3">
                            {RankStyle ? (
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${RankStyle.bg} ${RankStyle.border} border`}>
                                <RankStyle.icon className={`w-4 h-4 ${RankStyle.text}`} />
                              </div>
                            ) : (
                              <span className="text-zinc-400 font-mono">#{entry.rank}</span>
                            )}
                          </td>
                          <td className="py-3 px-3">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 rounded-full bg-[#1a1a1a] flex items-center justify-center">
                                <User className="w-4 h-4 text-zinc-500" />
                              </div>
                              <div>
                                <p className={`font-medium ${isCurrentUser ? 'text-orange-400' : 'text-white'}`}>
                                  {entry.display_name || 'Anonymous'}
                                  {isCurrentUser && <span className="ml-2 text-xs text-orange-400">(You)</span>}
                                </p>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <span className={`text-xs font-medium ${LEVEL_COLORS[entry.level] || 'text-zinc-400'}`}>
                              {entry.level || 'Newbie'}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            <span className="font-mono font-semibold text-white">
                              {entry.points?.toLocaleString() || 0}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            {entry.rank_change > 0 && (
                              <span className="text-emerald-400 flex items-center justify-end gap-1">
                                <ArrowUp className="w-3 h-3" />
                                {entry.rank_change}
                              </span>
                            )}
                            {entry.rank_change < 0 && (
                              <span className="text-red-400 flex items-center justify-end gap-1">
                                <ArrowDown className="w-3 h-3" />
                                {Math.abs(entry.rank_change)}
                              </span>
                            )}
                            {(!entry.rank_change || entry.rank_change === 0) && (
                              <span className="text-zinc-500">
                                <Minus className="w-3 h-3 mx-auto" />
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/[0.06]">
                  <p className="text-xs text-zinc-500">
                    Showing {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, leaderboard.length)} of {leaderboard.length}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="h-8 w-8 p-0"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="text-sm text-zinc-400">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="h-8 w-8 p-0"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
