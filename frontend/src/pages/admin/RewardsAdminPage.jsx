import React, { useState } from 'react';
import { rewardsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Search, Zap, Star, Trophy, Award, Clock, User, TrendingUp } from 'lucide-react';

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

const ACTIONS = [
  { value: 'test_trade', label: 'Simulate Trade', desc: 'Award first-trade bonus (25 pts) or streak/milestone points' },
  { value: 'test_deposit', label: 'Simulate Deposit', desc: 'Award deposit points (50 pts per $50)' },
  { value: 'test_referral', label: 'Simulate Referral', desc: 'Award qualified referral bonus (150 pts)' },
  { value: 'manual_bonus', label: 'Manual Bonus', desc: 'Award custom number of points' },
];

export default function RewardsAdminPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);

  const [simUserId, setSimUserId] = useState('');
  const [simAction, setSimAction] = useState('test_trade');
  const [simPoints, setSimPoints] = useState(100);
  const [simAmount, setSimAmount] = useState(100);
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  const handleLookup = async () => {
    if (!searchQuery.trim()) return;
    setLookupLoading(true);
    setLookupResult(null);
    try {
      const isEmail = searchQuery.includes('@');
      const params = isEmail ? { email: searchQuery.trim() } : { user_id: searchQuery.trim() };
      const res = await rewardsAPI.adminLookup(params);
      setLookupResult(res.data);
      setSimUserId(res.data.user_id);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'User not found');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleSimulate = async () => {
    if (!simUserId) { toast.error('Search for a user first'); return; }
    setSimLoading(true);
    setSimResult(null);
    try {
      const body = {
        user_id: simUserId,
        action_type: simAction,
        ...(simAction === 'manual_bonus' ? { points: simPoints } : {}),
        ...(simAction === 'test_deposit' ? { amount_usdt: simAmount } : {}),
      };
      const res = await rewardsAPI.adminSimulate(body);
      setSimResult(res.data);
      toast.success(res.data.action || 'Simulation complete');
      // Refresh lookup
      if (lookupResult) {
        const refreshRes = await rewardsAPI.adminLookup({ user_id: simUserId });
        setLookupResult(refreshRes.data);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Simulation failed');
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto" data-testid="rewards-admin-page">
      <div>
        <h1 className="text-2xl font-bold text-white">Rewards Admin</h1>
        <p className="text-sm text-zinc-400 mt-1">Look up user rewards and simulate point actions</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Rewards Lookup */}
        <Card className="glass-card" data-testid="rewards-lookup-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Search className="w-5 h-5 text-blue-400" /> User Rewards Lookup
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Email or user ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
                className="bg-zinc-900 border-zinc-700 text-white"
                data-testid="lookup-input"
              />
              <Button onClick={handleLookup} disabled={lookupLoading} className="bg-blue-600 hover:bg-blue-500" data-testid="lookup-btn">
                {lookupLoading ? '...' : 'Search'}
              </Button>
            </div>

            {lookupResult && (
              <div className="space-y-3" data-testid="lookup-result">
                <div className="p-3 rounded-lg bg-zinc-800/60 border border-zinc-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    <User className="w-4 h-4 text-zinc-400" />
                    <span className="text-white font-medium">{lookupResult.full_name}</span>
                    <span className="text-zinc-500 text-xs">{lookupResult.email}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center gap-1.5">
                      <Star className="w-3.5 h-3.5 text-amber-400" />
                      <span className="text-zinc-400">Points:</span>
                      <span className="text-white font-mono font-bold">{(lookupResult.lifetime_points || 0).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-zinc-400">USDT:</span>
                      <span className="text-white font-mono">${(lookupResult.estimated_usdt || 0).toFixed(2)}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5 text-purple-400" />
                      <span className="text-zinc-400">Level:</span>
                      <span className="text-white">{lookupResult.level}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Trophy className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="text-zinc-400">Rank:</span>
                      <span className="text-white font-mono">#{lookupResult.current_rank || '--'}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-zinc-400">Monthly:</span>
                      <span className="text-white font-mono">{(lookupResult.monthly_points || 0).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-zinc-400">Trades:</span>
                      <span className="text-white font-mono">{lookupResult.lifetime_trades || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Simulate Points */}
        <Card className="glass-card" data-testid="simulate-points-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" /> Simulate Points
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!simUserId ? (
              <p className="text-zinc-500 text-sm py-4">Search for a user first to simulate points.</p>
            ) : (
              <>
                <p className="text-xs text-zinc-400">
                  Simulating for: <span className="text-white font-medium">{lookupResult?.full_name || simUserId}</span>
                </p>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-zinc-400 block mb-1">Action Type</label>
                    <select
                      value={simAction}
                      onChange={(e) => setSimAction(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm"
                      data-testid="simulate-action-select"
                    >
                      {ACTIONS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                    </select>
                    <p className="text-[10px] text-zinc-500 mt-1">{ACTIONS.find(a => a.value === simAction)?.desc}</p>
                  </div>

                  {simAction === 'manual_bonus' && (
                    <div>
                      <label className="text-xs text-zinc-400 block mb-1">Points</label>
                      <Input type="number" value={simPoints} onChange={(e) => setSimPoints(Number(e.target.value))}
                        className="bg-zinc-900 border-zinc-700 text-white" data-testid="simulate-points-input" />
                    </div>
                  )}
                  {simAction === 'test_deposit' && (
                    <div>
                      <label className="text-xs text-zinc-400 block mb-1">Amount (USDT)</label>
                      <Input type="number" value={simAmount} onChange={(e) => setSimAmount(Number(e.target.value))}
                        className="bg-zinc-900 border-zinc-700 text-white" data-testid="simulate-amount-input" />
                    </div>
                  )}

                  <Button onClick={handleSimulate} disabled={simLoading}
                    className="w-full bg-amber-600 hover:bg-amber-500 text-white" data-testid="simulate-btn">
                    <Zap className="w-4 h-4 mr-2" />
                    {simLoading ? 'Processing...' : 'Run Simulation'}
                  </Button>
                </div>

                {simResult && (
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20" data-testid="simulate-result">
                    <p className="text-sm text-emerald-300 font-medium">{simResult.action}</p>
                    <div className="flex gap-4 mt-1 text-xs text-zinc-300">
                      <span>Points: <span className="font-mono font-bold text-white">{simResult.new_lifetime_points?.toLocaleString()}</span></span>
                      <span>Level: <span className="text-white">{simResult.level}</span></span>
                      <span>Rank: <span className="font-mono text-white">#{simResult.current_rank || '--'}</span></span>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Points History for looked-up user */}
      {lookupResult?.history?.length > 0 && (
        <Card className="glass-card" data-testid="admin-history-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-zinc-400" /> Points History — {lookupResult.full_name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
              <table className="w-full text-sm" data-testid="admin-history-table">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr className="border-b border-zinc-800">
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium">Date</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium">Type</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium">Source</th>
                    <th className="text-right py-2 px-3 text-zinc-400 font-medium">Points</th>
                    <th className="text-right py-2 px-3 text-zinc-400 font-medium">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {lookupResult.history.map((row, i) => {
                    const pts = row.points || 0;
                    const isEarn = pts > 0;
                    const isAdminTest = row.metadata?.admin_test;
                    return (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                        <td className="py-2 px-3 text-zinc-300 font-mono text-xs whitespace-nowrap">
                          {row.created_at ? new Date(row.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '--'}
                        </td>
                        <td className="py-2 px-3">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${isEarn ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                            {isEarn ? 'Earn' : 'Spend'}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-zinc-300 text-xs">
                          {SOURCE_LABELS[row.source] || row.source}
                          {isAdminTest && <span className="ml-1 text-amber-400 text-[10px]">(Admin Test)</span>}
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
          </CardContent>
        </Card>
      )}
    </div>
  );
}
