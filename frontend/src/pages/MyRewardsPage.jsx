import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { rewardsAPI } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  Star, Trophy, TrendingUp, ArrowUpRight, Gift, Clock, Zap, Award, ExternalLink,
  Filter, Download, ChevronLeft, ChevronRight, Calendar, Flame, Target, Medal,
  ArrowUp, Users, Loader2, Shield, Lock, Wallet, List, Coins, Snowflake, ShieldCheck, Minus, Plus
} from 'lucide-react';

// Level configurations with points thresholds
const LEVELS = [
  { name: 'Newbie', minPoints: 0, color: 'zinc' },
  { name: 'Trader', minPoints: 100, color: 'blue' },
  { name: 'Trade Novice', minPoints: 500, color: 'cyan' },
  { name: 'Amateur Trader', minPoints: 1500, color: 'teal' },
  { name: 'Seasoned Trader', minPoints: 3000, color: 'orange' },
  { name: 'Pro Trader', minPoints: 6000, color: 'amber' },
  { name: 'Elite', minPoints: 12000, color: 'yellow' },
  { name: 'Legend', minPoints: 25000, color: 'purple' },
];

const LEVEL_COLORS = {
  'Newbie': { bg: 'from-zinc-500/20 to-zinc-600/10', border: 'border-zinc-500/30', text: 'text-zinc-300', badge: 'bg-zinc-700', progress: 'bg-zinc-500' },
  'Trader': { bg: 'from-blue-500/20 to-blue-600/10', border: 'border-blue-500/30', text: 'text-blue-300', badge: 'bg-blue-900', progress: 'bg-blue-500' },
  'Investor': { bg: 'from-emerald-500/20 to-emerald-600/10', border: 'border-emerald-500/30', text: 'text-emerald-300', badge: 'bg-emerald-900', progress: 'bg-emerald-500' },
  'Connector': { bg: 'from-purple-500/20 to-purple-600/10', border: 'border-purple-500/30', text: 'text-purple-300', badge: 'bg-purple-900', progress: 'bg-purple-500' },
  'Trade Novice': { bg: 'from-cyan-500/20 to-cyan-600/10', border: 'border-cyan-500/30', text: 'text-cyan-300', badge: 'bg-cyan-900', progress: 'bg-cyan-500' },
  'Amateur Trader': { bg: 'from-teal-500/20 to-teal-600/10', border: 'border-teal-500/30', text: 'text-teal-300', badge: 'bg-teal-900', progress: 'bg-teal-500' },
  'Seasoned Trader': { bg: 'from-orange-500/20 to-orange-600/10', border: 'border-orange-500/30', text: 'text-orange-300', badge: 'bg-orange-900', progress: 'bg-orange-500' },
  'Pro Trader': { bg: 'from-amber-500/20 to-amber-600/10', border: 'border-amber-500/30', text: 'text-amber-300', badge: 'bg-amber-900', progress: 'bg-amber-500' },
  'Elite': { bg: 'from-yellow-500/20 to-yellow-600/10', border: 'border-yellow-500/30', text: 'text-yellow-300', badge: 'bg-yellow-900', progress: 'bg-yellow-500' },
  'Legend': { bg: 'from-purple-500/20 to-purple-600/10', border: 'border-purple-500/30', text: 'text-purple-300', badge: 'bg-purple-900', progress: 'bg-purple-500' },
};

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
  milestone_10_trade: '10 Trades Milestone',
  milestone_20_trade_streak: '20 Trade Streak',
  milestone_50_trade: '50 Trades Milestone',
  milestone_100_trade: '100 Trades Milestone',
  join_community: 'Join Community',
  first_daily_win: 'Daily Win',
  help_chat: 'Help Chat',
  manual_bonus: 'Bonus',
  manual_promo: 'Promotion',
  system_check_credit: 'System Test',
  system_check_restore: 'System Test',
  redeem: 'Redemption',
  streak_freeze_purchase: 'Streak Freeze',
};

