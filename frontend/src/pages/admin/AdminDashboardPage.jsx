import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { adminAPI, aiAssistantAPI } from '@/lib/api';
import { toast } from 'sonner';
import {
  Users, TrendingUp, DollarSign, Activity, Shield, Settings,
  BarChart3, Radio, HelpCircle, Sparkles, Award,
  ArrowUpRight, AlertTriangle, ChevronRight, BrainCircuit,
  Camera, UserCheck, UserX
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const StatCard = ({ label, value, subtext, icon: Icon, color, link }) => {
  const Wrapper = link ? Link : 'div';
  const iconGlow = {
    'from-orange-500 to-amber-600': 'rgba(249,115,22,0.25)',
    'from-emerald-500 to-emerald-600': 'rgba(16,185,129,0.25)',
    'from-teal-500 to-teal-600': 'rgba(20,184,166,0.25)',
    'from-purple-500 to-purple-600': 'rgba(139,92,246,0.25)',
    'from-blue-500 to-blue-600': 'rgba(59,130,246,0.25)',
  };
  return (
    <Wrapper to={link} className={`kpi-card p-5 transition-all ${link ? 'cursor-pointer group' : ''}`} data-testid={`admin-stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <div className="flex items-start justify-between relative">
        <div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-semibold">{label}</p>
          <p className="text-3xl font-bold font-mono text-white mt-2 tracking-tight">{value}</p>
          {subtext && <p className="text-[10px] text-zinc-600 mt-1">{subtext}</p>}
        </div>
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center`} style={{ boxShadow: `0 0 20px ${iconGlow[color] || 'rgba(249,115,22,0.2)'}` }}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      {link && <ChevronRight className="absolute bottom-3 right-3 w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />}
    </Wrapper>
  );
};

const QuickAction = ({ label, desc, icon: Icon, color, link }) => (
  <Link to={link} className="flex items-center gap-4 p-4 rounded-2xl bg-[#111111] border border-[#222222] hover:border-[#2a2a2a] transition-all group" data-testid={`quick-action-${label.toLowerCase().replace(/\s/g, '-')}`}>
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
  const [cleanup, setCleanup] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [membersRes, aiRes, cleanupRes] = await Promise.all([
          adminAPI.getMembers().catch(() => ({ data: { members: [] } })),
          aiAssistantAPI.getStats().catch(() => ({ data: {} })),
          adminAPI.getCleanupOverview().catch(() => ({ data: null })),
        ]);
        const members = membersRes.data.members || membersRes.data || [];
        setStats({
          totalMembers: membersRes.data.total || (Array.isArray(members) ? members.length : 0),
          activeToday: Array.isArray(members) ? members.filter(m => m.logged_today).length : 0,
        });
        setAiStats(aiRes.data || {});
        setCleanup(cleanupRes.data);
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

      {/* Cleanup Alerts */}
      {cleanup && (cleanup.pending_proofs > 0 || cleanup.fraud_warning_count > 0 || cleanup.in_danger_count > 0 || cleanup.pending_registrations > 0) && (
        <Link to="/admin/cleanup" className="block p-4 rounded-2xl bg-[#111111] border border-red-500/15 hover:border-red-500/25 transition-all group" data-testid="cleanup-alert-banner">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-400" />
              <h2 className="text-sm font-semibold text-white">Action Required</h2>
            </div>
            <div className="flex items-center gap-1 text-xs text-zinc-500 group-hover:text-zinc-400 transition-colors">
              View Cleanup Hub <ArrowUpRight className="w-3 h-3" />
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { label: 'Pending Proofs', val: cleanup.pending_proofs, icon: Camera, color: 'text-blue-400', show: cleanup.pending_proofs > 0 },
              { label: 'Fraud Warnings', val: cleanup.fraud_warning_count, icon: Shield, color: 'text-red-400', show: cleanup.fraud_warning_count > 0 },
              { label: 'In Danger', val: cleanup.in_danger_count, icon: AlertTriangle, color: 'text-amber-400', show: cleanup.in_danger_count > 0 },
              { label: 'Auto-Suspended', val: cleanup.auto_suspended_count, icon: UserX, color: 'text-rose-400', show: cleanup.auto_suspended_count > 0 },
              { label: 'Pending Signups', val: cleanup.pending_registrations, icon: UserCheck, color: 'text-cyan-400', show: cleanup.pending_registrations > 0 },
            ].filter(i => i.show).map(item => (
              <div key={item.label} className="flex items-center gap-2 bg-white/[0.02] rounded-lg px-3 py-2">
                <item.icon className={`w-4 h-4 ${item.color} shrink-0`} />
                <div>
                  <p className={`text-lg font-bold font-mono ${item.color}`}>{item.val}</p>
                  <p className="text-[9px] text-zinc-500">{item.label}</p>
                </div>
              </div>
            ))}
          </div>
        </Link>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Management */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">Management</h2>
          <div className="space-y-2">
            <QuickAction label="Manage Members" desc="View, edit, and manage all members" icon={Users} color="from-orange-500 to-amber-600" link="/admin/members" />
            <QuickAction label="Trading Signals" desc="Create and manage trade signals" icon={Radio} color="from-emerald-500 to-emerald-600" link="/admin/signals" />
            <QuickAction label="Transactions" desc="Review deposits and withdrawals" icon={DollarSign} color="from-amber-500 to-amber-600" link="/admin/transactions" />
            <QuickAction label="Licenses" desc="Manage member licenses" icon={Award} color="from-purple-500 to-purple-600" link="/admin/licenses" />
            <QuickAction label="Admin Cleanup" desc="Review flagged items and pending actions" icon={Shield} color="from-red-500 to-rose-600" link="/admin/cleanup" />
          </div>
        </div>

        {/* Analytics & Tools */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">Analytics & Tools</h2>
          <div className="space-y-2">
            <QuickAction label="Team Analytics" desc="View performance insights and reports" icon={BarChart3} color="from-teal-500 to-teal-600" link="/admin/analytics" />
            <QuickAction label="Referral Tree" desc="View and manage referral network" icon={TrendingUp} color="from-pink-500 to-rose-600" link="/admin/referrals" />
            <QuickAction label="Rewards Admin" desc="Manage points, badges, and leaderboard" icon={Award} color="from-amber-500 to-amber-600" link="/admin/rewards" />
            <QuickAction label="Quiz Manager" desc="Generate and approve community quizzes" icon={HelpCircle} color="from-indigo-500 to-indigo-600" link="/admin/quizzes" />
          </div>
        </div>

        {/* AI & Platform */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">AI & Platform</h2>
          <div className="space-y-2">
            <QuickAction label="AI Training Center" desc="Configure and train the adaptive AI assistant" icon={BrainCircuit} color="from-violet-500 to-violet-600" link="/admin/ai-training" />
            <QuickAction label="Platform Settings" desc="Configure appearance, features, and branding" icon={Settings} color="from-zinc-500 to-zinc-600" link="/admin/settings" />
          </div>

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

        {/* System */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-widest">System</h2>
          <div className="space-y-2">
            <QuickAction label="System Check" desc="Run integrity checks and validations" icon={Shield} color="from-red-500 to-red-600" link="/admin/system-check" />
            <QuickAction label="System Health" desc="Monitor server and database status" icon={Activity} color="from-cyan-500 to-cyan-600" link="/admin/system-health" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage;
