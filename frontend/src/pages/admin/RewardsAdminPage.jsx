import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { rewardsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  Search, User, Star, Award, Shield, TrendingUp, Zap,
  Loader2, X, Plus, Minus, Clock, ChevronLeft, ChevronRight,
  Edit2, Save, Download, BarChart3, Users, Trophy, Target,
  AlertTriangle, Flame, Snowflake, ArrowUpDown, Eye, EyeOff
} from 'lucide-react';

const HISTORY_PER_PAGE = 15;

const SOURCE_LABELS = {
  first_trade: 'First Trade',
  trade: 'Trade Logged',
  deposit: 'Deposit',
  withdrawal: 'Withdrawal',
  streak_freeze_purchase: 'Streak Freeze',
  admin_adjustment_credit: 'Admin Credit',
  admin_adjustment_deduct: 'Admin Deduct',
  referral: 'Referral',
  manual_bonus: 'Manual Bonus',
  forum_best_answer: 'Forum Best Answer',
  forum_active_collaborator: 'Forum Collaborator',
  earning_action: 'Earning Action',
};

const ACTIONS = [
  { value: 'test_trade', label: 'Simulate Trade', desc: 'Awards standard trade points' },
  { value: 'test_deposit', label: 'Simulate Deposit', desc: 'Awards deposit bonus points' },
  { value: 'manual_bonus', label: 'Manual Bonus', desc: 'Award custom points amount' },
];