const SOURCE_CATEGORIES = {
  all: 'All Activities',
  trading: 'Trading',
  deposits: 'Deposits & Withdrawals',
  referrals: 'Referrals',
  streaks: 'Streaks & Milestones',
  bonus: 'Bonuses & Promotions',
};

const SOURCE_CATEGORY_MAP = {
  trade: 'trading',
  first_trade: 'trading',
  deposit: 'deposits',
  withdrawal: 'deposits',
  qualified_referral: 'referrals',
  streak_5_day: 'streaks',
  streak_10_day: 'streaks',
  streak_20_day: 'streaks',
  milestone_10_trade: 'streaks',
  milestone_20_trade_streak: 'streaks',
  milestone_50_trade: 'streaks',
  milestone_100_trade: 'streaks',
  manual_bonus: 'bonus',
  manual_promo: 'bonus',
  signup_verify: 'bonus',
  join_community: 'bonus',
  first_daily_win: 'bonus',
  help_chat: 'bonus',
};

const ITEMS_PER_PAGE = 15;

// Icon map for badge icons
const BADGE_ICONS = {
  'trending-up': TrendingUp,
  'flame': Flame,
  'star': Star,
  'users': Users,
  'wallet': Wallet,
  'target': Target,
  'award': Award,
  'shield': Shield,
  'trophy': Trophy,
  'calendar': Calendar,
  'crown': Trophy,
};

