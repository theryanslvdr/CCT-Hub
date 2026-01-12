import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useBVE } from '@/contexts/BVEContext';
import { profitAPI, tradeAPI, currencyAPI, adminAPI } from '@/lib/api';
import api from '@/lib/api';
import { formatCurrency, formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, TrendingDown, DollarSign, Activity, Target, ArrowUpRight, ArrowDownRight, Eye, Wallet, BarChart3, History, FlaskConical } from 'lucide-react';
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

  // Simulation values
  const simulatedMemberId = getSimulatedMemberId();
  const simulatedMemberName = getSimulatedMemberName();
  const simulatedAccountValue = getSimulatedAccountValue();
  const simulatedTotalProfit = getSimulatedTotalProfit();
  const isSimulating = simulatedView && isMasterAdmin();
  
  // Check if user is a regular member (not admin)
  const isMember = !isAdmin();

  const loadDashboardData = useCallback(async () => {
    try {
      // If simulating a specific member, fetch their data from API
      if (isSimulating && simulatedMemberId) {
        // Fetch the simulated member's data - API returns license.current_amount for licensees
        const [memberRes, tradesRes, signalRes, ratesRes] = await Promise.all([
          adminAPI.getMemberDetails(simulatedMemberId),
          tradeAPI.getLogs(10, simulatedMemberId),
          tradeAPI.getActiveSignal(),
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
          performance_rate: 0,
          profit_difference: 0,
        });
        setTrades(tradesRes.data || []);
        setSignal(signalRes.data.signal);
        setRates(ratesRes.data.rates || {});
      } else if (isSimulating && !simulatedMemberId) {
        // Role-based simulation (demo mode) - use demo values
        const [tradesRes, signalRes, ratesRes] = await Promise.all([
          tradeAPI.getLogs(10),
          tradeAPI.getActiveSignal(),
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
        const [summaryRes, tradesRes, signalRes, ratesRes] = await Promise.all([
          profitAPI.getSummary(),
          tradeAPI.getLogs(10),
          tradeAPI.getActiveSignal(),
          currencyAPI.getRates('USDT'),
        ]);

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
  }, [isSimulating, simulatedMemberId, simulatedAccountValue, simulatedTotalProfit]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData, simulatedView]); // Also re-run when simulatedView changes

  const kpiCards = [
    {
      title: 'Account Value',
      value: summary?.account_value || 0,
      format: 'currency',
      icon: DollarSign,
      change: summary?.profit_difference || 0,
      color: 'blue',
    },
    {
      title: 'Total Profit',
      value: summary?.total_actual_profit || 0,
      format: 'currency',
      icon: TrendingUp,
      change: summary?.performance_rate || 0,
      changeFormat: 'percent',
      color: 'emerald',
    },
    {
      title: 'Total Trades',
      value: summary?.total_trades || 0,
      format: 'number',
      icon: Activity,
      color: 'cyan',
    },
    {
      title: 'Performance Rate',
      value: summary?.performance_rate || 0,
      format: 'percent',
      icon: Target,
      color: 'purple',
    },
  ];

  // Prepare chart data from trades
  const chartData = trades.slice().reverse().map((trade, index) => ({
    name: `Trade ${index + 1}`,
    projected: trade.projected_profit,
    actual: trade.actual_profit,
  }));

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

      {/* Welcome Section */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">
              Welcome back, {displayName}!
            </h2>
            <p className="text-zinc-400 mt-1">
              Here&apos;s your trading overview for today.
            </p>
          </div>
          {signal && (
            <div className="glass-highlight px-6 py-3 flex items-center gap-4">
              <div>
                <p className="text-xs text-zinc-400 uppercase tracking-wider">Active Signal</p>
                <p className="text-lg font-bold text-white">{signal.product}</p>
              </div>
              <div className={`px-4 py-2 rounded-lg font-bold ${signal.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                {signal.direction}
              </div>
              <div className="text-right">
                <p className="text-xs text-zinc-400">Trade Time (UTC)</p>
                <p className="text-lg font-mono text-blue-400">{signal.trade_time}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card, index) => {
          const Icon = card.icon;
          const colorClasses = {
            blue: 'from-blue-500 to-blue-600',
            emerald: 'from-emerald-500 to-emerald-600',
            cyan: 'from-cyan-500 to-cyan-600',
            purple: 'from-purple-500 to-purple-600',
          };

          return (
            <Card key={index} className="glass-card hover:border-blue-500/30 transition-all" data-testid={`kpi-${card.title.toLowerCase().replace(/\s/g, '-')}`}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-zinc-400">{card.title}</p>
                    <p className="text-3xl font-bold font-mono text-white mt-2">
                      {card.format === 'currency' && formatCurrency(card.value, 'USD')}
                      {card.format === 'number' && formatNumber(card.value, 0)}
                      {card.format === 'percent' && `${formatNumber(card.value, 1)}%`}
                    </p>
                  </div>
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[card.color]} flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                </div>
                {card.change !== undefined && card.changeFormat && (
                  <div className="mt-4 flex items-center gap-1">
                    {card.change >= 0 ? (
                      <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <ArrowDownRight className="w-4 h-4 text-red-400" />
                    )}
                    <span className={card.change >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                      {card.changeFormat === 'percent' ? `${formatNumber(Math.abs(card.change), 1)}%` : formatCurrency(Math.abs(card.change))}
                    </span>
                    <span className="text-zinc-500 text-sm">vs projected</span>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Tabbed Interface for Members */}
      {isMember && (
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
                      <p className="text-xs text-zinc-500 mt-1">LOT × 15 multiplier</p>
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

      {/* Original Layout for Admins (no tabs) */}
      {!isMember && (
        <>
          {/* Charts & Recent Trades */}
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

        {/* User Performance Stats */}
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
                <p className="text-xs text-zinc-500 mt-1">LOT × 15 multiplier</p>
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
