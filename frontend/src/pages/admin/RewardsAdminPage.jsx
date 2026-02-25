import React, { useState, useEffect, useRef, useCallback } from 'react';
import { rewardsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  Search, Zap, Star, Trophy, Award, Clock, User, TrendingUp, Shield,
  Plus, Minus, Filter, ChevronLeft, ChevronRight, Edit2, Save, X, Loader2
} from 'lucide-react';

const SOURCE_LABELS = {
  signup_verify: 'Sign Up & Verify',
  first_trade: 'First Trade Bonus',
  trade: 'Trade',
  deposit: 'Deposit',
  withdrawal: 'Withdrawal',
  qualified_referral: 'Referral',
  streak_5_day: '5-Day Streak',
  streak_10_day: '10-Day Streak',
  streak_20_day: '20-Day Streak',
  milestone_10_trade: '10-Trade Milestone',
  milestone_20_trade_streak: 'Trade Milestone',
  milestone_50_trade: '50-Trade Milestone',
  milestone_100_trade: '100-Trade Milestone',
  join_community: 'Join Community',
  first_daily_win: 'Daily Win',
  help_chat: 'Help Chat',
  manual_bonus: 'Bonus',
  manual_promo: 'Promotion',
  system_check_credit: 'System Test',
  system_check_restore: 'System Test',
  redeem: 'Redemption',
  admin_adjustment_credit: 'Admin Credit',
  admin_adjustment_deduct: 'Admin Deduction',
};

const ACTIONS = [
  { value: 'test_trade', label: 'Simulate Trade', desc: 'Award first-trade bonus (25 pts) or streak/milestone points' },
  { value: 'test_deposit', label: 'Simulate Deposit', desc: 'Award deposit points (50 pts per $50)' },
  { value: 'test_referral', label: 'Simulate Referral', desc: 'Award qualified referral bonus (150 pts)' },
  { value: 'manual_bonus', label: 'Manual Bonus', desc: 'Award custom number of points' },
];

const HISTORY_PER_PAGE = 20;