const BADGE_CATEGORY_COLORS = {
  trading: { bg: 'bg-blue-500/15', border: 'border-blue-500/40', text: 'text-blue-400', glow: 'shadow-blue-500/20' },
  streaks: { bg: 'bg-orange-500/15', border: 'border-orange-500/40', text: 'text-orange-400', glow: 'shadow-orange-500/20' },
  points: { bg: 'bg-amber-500/15', border: 'border-amber-500/40', text: 'text-amber-400', glow: 'shadow-amber-500/20' },
  referrals: { bg: 'bg-purple-500/15', border: 'border-purple-500/40', text: 'text-purple-400', glow: 'shadow-purple-500/20' },
  deposits: { bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', text: 'text-emerald-400', glow: 'shadow-emerald-500/20' },
  activity: { bg: 'bg-cyan-500/15', border: 'border-cyan-500/40', text: 'text-cyan-400', glow: 'shadow-cyan-500/20' },
};

// Rewards credit table — all actions and their point values
const REWARDS_CREDIT_TABLE = [
  { action: 'Sign Up & Verify Email', points: 25, category: 'Onboarding', icon: Shield },
  { action: 'Join Community', points: 5, category: 'Onboarding', icon: Users },
  { action: 'First Trade Bonus', points: 25, category: 'Trading', icon: TrendingUp },
  { action: 'Daily First Winning Trade', points: 10, category: 'Trading', icon: Zap },
  { action: 'Help in Chat', points: 5, category: 'Community', icon: Users },
  { action: 'Qualified Referral', points: 150, category: 'Referrals', icon: Gift },
  { action: 'Deposit (per $50 USDT)', points: 50, category: 'Deposits', icon: Wallet },
  { action: 'Withdrawal', points: 5, category: 'Transactions', icon: ArrowUp },
  { action: '5-Day Trading Streak', points: 50, category: 'Streaks', icon: Flame },
  { action: '10-Trade Milestone', points: 125, category: 'Milestones', icon: Target },
  { action: 'Every 20-Trade Milestone', points: 20, category: 'Milestones', icon: Award },
];

const USDT_PER_POINT = 0.01; // 1 point = $0.01 USDT

function RewardsFullListDialog({ open, onOpenChange, badges }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto bg-zinc-950 border-zinc-800" data-testid="rewards-full-list-dialog">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Coins className="w-5 h-5 text-amber-400" /> Rewards & Credit Equivalents
          </DialogTitle>
        </DialogHeader>

        {/* Points Actions Table */}
        <div className="mt-2">
          <h3 className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
            <Star className="w-4 h-4 text-amber-400" /> Earning Actions
          </h3>
          <div className="rounded-lg border border-zinc-800 overflow-hidden">
            <table className="w-full text-sm" data-testid="rewards-credit-table">
              <thead>
                <tr className="bg-zinc-900">
                  <th className="text-left py-2.5 px-4 text-zinc-400 font-medium">Action</th>
                  <th className="text-left py-2.5 px-4 text-zinc-400 font-medium">Category</th>
                  <th className="text-right py-2.5 px-4 text-zinc-400 font-medium">Points</th>
                  <th className="text-right py-2.5 px-4 text-zinc-400 font-medium">USDT Value</th>
                </tr>
              </thead>
              <tbody>
                {REWARDS_CREDIT_TABLE.map((row, i) => {
                  const Icon = row.icon;
                  return (
                    <tr key={i} className="border-t border-zinc-800/50 hover:bg-zinc-900/40">
                      <td className="py-2.5 px-4 text-zinc-200 flex items-center gap-2">
                        <Icon className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
                        {row.action}
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">{row.category}</span>
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-amber-400 font-semibold">+{row.points}</td>
                      <td className="py-2.5 px-4 text-right font-mono text-emerald-400 text-xs">${(row.points * USDT_PER_POINT).toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Badges Section */}
        {badges.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-purple-400" /> Achievement Badges
            </h3>
            <div className="rounded-lg border border-zinc-800 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-zinc-900">
                    <th className="text-left py-2.5 px-4 text-zinc-400 font-medium">Badge</th>
                    <th className="text-left py-2.5 px-4 text-zinc-400 font-medium">Requirement</th>
                    <th className="text-left py-2.5 px-4 text-zinc-400 font-medium">Category</th>
                    <th className="text-center py-2.5 px-4 text-zinc-400 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {badges.map((badge) => {
                    const Icon = BADGE_ICONS[badge.icon] || Award;
                    const colors = BADGE_CATEGORY_COLORS[badge.category] || BADGE_CATEGORY_COLORS.points;
                    return (
                      <tr key={badge.id} className="border-t border-zinc-800/50 hover:bg-zinc-900/40">
                        <td className="py-2.5 px-4 text-zinc-200 flex items-center gap-2">
                          <Icon className={`w-4 h-4 flex-shrink-0 ${badge.earned ? colors.text : 'text-zinc-600'}`} />
                          <span className={badge.earned ? '' : 'text-zinc-500'}>{badge.name}</span>
                        </td>
                        <td className="py-2.5 px-4 text-zinc-400 text-xs">{badge.description}</td>
                        <td className="py-2.5 px-4">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">{badge.category}</span>
                        </td>
                        <td className="py-2.5 px-4 text-center">
                          {badge.earned ? (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400">Earned</span>
                          ) : (
                            <Lock className="w-3.5 h-3.5 text-zinc-600 mx-auto" />
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <p className="text-[10px] text-zinc-600 mt-4 text-center">
          1 Point = ${USDT_PER_POINT.toFixed(2)} USDT equivalent
        </p>
      </DialogContent>
    </Dialog>
  );
}

function BadgesSection({ userId }) {
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFullList, setShowFullList] = useState(false);
  const checkedRef = useRef(false);

  useEffect(() => {
    if (!userId) return;
    const load = async () => {
      try {
        // Retroactive scan: recalculate real stats from DB and award badges
        if (!checkedRef.current) {
          checkedRef.current = true;
          try {
            const scanRes = await rewardsAPI.retroactiveScan();
            const newlyAwarded = scanRes.data?.newly_awarded || [];
            newlyAwarded.forEach((badgeName) => {
              toast.success(`New Badge Earned: ${badgeName}!`, {
                description: 'Check your badges collection!',
                duration: 6000,
              });
            });
          } catch (e) {
            // Fallback to simple badge check if scan fails
            const checkRes = await rewardsAPI.checkBadges();
            const newlyAwarded = checkRes.data?.newly_awarded || [];
            newlyAwarded.forEach((badgeName) => {
              toast.success(`New Badge Earned: ${badgeName}!`, {
                description: 'Check your badges collection!',
                duration: 6000,
              });
            });
          }
        }

        const res = await rewardsAPI.getUserBadges();
        setBadges(res.data?.badges || []);
      } catch (e) {
        console.error('Failed to load badges:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [userId]);

  const earned = badges.filter(b => b.earned);
  const locked = badges.filter(b => !b.earned);

  if (loading) {
    return (
      <Card className="glass-card">
        <CardContent className="py-8 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-zinc-500" />
        </CardContent>
      </Card>
    );
  }

  if (badges.length === 0) return null;

  return (
    <Card className="glass-card" data-testid="badges-section">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-amber-400" /> Badges & Achievements
            <span className="text-xs text-zinc-500 font-normal ml-2">{earned.length}/{badges.length} earned</span>
          </CardTitle>
          <button
            onClick={() => setShowFullList(true)}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            data-testid="see-full-list-btn"
          >
            <List className="w-3.5 h-3.5" /> See Full List
          </button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Earned badges */}
        {earned.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-zinc-400 uppercase tracking-wider mb-3">Earned</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {earned.map(badge => {
                const Icon = BADGE_ICONS[badge.icon] || Award;
                const colors = BADGE_CATEGORY_COLORS[badge.category] || BADGE_CATEGORY_COLORS.points;
                return (
                  <div
                    key={badge.id}
                    className={`p-3 rounded-xl ${colors.bg} border ${colors.border} text-center transition-transform hover:scale-105 shadow-lg ${colors.glow}`}
                    data-testid={`badge-${badge.id}`}
                    title={`${badge.description}\nEarned: ${badge.earned_at ? new Date(badge.earned_at).toLocaleDateString() : ''}`}
                  >
                    <Icon className={`w-7 h-7 mx-auto mb-1.5 ${colors.text}`} />
                    <p className="text-xs font-semibold text-white truncate">{badge.name}</p>
                    <p className="text-[10px] text-zinc-400 mt-0.5 line-clamp-2">{badge.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Locked badges */}
        {locked.length > 0 && (
          <div>
            <p className="text-xs text-zinc-400 uppercase tracking-wider mb-3">Locked</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {locked.map(badge => (
                <div
                  key={badge.id}
                  className="p-3 rounded-xl bg-zinc-900/40 border border-zinc-800 text-center opacity-50"
                  data-testid={`badge-locked-${badge.id}`}
                  title={badge.description}
                >
                  <Lock className="w-7 h-7 mx-auto mb-1.5 text-zinc-600" />
                  <p className="text-xs font-semibold text-zinc-500 truncate">{badge.name}</p>
                  <p className="text-[10px] text-zinc-600 mt-0.5 line-clamp-2">{badge.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
      <RewardsFullListDialog open={showFullList} onOpenChange={setShowFullList} badges={badges} />
    </Card>
  );
}

function StoreButton() {
  const [loading, setLoading] = useState(false);

  const handleOpenStore = async () => {
    setLoading(true);
    try {
      const res = await rewardsAPI.generateStoreToken();
      const storeUrl = res.data?.store_url;
      if (storeUrl) {
        window.open(storeUrl, '_blank', 'noopener,noreferrer');
      } else {
        toast.error('Failed to generate store access token');
      }
    } catch (e) {
      toast.error('Unable to connect to the rewards store');
      console.error('Store token error:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleOpenStore}
      disabled={loading}
      className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-semibold transition-all disabled:opacity-60"
      data-testid="open-rewards-store-btn"
    >
      {loading ? (
        <Loader2 className="w-5 h-5 animate-spin" />
      ) : (
        <Gift className="w-5 h-5" />
      )}
      {loading ? 'Connecting to Store...' : 'Open Rewards & Store'}
      {!loading && <ExternalLink className="w-4 h-4 ml-1" />}
    </button>
  );
}

function StreakFreezeSection() {
  const [freezeData, setFreezeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  const [quantities, setQuantities] = useState({ trade: 1, habit: 1 });

  const loadFreezes = useCallback(async () => {
    try {
      const res = await rewardsAPI.getStreakFreezes();
      setFreezeData(res.data);
    } catch (e) {
      console.error('Failed to load streak freezes:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadFreezes(); }, [loadFreezes]);

  const handlePurchase = async (type) => {
    setPurchasing(type);
    try {
      await rewardsAPI.purchaseStreakFreeze(type, quantities[type]);
      toast.success(`Purchased ${quantities[type]} ${type} streak freeze${quantities[type] > 1 ? 's' : ''}!`);
      setQuantities(prev => ({ ...prev, [type]: 1 }));
      loadFreezes();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to purchase streak freeze');
    } finally {
      setPurchasing(null);
    }
  };

  if (loading) return null;

  const freezeTypes = [
    {
      key: 'trade',
      label: 'Trade Streak Freeze',
      desc: 'Protects your trading streak when you miss a trading day',
      icon: TrendingUp,
      available: freezeData?.trade_freezes || 0,
      used: freezeData?.trade_freezes_used || 0,
      cost: freezeData?.costs?.trade || 200,
      color: 'blue',
    },
    {
      key: 'habit',
      label: 'Habit Streak Freeze',
      desc: 'Protects your daily habit streak when you miss a day',
      icon: Flame,
      available: freezeData?.habit_freezes || 0,
      used: freezeData?.habit_freezes_used || 0,
      cost: freezeData?.costs?.habit || 150,
      color: 'orange',
    },
  ];

  return (
    <Card className="glass-card" data-testid="streak-freeze-section">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Snowflake className="w-5 h-5 text-cyan-400" /> Streak Freezes
        </CardTitle>
        <p className="text-xs text-zinc-400 mt-1">Purchase streak freezes with your reward points. When you miss a day, a freeze is automatically applied to keep your streak alive.</p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {freezeTypes.map((ft) => {
            const Icon = ft.icon;
            const qty = quantities[ft.key];
            const totalCost = ft.cost * qty;
            const canAfford = (freezeData?.available_points || 0) >= totalCost;
            return (
              <div key={ft.key} className={`p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-${ft.color}-500/30 transition-all`} data-testid={`streak-freeze-${ft.key}`}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`p-2 rounded-lg bg-${ft.color}-500/10`}>
                    <Icon className={`w-5 h-5 text-${ft.color}-400`} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{ft.label}</p>
                    <p className="text-[11px] text-zinc-400">{ft.desc}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="text-[10px] text-zinc-500 uppercase">Available</p>
                      <p className="text-lg font-bold font-mono text-cyan-400" data-testid={`${ft.key}-freeze-count`}>{ft.available}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-zinc-500 uppercase">Used</p>
                      <p className="text-lg font-bold font-mono text-zinc-400">{ft.used}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-zinc-500 uppercase">Cost Each</p>
                    <p className="text-sm font-mono text-amber-400">{ft.cost} pts</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 bg-zinc-800 rounded-lg px-1 py-1">
                    <button
                      onClick={() => setQuantities(prev => ({ ...prev, [ft.key]: Math.max(1, qty - 1) }))}
                      className="p-1 rounded hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
                      data-testid={`${ft.key}-freeze-minus`}
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span className="text-sm font-mono text-white w-6 text-center">{qty}</span>
                    <button
                      onClick={() => setQuantities(prev => ({ ...prev, [ft.key]: Math.min(10, qty + 1) }))}
                      className="p-1 rounded hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
                      data-testid={`${ft.key}-freeze-plus`}
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <Button
                    onClick={() => handlePurchase(ft.key)}
                    disabled={!canAfford || purchasing === ft.key}
                    className={`flex-1 bg-${ft.color}-600 hover:bg-${ft.color}-500 text-white text-sm disabled:opacity-40`}
                    data-testid={`buy-${ft.key}-freeze-btn`}
                  >
                    {purchasing === ft.key ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-1" />
                    ) : (
                      <ShieldCheck className="w-4 h-4 mr-1" />
                    )}
                    Buy for {totalCost} pts
                  </Button>
                </div>
                {!canAfford && (
                  <p className="text-[10px] text-red-400 mt-1.5">Not enough points ({freezeData?.available_points || 0} available)</p>
                )}
              </div>
            );
          })}
        </div>

        {/* Recent Usage */}
        {freezeData?.usage_history?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-zinc-800">
            <p className="text-xs text-zinc-400 font-medium mb-2">Recent Freeze Usage</p>
            <div className="space-y-1.5">
              {freezeData.usage_history.slice(0, 5).map((u, i) => (
                <div key={i} className="flex items-center justify-between text-xs py-1.5 px-2 rounded bg-zinc-900/40">
                  <div className="flex items-center gap-2">
                    <Snowflake className="w-3 h-3 text-cyan-400" />
                    <span className="text-zinc-300 capitalize">{u.freeze_type} freeze</span>
                  </div>
                  <span className="text-zinc-500 font-mono">{u.date}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function MyRewardsPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filter & pagination state
  const [dateFilter, setDateFilter] = useState('all'); // all, 7d, 30d, 90d, custom
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const loadData = useCallback(async () => {
    if (!user?.id) return;
    try {
      const [sumRes, lbRes, histRes] = await Promise.allSettled([
        rewardsAPI.getSummary(user.id),
        rewardsAPI.getLeaderboard(user.id),
        rewardsAPI.getHistory(null, 500), // Get more history for filtering
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

  // Calculate level progress
  const levelProgress = useMemo(() => {
    const points = summary?.lifetime_points || 0;
    const currentLevel = LEVELS.findLast(l => points >= l.minPoints) || LEVELS[0];
    const nextLevel = LEVELS.find(l => l.minPoints > points);
    
    if (!nextLevel) {
      return { current: currentLevel, next: null, progress: 100, pointsToNext: 0 };
    }
    
    const pointsInLevel = points - currentLevel.minPoints;
    const pointsForLevel = nextLevel.minPoints - currentLevel.minPoints;
    const progress = Math.min(100, Math.round((pointsInLevel / pointsForLevel) * 100));
    
    return {
      current: currentLevel,
      next: nextLevel,
      progress,
      pointsToNext: nextLevel.minPoints - points,
    };
  }, [summary?.lifetime_points]);

  // Filter history based on selections
  const filteredHistory = useMemo(() => {
    let filtered = [...history];
    
    // Date filter
    if (dateFilter !== 'all') {
      const now = new Date();
      let startDate;
      
      if (dateFilter === '7d') {
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      } else if (dateFilter === '30d') {
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      } else if (dateFilter === '90d') {
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
      } else if (dateFilter === 'custom' && customStartDate) {
        startDate = new Date(customStartDate);
      }
      
      if (startDate) {
        filtered = filtered.filter(row => {
          const rowDate = new Date(row.created_at);
          if (dateFilter === 'custom' && customEndDate) {
            const endDate = new Date(customEndDate);
            endDate.setHours(23, 59, 59, 999);
            return rowDate >= startDate && rowDate <= endDate;
          }
          return rowDate >= startDate;
        });
      }
    }
    
    // Source category filter
    if (sourceFilter !== 'all') {
      filtered = filtered.filter(row => {
        const category = SOURCE_CATEGORY_MAP[row.source] || 'bonus';
        return category === sourceFilter;
      });
    }
    
    return filtered;
  }, [history, dateFilter, customStartDate, customEndDate, sourceFilter]);

  // Pagination
  const totalPages = Math.ceil(filteredHistory.length / ITEMS_PER_PAGE);
  const paginatedHistory = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredHistory.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredHistory, currentPage]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [dateFilter, sourceFilter, customStartDate, customEndDate]);

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['Date', 'Type', 'Source', 'Points', 'Balance After'];
    const rows = filteredHistory.map(row => [
      row.created_at ? new Date(row.created_at).toISOString() : '',
      row.points > 0 ? 'Earn' : 'Spend',
      SOURCE_LABELS[row.source] || row.source,
      row.points,
      row.balance_after || 0,
    ]);
    
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rewards-history-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Stats for filtered period
  const periodStats = useMemo(() => {
    const earned = filteredHistory.filter(r => r.points > 0).reduce((sum, r) => sum + r.points, 0);
    const spent = filteredHistory.filter(r => r.points < 0).reduce((sum, r) => sum + Math.abs(r.points), 0);
    return { earned, spent, net: earned - spent, transactions: filteredHistory.length };
  }, [filteredHistory]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const levelStyle = LEVEL_COLORS[summary?.level] || LEVEL_COLORS['Newbie'];

  return (
    <div className="space-y-6 max-w-5xl mx-auto" data-testid="my-rewards-page">
      <div>
        <h1 className="text-2xl font-bold text-white">My Rewards</h1>
        <p className="text-sm text-zinc-400 mt-1">Track your points, level, rank, and activity</p>
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

        {/* Level with Progress */}
        <Card className="glass-card" data-testid="rewards-level-card">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">Level</p>
                <div className="mt-2">
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${levelStyle.badge} ${levelStyle.text}`}>
                    {summary?.level || 'Newbie'}
                  </span>
                </div>
              </div>
              <div className="p-3 rounded-xl bg-purple-500/10">
                <Award className="w-6 h-6 text-purple-400" />
              </div>
            </div>
            {/* Progress bar */}
            {levelProgress.next && (
              <div className="mt-3">
                <div className="flex justify-between text-xs text-zinc-400 mb-1">
                  <span>{levelProgress.current.name}</span>
                  <span>{levelProgress.next.name}</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${levelStyle.progress} transition-all duration-500`}
                    style={{ width: `${levelProgress.progress}%` }}
                  />
                </div>
                <p className="text-xs text-zinc-500 mt-1 text-center">
                  <span className="text-cyan-400 font-mono">{levelProgress.pointsToNext.toLocaleString()}</span> pts to next level
                </p>
              </div>
            )}
            {!levelProgress.next && (
              <p className="text-xs text-amber-400 mt-2 flex items-center gap-1">
                <Medal className="w-3 h-3" /> Max level reached!
              </p>
            )}
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
                  <p className="text-xs text-cyan-400 mt-1 flex items-center gap-1">
                    <ArrowUp className="w-3 h-3" />
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

      {/* Streak & Activity Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
          <div className="flex items-center gap-2 text-orange-400 mb-1">
            <Flame className="w-4 h-4" />
            <span className="text-xs font-medium">Current Streak</span>
          </div>
          <p className="text-xl font-bold text-white font-mono">
            {summary?.current_streak || 0} days
          </p>
        </div>
        <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
          <div className="flex items-center gap-2 text-emerald-400 mb-1">
            <Target className="w-4 h-4" />
            <span className="text-xs font-medium">Best Streak</span>
          </div>
          <p className="text-xl font-bold text-white font-mono">
            {summary?.best_streak || 0} days
          </p>
        </div>
        <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
          <div className="flex items-center gap-2 text-blue-400 mb-1">
            <TrendingUp className="w-4 h-4" />
            <span className="text-xs font-medium">This Month</span>
          </div>
          <p className="text-xl font-bold text-white font-mono">
            +{(summary?.monthly_points || 0).toLocaleString()}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
          <div className="flex items-center gap-2 text-purple-400 mb-1">
            <Users className="w-4 h-4" />
            <span className="text-xs font-medium">Referrals</span>
          </div>
          <p className="text-xl font-bold text-white font-mono">
            {summary?.referral_count || 0}
          </p>
        </div>
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

      {/* Badges Section */}
      <BadgesSection userId={user?.id} />

      {/* Streak Freeze Section */}
      <StreakFreezeSection />

      {/* CTA - Rewards Store */}
      <StoreButton />

      {/* Points History */}
      <Card className="glass-card" data-testid="rewards-history-card">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-zinc-400" /> Points History
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowFilters(!showFilters)}
                className="gap-1 text-xs"
                data-testid="toggle-filters-btn"
              >
                <Filter className="w-3 h-3" /> Filters
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={exportToCSV}
                className="gap-1 text-xs"
                disabled={filteredHistory.length === 0}
                data-testid="export-csv-btn"
              >
                <Download className="w-3 h-3" /> Export CSV
              </Button>
            </div>
          </div>
          
          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-4 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 space-y-4" data-testid="filters-panel">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Date Filter */}
                <div>
                  <label className="text-xs text-zinc-400 block mb-2">Time Period</label>
                  <div className="flex flex-wrap gap-2">
                    {[
                      { value: 'all', label: 'All Time' },
                      { value: '7d', label: '7 Days' },
                      { value: '30d', label: '30 Days' },
                      { value: '90d', label: '90 Days' },
                      { value: 'custom', label: 'Custom' },
                    ].map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => setDateFilter(opt.value)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          dateFilter === opt.value 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                  {dateFilter === 'custom' && (
                    <div className="flex gap-2 mt-2">
                      <Input
                        type="date"
                        value={customStartDate}
                        onChange={(e) => setCustomStartDate(e.target.value)}
                        className="text-xs h-8 bg-zinc-800 border-zinc-700"
                        placeholder="Start"
                      />
                      <Input
                        type="date"
                        value={customEndDate}
                        onChange={(e) => setCustomEndDate(e.target.value)}
                        className="text-xs h-8 bg-zinc-800 border-zinc-700"
                        placeholder="End"
                      />
                    </div>
                  )}
                </div>
                
                {/* Source Filter */}
                <div>
                  <label className="text-xs text-zinc-400 block mb-2">Activity Type</label>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(SOURCE_CATEGORIES).map(([value, label]) => (
                      <button
                        key={value}
                        onClick={() => setSourceFilter(value)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          sourceFilter === value 
                            ? 'bg-emerald-500 text-white' 
                            : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Period Stats */}
              <div className="flex items-center gap-4 pt-3 border-t border-zinc-800">
                <span className="text-xs text-zinc-500">Period Summary:</span>
                <span className="text-xs text-emerald-400 font-mono">+{periodStats.earned.toLocaleString()} earned</span>
                <span className="text-xs text-red-400 font-mono">-{periodStats.spent.toLocaleString()} spent</span>
                <span className="text-xs text-zinc-300 font-mono">= {periodStats.net.toLocaleString()} net</span>
                <span className="text-xs text-zinc-500">({periodStats.transactions} transactions)</span>
              </div>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {paginatedHistory.length === 0 ? (
            <div className="text-center py-10 text-zinc-500">
              <TrendingUp className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p>No points activity {dateFilter !== 'all' || sourceFilter !== 'all' ? 'matching filters' : 'yet'}.</p>
              <p className="text-xs mt-1">
                {dateFilter === 'all' && sourceFilter === 'all' 
                  ? 'Start trading or depositing to earn your first points!'
                  : 'Try adjusting your filters to see more activity.'
                }
              </p>
            </div>
          ) : (
            <>
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
                    {paginatedHistory.map((row, i) => {
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
              
              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                  <p className="text-xs text-zinc-500">
                    Showing {((currentPage - 1) * ITEMS_PER_PAGE) + 1}-{Math.min(currentPage * ITEMS_PER_PAGE, filteredHistory.length)} of {filteredHistory.length}
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
