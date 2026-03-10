import React, { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatNumber } from '@/lib/utils';
import { AIDailyReport } from '@/components/AIFeatures';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  DollarSign, TrendingUp, Users, Target, Bell, Archive,
  ChevronLeft, ChevronRight, AlertTriangle, BarChart3,
  Activity, Trophy, Calendar, User, Filter, X, Image, Download, Loader2, Eye
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar 
} from 'recharts';
import api from '@/lib/api';

export const AdminAnalyticsPage = () => {
  const { isSuperAdmin } = useAuth();
  const [teamStats, setTeamStats] = useState(null);
  const [missedTrades, setMissedTrades] = useState(null);
  const [recentTrades, setRecentTrades] = useState([]);
  const [growthData, setGrowthData] = useState([]);
  const [topPerformers, setTopPerformers] = useState([]);
  const [excludeNonTraders, setExcludeNonTraders] = useState(true);
  const [loading, setLoading] = useState(true);
  const [notifyingUser, setNotifyingUser] = useState(null);
  
  // Member selector state
  const [selectedMember, setSelectedMember] = useState('all');
  const [memberAnalytics, setMemberAnalytics] = useState(null);
  const [memberDialogOpen, setMemberDialogOpen] = useState(false);
  
  // Team Report state
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [reportPeriod, setReportPeriod] = useState('monthly');
  const [reportLoading, setReportLoading] = useState(false);
  const [reportPreview, setReportPreview] = useState(null);
  
  // Date range filter state
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [dateFilterApplied, setDateFilterApplied] = useState(false);
  
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
      const [teamRes, missedRes, growthRes, performersRes] = await Promise.all([
        adminAPI.getTeamAnalytics(),
        adminAPI.getMissedTrades(),
        adminAPI.getGrowthData(),
        adminAPI.getTopPerformers(10, excludeNonTraders),
      ]);
      
      setTeamStats(teamRes.data);
      setMissedTrades(missedRes.data);
      setGrowthData(growthRes.data.chart_data || []);
      setTopPerformers(performersRes.data.performers || []);
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

  const loadMemberAnalytics = async (memberId) => {
    try {
      const res = await adminAPI.getMemberAnalytics(memberId);
      setMemberAnalytics(res.data);
      setMemberDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load member analytics');
    }
  };

  const handleApplyDateFilter = async () => {
    if (!startDate && !endDate) {
      toast.error('Please select at least one date');
      return;
    }
    
    try {
      const res = await adminAPI.getGrowthData(startDate || undefined, endDate || undefined);
      setGrowthData(res.data.chart_data || []);
      setDateFilterApplied(true);
      toast.success('Date filter applied');
    } catch (error) {
      toast.error('Failed to apply date filter');
    }
  };

  const handleClearDateFilter = async () => {
    setStartDate('');
    setEndDate('');
    setDateFilterApplied(false);
    
    try {
      const res = await adminAPI.getGrowthData();
      setGrowthData(res.data.chart_data || []);
    } catch (error) {
      console.error('Failed to reload growth data');
    }
  };

  // Team Report handlers
  const handleGenerateReport = async () => {
    setReportLoading(true);
    try {
      const res = await api.get('/admin/analytics/report/base64', { params: { period: reportPeriod } });
      setReportPreview(res.data);
      toast.success('Report generated successfully!');
    } catch (error) {
      console.error('Failed to generate report:', error);
      toast.error('Failed to generate report');
    } finally {
      setReportLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    setReportLoading(true);
    try {
      const res = await api.get('/admin/analytics/report/image', { params: { period: reportPeriod }, responseType: 'blob' });
      const blob = res.data;
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `team_performance_report_${reportPeriod}_${new Date().toISOString().split('T')[0]}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded!');
    } catch (error) {
      console.error('Failed to download report:', error);
      toast.error('Failed to download report');
    } finally {
      setReportLoading(false);
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

  const handleMemberChange = (value) => {
    setSelectedMember(value);
    if (value !== 'all') {
      loadMemberAnalytics(value);
    }
  };

  // Format currency
  const formatCurrency = (value) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
    return `$${formatNumber(value, 2)}`;
  };

  // Get role badge class
  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'master_admin': return 'bg-amber-500/20 text-amber-400';
      case 'super_admin': return 'bg-purple-500/20 text-purple-400';
      case 'basic_admin': 
      case 'admin': return 'bg-orange-500/10 text-orange-400';
      default: return 'bg-zinc-500/20 text-zinc-400';
    }
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
          <p className="text-zinc-400">Track your trading team&apos;s collective performance</p>
        </div>
        <div className="flex gap-2">
          {/* Member Selector */}
          <Select value={selectedMember} onValueChange={handleMemberChange}>
            <SelectTrigger className="w-48 input-dark" data-testid="member-selector">
              <User className="w-4 h-4 mr-2" />
              <SelectValue placeholder="All Members" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Members</SelectItem>
              {teamStats?.member_stats?.map((member) => (
                <SelectItem key={member.id} value={member.id}>
                  {member.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
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
          
          {/* Generate Report Button */}
          <Button 
            variant="outline" 
            onClick={() => setReportDialogOpen(true)}
            className="btn-secondary gap-2 text-cyan-400 hover:text-cyan-300"
            data-testid="generate-team-report-btn"
          >
            <Image className="w-4 h-4" /> Generate Report
          </Button>
        </div>
      </div>

      {/* Team Report Dialog */}
      <Dialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Image className="w-5 h-5 text-cyan-400" /> Team Performance Report
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-zinc-300">Report Period</Label>
              <Select value={reportPeriod} onValueChange={setReportPeriod}>
                <SelectTrigger className="input-dark mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800">
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly (Last 7 days)</SelectItem>
                  <SelectItem value="monthly">Monthly (Last 30 days)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {reportPreview && (
              <div className="rounded-lg border border-zinc-800 overflow-hidden">
                <img 
                  src={`data:image/png;base64,${reportPreview.image_base64}`} 
                  alt="Team Performance Report Preview" 
                  className="w-full"
                />
              </div>
            )}
            
            <div className="flex gap-3">
              <Button 
                onClick={handleGenerateReport} 
                disabled={reportLoading}
                className="flex-1 btn-secondary"
              >
                {reportLoading ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
                ) : (
                  <><Eye className="w-4 h-4 mr-2" /> Preview Report</>
                )}
              </Button>
              <Button 
                onClick={handleDownloadReport} 
                disabled={reportLoading}
                className="flex-1 btn-primary"
              >
                {reportLoading ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Downloading...</>
                ) : (
                  <><Download className="w-4 h-4 mr-2" /> Download PNG</>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* AI Daily Report */}
      <AIDailyReport />

      {/* Team KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card, index) => {
          const Icon = card.icon;
          const colorClasses = {
            blue: 'from-orange-500 to-amber-600',
            emerald: 'from-emerald-500 to-emerald-600',
            cyan: 'from-cyan-500 to-cyan-600',
            purple: 'from-purple-500 to-purple-600',
          };

          return (
            <Card key={index} className="glass-card hover:border-orange-500/20 transition-all" data-testid={`kpi-${card.title.toLowerCase().replace(/\s/g, '-')}`}>
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
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <CardTitle className="text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-orange-400" /> Performance Overview
              </CardTitle>
              
              {/* Date Range Filter */}
              <div className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <Label className="text-xs text-zinc-500">From</Label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="input-dark w-36 h-8 text-sm"
                    data-testid="start-date-picker"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Label className="text-xs text-zinc-500">To</Label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="input-dark w-36 h-8 text-sm"
                    data-testid="end-date-picker"
                  />
                </div>
                <Button
                  size="sm"
                  onClick={handleApplyDateFilter}
                  className="btn-primary h-8"
                  data-testid="apply-date-filter"
                >
                  <Filter className="w-3 h-3 mr-1" /> Apply
                </Button>
                {dateFilterApplied && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleClearDateFilter}
                    className="h-8 text-zinc-400 hover:text-white"
                  >
                    <X className="w-3 h-3 mr-1" /> Clear
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="account_value" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-zinc-900/50">
                <TabsTrigger value="account_value" className="data-[state=active]:bg-orange-500/10">
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
              <AlertTriangle className="w-5 h-5 text-amber-400" /> Missed Today&apos;s Trade
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

        {/* Top Performers Card */}
        <Card className="glass-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white flex items-center gap-2">
                <Trophy className="w-5 h-5 text-amber-400" />
                Top Performers
              </CardTitle>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={excludeNonTraders}
                    onChange={(e) => {
                      setExcludeNonTraders(e.target.checked);
                      // Reload performers with new filter
                      adminAPI.getTopPerformers(10, e.target.checked)
                        .then(res => setTopPerformers(res.data.performers || []))
                        .catch(() => {});
                    }}
                    className="w-4 h-4 rounded bg-zinc-800 border-zinc-700 text-orange-500 focus:ring-orange-500"
                  />
                  Active traders only
                </label>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {topPerformers.length > 0 ? (
              <div className="space-y-3">
                {topPerformers.map((performer, index) => (
                  <div 
                    key={performer.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/30 hover:bg-zinc-800/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                        index === 0 ? 'bg-amber-500/20 text-amber-400' :
                        index === 1 ? 'bg-zinc-400/20 text-zinc-300' :
                        index === 2 ? 'bg-orange-600/20 text-orange-400' :
                        'bg-zinc-700/50 text-zinc-400'
                      }`}>
                        {performer.rank}
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">{performer.full_name}</p>
                        <p className="text-xs text-zinc-500">{performer.total_trades} trades</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-mono font-medium ${performer.total_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {performer.total_profit >= 0 ? '+' : ''}${formatNumber(performer.total_profit, 2)}
                      </p>
                      <p className="text-xs text-zinc-500">
                        Avg: ${formatNumber(performer.avg_profit_per_trade, 2)}/trade
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Trophy className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
                <p className="text-zinc-500">No performers found</p>
                <p className="text-zinc-600 text-sm mt-1">
                  {excludeNonTraders ? 'Try unchecking "Active traders only"' : 'No trade data available'}
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
                        <td className="font-mono text-orange-400">${formatNumber(trade.projected_profit, 2)}</td>
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
                  className={`p-4 rounded-lg bg-zinc-900/50 flex items-center gap-4 cursor-pointer hover:bg-zinc-800/50 transition-colors ${index === 0 ? 'border border-amber-500/30' : ''}`}
                  onClick={() => loadMemberAnalytics(member.id)}
                  data-testid={`performer-${member.id}`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                    index === 0 ? 'bg-gradient-to-br from-amber-500 to-orange-500' :
                    index === 1 ? 'bg-gradient-to-br from-zinc-400 to-zinc-500' :
                    index === 2 ? 'bg-gradient-to-br from-amber-700 to-amber-800' :
                    'bg-gradient-to-br from-orange-500 to-amber-500'
                  }`}>
                    {index < 3 ? index + 1 : member.name?.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-white font-medium">{member.name}</p>
                      {member.role && member.role !== 'user' && member.role !== 'member' && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getRoleBadgeClass(member.role)}`}>
                          {member.role.replace('_', ' ')}
                        </span>
                      )}
                    </div>
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

      {/* Member Analytics Dialog */}
      <Dialog open={memberDialogOpen} onOpenChange={setMemberDialogOpen}>
        <DialogContent className="glass-card border-zinc-800 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <User className="w-5 h-5" /> {memberAnalytics?.member?.name || 'Member'} Analytics
            </DialogTitle>
          </DialogHeader>
          {memberAnalytics ? (
            <div className="space-y-6 mt-4">
              {/* Member Info */}
              <div className="flex items-center gap-4 p-4 rounded-lg bg-zinc-900/50">
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center text-white text-xl font-bold">
                  {memberAnalytics.member.name?.charAt(0)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-white font-bold text-lg">{memberAnalytics.member.name}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getRoleBadgeClass(memberAnalytics.member.role)}`}>
                      {memberAnalytics.member.role?.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-zinc-400 text-sm">{memberAnalytics.member.email}</p>
                  <p className="text-zinc-500 text-xs">Joined {new Date(memberAnalytics.member.joined).toLocaleDateString()}</p>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-zinc-900/50 text-center">
                  <p className="text-xs text-zinc-500">Account Value</p>
                  <p className="text-xl font-bold text-orange-400 font-mono">${formatNumber(memberAnalytics.stats.account_value, 2)}</p>
                </div>
                <div className="p-4 rounded-lg bg-zinc-900/50 text-center">
                  <p className="text-xs text-zinc-500">LOT Size</p>
                  <p className="text-xl font-bold text-purple-400 font-mono">{memberAnalytics.stats.lot_size.toFixed(2)}</p>
                </div>
                <div className="p-4 rounded-lg bg-zinc-900/50 text-center">
                  <p className="text-xs text-zinc-500">Total Profit</p>
                  <p className="text-xl font-bold text-emerald-400 font-mono">${formatNumber(memberAnalytics.stats.total_profit, 2)}</p>
                </div>
                <div className="p-4 rounded-lg bg-zinc-900/50 text-center">
                  <p className="text-xs text-zinc-500">Performance</p>
                  <p className="text-xl font-bold text-amber-400 font-mono">{memberAnalytics.stats.performance_rate}%</p>
                </div>
              </div>

              {/* Trade Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 rounded-lg bg-zinc-900/50 text-center">
                  <p className="text-xs text-zinc-500">Total Trades</p>
                  <p className="text-lg font-bold text-white">{memberAnalytics.stats.total_trades}</p>
                </div>
                <div className="p-3 rounded-lg bg-zinc-900/50 text-center">
                  <p className="text-xs text-zinc-500">Winning Trades</p>
                  <p className="text-lg font-bold text-emerald-400">{memberAnalytics.stats.winning_trades}</p>
                </div>
                <div className="p-3 rounded-lg bg-zinc-900/50 text-center">
                  <p className="text-xs text-zinc-500">Total Deposits</p>
                  <p className="text-lg font-bold text-cyan-400">${formatNumber(memberAnalytics.stats.total_deposits, 2)}</p>
                </div>
              </div>

              {/* Recent Trades */}
              {memberAnalytics.recent_trades?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-zinc-400 mb-3">Recent Trades</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {memberAnalytics.recent_trades.map((trade, idx) => (
                      <div key={idx} className="flex justify-between items-center p-3 rounded-lg bg-zinc-900/50">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${trade.direction === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                            {trade.direction}
                          </span>
                          <span className="text-zinc-400 text-sm">{new Date(trade.created_at).toLocaleDateString()}</span>
                        </div>
                        <span className={`font-mono ${trade.actual_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {trade.actual_profit >= 0 ? '+' : ''}${trade.actual_profit?.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-orange-500/20 border-t-orange-500 rounded-full animate-spin" />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