function UserSearchInput({ onUserSelect, selectedUser }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = useCallback(async (q) => {
    if (!q || q.length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    setSearching(true);
    try {
      const res = await rewardsAPI.adminSearchUsers(q);
      setResults(res.data?.users || []);
      setShowDropdown(true);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => handleSearch(val), 300);
  };

  const handleSelect = (user) => {
    setQuery(user.full_name || user.email);
    setShowDropdown(false);
    onUserSelect(user);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <Input
            placeholder="Search by name or email..."
            value={query}
            onChange={handleInputChange}
            onFocus={() => results.length > 0 && setShowDropdown(true)}
            className="bg-zinc-900 border-zinc-700 text-white pl-9"
            data-testid="user-search-input"
          />
          {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-zinc-500" />}
        </div>
      </div>

      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl max-h-60 overflow-y-auto" data-testid="user-search-dropdown">
          {results.map((user) => (
            <button
              key={user.id}
              onClick={() => handleSelect(user)}
              className="w-full px-3 py-2.5 text-left hover:bg-zinc-800 transition-colors flex items-center gap-3 border-b border-zinc-800/50 last:border-0"
              data-testid={`user-option-${user.id}`}
            >
              <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-zinc-500" />
              </div>
              <div className="min-w-0">
                <p className="text-sm text-white font-medium truncate">{user.full_name}</p>
                <p className="text-xs text-zinc-500 truncate">{user.email}</p>
              </div>
              <span className="ml-auto text-[10px] text-zinc-600 uppercase">{user.role?.replace('_', ' ')}</span>
            </button>
          ))}
        </div>
      )}

      {showDropdown && results.length === 0 && query.length >= 2 && !searching && (
        <div className="absolute z-50 w-full mt-1 bg-zinc-900 border border-zinc-700 rounded-lg p-3 text-sm text-zinc-500 text-center">
          No users found
        </div>
      )}

      {selectedUser && (
        <div className="mt-2 px-3 py-2 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center gap-2">
          <User className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-blue-300 font-medium">{selectedUser.full_name}</span>
          <span className="text-xs text-blue-400/60">{selectedUser.email}</span>
          <button onClick={() => { onUserSelect(null); setQuery(''); }} className="ml-auto text-zinc-500 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}

export default function RewardsAdminPage() {
  // User lookup state
  const [selectedUser, setSelectedUser] = useState(null);
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);

  // Simulate state
  const [simAction, setSimAction] = useState('test_trade');
  const [simPoints, setSimPoints] = useState(100);
  const [simAmount, setSimAmount] = useState(100);
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  // Manual adjustment state
  const [adjPoints, setAdjPoints] = useState(0);
  const [adjReason, setAdjReason] = useState('');
  const [adjIsDeduction, setAdjIsDeduction] = useState(false);
  const [adjLoading, setAdjLoading] = useState(false);

  // History filter/pagination
  const [historyFilter, setHistoryFilter] = useState('all');
  const [historyPage, setHistoryPage] = useState(1);

  // Badge management
  const [badges, setBadges] = useState([]);
  const [editingBadge, setEditingBadge] = useState(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [badgesLoading, setBadgesLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('lookup'); // lookup, badges

  useEffect(() => {
    loadBadges();
  }, []);

  const loadBadges = async () => {
    try {
      const res = await rewardsAPI.adminGetBadges();
      setBadges(res.data?.badges || []);
    } catch (e) {
      console.error('Failed to load badges:', e);
    } finally {
      setBadgesLoading(false);
    }
  };

  const handleUserSelect = async (user) => {
    setSelectedUser(user);
    setLookupResult(null);
    setSimResult(null);
    setHistoryPage(1);
    setHistoryFilter('all');

    if (!user) return;

    setLookupLoading(true);
    try {
      const res = await rewardsAPI.adminLookup({ user_id: user.id });
      setLookupResult(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load user rewards');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleSimulate = async () => {
    if (!selectedUser) { toast.error('Search for a user first'); return; }
    setSimLoading(true);
    setSimResult(null);
    try {
      const body = {
        user_id: selectedUser.id,
        action_type: simAction,
        ...(simAction === 'manual_bonus' ? { points: simPoints } : {}),
        ...(simAction === 'test_deposit' ? { amount_usdt: simAmount } : {}),
      };
      const res = await rewardsAPI.adminSimulate(body);
      setSimResult(res.data);
      toast.success(res.data.action || 'Simulation complete');
      // Refresh lookup
      const refreshRes = await rewardsAPI.adminLookup({ user_id: selectedUser.id });
      setLookupResult(refreshRes.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Simulation failed');
    } finally {
      setSimLoading(false);
    }
  };

  const handleAdjustPoints = async () => {
    if (!selectedUser) { toast.error('Search for a user first'); return; }
    if (!adjPoints || adjPoints <= 0) { toast.error('Enter a valid points amount'); return; }
    if (!adjReason.trim()) { toast.error('Please provide a reason for the adjustment'); return; }

    setAdjLoading(true);
    try {
      await rewardsAPI.adminAdjustPoints({
        user_id: selectedUser.id,
        points: adjPoints,
        reason: adjReason,
        is_deduction: adjIsDeduction,
      });
      toast.success(`${adjIsDeduction ? 'Deducted' : 'Credited'} ${adjPoints} points`);
      setAdjPoints(0);
      setAdjReason('');
      // Refresh
      const refreshRes = await rewardsAPI.adminLookup({ user_id: selectedUser.id });
      setLookupResult(refreshRes.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Adjustment failed');
    } finally {
      setAdjLoading(false);
    }
  };

  const handleBadgeSave = async (badgeId) => {
    try {
      await rewardsAPI.adminUpdateBadge(badgeId, { name: editName, description: editDesc });
      toast.success('Badge updated');
      setEditingBadge(null);
      loadBadges();
    } catch (err) {
      toast.error('Failed to update badge');
    }
  };

  const handleBadgeToggle = async (badge) => {
    try {
      await rewardsAPI.adminUpdateBadge(badge.id, { is_active: !badge.is_active });
      toast.success(`Badge ${badge.is_active ? 'disabled' : 'enabled'}`);
      loadBadges();
    } catch (err) {
      toast.error('Failed to toggle badge');
    }
  };

  // Filtered & paginated history
  const filteredHistory = (lookupResult?.history || []).filter(row => {
    if (historyFilter === 'all') return true;
    if (historyFilter === 'earn') return (row.points || 0) > 0;
    if (historyFilter === 'spend') return (row.points || 0) < 0;
    if (historyFilter === 'admin') return row.metadata?.admin_test || row.metadata?.admin_adjustment || row.source?.includes('admin_adjustment');
    return true;
  });
  const historyTotalPages = Math.ceil(filteredHistory.length / HISTORY_PER_PAGE);
  const paginatedHistory = filteredHistory.slice(
    (historyPage - 1) * HISTORY_PER_PAGE,
    historyPage * HISTORY_PER_PAGE
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto" data-testid="rewards-admin-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Rewards Admin</h1>
          <p className="text-sm text-zinc-400 mt-1">Manage user rewards, simulate actions, and customize badges</p>
        </div>
        <div className="flex gap-2 bg-zinc-900 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('lookup')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'lookup' ? 'bg-blue-500 text-white' : 'text-zinc-400 hover:text-white'
            }`}
            data-testid="tab-lookup"
          >
            <User className="w-4 h-4 inline mr-1" /> User Lookup
          </button>
          <button
            onClick={() => setActiveTab('badges')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'badges' ? 'bg-purple-500 text-white' : 'text-zinc-400 hover:text-white'
            }`}
            data-testid="tab-badges"
          >
            <Shield className="w-4 h-4 inline mr-1" /> Badge Management
          </button>
        </div>
      </div>

      {activeTab === 'lookup' && (
        <>
          {/* User Search */}
          <Card className="glass-card" data-testid="rewards-lookup-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-400" /> User Rewards Lookup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <UserSearchInput onUserSelect={handleUserSelect} selectedUser={selectedUser} />

              {lookupLoading && (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                </div>
              )}

              {lookupResult && !lookupLoading && (
                <div className="mt-4 space-y-3" data-testid="lookup-result">
                  <div className="p-4 rounded-lg bg-zinc-800/60 border border-zinc-700/50">
                    <div className="flex items-center gap-2 mb-3">
                      <User className="w-4 h-4 text-zinc-400" />
                      <span className="text-white font-medium">{lookupResult.full_name}</span>
                      <span className="text-zinc-500 text-xs">{lookupResult.email}</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      <div className="p-2 rounded bg-zinc-900/50">
                        <div className="flex items-center gap-1.5 text-amber-400 mb-1">
                          <Star className="w-3.5 h-3.5" />
                          <span className="text-zinc-400">Lifetime Points</span>
                        </div>
                        <span className="text-white font-mono font-bold text-sm">{(lookupResult.lifetime_points || 0).toLocaleString()}</span>
                      </div>
                      <div className="p-2 rounded bg-zinc-900/50">
                        <div className="flex items-center gap-1.5 text-emerald-400 mb-1">
                          <TrendingUp className="w-3.5 h-3.5" />
                          <span className="text-zinc-400">USDT Value</span>
                        </div>
                        <span className="text-white font-mono text-sm">${(lookupResult.estimated_usdt || 0).toFixed(2)}</span>
                      </div>
                      <div className="p-2 rounded bg-zinc-900/50">
                        <div className="flex items-center gap-1.5 text-purple-400 mb-1">
                          <Award className="w-3.5 h-3.5" />
                          <span className="text-zinc-400">Level</span>
                        </div>
                        <span className="text-white text-sm">{lookupResult.level}</span>
                      </div>
                      <div className="p-2 rounded bg-zinc-900/50">
                        <div className="flex items-center gap-1.5 text-cyan-400 mb-1">
                          <Trophy className="w-3.5 h-3.5" />
                          <span className="text-zinc-400">Monthly Rank</span>
                        </div>
                        <span className="text-white font-mono text-sm">#{lookupResult.current_rank || '--'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Tools row - only show when user is selected */}
          {selectedUser && lookupResult && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Simulate Points */}
              <Card className="glass-card" data-testid="simulate-points-card">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2 text-base">
                    <Zap className="w-5 h-5 text-amber-400" /> Simulate Points
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
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

                  {simResult && (
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20" data-testid="simulate-result">
                      <p className="text-sm text-emerald-300 font-medium">{simResult.action}</p>
                      <div className="flex gap-4 mt-1 text-xs text-zinc-300">
                        <span>Points: <span className="font-mono font-bold text-white">{simResult.new_lifetime_points?.toLocaleString()}</span></span>
                        <span>Level: <span className="text-white">{simResult.level}</span></span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Manual Point Adjustment */}
              <Card className="glass-card" data-testid="adjust-points-card">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2 text-base">
                    <Star className="w-5 h-5 text-blue-400" /> Manual Adjustment
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAdjIsDeduction(false)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
                        !adjIsDeduction ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-zinc-900 text-zinc-400 border border-zinc-800'
                      }`}
                      data-testid="adj-credit-btn"
                    >
                      <Plus className="w-4 h-4" /> Credit
                    </button>
                    <button
                      onClick={() => setAdjIsDeduction(true)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
                        adjIsDeduction ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-zinc-900 text-zinc-400 border border-zinc-800'
                      }`}
                      data-testid="adj-deduct-btn"
                    >
                      <Minus className="w-4 h-4" /> Deduct
                    </button>
                  </div>
                  <div>
                    <label className="text-xs text-zinc-400 block mb-1">Points</label>
                    <Input type="number" value={adjPoints} onChange={(e) => setAdjPoints(Number(e.target.value))}
                      className="bg-zinc-900 border-zinc-700 text-white" min={1} data-testid="adj-points-input" />
                  </div>
                  <div>
                    <label className="text-xs text-zinc-400 block mb-1">Reason (required for audit trail)</label>
                    <Input value={adjReason} onChange={(e) => setAdjReason(e.target.value)}
                      placeholder="e.g., Compensation for system error"
                      className="bg-zinc-900 border-zinc-700 text-white" data-testid="adj-reason-input" />
                  </div>
                  <Button onClick={handleAdjustPoints} disabled={adjLoading || !adjReason.trim() || !adjPoints}
                    className={`w-full ${adjIsDeduction ? 'bg-red-600 hover:bg-red-500' : 'bg-emerald-600 hover:bg-emerald-500'} text-white`}
                    data-testid="adj-submit-btn">
                    {adjLoading ? 'Processing...' : `${adjIsDeduction ? 'Deduct' : 'Credit'} ${adjPoints} Points`}
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Points History for looked-up user */}
          {lookupResult?.history?.length > 0 && (
            <Card className="glass-card" data-testid="admin-history-card">
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Clock className="w-5 h-5 text-zinc-400" /> Transaction History
                  </CardTitle>
                  <div className="flex gap-1.5 flex-wrap">
                    {[
                      { value: 'all', label: 'All' },
                      { value: 'earn', label: 'Earned' },
                      { value: 'spend', label: 'Spent' },
                      { value: 'admin', label: 'Admin Actions' },
                    ].map(f => (
                      <button
                        key={f.value}
                        onClick={() => { setHistoryFilter(f.value); setHistoryPage(1); }}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          historyFilter === f.value
                            ? 'bg-blue-500 text-white'
                            : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                        }`}
                        data-testid={`history-filter-${f.value}`}
                      >
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                  <table className="w-full text-sm" data-testid="admin-history-table">
                    <thead className="sticky top-0 bg-zinc-900">
                      <tr className="border-b border-zinc-800">
                        <th className="text-left py-2 px-3 text-zinc-400 font-medium">Date</th>
                        <th className="text-left py-2 px-3 text-zinc-400 font-medium">Type</th>
                        <th className="text-left py-2 px-3 text-zinc-400 font-medium">Source</th>
                        <th className="text-left py-2 px-3 text-zinc-400 font-medium">Details</th>
                        <th className="text-right py-2 px-3 text-zinc-400 font-medium">Points</th>
                        <th className="text-right py-2 px-3 text-zinc-400 font-medium">Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedHistory.map((row, i) => {
                        const pts = row.points || 0;
                        const isEarn = pts > 0;
                        const isAdminAction = row.metadata?.admin_test || row.metadata?.admin_adjustment;
                        const reason = row.metadata?.reason;
                        return (
                          <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
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
                              {isAdminAction && <span className="ml-1 text-amber-400 text-[10px]">(Admin)</span>}
                            </td>
                            <td className="py-2 px-3 text-zinc-500 text-xs max-w-[200px] truncate">
                              {reason || (row.metadata?.amount_usdt ? `$${row.metadata.amount_usdt}` : '')}
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

                {historyTotalPages > 1 && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                    <p className="text-xs text-zinc-500">
                      {filteredHistory.length} transactions
                    </p>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={() => setHistoryPage(p => Math.max(1, p - 1))} disabled={historyPage === 1} className="h-8 w-8 p-0">
                        <ChevronLeft className="w-4 h-4" />
                      </Button>
                      <span className="text-sm text-zinc-400">Page {historyPage}/{historyTotalPages}</span>
                      <Button variant="outline" size="sm" onClick={() => setHistoryPage(p => Math.min(historyTotalPages, p + 1))} disabled={historyPage === historyTotalPages} className="h-8 w-8 p-0">
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {activeTab === 'badges' && (
        <Card className="glass-card" data-testid="badge-management-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-purple-400" /> Badge Definitions
              <span className="text-xs text-zinc-500 font-normal ml-2">{badges.length} badges</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {badgesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 animate-spin text-zinc-500" />
              </div>
            ) : (
              <div className="space-y-2">
                {badges.map(badge => (
                  <div
                    key={badge.id}
                    className={`p-3 rounded-lg border ${badge.is_active ? 'bg-zinc-800/50 border-zinc-700' : 'bg-zinc-900/30 border-zinc-800 opacity-60'} flex items-center gap-4`}
                    data-testid={`badge-def-${badge.id}`}
                  >
                    {editingBadge === badge.id ? (
                      <div className="flex-1 flex items-center gap-3">
                        <Input value={editName} onChange={(e) => setEditName(e.target.value)}
                          className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm flex-1" placeholder="Badge name" />
                        <Input value={editDesc} onChange={(e) => setEditDesc(e.target.value)}
                          className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm flex-[2]" placeholder="Description" />
                        <Button size="sm" className="h-8 bg-emerald-600" onClick={() => handleBadgeSave(badge.id)}>
                          <Save className="w-3.5 h-3.5" />
                        </Button>
                        <Button size="sm" variant="outline" className="h-8" onClick={() => setEditingBadge(null)}>
                          <X className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <div className="w-10 h-10 rounded-lg bg-zinc-900 flex items-center justify-center flex-shrink-0">
                          <Award className="w-5 h-5 text-amber-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white font-medium">{badge.name}</p>
                          <p className="text-xs text-zinc-500">{badge.description}</p>
                          <div className="flex gap-2 mt-1">
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400">{badge.category}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400">{badge.condition_type}: {badge.condition_value}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Button size="sm" variant="outline" className="h-7 text-xs"
                            onClick={() => { setEditingBadge(badge.id); setEditName(badge.name); setEditDesc(badge.description); }}
                            data-testid={`edit-badge-${badge.id}`}>
                            <Edit2 className="w-3 h-3 mr-1" /> Edit
                          </Button>
                          <Button size="sm" variant="outline"
                            className={`h-7 text-xs ${badge.is_active ? 'text-red-400 border-red-500/30' : 'text-emerald-400 border-emerald-500/30'}`}
                            onClick={() => handleBadgeToggle(badge)}
                            data-testid={`toggle-badge-${badge.id}`}>
                            {badge.is_active ? 'Disable' : 'Enable'}
                          </Button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
