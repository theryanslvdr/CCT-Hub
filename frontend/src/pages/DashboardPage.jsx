import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useBVE } from '@/contexts/BVEContext';
import { profitAPI, tradeAPI, currencyAPI, adminAPI, familyAPI, rewardsAPI } from '@/lib/api';
import api from '@/lib/api';
import { formatCurrency, formatCurrencyCompact, formatNumber, formatNumberCompact } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ValueTooltip } from '@/components/ui/value-tooltip';
import { MissedTradersWidget } from '@/components/admin/MissedTradersWidget';
import { ActivityFeed } from '@/components/admin/ActivityFeed';
import { TrendingUp, TrendingDown, DollarSign, Activity, Target, ArrowUpRight, ArrowDownRight, Eye, EyeOff, Wallet, BarChart3, History, FlaskConical, ChevronRight, Users, Calendar, AlertTriangle, Star, ExternalLink, Trophy, Award, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts';

export const DashboardPage = () => {
  const { 
    user, 
    simulatedView, 
    isMasterAdmin,
    isAdmin,
    getSimulatedAccountValue,
    getSimulatedLotSize,
    getSimulatedTotalDeposits,
    getSimulatedTotalProfit,
    getSimulatedMemberName,
    getSimulatedMemberId
  } = useAuth();
  const { isInBVE } = useBVE();
  const [summary, setSummary] = useState(null);
  const [trades, setTrades] = useState([]);
  const [signal, setSignal] = useState(null);
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Licensee-specific data
  const [yearProjections, setYearProjections] = useState(null);
  const [familyMembers, setFamilyMembers] = useState([]);
  const [projectionError, setProjectionError] = useState(false);
  const [rewardsSummary, setRewardsSummary] = useState(null);
  const [rewardsLeaderboard, setRewardsLeaderboard] = useState(null);
  const [valuesHidden, setValuesHidden] = useState(() => localStorage.getItem('hideAccountValues') === 'true');

  // Simulation values
  const simulatedMemberId = getSimulatedMemberId();
  const simulatedMemberName = getSimulatedMemberName();
  const simulatedAccountValue = getSimulatedAccountValue();
  const simulatedTotalProfit = getSimulatedTotalProfit();
  const isSimulating = simulatedView && isMasterAdmin();
  
  // Check if user is a regular member (not admin)
  const isMember = !isAdmin();
  
  // Check if viewing as a licensee (either simulated or actual licensee user)
  const isLicenseeView = simulatedView?.license_type || user?.license_type || summary?.is_licensee;

  const toggleValuesHidden = useCallback(() => {
    setValuesHidden(prev => {
      const newVal = !prev;
      localStorage.setItem('hideAccountValues', newVal.toString());
      return newVal;
    });
  }, []);

  const loadDashboardData = useCallback(async () => {
    try {
      // Determine which signal endpoint to use
      const signalEndpoint = isInBVE ? api.get('/bve/active-signal') : tradeAPI.getActiveSignal();
      
      // If simulating a specific member, fetch their data from API
      if (isSimulating && simulatedMemberId) {
        // Fetch the simulated member's data - API returns license.current_amount for licensees
        const [memberRes, tradesRes, signalRes, ratesRes] = await Promise.all([
          adminAPI.getMemberDetails(simulatedMemberId),
          tradeAPI.getLogs(10, simulatedMemberId),
          signalEndpoint,
          currencyAPI.getRates('USDT'),
        ]);

        // Build summary from member data - API returns { user, stats, recent_trades }
        // For licensees, stats.account_value comes from license.current_amount
        const stats = memberRes.data.stats || {};
        const user = memberRes.data.user || {};
        
        setSummary({
          account_value: stats.account_value || 0,  // This is the authoritative value from license.current_amount
          total_actual_profit: stats.total_profit || 0,
          total_trades: stats.total_trades || 0,
          performance_rate: stats.performance_rate || 0,
          profit_difference: 0,
          is_licensee: stats.is_licensee || false,
        });
        setTrades(tradesRes.data || []);
        setSignal(signalRes.data.signal);
        setRates(ratesRes.data.rates || {});
      } else if (isSimulating && !simulatedMemberId) {
        // Role-based simulation (demo mode) - use demo values
        const [tradesRes, signalRes, ratesRes] = await Promise.all([
          tradeAPI.getLogs(10),
          signalEndpoint,
          currencyAPI.getRates('USDT'),
        ]);

        setSummary({
          account_value: simulatedAccountValue || 5000,  // Demo value
          total_actual_profit: simulatedTotalProfit || 0,
          total_trades: 0,
          performance_rate: 0,
          profit_difference: 0,
        });
        setTrades([]);  // No trades for demo mode
        setSignal(signalRes.data.signal);
        setRates(ratesRes.data.rates || {});
      } else {
        // Normal flow - load current user's data
        // In BVE mode, use BVE summary
        const summaryEndpoint = isInBVE ? api.get('/bve/summary') : profitAPI.getSummary();
        
        const [summaryRes, tradesRes, signalRes, ratesRes] = await Promise.all([
          summaryEndpoint,
          tradeAPI.getLogs(10),
          signalEndpoint,
          currencyAPI.getRates('USDT'),
        ]);

        // DEBUG: Log the API response to help diagnose display issues
        console.log('=== DASHBOARD DEBUG ===');
        console.log('API Response summaryRes.data:', summaryRes.data);
        console.log('account_value from API:', summaryRes.data?.account_value);
        console.log('total_actual_profit from API:', summaryRes.data?.total_actual_profit);
        console.log('total_trades from API:', summaryRes.data?.total_trades);
        console.log('is_licensee from API:', summaryRes.data?.is_licensee);
        
        setSummary(summaryRes.data);
        setTrades(tradesRes.data);
        setSignal(signalRes.data.signal);
        setRates(ratesRes.data.rates || {});
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, [isSimulating, simulatedMemberId, simulatedAccountValue, simulatedTotalProfit, isInBVE]);

  // Load licensee-specific data (year projections + family members)
  // AUTO-RETRY: retries up to 2 times to prevent transient failures
  const loadLicenseeData = useCallback(async () => {
    if (!isLicenseeView) return;
    const maxRetries = 2;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        setProjectionError(false);
        
        // For simulated views, use admin endpoints with user_id
        const targetUserId = isSimulating ? simulatedMemberId : null;
        
        // Don't call projection endpoint without a valid target for simulation
        if (isSimulating && !simulatedMemberId) return;
        
        const [projRes, famRes] = await Promise.allSettled([
          profitAPI.getLicenseeYearProjections(targetUserId),
          isSimulating && simulatedMemberId
            ? familyAPI.adminGetMembers(simulatedMemberId)
            : familyAPI.getMembers(),
        ]);
        if (projRes.status === 'fulfilled') {
          setYearProjections(projRes.value.data);
          if (famRes.status === 'fulfilled') {
            setFamilyMembers(famRes.value.data?.family_members || []);
          }
          return; // Success — stop retrying
        } else {
          if (attempt < maxRetries) {
            console.warn(`Projection load attempt ${attempt + 1} failed, retrying...`);
            await new Promise(r => setTimeout(r, 1000)); // 1s delay before retry
            continue;
          }
          console.error('Projection load failed after retries:', projRes.reason);
          setProjectionError(true);
        }
        if (famRes.status === 'fulfilled') {
          setFamilyMembers(famRes.value.data?.family_members || []);
        }
        return;
      } catch (e) {
        if (attempt < maxRetries) {
          await new Promise(r => setTimeout(r, 1000));
          continue;
        }
        console.error('Failed to load licensee data after retries:', e);
        setProjectionError(true);
      }
    }
  }, [isLicenseeView, isSimulating, simulatedMemberId]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData, simulatedView, isInBVE]);

  useEffect(() => {
    loadLicenseeData();
  }, [loadLicenseeData, summary]);

  // Load rewards data
  useEffect(() => {
    const uid = isSimulating ? simulatedMemberId : user?.id;
    if (!uid) return;
    const loadRewards = async () => {
      try {
        const [sumRes, lbRes] = await Promise.allSettled([
          rewardsAPI.getSummary(uid),
          rewardsAPI.getLeaderboard(uid),
        ]);
        if (sumRes.status === 'fulfilled') setRewardsSummary(sumRes.value.data);
        if (lbRes.status === 'fulfilled') setRewardsLeaderboard(lbRes.value.data);
      } catch (e) { /* silent */ }
    };
    loadRewards();
  }, [user?.id, isSimulating, simulatedMemberId]);

  // Define KPI cards - filter based on licensee view
  // DEBUG: Log the summary state when cards are defined
  console.log('=== KPI CARDS DEBUG ===');
  console.log('summary state:', summary);
  console.log('summary?.account_value:', summary?.account_value);
  console.log('summary?.total_actual_profit:', summary?.total_actual_profit);
  console.log('summary?.total_trades:', summary?.total_trades);
  
  const allKpiCards = [
    {
      title: 'Account Value',
      value: summary?.account_value || 0,
      format: 'currency',
      icon: DollarSign,
      change: summary?.profit_difference || 0,
      color: 'blue',
      showForLicensee: true,
    },
    {
      title: 'Total Profit',
      value: summary?.total_actual_profit || 0,
      format: 'currency',
      icon: TrendingUp,
      change: summary?.performance_rate || 0,
      changeFormat: 'percent',
      color: 'emerald',
      showForLicensee: true,
    },
    {
      title: 'Total Trades',
      value: summary?.total_trades || 0,
      format: 'number',
      icon: Activity,
      color: 'cyan',
      showForLicensee: true,
    },
    {
      title: 'Actual vs Projected',
      value: summary?.performance_rate || 0,
      format: 'percent',
      icon: Target,
      color: 'purple',
      subtitle: summary?.performance_rate > 100 ? 'Above target!' : summary?.performance_rate === 100 ? 'On target' : 'Below target',
      showForLicensee: true,
    },
  ];
  
  // Filter cards for licensees - they see all 4 cards but full width (3 columns on lg)
  const kpiCards = isLicenseeView 
    ? allKpiCards.filter(card => card.showForLicensee)
    : allKpiCards;

  // Prepare chart data from trades - use actual trade dates
  const chartData = trades.slice().reverse().map((trade, index) => {
    const tradeDate = new Date(trade.created_at);
    const dateLabel = tradeDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return {
      name: dateLabel,
      projected: trade.projected_profit,
      actual: trade.actual_profit,
    };
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-4 w-24 bg-zinc-800 rounded mb-4" />
              <div className="h-8 w-32 bg-zinc-800 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Get effective display name
  const displayName = isSimulating && simulatedMemberName 
    ? simulatedMemberName.split(' ')[0] 
    : user?.full_name?.split(' ')[0];

  return (
    <div className="space-y-6">
      {/* BVE Mode Banner */}
      {isInBVE && (
        <div className="p-4 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center gap-3" data-testid="bve-banner">
          <FlaskConical className="w-6 h-6 text-purple-400 animate-pulse" />
          <div>
            <h3 className="text-purple-300 font-semibold">Beta Virtual Environment Active</h3>
            <p className="text-purple-400/70 text-sm">All data shown is from BVE. Actions won&apos;t affect real data.</p>
          </div>
        </div>
      )}
      
      {/* Simulation Banner */}
      {isSimulating && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30" data-testid="simulation-banner">
          <div className="flex items-center gap-3">
            <Eye className="w-5 h-5 text-amber-400" />
            <div>
              <p className="text-amber-400 font-medium">
                Simulating: {simulatedMemberName || simulatedView?.displayName || 'Member View'}
              </p>
              <p className="text-xs text-amber-400/70">
                You are viewing this dashboard as {simulatedView?.license_type ? `a ${simulatedView.license_type} licensee` : 'a member'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Welcome Section - Mobile: 2 rows when signal active */}
      <div className="glass-card p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Row 1: Greeting */}
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-white">
              Welcome back, {displayName}!
            </h2>
            <p className="text-zinc-400 text-sm md:text-base mt-1">
              Here&apos;s your trading overview for today.
            </p>
          </div>
          {/* Row 2 on Mobile / Right side on Desktop: Signal Card - Clickable to Trade Monitor - Hidden for licensees */}
          {signal && !isLicenseeView && (
            <div 
              onClick={() => window.location.href = '/trade-monitor'}
              className="glass-highlight px-4 md:px-6 py-3 flex items-center gap-3 md:gap-4 cursor-pointer hover:border-blue-500/50 transition-all"
              data-testid="dashboard-signal-card"
            >
              <div className={`w-10 h-10 md:w-auto md:h-auto md:px-4 md:py-2 rounded-lg font-bold flex items-center justify-center ${signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                <span className="hidden md:block">{signal.direction}</span>
                {signal.direction === 'BUY' ? (
                  <TrendingUp className="w-5 h-5 md:hidden" />
                ) : (
                  <TrendingDown className="w-5 h-5 md:hidden" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-xs text-zinc-400 uppercase tracking-wider hidden md:block">Active Signal</p>
                  <span className={`md:hidden text-xs font-bold ${signal.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>{signal.direction}</span>
                  <span className="text-xs text-zinc-500 md:hidden">{signal.product}</span>
                </div>
                <p className="text-base md:text-lg font-bold text-white hidden md:block">{signal.product}</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] md:text-xs text-zinc-400">Trade Time</p>
                <p className="text-sm md:text-lg font-mono text-blue-400">{signal.trade_time}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-zinc-500 hidden md:block" />
            </div>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        {kpiCards.map((card, index) => {
          const Icon = card.icon;
          const colorClasses = {
            blue: 'from-blue-500 to-blue-600',
            emerald: 'from-emerald-500 to-emerald-600',
            cyan: 'from-cyan-500 to-cyan-600',
            purple: 'from-purple-500 to-purple-600',
          };

          const isCurrencyCard = card.format === 'currency';
          const shouldHide = valuesHidden && isCurrencyCard;

          // Format exact value for tooltip
          const exactValue = card.format === 'currency' 
            ? formatCurrency(card.value, 'USD')
            : card.format === 'percent' 
            ? `${card.value.toFixed(2)}%`
            : card.value.toString();

          // Mobile compact format (K, M, B, T) - 3 digits, no rounding
          const mobileValue = card.format === 'currency' 
            ? formatCurrencyCompact(card.value)
            : card.format === 'number' 
            ? formatNumberCompact(card.value)
            : `${formatNumberCompact(card.value)}%`;

          // Desktop full format
          const desktopValue = card.format === 'currency' 
            ? formatCurrency(card.value, 'USD')
            : card.format === 'number' 
            ? formatNumber(card.value, 0)
            : `${formatNumber(card.value, 1)}%`;

          return (
            <Card key={index} className="glass-card hover:border-blue-500/30 transition-all" data-testid={`kpi-${card.title.toLowerCase().replace(/\s/g, '-')}`}>
              <CardContent className="p-3 md:p-6">
                <div className="flex items-start justify-between gap-1 md:gap-2">
                  <div className="flex-1 min-w-0 overflow-hidden">
                    <div className="flex items-center gap-1">
                      <p className="text-[10px] md:text-sm text-zinc-400 truncate">{card.title}</p>
                      {isCurrencyCard && (
                        <button 
                          onClick={toggleValuesHidden} 
                          className="text-zinc-500 hover:text-zinc-300 transition-colors p-0.5"
                          data-testid={`toggle-hide-${card.title.toLowerCase().replace(/\s/g, '-')}`}
                        >
                          {valuesHidden ? <EyeOff className="w-3 h-3 md:w-3.5 md:h-3.5" /> : <Eye className="w-3 h-3 md:w-3.5 md:h-3.5" />}
                        </button>
                      )}
                    </div>
                    {shouldHide ? (
                      <>
                        <p className="text-lg md:hidden font-bold font-mono text-white mt-1">****</p>
                        <p className="hidden md:block text-3xl font-bold font-mono text-white mt-2">****</p>
                      </>
                    ) : (
                      <ValueTooltip exactValue={exactValue}>
                        <p className="text-lg md:hidden font-bold font-mono text-white mt-1">
                          {mobileValue}
                        </p>
                        <p className="hidden md:block text-3xl font-bold font-mono text-white mt-2">
                          {desktopValue}
                        </p>
                      </ValueTooltip>
                    )}
                    {card.subtitle && (
                      <p className={`text-[9px] md:text-xs mt-1 truncate ${card.value > 100 ? 'text-emerald-400' : card.value === 100 ? 'text-blue-400' : 'text-amber-400'}`}>
                        {card.subtitle}
                      </p>
                    )}
                  </div>
                  <div className={`w-8 h-8 md:w-12 md:h-12 rounded-lg md:rounded-xl bg-gradient-to-br ${colorClasses[card.color]} flex items-center justify-center flex-shrink-0`}>
                    <Icon className="w-4 h-4 md:w-6 md:h-6 text-white" />
                  </div>
                </div>
                {card.change !== undefined && card.changeFormat && !shouldHide && (
                  <div className="mt-2 md:mt-4 flex items-center gap-1 flex-wrap">
                    {card.change >= 100 ? (
                      <ArrowUpRight className="w-3 h-3 md:w-4 md:h-4 text-emerald-400" />
                    ) : (
                      <ArrowDownRight className="w-3 h-3 md:w-4 md:h-4 text-red-400" />
                    )}
                    <span className={`text-[10px] md:text-sm ${card.change >= 100 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {card.changeFormat === 'percent' 
                        ? `${formatNumber(card.change, 1)}%` 
                        : <><span className="md:hidden">{formatCurrencyCompact(Math.abs(card.change))}</span><span className="hidden md:inline">{formatCurrency(Math.abs(card.change))}</span></>
                      }
                    </span>
                    <span className="text-zinc-500 text-[9px] md:text-sm">vs projected</span>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Rewards section — prominent, right after KPI cards. HIDDEN for licensees. */}
      {(isMember || isSimulating) && !isLicenseeView && (
        <Card className="glass-card overflow-hidden" data-testid="rewards-card">
          <div className="relative">
            <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-yellow-500" />
            <CardContent className="pt-6 pb-5 px-5">
              <div className="flex items-center gap-2 mb-4">
                <Star className="w-5 h-5 text-amber-400" />
                <span className="text-sm font-semibold text-white tracking-wide">CrossCurrent Rewards</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div data-testid="rewards-dash-points">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold">Points</p>
                  <p className="text-xl font-bold font-mono text-white mt-0.5">{(rewardsSummary?.lifetime_points || 0).toLocaleString()}</p>
                  <p className="text-xs text-emerald-400 font-mono">~${(rewardsSummary?.estimated_usdt || 0).toFixed(2)} USDT</p>
                </div>
                <div data-testid="rewards-dash-level">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold">Level</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <Award className="w-4 h-4 text-purple-400" />
                    <span className="text-sm font-bold text-white">{rewardsSummary?.level || 'Newbie'}</span>
                  </div>
                </div>
                <div data-testid="rewards-dash-rank">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold">Monthly Rank</p>
                  <p className="text-xl font-bold font-mono text-white mt-0.5">
                    {rewardsLeaderboard?.current_rank ? `#${rewardsLeaderboard.current_rank}` : '--'}
                  </p>
                  {rewardsLeaderboard?.distance_to_next > 0 && (
                    <p className="text-[10px] text-cyan-400 truncate">
                      {rewardsLeaderboard.distance_to_next} pts to #{(rewardsLeaderboard.current_rank || 1) - 1}
                    </p>
                  )}
                </div>
                <div className="flex flex-col justify-center items-end gap-2">
                  <a
                    href={`https://rewards.crosscur.rent/store?user_id=${isSimulating ? simulatedMemberId : user?.id || ''}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-xs font-semibold transition-all shadow-lg shadow-amber-500/10"
                    data-testid="open-rewards-store-btn"
                  >
                    Open Rewards & Store
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                  <a href="/my-rewards" className="text-[10px] text-zinc-400 hover:text-zinc-200 transition-colors" data-testid="view-all-rewards-link">
                    View all rewards details →
                  </a>
                </div>
              </div>
              {rewardsLeaderboard?.suggested_message && (
                <div className="mt-3 px-3 py-2 rounded-lg bg-blue-500/8 border border-blue-500/15">
                  <p className="text-xs text-blue-300 flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 flex-shrink-0" />
                    {rewardsLeaderboard.suggested_message}
                  </p>
                </div>
              )}
            </CardContent>
          </div>
        </Card>
      )}

      {/* Tabbed Interface for Members */}
      {isMember && !isLicenseeView && (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-zinc-900/50 border border-zinc-800 rounded-lg p-1" data-testid="dashboard-tabs">
            <TabsTrigger 
              value="overview" 
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md gap-2"
              data-testid="tab-overview"
            >
              <Wallet className="w-4 h-4" /> Overview
            </TabsTrigger>
            <TabsTrigger 
              value="profit" 
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md gap-2"
              data-testid="tab-profit"
            >
              <TrendingUp className="w-4 h-4" /> Profit
            </TabsTrigger>
            <TabsTrigger 
              value="trades" 
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md gap-2"
              data-testid="tab-trades"
            >
              <History className="w-4 h-4" /> Trades
            </TabsTrigger>
            <TabsTrigger 
              value="charts" 
              className="data-[state=active]:bg-blue-500 data-[state=active]:text-white rounded-md gap-2"
              data-testid="tab-charts"
            >
              <BarChart3 className="w-4 h-4" /> Charts
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-6 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Performance Chart */}
              <Card className="glass-card lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-white">Performance Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="colorActualOverview" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorProjectedOverview" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                        <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                        <YAxis stroke="#71717A" fontSize={12} />
                        <Tooltip contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }} />
                        <Area type="monotone" dataKey="projected" stroke="#3B82F6" fillOpacity={1} fill="url(#colorProjectedOverview)" name="Projected" />
                        <Area type="monotone" dataKey="actual" stroke="#10B981" fillOpacity={1} fill="url(#colorActualOverview)" name="Actual" />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-zinc-500">
                      No trade data yet. Start trading to see your performance!
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Your Stats */}
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white">Your Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
                      <p className="text-xs text-emerald-400 uppercase tracking-wider">Total Profit</p>
                      <p className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                        {formatCurrency(summary?.total_actual_profit || 0, 'USD')}
                      </p>
                    </div>
                    <div className="p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-blue-500/5 border border-blue-500/20">
                      <p className="text-xs text-blue-400 uppercase tracking-wider">LOT Size</p>
                      <p className="text-2xl font-bold font-mono text-blue-400 mt-1">
                        {((summary?.account_value || 0) / 980).toFixed(2)}
                      </p>
                      <p className="text-xs text-zinc-500 mt-1">Based on account value</p>
                    </div>
                    <div className="p-4 rounded-lg bg-gradient-to-r from-purple-500/10 to-purple-500/5 border border-purple-500/20">
                      <p className="text-xs text-purple-400 uppercase tracking-wider">Projected Daily</p>
                      <p className="text-2xl font-bold font-mono text-purple-400 mt-1">
                        {formatCurrency(((summary?.account_value || 0) / 980) * 15, 'USD')}
                      </p>
                      <p className="text-xs text-zinc-500 mt-1">LOT x 15 multiplier</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Profit Tab */}
          <TabsContent value="profit" className="mt-6 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-emerald-400" /> Profit Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-900/50">
                      <span className="text-zinc-400">Total Deposits</span>
                      <span className="text-xl font-mono text-white">{formatCurrency(summary?.total_deposits || 0, 'USD')}</span>
                    </div>
                    <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-900/50">
                      <span className="text-zinc-400">Total Profit</span>
                      <span className="text-xl font-mono text-emerald-400">{formatCurrency(summary?.total_actual_profit || 0, 'USD')}</span>
                    </div>
                    <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-900/50">
                      <span className="text-zinc-400">Projected Profit</span>
                      <span className="text-xl font-mono text-blue-400">{formatCurrency(summary?.total_projected_profit || 0, 'USD')}</span>
                    </div>
                    <div className="flex justify-between items-center p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                      <span className="text-zinc-300 font-medium">Current Balance</span>
                      <span className="text-2xl font-mono font-bold text-emerald-400">{formatCurrency(summary?.account_value || 0, 'USD')}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Target className="w-5 h-5 text-purple-400" /> Performance Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-900/50">
                      <span className="text-zinc-400">Performance Rate</span>
                      <span className="text-xl font-mono text-purple-400">{formatNumber(summary?.performance_rate || 0, 1)}%</span>
                    </div>
                    <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-900/50">
                      <span className="text-zinc-400">Profit Difference</span>
                      <span className={`text-xl font-mono ${(summary?.profit_difference || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {(summary?.profit_difference || 0) >= 0 ? '+' : ''}{formatCurrency(summary?.profit_difference || 0, 'USD')}
                      </span>
                    </div>
                    <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-900/50">
                      <span className="text-zinc-400">Total Trades</span>
                      <span className="text-xl font-mono text-cyan-400">{summary?.total_trades || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-4 rounded-lg bg-zinc-900/50">
                      <span className="text-zinc-400">Current LOT Size</span>
                      <span className="text-xl font-mono text-blue-400">{((summary?.account_value || 0) / 980).toFixed(2)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Trades Tab */}
          <TabsContent value="trades" className="mt-6">
            <Card className="glass-card">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-cyan-400" /> Trade History
                </CardTitle>
              </CardHeader>
              <CardContent>
                {trades.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full data-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Direction</th>
                          <th>LOT Size</th>
                          <th>Projected</th>
                          <th>Actual</th>
                          <th>Difference</th>
                          <th>Performance</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trades.map((trade) => (
                          <tr key={trade.id}>
                            <td className="font-mono">{new Date(trade.created_at).toLocaleDateString()}</td>
                            <td>
                              <span className={`status-badge ${trade.direction === 'BUY' ? 'direction-buy' : 'direction-sell'}`}>
                                {trade.direction}
                              </span>
                            </td>
                            <td className="font-mono">{trade.lot_size}</td>
                            <td className="font-mono">${formatNumber(trade.projected_profit)}</td>
                            <td className="font-mono">${formatNumber(trade.actual_profit)}</td>
                            <td className={`font-mono ${trade.profit_difference >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {trade.profit_difference >= 0 ? '+' : ''}${formatNumber(trade.profit_difference)}
                            </td>
                            <td>
                              <span className={`status-badge performance-${trade.performance}`}>
                                {trade.performance === 'exceeded' ? 'Exceeded' : trade.performance === 'perfect' ? 'Perfect' : 'Below'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-zinc-500">
                    No trades recorded yet. Log your first trade in the Trade Monitor!
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Charts Tab */}
          <TabsContent value="charts" className="mt-6 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white">Profit Trend</CardTitle>
                </CardHeader>
                <CardContent>
                  {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                        <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                        <YAxis stroke="#71717A" fontSize={12} />
                        <Tooltip contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }} />
                        <Line type="monotone" dataKey="actual" stroke="#10B981" strokeWidth={2} dot={{ fill: '#10B981' }} name="Actual Profit" />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-zinc-500">
                      No trade data yet.
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="glass-card">
                <CardHeader>
                  <CardTitle className="text-white">Projected vs Actual</CardTitle>
                </CardHeader>
                <CardContent>
                  {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                        <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                        <YAxis stroke="#71717A" fontSize={12} />
                        <Tooltip contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }} />
                        <Bar dataKey="projected" fill="#3B82F6" name="Projected" />
                        <Bar dataKey="actual" fill="#10B981" name="Actual" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[300px] flex items-center justify-center text-zinc-500">
                      No trade data yet.
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      )}

      {/* Licensee Dashboard - Year Projections & Family Members */}
      {(isMember || isSimulating) && isLicenseeView && (
        <div className="space-y-6">
          {/* Year-by-Year Growth Projections */}
          <Card className="glass-card" data-testid="licensee-year-projections">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Calendar className="w-5 h-5 text-blue-400" /> Growth Projections
              </CardTitle>
              <p className="text-sm text-zinc-400">Projected values based on quarterly compounding (250 trading days/year)</p>
            </CardHeader>
            <CardContent>
              {yearProjections ? (
                <>
                  {/* License Year End Projections - From Start Date */}
                  {yearProjections.license_year_projections && yearProjections.license_year_projections.length > 0 && (
                    <div className="mb-6">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">License Year End</span>
                        <span className="text-xs text-zinc-500">(from {yearProjections.effective_start_date})</span>
                      </div>
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                        {yearProjections.license_year_projections.map((p) => {
                          const colors = {
                            1: { border: 'border-cyan-500/30', bg: 'from-cyan-500/15 to-cyan-500/5', text: 'text-cyan-400', label: 'text-cyan-300' },
                            2: { border: 'border-teal-500/30', bg: 'from-teal-500/15 to-teal-500/5', text: 'text-teal-400', label: 'text-teal-300' },
                            3: { border: 'border-sky-500/30', bg: 'from-sky-500/15 to-sky-500/5', text: 'text-sky-400', label: 'text-sky-300' },
                            5: { border: 'border-indigo-500/30', bg: 'from-indigo-500/15 to-indigo-500/5', text: 'text-indigo-400', label: 'text-indigo-300' },
                          };
                          const c = colors[p.license_year] || colors[1];
                          return (
                            <div key={`license-${p.license_year}`} className={`p-4 rounded-xl bg-gradient-to-b ${c.bg} border ${c.border}`} data-testid={`license-year-${p.license_year}`}>
                              <p className={`text-xs uppercase tracking-wider font-semibold ${c.label}`}>
                                Year {p.license_year}
                              </p>
                              <p className={`text-xl md:text-2xl font-bold font-mono mt-2 ${c.text}`}>
                                {formatCurrencyCompact(p.projected_value)}
                              </p>
                              <p className="text-[10px] md:text-xs text-zinc-500 mt-1 hidden md:block">
                                {formatCurrency(p.projected_value, 'USD')}
                              </p>
                              <div className="mt-2 flex items-center gap-1">
                                <ArrowUpRight className={`w-3 h-3 ${c.text}`} />
                                <span className={`text-xs font-mono ${c.text}`}>+{p.growth_percent}%</span>
                              </div>
                              <p className="text-[10px] text-zinc-500 mt-0.5">
                                Profit: {formatCurrencyCompact(p.total_profit)}
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {/* Forward Projections - From Today */}
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Forward Projections</span>
                      <span className="text-xs text-zinc-500">(from today's balance)</span>
                    </div>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                      {yearProjections.projections?.map((p) => {
                        const colors = {
                          1: { border: 'border-blue-500/30', bg: 'from-blue-500/15 to-blue-500/5', text: 'text-blue-400', label: 'text-blue-300' },
                          2: { border: 'border-emerald-500/30', bg: 'from-emerald-500/15 to-emerald-500/5', text: 'text-emerald-400', label: 'text-emerald-300' },
                          3: { border: 'border-purple-500/30', bg: 'from-purple-500/15 to-purple-500/5', text: 'text-purple-400', label: 'text-purple-300' },
                          5: { border: 'border-amber-500/30', bg: 'from-amber-500/15 to-amber-500/5', text: 'text-amber-400', label: 'text-amber-300' },
                        };
                        const c = colors[p.years] || colors[1];
                        return (
                          <div key={p.years} className={`p-4 rounded-xl bg-gradient-to-b ${c.bg} border ${c.border}`} data-testid={`projection-${p.years}yr`}>
                            <p className={`text-xs uppercase tracking-wider font-semibold ${c.label}`}>
                              +{p.years} Year{p.years > 1 ? 's' : ''}
                            </p>
                            <p className={`text-xl md:text-2xl font-bold font-mono mt-2 ${c.text}`}>
                              {formatCurrencyCompact(p.projected_value)}
                            </p>
                            <p className="text-[10px] md:text-xs text-zinc-500 mt-1 hidden md:block">
                              {formatCurrency(p.projected_value, 'USD')}
                            </p>
                            <div className="mt-2 flex items-center gap-1">
                              <ArrowUpRight className={`w-3 h-3 ${c.text}`} />
                              <span className={`text-xs font-mono ${c.text}`}>+{p.growth_percent}%</span>
                            </div>
                            <p className="text-[10px] text-zinc-500 mt-0.5">
                              Profit: {formatCurrencyCompact(p.total_profit)}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  
                  {/* Projection chart - Use License Year projections */}
                  <div className="mt-4">
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={yearProjections.license_year_projections?.map(p => ({
                        name: `Yr ${p.license_year}`,
                        value: p.projected_value,
                        profit: p.total_profit
                      })) || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                        <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                        <YAxis stroke="#71717A" fontSize={12} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                          formatter={(value) => formatCurrency(value, 'USD')}
                        />
                        <Bar dataKey="value" fill="#06B6D4" name="License Year End" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </>
              ) : projectionError ? (
                <div className="h-[200px] flex flex-col items-center justify-center text-zinc-500 gap-2" data-testid="projection-error">
                  <AlertTriangle className="w-8 h-8 text-amber-500/50" />
                  <p>Failed to load projections</p>
                  <div className="flex gap-2">
                    <button onClick={loadLicenseeData} className="text-blue-400 text-sm hover:underline">Retry</button>
                    <span className="text-zinc-600">|</span>
                    <button 
                      onClick={async () => {
                        try {
                          const res = await api.get('/profit/debug-calculation');
                          console.log('Debug calculation:', res.data);
                          alert('Debug info copied to console. Press F12 to view.\n\nSteps:\n' + (res.data.steps || []).join('\n'));
                        } catch (e) {
                          alert('Debug failed: ' + e.message);
                        }
                      }} 
                      className="text-amber-400 text-sm hover:underline"
                    >
                      Debug My Account
                    </button>
                  </div>
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-zinc-500">
                  Loading projections...
                </div>
              )}
            </CardContent>
          </Card>

          {/* Family Members Stats */}
          <Card className="glass-card" data-testid="licensee-family-stats">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-emerald-400" /> Family Account Members
              </CardTitle>
              {familyMembers.length > 0 && (
                <p className="text-sm text-zinc-400">{familyMembers.length} member{familyMembers.length !== 1 ? 's' : ''} under your account</p>
              )}
            </CardHeader>
            <CardContent>
              {familyMembers.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full data-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Starting Amount</th>
                        <th>Current Value</th>
                        <th>Profit</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {familyMembers.map((member) => {
                        const profit = member.profit || 0;
                        return (
                          <tr key={member.id} data-testid={`family-member-${member.id}`}>
                            <td>
                              <div>
                                <p className="font-medium text-white">{member.name}</p>
                                <p className="text-xs text-zinc-500">{member.relationship || 'Family'}</p>
                              </div>
                            </td>
                            <td className="font-mono">{formatCurrency(member.starting_amount || 0, 'USD')}</td>
                            <td className="font-mono text-blue-400">{formatCurrency(member.account_value || member.starting_amount || 0, 'USD')}</td>
                            <td className={`font-mono ${profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {profit >= 0 ? '+' : ''}{formatCurrency(profit, 'USD')}
                            </td>
                            <td>
                              <span className={`px-2 py-1 rounded-full text-xs ${member.is_active !== false ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-700 text-zinc-400'}`}>
                                {member.is_active !== false ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="w-10 h-10 text-zinc-600 mx-auto mb-3" />
                  <p className="text-zinc-400">No family members yet</p>
                  <p className="text-xs text-zinc-500 mt-1">Add family members from the Family Accounts page</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Combined Account Overview - shows licensee + family members total */}
          {familyMembers.length > 0 && (
            <Card className="glass-card" data-testid="combined-account-overview">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Wallet className="w-5 h-5 text-blue-400" /> Overall Account Growth
                </CardTitle>
                <p className="text-sm text-zinc-400">Your account + family members combined</p>
              </CardHeader>
              <CardContent>
                {(() => {
                  const ownValue = summary?.account_value || 0;
                  const familyTotal = familyMembers.reduce((sum, m) => sum + (m.account_value || m.starting_amount || 0), 0);
                  const familyProfit = familyMembers.reduce((sum, m) => sum + (m.profit || 0), 0);
                  const combinedValue = ownValue + familyTotal;
                  const combinedProfit = (summary?.total_actual_profit || 0) + familyProfit;
                  return (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="p-4 rounded-xl bg-gradient-to-b from-blue-500/15 to-blue-500/5 border border-blue-500/30">
                        <p className="text-xs text-blue-300 uppercase tracking-wider font-semibold">Your Account</p>
                        <p className="text-xl font-bold font-mono text-blue-400 mt-2">{formatCurrencyCompact(ownValue)}</p>
                        <p className="text-[10px] text-zinc-500 mt-1">{formatCurrency(ownValue, 'USD')}</p>
                      </div>
                      <div className="p-4 rounded-xl bg-gradient-to-b from-purple-500/15 to-purple-500/5 border border-purple-500/30">
                        <p className="text-xs text-purple-300 uppercase tracking-wider font-semibold">Family Total</p>
                        <p className="text-xl font-bold font-mono text-purple-400 mt-2">{formatCurrencyCompact(familyTotal)}</p>
                        <p className="text-[10px] text-zinc-500 mt-1">{formatCurrency(familyTotal, 'USD')}</p>
                      </div>
                      <div className="p-4 rounded-xl bg-gradient-to-b from-emerald-500/15 to-emerald-500/5 border border-emerald-500/30">
                        <p className="text-xs text-emerald-300 uppercase tracking-wider font-semibold">Combined Value</p>
                        <p className="text-xl font-bold font-mono text-emerald-400 mt-2">{formatCurrencyCompact(combinedValue)}</p>
                        <p className="text-[10px] text-zinc-500 mt-1">{formatCurrency(combinedValue, 'USD')}</p>
                      </div>
                      <div className="p-4 rounded-xl bg-gradient-to-b from-amber-500/15 to-amber-500/5 border border-amber-500/30">
                        <p className="text-xs text-amber-300 uppercase tracking-wider font-semibold">Combined Profit</p>
                        <p className="text-xl font-bold font-mono text-amber-400 mt-2">{formatCurrencyCompact(combinedProfit)}</p>
                        <p className="text-[10px] text-zinc-500 mt-1">{formatCurrency(combinedProfit, 'USD')}</p>
                      </div>
                    </div>
                  );
                })()}
              </CardContent>
            </Card>
          )}

          {/* Licensee Stats Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="glass-card">
              <CardContent className="p-6">
                <div className="p-4 rounded-lg bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
                  <p className="text-xs text-emerald-400 uppercase tracking-wider">Current Profit</p>
                  <p className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                    {formatCurrency(summary?.total_actual_profit || 0, 'USD')}
                  </p>
                </div>
              </CardContent>
            </Card>
            <Card className="glass-card">
              <CardContent className="p-6">
                <div className="p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-blue-500/5 border border-blue-500/20">
                  <p className="text-xs text-blue-400 uppercase tracking-wider">Days Manager Traded</p>
                  <p className="text-2xl font-bold font-mono text-blue-400 mt-1">
                    {summary?.total_trades || 0}
                  </p>
                </div>
              </CardContent>
            </Card>
            <Card className="glass-card">
              <CardContent className="p-6">
                <div className="p-4 rounded-lg bg-gradient-to-r from-purple-500/10 to-purple-500/5 border border-purple-500/20">
                  <p className="text-xs text-purple-400 uppercase tracking-wider">Performance Rate</p>
                  <p className="text-2xl font-bold font-mono text-purple-400 mt-1">
                    {formatNumber(summary?.performance_rate || 0, 1)}%
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Original Layout for Admins (no tabs) - hide when simulating a licensee */}
      {!isMember && !isLicenseeView && (
        <>
          {/* Charts & No Trade Members Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Chart */}
        <Card className="glass-card lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-white">Performance Overview</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorProjected" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                  <XAxis dataKey="name" stroke="#71717A" fontSize={12} />
                  <YAxis stroke="#71717A" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#18181B',
                      border: '1px solid #27272A',
                      borderRadius: '8px',
                    }}
                  />
                  <Area type="monotone" dataKey="projected" stroke="#3B82F6" fillOpacity={1} fill="url(#colorProjected)" name="Projected" />
                  <Area type="monotone" dataKey="actual" stroke="#10B981" fillOpacity={1} fill="url(#colorActual)" name="Actual" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-zinc-500">
                No trade data yet. Start trading to see your performance!
              </div>
            )}
          </CardContent>
        </Card>

        {/* No Trade Members Widget - beside Performance Overview */}
        {isAdmin() && !isSimulating && (
          <MissedTradersWidget />
        )}

        {/* Live Activity Feed - Admin only */}
        {isAdmin() && !isSimulating && (
          <ActivityFeed />
        )}
        
        {/* Your Stats - only show if simulating a non-licensee OR not admin */}
        {(!isAdmin() || (isSimulating && !isLicenseeView)) && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white">Your Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
                <p className="text-xs text-emerald-400 uppercase tracking-wider">Total Profit</p>
                <p className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                  {formatCurrency(summary?.total_actual_profit || 0, 'USD')}
                </p>
              </div>
              <div className="p-4 rounded-lg bg-gradient-to-r from-blue-500/10 to-blue-500/5 border border-blue-500/20">
                <p className="text-xs text-blue-400 uppercase tracking-wider">LOT Size</p>
                <p className="text-2xl font-bold font-mono text-blue-400 mt-1">
                  {((summary?.account_value || 0) / 980).toFixed(2)}
                </p>
                <p className="text-xs text-zinc-500 mt-1">Based on account value</p>
              </div>
              <div className="p-4 rounded-lg bg-gradient-to-r from-purple-500/10 to-purple-500/5 border border-purple-500/20">
                <p className="text-xs text-purple-400 uppercase tracking-wider">Projected Daily</p>
                <p className="text-2xl font-bold font-mono text-purple-400 mt-1">
                  {formatCurrency(((summary?.account_value || 0) / 980) * 15, 'USD')}
                </p>
                <p className="text-xs text-zinc-500 mt-1">LOT x 15 multiplier</p>
              </div>
              <div className="p-4 rounded-lg bg-zinc-900/50">
                <p className="text-xs text-zinc-400 uppercase tracking-wider">Performance Rate</p>
                <p className="text-2xl font-bold font-mono text-white mt-1">
                  {formatNumber(summary?.performance_rate || 0, 1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        )}
      </div>

      {/* Recent Trades */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-white">Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          {trades.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Direction</th>
                    <th>LOT Size</th>
                    <th>Projected</th>
                    <th>Actual</th>
                    <th>Difference</th>
                    <th>Performance</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.slice(0, 5).map((trade) => (
                    <tr key={trade.id}>
                      <td className="font-mono">{new Date(trade.created_at).toLocaleDateString()}</td>
                      <td>
                        <span className={`status-badge ${trade.direction === 'BUY' ? 'direction-buy' : 'direction-sell'}`}>
                          {trade.direction}
                        </span>
                      </td>
                      <td className="font-mono">{trade.lot_size}</td>
                      <td className="font-mono">${formatNumber(trade.projected_profit)}</td>
                      <td className="font-mono">${formatNumber(trade.actual_profit)}</td>
                      <td className={`font-mono ${trade.profit_difference >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {trade.profit_difference >= 0 ? '+' : ''}${formatNumber(trade.profit_difference)}
                      </td>
                      <td>
                        <span className={`status-badge performance-${trade.performance}`}>
                          {trade.performance === 'exceeded' ? 'Exceeded' : trade.performance === 'perfect' ? 'Perfect' : 'Below'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No trades recorded yet. Log your first trade in the Trade Monitor!
            </div>
          )}
        </CardContent>
      </Card>
        </>
      )}
    </div>
  );
};
