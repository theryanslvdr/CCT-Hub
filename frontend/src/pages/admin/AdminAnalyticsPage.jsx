import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatNumber } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  DollarSign, TrendingUp, Users, Target, Bell, Archive,
  ChevronLeft, ChevronRight, AlertTriangle, Send, BarChart3,
  LineChart as LineChartIcon, Activity, Trophy
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar 
} from 'recharts';

export const AdminAnalyticsPage = () => {
  const { isSuperAdmin } = useAuth();
  const [teamStats, setTeamStats] = useState(null);
  const [missedTrades, setMissedTrades] = useState(null);
  const [recentTrades, setRecentTrades] = useState([]);
  const [growthData, setGrowthData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notifyingUser, setNotifyingUser] = useState(null);
  
  // Pagination for recent trades
  const [tradesPage, setTradesPage] = useState(1);
  const [tradesTotalPages, setTradesTotalPages] = useState(1);

  useEffect(() => {
    loadAnalytics();
  }, []);

  useEffect(() => {
    loadRecentTrades();
  }, [tradesPage]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [teamRes, missedRes, growthRes] = await Promise.all([
        adminAPI.getTeamAnalytics(),
        adminAPI.getMissedTrades(),
        adminAPI.getGrowthData(),
      ]);
      
      setTeamStats(teamRes.data);
      setMissedTrades(missedRes.data);
      setGrowthData(growthRes.data.chart_data || []);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const loadRecentTrades = async () => {
    try {
      const res = await adminAPI.getRecentTeamTrades(tradesPage, 10);
      setRecentTrades(res.data.trades);
      setTradesTotalPages(res.data.total_pages);
    } catch (error) {
      console.error('Failed to load recent trades:', error);
    }
  };

  const handleNotify = async (userId, userName) => {
    setNotifyingUser(userId);
    try {
      const res = await adminAPI.notifyMissedTrade(userId);
      toast.success(res.data.message || `Notification sent to ${userName}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send notification');
    } finally {
      setNotifyingUser(null);
    }
  };

  const handleArchiveTrades = async () => {
    try {
      const res = await adminAPI.archiveTrades();
      toast.success(`Archived ${res.data.archived_count} trades, deleted ${res.data.deleted_count} old archives`);
      loadAnalytics();
      loadRecentTrades();
    } catch (error) {
      toast.error('Failed to archive trades');
    }
  };

  // Format currency
  const formatCurrency = (value) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
    return `$${formatNumber(value, 2)}`;
  };

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

  const kpiCards = [
    {
      title: 'Team Account Value',
      value: teamStats?.total_account_value || 0,
      icon: DollarSign,
      color: 'blue',
      description: 'Combined value of all traders'
    },
    {
      title: 'Team Total Profit',
      value: teamStats?.total_profit || 0,
      icon: TrendingUp,
      color: 'emerald',
      description: 'Total profit earned by team'
    },
    {
      title: 'Total Traders',
      value: teamStats?.total_traders || 0,
      format: 'number',
      icon: Users,
      color: 'cyan',
      description: 'Active team members'
    },
    {
      title: 'Performance Rate',
      value: teamStats?.performance_rate || 0,
      format: 'percent',
      icon: Target,
      color: 'purple',
      description: `${teamStats?.winning_trades || 0}/${teamStats?.total_trades || 0} winning trades`
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Team Analytics</h1>
          <p className="text-zinc-400">Track your trading team's collective performance</p>
        </div>
        {isSuperAdmin() && (
          <Button 
            variant="outline" 
            onClick={handleArchiveTrades} 
            className="btn-secondary gap-2"
            data-testid="archive-trades-btn"
          >
            <Archive className="w-4 h-4" /> Archive Old Trades
          </Button>
        )}
      </div>

      {/* Team KPIs */}
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
                      {card.format === 'number' && formatNumber(card.value, 0)}
                      {card.format === 'percent' && `${formatNumber(card.value, 1)}%`}
                      {!card.format && formatCurrency(card.value)}
                    </p>
                    <p className="text-xs text-zinc-500 mt-1">{card.description}</p>
                  </div>
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[card.color]} flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Charts & Missed Trades */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Charts with Tabs */}
        <Card className="glass-card lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" /> Performance Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="account_value" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-zinc-900/50">
                <TabsTrigger value="account_value" className="data-[state=active]:bg-blue-500/20">
                  Account Value
                </TabsTrigger>
                <TabsTrigger value="profit" className="data-[state=active]:bg-emerald-500/20">
                  Profit
                </TabsTrigger>
                <TabsTrigger value="trades" className="data-[state=active]:bg-cyan-500/20">
                  Trades
                </TabsTrigger>
                <TabsTrigger value="performance" className="data-[state=active]:bg-purple-500/20">
                  Performance
                </TabsTrigger>
              </TabsList>
              
              {/* Account Value Growth */}
              <TabsContent value="account_value" className="mt-4">
                {growthData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={growthData}>
                      <defs>
                        <linearGradient id="colorAccountValue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                      <XAxis dataKey="date" stroke="#71717A" fontSize={10} tickFormatter={(d) => d.slice(5)} />
                      <YAxis stroke="#71717A" fontSize={10} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                        formatter={(v) => [`$${formatNumber(v, 2)}`, 'Account Value']}
                      />
                      <Area type="monotone" dataKey="account_value" stroke="#3B82F6" fillOpacity={1} fill="url(#colorAccountValue)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-zinc-500">
                    No data available
                  </div>
                )}
              </TabsContent>
              
              {/* Profit Growth */}
              <TabsContent value="profit" className="mt-4">
                {growthData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={growthData}>
                      <defs>
                        <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                      <XAxis dataKey="date" stroke="#71717A" fontSize={10} tickFormatter={(d) => d.slice(5)} />
                      <YAxis stroke="#71717A" fontSize={10} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                        formatter={(v) => [`$${formatNumber(v, 2)}`, 'Total Profit']}
                      />
                      <Area type="monotone" dataKey="total_profit" stroke="#10B981" fillOpacity={1} fill="url(#colorProfit)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-zinc-500">
                    No data available
                  </div>
                )}
              </TabsContent>
              
              {/* Total Trades */}
              <TabsContent value="trades" className="mt-4">
                {growthData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={growthData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                      <XAxis dataKey="date" stroke="#71717A" fontSize={10} tickFormatter={(d) => d.slice(5)} />
                      <YAxis stroke="#71717A" fontSize={10} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                        formatter={(v) => [v, 'Total Trades']}
                      />
                      <Bar dataKey="total_trades" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-zinc-500">
                    No data available
                  </div>
                )}
              </TabsContent>
              
              {/* Performance Rate */}
              <TabsContent value="performance" className="mt-4">
                {growthData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={growthData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272A" />
                      <XAxis dataKey="date" stroke="#71717A" fontSize={10} tickFormatter={(d) => d.slice(5)} />
                      <YAxis stroke="#71717A" fontSize={10} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#18181B', border: '1px solid #27272A', borderRadius: '8px' }}
                        formatter={(v) => [`${formatNumber(v, 1)}%`, 'Performance Rate']}
                      />
                      <Line type="monotone" dataKey="performance_rate" stroke="#A855F7" strokeWidth={2} dot={{ fill: '#A855F7' }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-zinc-500">
                    No data available
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Missed Trades */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" /> Missed Today's Trade
            </CardTitle>
          </CardHeader>
          <CardContent>
            {missedTrades?.missed_members?.length > 0 ? (
              <div className="space-y-3">
                {/* Today's Stats */}
                <div className="p-3 rounded-lg bg-zinc-900/50 mb-4">
                  <p className="text-xs text-zinc-500 mb-1">Team Profit Today</p>
                  <p className="text-2xl font-bold text-emerald-400">${formatNumber(missedTrades.team_profit_today, 2)}</p>
                  {missedTrades.highest_earner && (
                    <p className="text-xs text-zinc-400 mt-1 flex items-center gap-1">
                      <Trophy className="w-3 h-3 text-amber-400" />
                      Top: {missedTrades.highest_earner} (${formatNumber(missedTrades.highest_profit, 2)})
                    </p>
                  )}
                </div>
                
                {/* Members who missed */}
                <div className="space-y-2 max-h-[280px] overflow-y-auto">
                  {missedTrades.missed_members.map((member) => (
                    <div key={member.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/50 hover:bg-zinc-800/50 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-white text-sm font-medium">
                          {member.name?.charAt(0) || '?'}
                        </div>
                        <div>
                          <p className="text-white text-sm font-medium">{member.name}</p>
                          <p className="text-xs text-zinc-500">{member.email}</p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleNotify(member.id, member.name)}
                        disabled={notifyingUser === member.id}
                        className="text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                        data-testid={`notify-${member.id}`}
                      >
                        {notifyingUser === member.id ? (
                          <div className="w-4 h-4 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
                        ) : (
                          <Bell className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-emerald-500/50 mx-auto mb-4" />
                <p className="text-emerald-400 font-medium">Everyone traded today! 🎉</p>
                <p className="text-zinc-500 text-sm mt-1">
                  {missedTrades?.total_traded_today || 0} traders participated
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Team Trades */}
      <Card className="glass-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white">Recent Team Trades</CardTitle>
          <p className="text-sm text-zinc-500">All team trades</p>
        </CardHeader>
        <CardContent>
          {recentTrades.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full data-table">
                  <thead>
                    <tr>
                      <th>Trader</th>
                      <th>Date</th>
                      <th>Direction</th>
                      <th>LOT</th>
                      <th>Projected</th>
                      <th>Actual</th>
                      <th>P/L</th>
                      <th>Performance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentTrades.map((trade) => (
                      <tr key={trade.id}>
                        <td className="font-medium text-white">{trade.trader_name}</td>
                        <td className="font-mono text-zinc-400">
                          {new Date(trade.created_at).toLocaleDateString()}
                        </td>
                        <td>
                          <span className={`status-badge ${trade.direction === 'BUY' ? 'direction-buy' : 'direction-sell'}`}>
                            {trade.direction}
                          </span>
                        </td>
                        <td className="font-mono text-purple-400">{trade.lot_size?.toFixed(2)}</td>
                        <td className="font-mono text-blue-400">${formatNumber(trade.projected_profit, 2)}</td>
                        <td className="font-mono text-emerald-400">${formatNumber(trade.actual_profit, 2)}</td>
                        <td className={`font-mono ${trade.profit_difference >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {trade.profit_difference >= 0 ? '+' : ''}${formatNumber(trade.profit_difference, 2)}
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
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-zinc-800">
                <p className="text-sm text-zinc-500">Page {tradesPage} of {tradesTotalPages}</p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setTradesPage(p => Math.max(1, p - 1))}
                    disabled={tradesPage === 1}
                    className="btn-secondary"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setTradesPage(p => Math.min(tradesTotalPages, p + 1))}
                    disabled={tradesPage === tradesTotalPages}
                    className="btn-secondary"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              No trades recorded yet.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Performers */}
      {teamStats?.member_stats?.length > 0 && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Trophy className="w-5 h-5 text-amber-400" /> Top Performers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {teamStats.member_stats.slice(0, 6).map((member, index) => (
                <div 
                  key={member.id} 
                  className={`p-4 rounded-lg bg-zinc-900/50 flex items-center gap-4 ${index === 0 ? 'border border-amber-500/30' : ''}`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                    index === 0 ? 'bg-gradient-to-br from-amber-500 to-orange-500' :
                    index === 1 ? 'bg-gradient-to-br from-zinc-400 to-zinc-500' :
                    index === 2 ? 'bg-gradient-to-br from-amber-700 to-amber-800' :
                    'bg-gradient-to-br from-blue-500 to-cyan-500'
                  }`}>
                    {index < 3 ? index + 1 : member.name?.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-medium">{member.name}</p>
                    <p className="text-xs text-zinc-500">{member.trades_count} trades</p>
                  </div>
                  <div className="text-right">
                    <p className="text-emerald-400 font-mono font-bold">${formatNumber(member.total_profit, 2)}</p>
                    <p className="text-xs text-zinc-500">${formatNumber(member.account_value, 2)} value</p>
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