// ─── User Search Component ───
function UserSearchInput({ onUserSelect, selectedUser }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setShowDropdown(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = useCallback(async (q) => {
    if (!q || q.length < 2) { setResults([]); setShowDropdown(false); return; }
    setSearching(true);
    try {
      const res = await rewardsAPI.adminSearchUsers(q);
      setResults(res.data?.users || []);
      setShowDropdown(true);
    } catch { setResults([]); } finally { setSearching(false); }
  }, []);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => handleSearch(val), 300);
  };

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
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
      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
          {results.map((user) => (
            <button
              key={user.id}
              onClick={() => { setQuery(user.full_name || user.email); setShowDropdown(false); onUserSelect(user); }}
              className="w-full px-3 py-2.5 text-left hover:bg-zinc-800 transition-colors flex items-center gap-3 border-b border-zinc-800/50 last:border-0"
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
      {selectedUser && (
        <div className="mt-2 px-3 py-2 rounded-lg bg-orange-500/10 border border-orange-500/15 flex items-center gap-2">
          <User className="w-4 h-4 text-orange-400" />
          <span className="text-sm text-orange-300 font-medium">{selectedUser.full_name}</span>
          <span className="text-xs text-orange-400/60">{selectedUser.email}</span>
          <button onClick={() => { onUserSelect(null); setQuery(''); }} className="ml-auto text-zinc-500 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Overview Tab ───
function OverviewTab() {
  const [overview, setOverview] = useState(null);
  const [members, setMembers] = useState([]);
  const [membersTotal, setMembersTotal] = useState(0);
  const [membersPage, setMembersPage] = useState(1);
  const [membersSearch, setMembersSearch] = useState('');
  const [sortBy, setSortBy] = useState('lifetime_points');
  const [sortDir, setSortDir] = useState('desc');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [valuesHidden, setValuesHidden] = useState(false);

  useEffect(() => {
    rewardsAPI.adminGetOverview().then(r => setOverview(r.data)).catch(() => {});
  }, []);

  const loadMembers = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page: membersPage, page_size: 20, sort_by: sortBy, sort_dir: sortDir };
      if (membersSearch.trim()) params.search = membersSearch.trim();
      const res = await rewardsAPI.adminListMembers(params);
      setMembers(res.data.members || []);
      setMembersTotal(res.data.total || 0);
    } catch { toast.error('Failed to load members'); }
    finally { setLoading(false); }
  }, [membersPage, membersSearch, sortBy, sortDir]);

  useEffect(() => { loadMembers(); }, [loadMembers]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await rewardsAPI.adminExportCsv();
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = 'rewards_export.csv'; a.click();
      URL.revokeObjectURL(url);
      toast.success('CSV exported!');
    } catch { toast.error('Export failed'); }
    finally { setExporting(false); }
  };

  const toggleSort = (field) => {
    if (sortBy === field) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortBy(field); setSortDir('desc'); }
    setMembersPage(1);
  };

  const totalPages = Math.ceil(membersTotal / 20);
  const maskValue = (v) => valuesHidden ? '***' : v;

  return (
    <div className="space-y-5">
      {/* Summary Cards */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {[
            { label: 'Members', value: overview.total_members, icon: Users, color: 'text-orange-400' },
            { label: 'In Circulation', value: maskValue(overview.points_in_circulation?.toLocaleString()), icon: TrendingUp, color: 'text-emerald-400' },
            { label: 'Total Spent', value: maskValue(overview.total_spent_points?.toLocaleString()), icon: Target, color: 'text-amber-400' },
            { label: 'Avg / Member', value: maskValue(overview.avg_points_per_member?.toLocaleString()), icon: BarChart3, color: 'text-cyan-400' },
            { label: 'Badges Awarded', value: overview.total_badges_awarded, icon: Award, color: 'text-purple-400' },
          ].map(c => (
            <div key={c.label} className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800">
              <div className="flex items-center gap-1.5 mb-1">
                <c.icon className={`w-3.5 h-3.5 ${c.color}`} />
                <span className="text-[10px] text-zinc-500 uppercase">{c.label}</span>
              </div>
              <p className="text-xl font-bold text-white">{c.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Members Table Header */}
      <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <Input
            placeholder="Search members..."
            value={membersSearch}
            onChange={e => { setMembersSearch(e.target.value); setMembersPage(1); }}
            className="pl-9 input-dark"
            data-testid="members-search"
          />
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => setValuesHidden(!valuesHidden)} className="btn-secondary gap-1.5" data-testid="toggle-hide-values">
            {valuesHidden ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            {valuesHidden ? 'Show' : 'Hide'}
          </Button>
          <Button size="sm" onClick={handleExport} disabled={exporting} className="gap-1.5 bg-emerald-600 hover:bg-emerald-700" data-testid="export-csv-btn">
            {exporting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />} Export CSV
          </Button>
        </div>
      </div>

      {/* Members Table */}
      <div className="overflow-x-auto rounded-lg border border-zinc-800">
        <table className="w-full text-sm" data-testid="members-table">
          <thead className="bg-zinc-900/80">
            <tr className="border-b border-zinc-800">
              {[
                { key: 'name', label: 'Member' },
                { key: 'lifetime_points', label: 'Lifetime' },
                { key: 'balance', label: 'Balance' },
                { key: 'level', label: 'Level' },
                { key: 'badges_count', label: 'Badges' },
                { key: 'best_trade_streak', label: 'Best Streak' },
                { key: 'streak_freezes', label: 'Freezes' },
              ].map(col => (
                <th
                  key={col.key}
                  className="text-left py-2.5 px-3 text-zinc-400 font-medium text-xs cursor-pointer hover:text-white transition-colors"
                  onClick={() => toggleSort(col.key)}
                >
                  <span className="flex items-center gap-1">
                    {col.label}
                    {sortBy === col.key && <ArrowUpDown className="w-3 h-3 text-orange-400" />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="py-8 text-center"><Loader2 className="w-5 h-5 animate-spin mx-auto text-zinc-500" /></td></tr>
            ) : members.length === 0 ? (
              <tr><td colSpan={7} className="py-8 text-center text-zinc-500 text-sm">No members found</td></tr>
            ) : members.map(m => (
              <tr key={m.user_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30" data-testid={`member-row-${m.user_id}`}>
                <td className="py-2 px-3">
                  <p className="text-white text-xs font-medium truncate max-w-[150px]">{m.name}</p>
                  <p className="text-[10px] text-zinc-500 truncate max-w-[150px]">{m.email}</p>
                </td>
                <td className="py-2 px-3 text-xs font-mono text-amber-400">{maskValue(m.lifetime_points?.toLocaleString())}</td>
                <td className="py-2 px-3 text-xs font-mono text-emerald-400">{maskValue(m.balance?.toLocaleString())}</td>
                <td className="py-2 px-3 text-xs text-zinc-300">{m.level}</td>
                <td className="py-2 px-3 text-xs text-purple-400">{m.badges_count}</td>
                <td className="py-2 px-3 text-xs text-cyan-400">{m.best_trade_streak}</td>
                <td className="py-2 px-3 text-xs text-orange-400">{m.streak_freezes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-500">{membersTotal} total members</span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={membersPage <= 1} onClick={() => setMembersPage(p => p - 1)} className="btn-secondary h-8 w-8 p-0">
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-xs text-zinc-400">Page {membersPage}/{totalPages}</span>
            <Button variant="outline" size="sm" disabled={membersPage >= totalPages} onClick={() => setMembersPage(p => p + 1)} className="btn-secondary h-8 w-8 p-0">
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Audit Trail Tab ───
function AuditTrailTab() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await rewardsAPI.adminAuditTrail({ page, page_size: 50 });
      setLogs(res.data.logs || []);
      setTotal(res.data.total || 0);
    } catch { toast.error('Failed to load audit trail'); }
    finally { setLoading(false); }
  }, [page]);

  useEffect(() => { loadLogs(); }, [loadLogs]);
  const totalPages = Math.ceil(total / 50);

  return (
    <Card className="glass-card" data-testid="audit-trail-card">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Clock className="w-5 h-5 text-amber-400" /> Admin Audit Trail
          <span className="text-xs text-zinc-500 font-normal ml-2">{total} entries</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-zinc-500" /></div>
        ) : logs.length === 0 ? (
          <p className="text-center text-zinc-500 py-8 text-sm">No admin adjustments recorded yet</p>
        ) : (
          <>
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-zinc-900">
                  <tr className="border-b border-zinc-800">
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Date</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Admin</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Member</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Action</th>
                    <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Reason</th>
                    <th className="text-right py-2 px-3 text-zinc-400 font-medium text-xs">Points</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, i) => {
                    const pts = log.points || 0;
                    const isCredit = pts > 0;
                    return (
                      <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                        <td className="py-2 px-3 text-zinc-300 font-mono text-xs whitespace-nowrap">
                          {log.created_at ? new Date(log.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '--'}
                        </td>
                        <td className="py-2 px-3 text-xs text-amber-400">{log.metadata?.adjusted_by_name || 'Admin'}</td>
                        <td className="py-2 px-3 text-xs text-zinc-300">{log.target_name || log.user_id?.slice(0, 8)}</td>
                        <td className="py-2 px-3">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                            log.metadata?.reset ? 'bg-red-500/15 text-red-400'
                            : isCredit ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'
                          }`}>
                            {log.metadata?.reset ? 'Reset' : isCredit ? 'Credit' : 'Deduct'}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-xs text-zinc-500 max-w-[200px] truncate">{log.metadata?.reason || '--'}</td>
                        <td className={`py-2 px-3 text-right font-mono text-xs font-semibold ${isCredit ? 'text-emerald-400' : 'text-red-400'}`}>
                          {isCredit ? '+' : ''}{pts.toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t border-zinc-800">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="btn-secondary h-8 w-8 p-0">
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-xs text-zinc-400">Page {page}/{totalPages}</span>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="btn-secondary h-8 w-8 p-0">
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Main Page ───
export default function RewardsAdminPage() {
  const { user } = useAuth();
  const isMasterAdmin = user?.role === 'master_admin';
  const [activeTab, setActiveTab] = useState('overview');

  // User Lookup state
  const [selectedUser, setSelectedUser] = useState(null);
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);

  // Simulate
  const [simAction, setSimAction] = useState('test_trade');
  const [simPoints, setSimPoints] = useState(100);
  const [simAmount, setSimAmount] = useState(100);
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  // Manual adjustment
  const [adjPoints, setAdjPoints] = useState(0);
  const [adjReason, setAdjReason] = useState('');
  const [adjIsDeduction, setAdjIsDeduction] = useState(false);
  const [adjLoading, setAdjLoading] = useState(false);

  // History
  const [historyFilter, setHistoryFilter] = useState('all');
  const [historyPage, setHistoryPage] = useState(1);

  // Badge management
  const [badges, setBadges] = useState([]);
  const [editingBadge, setEditingBadge] = useState(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [badgesLoading, setBadgesLoading] = useState(true);

  // Override dialogs
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetReason, setResetReason] = useState('');
  const [resetting, setResetting] = useState(false);
  const [badgeDialogOpen, setBadgeDialogOpen] = useState(false);
  const [freezeDialogOpen, setFreezeDialogOpen] = useState(false);
  const [freezeType, setFreezeType] = useState('trade');
  const [freezeAction, setFreezeAction] = useState('add');
  const [freezeCount, setFreezeCount] = useState(1);
  const [freezeLoading, setFreezeLoading] = useState(false);

  useEffect(() => { loadBadges(); }, []);

  const loadBadges = async () => {
    try {
      const res = await rewardsAPI.adminGetBadges();
      setBadges(res.data?.badges || []);
    } catch {} finally { setBadgesLoading(false); }
  };

  const handleUserSelect = async (u) => {
    setSelectedUser(u);
    setLookupResult(null);
    setSimResult(null);
    setHistoryPage(1);
    setHistoryFilter('all');
    if (!u) return;
    setLookupLoading(true);
    try {
      const res = await rewardsAPI.adminLookup({ user_id: u.id });
      setLookupResult(res.data);
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to load'); }
    finally { setLookupLoading(false); }
  };

  const refreshLookup = async () => {
    if (!selectedUser) return;
    const res = await rewardsAPI.adminLookup({ user_id: selectedUser.id });
    setLookupResult(res.data);
  };

  const handleSimulate = async () => {
    if (!selectedUser) return;
    setSimLoading(true); setSimResult(null);
    try {
      const body = { user_id: selectedUser.id, action_type: simAction, ...(simAction === 'manual_bonus' ? { points: simPoints } : {}), ...(simAction === 'test_deposit' ? { amount_usdt: simAmount } : {}) };
      const res = await rewardsAPI.adminSimulate(body);
      setSimResult(res.data);
      toast.success(res.data.action || 'Simulation complete');
      refreshLookup();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSimLoading(false); }
  };

  const handleAdjustPoints = async () => {
    if (!selectedUser || !adjPoints || !adjReason.trim()) return;
    setAdjLoading(true);
    try {
      await rewardsAPI.adminAdjustPoints({ user_id: selectedUser.id, points: adjPoints, reason: adjReason, is_deduction: adjIsDeduction });
      toast.success(`${adjIsDeduction ? 'Deducted' : 'Credited'} ${adjPoints} points`);
      setAdjPoints(0); setAdjReason('');
      refreshLookup();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setAdjLoading(false); }
  };

  const handleResetPoints = async () => {
    if (!selectedUser || !resetReason.trim()) return;
    setResetting(true);
    try {
      await rewardsAPI.adminResetPoints({ user_id: selectedUser.id, reason: resetReason });
      toast.success('Points reset to zero');
      setResetDialogOpen(false); setResetReason('');
      refreshLookup();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setResetting(false); }
  };

  const handleAwardBadge = async (badgeId) => {
    if (!selectedUser) return;
    try {
      await rewardsAPI.adminAwardBadge({ user_id: selectedUser.id, badge_id: badgeId });
      toast.success('Badge awarded');
      refreshLookup();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
  };

  const handleRevokeBadge = async (badgeId) => {
    if (!selectedUser) return;
    try {
      await rewardsAPI.adminRevokeBadge({ user_id: selectedUser.id, badge_id: badgeId });
      toast.success('Badge revoked');
      refreshLookup();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
  };

  const handleEditFreeze = async () => {
    if (!selectedUser) return;
    setFreezeLoading(true);
    try {
      await rewardsAPI.adminEditStreakFreezes({ user_id: selectedUser.id, freeze_type: freezeType, action: freezeAction, count: freezeCount });
      toast.success(`${freezeAction === 'add' ? 'Added' : 'Removed'} ${freezeCount} ${freezeType} freeze(s)`);
      setFreezeDialogOpen(false); setFreezeCount(1);
      refreshLookup();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setFreezeLoading(false); }
  };

  const handleBadgeSave = async (badgeId) => {
    try {
      await rewardsAPI.adminUpdateBadge(badgeId, { name: editName, description: editDesc });
      toast.success('Badge updated');
      setEditingBadge(null); loadBadges();
    } catch { toast.error('Failed to update'); }
  };

  const handleBadgeToggle = async (badge) => {
    try {
      await rewardsAPI.adminUpdateBadge(badge.id, { is_active: !badge.is_active });
      toast.success(`Badge ${badge.is_active ? 'disabled' : 'enabled'}`);
      loadBadges();
    } catch { toast.error('Failed'); }
  };

  const filteredHistory = (lookupResult?.history || []).filter(row => {
    if (historyFilter === 'all') return true;
    if (historyFilter === 'earn') return (row.points || 0) > 0;
    if (historyFilter === 'spend') return (row.points || 0) < 0;
    if (historyFilter === 'admin') return row.source?.includes('admin_adjustment');
    return true;
  });
  const historyTotalPages = Math.ceil(filteredHistory.length / HISTORY_PER_PAGE);
  const paginatedHistory = filteredHistory.slice((historyPage - 1) * HISTORY_PER_PAGE, historyPage * HISTORY_PER_PAGE);

  // Get user's badge IDs
  const userBadgeIds = (lookupResult?.badges || []).map(b => b.badge_id);

  const tabs = [
    { key: 'overview', label: 'Overview', icon: BarChart3 },
    { key: 'lookup', label: 'User Lookup', icon: User },
    { key: 'audit', label: 'Audit Trail', icon: Clock },
    { key: 'badges', label: 'Badges', icon: Shield },
  ];

  return (
    <div className="space-y-5 pb-20 md:pb-6 max-w-6xl mx-auto" data-testid="rewards-admin-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white flex items-center gap-2">
            <Star className="w-5 h-5 md:w-6 md:h-6 text-amber-400" /> Rewards Admin
          </h1>
          <p className="text-sm text-zinc-500 mt-0.5">Bird's eye view of member points, badges & overrides</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-zinc-900 p-1 rounded-lg overflow-x-auto">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === t.key ? 'bg-orange-500 text-white' : 'text-zinc-400 hover:text-white'
            }`}
            data-testid={`tab-${t.key}`}
          >
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && <OverviewTab />}

      {/* Audit Trail Tab */}
      {activeTab === 'audit' && <AuditTrailTab />}

      {/* User Lookup Tab */}
      {activeTab === 'lookup' && (
        <>
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2"><Search className="w-5 h-5 text-orange-400" /> User Rewards Lookup</CardTitle>
            </CardHeader>
            <CardContent>
              <UserSearchInput onUserSelect={handleUserSelect} selectedUser={selectedUser} />
              {lookupLoading && <div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-orange-500" /></div>}
              {lookupResult && !lookupLoading && (
                <div className="mt-4 space-y-3" data-testid="lookup-result">
                  <div className="p-4 rounded-lg bg-zinc-800/60 border border-zinc-700/50">
                    <div className="flex items-center gap-2 mb-3">
                      <User className="w-4 h-4 text-zinc-400" />
                      <span className="text-white font-medium">{lookupResult.full_name}</span>
                      <span className="text-zinc-500 text-xs">{lookupResult.email}</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      {[
                        { label: 'Lifetime Points', value: (lookupResult.lifetime_points || 0).toLocaleString(), icon: Star, color: 'text-amber-400' },
                        { label: 'USDT Value', value: `$${(lookupResult.estimated_usdt || 0).toFixed(2)}`, icon: TrendingUp, color: 'text-emerald-400' },
                        { label: 'Level', value: lookupResult.level, icon: Award, color: 'text-purple-400' },
                        { label: 'Monthly Rank', value: `#${lookupResult.current_rank || '--'}`, icon: Trophy, color: 'text-cyan-400' },
                      ].map(c => (
                        <div key={c.label} className="p-2 rounded bg-zinc-900/50">
                          <div className="flex items-center gap-1.5 mb-1">
                            <c.icon className={`w-3.5 h-3.5 ${c.color}`} /><span className="text-zinc-400">{c.label}</span>
                          </div>
                          <span className="text-white font-mono font-bold text-sm">{c.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Override controls - Master Admin only */}
                  {isMasterAdmin && (
                    <div className="flex flex-wrap gap-2 p-3 rounded-lg bg-red-500/5 border border-red-500/20">
                      <span className="text-xs text-red-400 font-medium flex items-center gap-1 w-full mb-1"><AlertTriangle className="w-3 h-3" /> Master Admin Overrides</span>
                      <Button size="sm" onClick={() => setResetDialogOpen(true)} className="gap-1 bg-red-600 hover:bg-red-700 text-xs h-7" data-testid="reset-points-btn">
                        <AlertTriangle className="w-3 h-3" /> Reset Points
                      </Button>
                      <Button size="sm" onClick={() => setBadgeDialogOpen(true)} className="gap-1 bg-purple-600 hover:bg-purple-700 text-xs h-7" data-testid="manage-badges-btn">
                        <Award className="w-3 h-3" /> Award/Revoke Badge
                      </Button>
                      <Button size="sm" onClick={() => setFreezeDialogOpen(true)} className="gap-1 bg-orange-600 hover:bg-orange-700 text-xs h-7" data-testid="manage-freezes-btn">
                        <Snowflake className="w-3 h-3" /> Edit Freezes
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Tools row */}
          {selectedUser && lookupResult && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Simulate */}
              <Card className="glass-card">
                <CardHeader><CardTitle className="text-white flex items-center gap-2 text-base"><Zap className="w-5 h-5 text-amber-400" /> Simulate Points</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-xs text-zinc-400 block mb-1">Action Type</label>
                    <select value={simAction} onChange={(e) => setSimAction(e.target.value)} className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm">
                      {ACTIONS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                    </select>
                  </div>
                  {simAction === 'manual_bonus' && (
                    <div><label className="text-xs text-zinc-400 block mb-1">Points</label><Input type="number" value={simPoints} onChange={(e) => setSimPoints(Number(e.target.value))} className="bg-zinc-900 border-zinc-700 text-white" /></div>
                  )}
                  {simAction === 'test_deposit' && (
                    <div><label className="text-xs text-zinc-400 block mb-1">Amount (USDT)</label><Input type="number" value={simAmount} onChange={(e) => setSimAmount(Number(e.target.value))} className="bg-zinc-900 border-zinc-700 text-white" /></div>
                  )}
                  <Button onClick={handleSimulate} disabled={simLoading} className="w-full bg-amber-600 hover:bg-amber-500"><Zap className="w-4 h-4 mr-2" />{simLoading ? 'Processing...' : 'Run Simulation'}</Button>
                  {simResult && (
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                      <p className="text-sm text-emerald-300 font-medium">{simResult.action}</p>
                      <div className="flex gap-4 mt-1 text-xs text-zinc-300">
                        <span>Points: <span className="font-mono font-bold text-white">{simResult.new_lifetime_points?.toLocaleString()}</span></span>
                        <span>Level: <span className="text-white">{simResult.level}</span></span>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Manual Adjustment */}
              <Card className="glass-card">
                <CardHeader><CardTitle className="text-white flex items-center gap-2 text-base"><Star className="w-5 h-5 text-orange-400" /> Manual Adjustment</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <button onClick={() => setAdjIsDeduction(false)} className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 ${!adjIsDeduction ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-zinc-900 text-zinc-400 border border-zinc-800'}`} data-testid="adj-credit-btn">
                      <Plus className="w-4 h-4" /> Credit
                    </button>
                    <button onClick={() => setAdjIsDeduction(true)} className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 ${adjIsDeduction ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-zinc-900 text-zinc-400 border border-zinc-800'}`} data-testid="adj-deduct-btn">
                      <Minus className="w-4 h-4" /> Deduct
                    </button>
                  </div>
                  <div><label className="text-xs text-zinc-400 block mb-1">Points</label><Input type="number" value={adjPoints} onChange={(e) => setAdjPoints(Number(e.target.value))} className="bg-zinc-900 border-zinc-700 text-white" min={1} data-testid="adj-points-input" /></div>
                  <div><label className="text-xs text-zinc-400 block mb-1">Reason (required for audit trail)</label><Input value={adjReason} onChange={(e) => setAdjReason(e.target.value)} placeholder="e.g., Compensation for system error" className="bg-zinc-900 border-zinc-700 text-white" data-testid="adj-reason-input" /></div>
                  <Button onClick={handleAdjustPoints} disabled={adjLoading || !adjReason.trim() || !adjPoints} className={`w-full ${adjIsDeduction ? 'bg-red-600 hover:bg-red-500' : 'bg-emerald-600 hover:bg-emerald-500'}`} data-testid="adj-submit-btn">
                    {adjLoading ? 'Processing...' : `${adjIsDeduction ? 'Deduct' : 'Credit'} ${adjPoints} Points`}
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Transaction History */}
          {lookupResult?.history?.length > 0 && (
            <Card className="glass-card">
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <CardTitle className="text-white flex items-center gap-2"><Clock className="w-5 h-5 text-zinc-400" /> Transaction History</CardTitle>
                  <div className="flex gap-1.5 flex-wrap">
                    {[{ value: 'all', label: 'All' }, { value: 'earn', label: 'Earned' }, { value: 'spend', label: 'Spent' }, { value: 'admin', label: 'Admin' }].map(f => (
                      <button key={f.value} onClick={() => { setHistoryFilter(f.value); setHistoryPage(1); }} className={`px-3 py-1 rounded-full text-xs font-medium ${historyFilter === f.value ? 'bg-orange-500 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}`}>
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-zinc-900"><tr className="border-b border-zinc-800">
                      <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Date</th>
                      <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Type</th>
                      <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Source</th>
                      <th className="text-left py-2 px-3 text-zinc-400 font-medium text-xs">Details</th>
                      <th className="text-right py-2 px-3 text-zinc-400 font-medium text-xs">Points</th>
                      <th className="text-right py-2 px-3 text-zinc-400 font-medium text-xs">Balance</th>
                    </tr></thead>
                    <tbody>
                      {paginatedHistory.map((row, i) => {
                        const pts = row.points || 0;
                        const isEarn = pts > 0;
                        return (
                          <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                            <td className="py-2 px-3 text-zinc-300 font-mono text-xs whitespace-nowrap">{row.created_at ? new Date(row.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }) : '--'}</td>
                            <td className="py-2 px-3"><span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${isEarn ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>{isEarn ? 'Earn' : 'Spend'}</span></td>
                            <td className="py-2 px-3 text-zinc-300 text-xs">{SOURCE_LABELS[row.source] || row.source}{row.source?.includes('admin') && <span className="ml-1 text-amber-400 text-[10px]">(Admin)</span>}</td>
                            <td className="py-2 px-3 text-zinc-500 text-xs max-w-[200px] truncate">{row.metadata?.reason || ''}</td>
                            <td className={`py-2 px-3 text-right font-mono text-xs font-semibold ${isEarn ? 'text-emerald-400' : 'text-red-400'}`}>{isEarn ? '+' : ''}{pts.toLocaleString()}</td>
                            <td className="py-2 px-3 text-right font-mono text-xs text-zinc-300">{(row.balance_after ?? 0).toLocaleString()}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                {historyTotalPages > 1 && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                    <p className="text-xs text-zinc-500">{filteredHistory.length} transactions</p>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={() => setHistoryPage(p => Math.max(1, p - 1))} disabled={historyPage === 1} className="h-8 w-8 p-0"><ChevronLeft className="w-4 h-4" /></Button>
                      <span className="text-sm text-zinc-400">Page {historyPage}/{historyTotalPages}</span>
                      <Button variant="outline" size="sm" onClick={() => setHistoryPage(p => Math.min(historyTotalPages, p + 1))} disabled={historyPage === historyTotalPages} className="h-8 w-8 p-0"><ChevronRight className="w-4 h-4" /></Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Badges Tab */}
      {activeTab === 'badges' && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2"><Shield className="w-5 h-5 text-purple-400" /> Badge Definitions <span className="text-xs text-zinc-500 font-normal ml-2">{badges.length} badges</span></CardTitle>
          </CardHeader>
          <CardContent>
            {badgesLoading ? <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-zinc-500" /></div> : (
              <div className="space-y-2">
                {badges.map(badge => (
                  <div key={badge.id} className={`p-3 rounded-lg border ${badge.is_active ? 'bg-zinc-800/50 border-zinc-700' : 'bg-zinc-900/30 border-zinc-800 opacity-60'} flex items-center gap-4`}>
                    {editingBadge === badge.id ? (
                      <div className="flex-1 flex items-center gap-3">
                        <Input value={editName} onChange={(e) => setEditName(e.target.value)} className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm flex-1" placeholder="Badge name" />
                        <Input value={editDesc} onChange={(e) => setEditDesc(e.target.value)} className="bg-zinc-900 border-zinc-700 text-white h-8 text-sm flex-[2]" placeholder="Description" />
                        <Button size="sm" className="h-8 bg-emerald-600" onClick={() => handleBadgeSave(badge.id)}><Save className="w-3.5 h-3.5" /></Button>
                        <Button size="sm" variant="outline" className="h-8" onClick={() => setEditingBadge(null)}><X className="w-3.5 h-3.5" /></Button>
                      </div>
                    ) : (
                      <>
                        <div className="w-10 h-10 rounded-lg bg-zinc-900 flex items-center justify-center flex-shrink-0"><Award className="w-5 h-5 text-amber-400" /></div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white font-medium">{badge.name}</p>
                          <p className="text-xs text-zinc-500">{badge.description}</p>
                          <div className="flex gap-2 mt-1">
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400">{badge.category}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400">{badge.condition_type}: {badge.condition_value}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => { setEditingBadge(badge.id); setEditName(badge.name); setEditDesc(badge.description); }}><Edit2 className="w-3 h-3 mr-1" /> Edit</Button>
                          <Button size="sm" variant="outline" className={`h-7 text-xs ${badge.is_active ? 'text-red-400 border-red-500/30' : 'text-emerald-400 border-emerald-500/30'}`} onClick={() => handleBadgeToggle(badge)}>
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

      {/* Reset Points Dialog */}
      <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <DialogHeader><DialogTitle className="text-white flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-red-400" /> Reset Points to Zero</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-zinc-400">This will reset <span className="text-white font-medium">{selectedUser?.full_name}</span>'s points to zero. This action is logged in the audit trail.</p>
            <Input value={resetReason} onChange={e => setResetReason(e.target.value)} placeholder="Reason for reset (required)" className="input-dark" data-testid="reset-reason-input" />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResetDialogOpen(false)} className="btn-secondary">Cancel</Button>
            <Button onClick={handleResetPoints} disabled={resetting || !resetReason.trim()} className="bg-red-600 hover:bg-red-700 gap-2" data-testid="confirm-reset-btn">
              {resetting ? <Loader2 className="w-4 h-4 animate-spin" /> : <AlertTriangle className="w-4 h-4" />} Reset
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Award/Revoke Badge Dialog */}
      <Dialog open={badgeDialogOpen} onOpenChange={setBadgeDialogOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
          <DialogHeader><DialogTitle className="text-white flex items-center gap-2"><Award className="w-5 h-5 text-purple-400" /> Award / Revoke Badge</DialogTitle></DialogHeader>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {badges.filter(b => b.is_active).map(badge => {
              const hasBadge = userBadgeIds.includes(badge.id);
              return (
                <div key={badge.id} className={`flex items-center justify-between p-3 rounded-lg border ${hasBadge ? 'bg-amber-500/5 border-amber-500/20' : 'bg-zinc-800/50 border-zinc-700'}`}>
                  <div className="flex items-center gap-3 min-w-0">
                    <Award className={`w-5 h-5 ${hasBadge ? 'text-amber-400' : 'text-zinc-600'}`} />
                    <div className="min-w-0">
                      <p className="text-sm text-white">{badge.name}</p>
                      <p className="text-xs text-zinc-500 truncate">{badge.description}</p>
                    </div>
                  </div>
                  {hasBadge ? (
                    <Button size="sm" onClick={() => handleRevokeBadge(badge.id)} className="bg-red-600 hover:bg-red-700 text-xs h-7 gap-1">
                      <Minus className="w-3 h-3" /> Revoke
                    </Button>
                  ) : (
                    <Button size="sm" onClick={() => handleAwardBadge(badge.id)} className="bg-purple-600 hover:bg-purple-700 text-xs h-7 gap-1">
                      <Plus className="w-3 h-3" /> Award
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Streak Freezes Dialog */}
      <Dialog open={freezeDialogOpen} onOpenChange={setFreezeDialogOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <DialogHeader><DialogTitle className="text-white flex items-center gap-2"><Snowflake className="w-5 h-5 text-orange-400" /> Edit Streak Freezes</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2">
              {['trade', 'habit'].map(t => (
                <button key={t} onClick={() => setFreezeType(t)} className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 ${freezeType === t ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' : 'bg-zinc-900 text-zinc-400 border border-zinc-800'}`}>
                  {t === 'trade' ? <TrendingUp className="w-4 h-4" /> : <Flame className="w-4 h-4" />} {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              {['add', 'remove'].map(a => (
                <button key={a} onClick={() => setFreezeAction(a)} className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 ${freezeAction === a ? (a === 'add' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30') : 'bg-zinc-900 text-zinc-400 border border-zinc-800'}`}>
                  {a === 'add' ? <Plus className="w-4 h-4" /> : <Minus className="w-4 h-4" />} {a.charAt(0).toUpperCase() + a.slice(1)}
                </button>
              ))}
            </div>
            <div><label className="text-xs text-zinc-400 block mb-1">Count</label><Input type="number" value={freezeCount} onChange={e => setFreezeCount(Number(e.target.value))} min={1} max={10} className="input-dark" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFreezeDialogOpen(false)} className="btn-secondary">Cancel</Button>
            <Button onClick={handleEditFreeze} disabled={freezeLoading} className={`gap-2 ${freezeAction === 'add' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-red-600 hover:bg-red-700'}`} data-testid="confirm-freeze-btn">
              {freezeLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Snowflake className="w-4 h-4" />}
              {freezeAction === 'add' ? 'Add' : 'Remove'} {freezeCount} Freeze(s)
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
