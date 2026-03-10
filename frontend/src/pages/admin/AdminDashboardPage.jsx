import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { adminAPI, aiAssistantAPI } from '@/lib/api';
import { toast } from 'sonner';
import {
  Users, TrendingUp, DollarSign, Activity, Shield, Settings,
  BarChart3, Radio, HelpCircle, Sparkles, Award, MessageSquare,
  ArrowUpRight, Clock, AlertTriangle, ChevronRight, BrainCircuit
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const StatCard = ({ label, value, subtext, icon: Icon, color, link }) => {
  const Wrapper = link ? Link : 'div';
  return (
    <Wrapper to={link} className={`relative overflow-hidden bg-[#111111]/80 border border-white/[0.06] hover:border-white/[0.1] rounded-xl p-4 transition-all ${link ? 'cursor-pointer group' : ''}`} data-testid={`admin-stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <div className={`absolute -top-6 -right-6 w-24 h-24 bg-gradient-to-br ${color} rounded-full blur-2xl opacity-[0.06] pointer-events-none`} />
      <div className="flex items-start justify-between relative">
        <div>
          <p className="text-[11px] text-zinc-500 uppercase tracking-wider font-medium">{label}</p>
          <p className="text-2xl font-bold font-mono text-white mt-1">{value}</p>
          {subtext && <p className="text-[10px] text-zinc-600 mt-0.5">{subtext}</p>}
        </div>
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center shadow-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      {link && <ChevronRight className="absolute bottom-3 right-3 w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />}
    </Wrapper>
  );
};

const QuickAction = ({ label, desc, icon: Icon, color, link }) => (
  <Link to={link} className="flex items-center gap-4 p-4 rounded-xl bg-[#111111]/60 border border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.03] transition-all group" data-testid={`quick-action-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center flex-shrink-0`}>
      <Icon className="w-5 h-5 text-white" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-white">{label}</p>
      <p className="text-[11px] text-zinc-500">{desc}</p>
    </div>
    <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors flex-shrink-0" />
  </Link>
);

const AdminDashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({});
  const [aiStats, setAiStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [membersRes, aiRes] = await Promise.all([
          adminAPI.getMembers().catch(() => ({ data: { members: [] } })),
          aiAssistantAPI.getStats().catch(() => ({ data: {} })),
        ]);
        const members = membersRes.data.members || membersRes.data || [];
        setStats({
          totalMembers: Array.isArray(members) ? members.length : 0,
          activeToday: Array.isArray(members) ? members.filter(m => m.logged_today).length : 0,
        });
        setAiStats(aiRes.data || {});
      } catch { /* ignore */ }
      setLoading(false);
    };
    loadStats();
  }, []);

  return (
    <div className="space-y-6" data-testid="admin-dashboard-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-1">Welcome back, {user?.full_name}. Here's your platform overview.</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Total Members" value={stats.totalMembers ?? '--'} icon={Users} color="from-orange-500 to-amber-600" link="/admin/members" />
        <StatCard label="Active Today" value={stats.activeToday ?? '--'} subtext="Logged trades today" icon={Activity} color="from-emerald-500 to-emerald-600" />
        <StatCard label="AI Sessions" value={aiStats.total_sessions ?? '--'} subtext={`${aiStats.pending_unanswered ?? 0} pending`} icon={BrainCircuit} color="from-purple-500 to-purple-600" link="/admin/ai-training" />
        <StatCard label="Knowledge Base" value={aiStats.knowledge_entries ?? '--'} subtext={`${aiStats.escalation_rate ?? 0}% escalation`} icon={Sparkles} color="from-teal-500 to-teal-600" link="/admin/ai-training" />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">Quick Actions</h2>
          <div className="space-y-2">
            <QuickAction label="Manage Members" desc="View, edit, and manage all members" icon={Users} color="from-orange-500 to-amber-600" link="/admin/members" />
            <QuickAction label="Trading Signals" desc="Create and manage trade signals" icon={Radio} color="from-emerald-500 to-emerald-600" link="/admin/signals" />
            <QuickAction label="Quiz Manager" desc="Generate and approve community quizzes" icon={HelpCircle} color="from-purple-500 to-purple-600" link="/admin/quizzes" />
            <QuickAction label="AI Training" desc="Configure RyAI and zxAI assistants" icon={BrainCircuit} color="from-teal-500 to-teal-600" link="/admin/ai-training" />
            <QuickAction label="Rewards Admin" desc="Manage points, badges, and leaderboard" icon={Award} color="from-amber-500 to-amber-600" link="/admin/rewards" />
            <QuickAction label="Platform Settings" desc="Configure platform appearance and features" icon={Settings} color="from-zinc-500 to-zinc-600" link="/admin/settings" />
          </div>
        </div>

        {/* System Status */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">Platform Overview</h2>
          <Card className="bg-[#111111]/80 border-white/[0.06] rounded-xl overflow-hidden">
            <CardContent className="p-0">
              {[
                { label: 'Members', link: '/admin/members', icon: Users, stat: `${stats.totalMembers ?? 0} total`, color: 'text-orange-400' },
                { label: 'AI Conversations', link: '/admin/ai-training', icon: MessageSquare, stat: `${aiStats.total_messages ?? 0} messages`, color: 'text-purple-400' },
                { label: 'Analytics', link: '/admin/analytics', icon: BarChart3, stat: 'View insights', color: 'text-emerald-400' },
                { label: 'Transactions', link: '/admin/transactions', icon: DollarSign, stat: 'Review pending', color: 'text-amber-400' },
                { label: 'System Health', link: '/admin/system-health', icon: Shield, stat: 'Check status', color: 'text-teal-400' },
                { label: 'Referral Tree', link: '/admin/referral-tree', icon: TrendingUp, stat: 'View network', color: 'text-pink-400' },
              ].map((item, i) => (
                <Link key={i} to={item.link} className="flex items-center gap-3 px-4 py-3 border-b border-white/[0.04] last:border-0 hover:bg-white/[0.03] transition-colors group">
                  <item.icon className={`w-4 h-4 ${item.color}`} />
                  <span className="flex-1 text-sm text-zinc-300">{item.label}</span>
                  <span className="text-xs text-zinc-600">{item.stat}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                </Link>
              ))}
            </CardContent>
          </Card>

          {/* AI Assistant Status */}
          {aiStats.pending_unanswered > 0 && (
            <Link to="/admin/ai-training" className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/5 border border-amber-500/15 hover:border-amber-500/25 transition-all">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-300">{aiStats.pending_unanswered} Unanswered AI Questions</p>
                <p className="text-[11px] text-zinc-500">Members need your help — answer to train the AI</p>
              </div>
              <ArrowUpRight className="w-4 h-4 text-amber-400" />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage;
